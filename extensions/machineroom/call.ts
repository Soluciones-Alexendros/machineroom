/**
 * Outbound Pi subagent call: argv shape, one-shot process settlement and retry.
 *
 * Retry only a process that exits before writing stdout. A timeout, a cancel,
 * or any model output is final — the call may already have written files.
 */
import { spawn } from "node:child_process";

export const SPAWN_ATTEMPTS = 3;
export const SPAWN_BASE_DELAY_MS = 200;
export const SPAWN_DELAY_CAP_MS = 2000;

export interface SpawnRetryState {
  attempt: number;
  attempts: number;
  timedOut: boolean;
  aborted: boolean;
  stdout: string;
  exitCode: number;
}

/** Same exit code the Python adapter records when the call runs out of time. */
export const TIMEOUT_EXIT_CODE = 124;

export interface OpenSpawn {
  settled: boolean;
  exitCode: number;
  stdout: string;
  timedOut: boolean;
  aborted: boolean;
  closes: number;
}

export type SpawnNotice =
  | { kind: "output"; text: string }
  | { kind: "error" }
  | { kind: "close"; code: number | null }
  | { kind: "timeout" }
  | { kind: "abort" };

export function openSpawn(): OpenSpawn {
  return {
    settled: false,
    exitCode: 1,
    stdout: "",
    timedOut: false,
    aborted: false,
    closes: 0,
  };
}

/**
 * Record one notice from the child process.
 * An error does not finish the call: the close that follows still carries the
 * output. A second close, or anything after a timeout or cancel, is ignored.
 */
export function noteSpawn(state: OpenSpawn, notice: SpawnNotice): OpenSpawn {
  if (state.settled) return state;
  if (notice.kind === "output") {
    return { ...state, stdout: state.stdout + notice.text };
  }
  if (notice.kind === "error") return state;
  if (notice.kind === "timeout") {
    return {
      ...state,
      settled: true,
      timedOut: true,
      exitCode: TIMEOUT_EXIT_CODE,
    };
  }
  if (notice.kind === "abort") {
    return { ...state, settled: true, aborted: true, exitCode: 1 };
  }
  return { ...state, settled: true, exitCode: notice.code ?? 1, closes: 1 };
}

export function shouldRetrySpawn(state: SpawnRetryState): boolean {
  if (state.attempt + 1 >= state.attempts) return false;
  if (state.timedOut || state.aborted) return false;
  if (state.stdout.trim()) return false;
  return state.exitCode !== 0;
}

export function backoffMs(
  attempt: number,
  baseMs = SPAWN_BASE_DELAY_MS,
  capMs = SPAWN_DELAY_CAP_MS
): number {
  const shift = attempt < 0 ? 0 : attempt;
  const delay = baseMs * 2 ** shift;
  return delay > capMs ? capMs : delay;
}

export function buildSubagentArgs(input: {
  tools: string[];
  worker: string;
  skill: string;
  task: string;
  model: string;
}): string[] {
  return [
    "--mode",
    "json",
    "-p",
    "--no-session",
    "--tools",
    input.tools.join(","),
    "--append-system-prompt",
    input.worker,
    "--model",
    input.model,
    `/skill:${input.skill}\n\nExecute exactly this task packet:\n${input.task}`,
  ];
}

const OUTPUT_CAP = 50 * 1024;

export interface PiSpawnState {
  events: any[];
  stderr: string;
  parseError: string;
  timedOut: boolean;
  aborted: boolean;
  exitCode: number;
  stdout: string;
}

function killChild(child: ReturnType<typeof spawn>): void {
  if (child.pid && process.platform !== "win32")
    process.kill(-child.pid, "SIGKILL");
  else child.kill("SIGKILL");
}

function eventsFromStdout(stdout: string): {
  events: any[];
  parseError: string;
} {
  const events: any[] = [];
  let parseError = "";
  for (const line of stdout.split("\n")) {
    if (!line.trim()) continue;
    try {
      events.push(JSON.parse(line));
    } catch {
      parseError = "invalid Pi JSONL";
    }
  }
  return { events, parseError };
}

function stateFrom(noted: OpenSpawn, stderr: string): PiSpawnState {
  const parsed = eventsFromStdout(noted.stdout);
  return {
    events: parsed.events,
    stderr,
    parseError: parsed.parseError,
    timedOut: noted.timedOut,
    aborted: noted.aborted,
    exitCode: noted.exitCode,
    stdout: noted.stdout,
  };
}

/** Run one Pi process. The timer exists before the process, and the call settles once. */
export function runPiOnce(
  args: string[],
  cwd: string,
  timeoutMs: number,
  signal: AbortSignal | undefined
): Promise<PiSpawnState> {
  if (signal?.aborted) {
    return Promise.resolve(
      stateFrom(noteSpawn(openSpawn(), { kind: "abort" }), "")
    );
  }
  return new Promise((resolve) => {
    let noted = openSpawn();
    let stderr = "";
    let child: ReturnType<typeof spawn> | undefined;
    let onAbort = () => {};
    const settle = (next: OpenSpawn) => {
      if (noted.settled) return;
      noted = next;
      if (!noted.settled) return;
      clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
      resolve(stateFrom(noted, stderr));
    };
    const timer = setTimeout(() => {
      settle(noteSpawn(noted, { kind: "timeout" }));
      if (child) killChild(child);
    }, timeoutMs);
    onAbort = () => {
      settle(noteSpawn(noted, { kind: "abort" }));
      if (child) killChild(child);
    };
    child = spawn("pi", args, {
      cwd,
      shell: false,
      detached: process.platform !== "win32",
      stdio: ["ignore", "pipe", "pipe"],
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.stdout.on("data", (chunk) => {
      noted = noteSpawn(noted, { kind: "output", text: chunk.toString() });
    });
    signal?.addEventListener("abort", onAbort, { once: true });
    child.on("error", () => {
      noted = noteSpawn(noted, { kind: "error" });
    });
    child.on("close", (code) => {
      settle(noteSpawn(noted, { kind: "close", code }));
    });
  });
}

function finalText(events: any[]): string {
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const message = events[index]?.message;
    if (
      events[index]?.type === "message_end" &&
      message?.role === "assistant"
    ) {
      const text = (message.content ?? [])
        .filter((part: any) => part?.type === "text")
        .map((part: any) => part.text)
        .join("");
      if (text.length <= OUTPUT_CAP) return text;
      return `${text.slice(0, OUTPUT_CAP)}\n[output truncated]`;
    }
  }
  return "";
}

export function spawnResult(state: PiSpawnState) {
  const modelFailed = state.events.some((event) =>
    ["error", "aborted"].includes(event?.message?.stopReason)
  );
  const failed =
    state.parseError ||
    modelFailed ||
    state.timedOut ||
    state.aborted ||
    state.exitCode !== 0;
  const result = {
    outcome:
      state.timedOut || state.aborted
        ? "cancelled"
        : failed
          ? "failed"
          : "succeeded",
    exitCode: state.exitCode,
    output: finalText(state.events),
    detail: state.parseError
      ? `mr_subagent parse: ${state.parseError}`
      : `mr_subagent execute: ${state.stderr.slice(0, 2000)}`,
    reconciliationRequired: state.timedOut || state.aborted,
  };
  return {
    content: [{ type: "text", text: JSON.stringify(result) }],
    details: result,
    isError: result.outcome !== "succeeded",
  };
}
