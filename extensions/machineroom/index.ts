import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import {
  SPAWN_ATTEMPTS,
  backoffMs,
  buildSubagentArgs,
  runPiOnce,
  shouldRetrySpawn,
  spawnResult,
} from "./call.ts";
import { decideWithFallback, loadMatcher } from "./gates.ts";
import { loadModelScope, resolveSubagentModel } from "./model-scope.ts";

const STATUS_COMMAND = "/mr-status";
const SUBAGENT_TOOL = "mr_subagent";

/**
 * Skills the isolated subagent may load by default.
 *
 * The set is a least-privilege subset of the catalog: implementation, planning
 * and self-audit only. Host mutation (`local-*`), status/hygiene/release
 * (`project-status`) and web audits are excluded because they need explicit
 * operator consent in the coordinator session. Override with
 * `MACHINEROOM_SUBAGENT_SKILLS=comma,list`.
 */
const DEFAULT_ALLOWED_SKILLS = [
  "plan-testing",
  "plan-specification",
  "project-machineroom",
  "role-back",
  "role-clean-code",
  "role-front",
  "role-linux",
] as const;

const DEFAULT_TIMEOUT_SECONDS = 300;

function allowedSkills(env: NodeJS.ProcessEnv = process.env): Set<string> {
  const raw = (env.MACHINEROOM_SUBAGENT_SKILLS ?? "").trim();
  const list = raw
    ? raw
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean)
    : [...DEFAULT_ALLOWED_SKILLS];
  return new Set(list);
}

function allowedCwd(candidate: string, parent: string): boolean {
  const resolved = path.resolve(candidate);
  const root = path.resolve(parent);
  return (
    resolved === root ||
    resolved.startsWith(root + path.sep) ||
    resolved.startsWith("/tmp/machineroom-")
  );
}

function rejected(detail: string) {
  return {
    content: [{ type: "text", text: detail }],
    details: {
      outcome: "blocked",
      exitCode: null,
      output: "",
      detail: `mr_subagent input: ${detail}`,
      reconciliationRequired: false,
    },
    isError: true,
  };
}

function policyRoot(): string {
  // Installed layout: <runtime>/extensions/machineroom/index.ts
  const extensionDir = path.dirname(
    fs.realpathSync(fileURLToPath(import.meta.url))
  );
  return path.resolve(extensionDir, "..", "..");
}

function shellPrefilter(command: string): {
  kind: "skip" | "enter" | "closed";
  reason: string;
} {
  try {
    const matched = loadMatcher(policyRoot()).test(command);
    return { kind: matched ? "enter" : "skip", reason: "" };
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    return { kind: "closed", reason: `shell gate: ${detail}` };
  }
}

export default function machineroom(pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "bash") return undefined;
    const command = String(
      (event.input as { command?: unknown })?.command ?? ""
    );
    const gate = shellPrefilter(command);
    if (gate.kind === "skip") return undefined;
    if (gate.kind === "closed") return { block: true, reason: gate.reason };
    const decision = decideWithFallback(command, policyRoot());
    if (decision.permission === "allow") return undefined;
    if (decision.permission === "deny") {
      if (ctx.hasUI) ctx.ui.notify(decision.user_message, "warning");
      return { block: true, reason: decision.agent_message };
    }
    if (!ctx.hasUI)
      return {
        block: true,
        reason: `${decision.agent_message} (no UI to confirm)`,
      };
    const ok = await ctx.ui.confirm(
      decision.user_message,
      command.slice(0, 500)
    );
    return ok ? undefined : { block: true, reason: decision.agent_message };
  });

  pi.on("user_bash", async (event, ctx) => {
    const command = String((event as { command?: unknown })?.command ?? "");
    const gate = shellPrefilter(command);
    if (gate.kind === "skip") return undefined;
    if (gate.kind === "closed") {
      return {
        result: {
          output: `${gate.reason}\n`,
          exitCode: 1,
          cancelled: true,
          truncated: false,
        },
      };
    }
    const decision = decideWithFallback(command, policyRoot());
    if (decision.permission === "allow") return undefined;
    return {
      result: {
        output: `shell gate: ${decision.permission} — ${decision.agent_message}
`,
        exitCode: 1,
        cancelled: true,
        truncated: false,
      },
    };
  });

  pi.registerCommand("mr-status", {
    description: "Confirm that the machineroom Pi extension is loaded",
    async handler(_args, ctx) {
      ctx.ui.notify(`machineroom extension loaded (${STATUS_COMMAND})`, "info");
    },
  });

  pi.registerTool({
    name: SUBAGENT_TOOL,
    label: "Machineroom subagent",
    description:
      "Execute one bounded task in an isolated Pi process. The coordinator remains responsible for verification.",
    parameters: Type.Object({
      skill: Type.String(),
      task: Type.String(),
      cwd: Type.Optional(Type.String()),
      write: Type.Optional(Type.Boolean()),
      allow_bash: Type.Optional(Type.Boolean()),
      timeout_seconds: Type.Optional(
        Type.Integer({ minimum: 1, maximum: 3600 })
      ),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      if (!allowedSkills().has(params.skill)) {
        return rejected(`skill not allowed: ${params.skill}`);
      }
      const cwd = path.resolve(params.cwd ?? ctx.cwd);
      if (!allowedCwd(cwd, ctx.cwd)) {
        return rejected(
          `cwd outside authorized workspace/worktree roots: ${cwd}`
        );
      }
      const tools = ["read", "grep", "find", "ls"];
      if (params.write) tools.push("write", "edit");
      if (params.allow_bash) tools.push("bash");
      // Follow symlink when installed as ~/.pi/agent/extensions/machineroom.ts
      const extensionDir = path.dirname(
        fs.realpathSync(fileURLToPath(import.meta.url))
      );
      const worker = path.join(extensionDir, "agents", "worker.md");
      let model: string;
      try {
        model = resolveSubagentModel(
          process.env.MR_PI_MODEL,
          loadModelScope(policyRoot())
        );
      } catch (error) {
        const detail = error instanceof Error ? error.message : String(error);
        return rejected(detail);
      }
      const args = buildSubagentArgs({
        tools,
        worker,
        skill: params.skill,
        task: params.task,
        model,
      });
      const timeoutMs =
        (params.timeout_seconds ?? DEFAULT_TIMEOUT_SECONDS) * 1000;
      let state: Awaited<ReturnType<typeof runPiOnce>> | undefined;
      for (let attempt = 0; attempt < SPAWN_ATTEMPTS; attempt += 1) {
        state = await runPiOnce(args, cwd, timeoutMs, signal);
        if (
          !shouldRetrySpawn({
            attempt,
            attempts: SPAWN_ATTEMPTS,
            timedOut: state.timedOut,
            aborted: state.aborted,
            stdout: state.stdout,
            exitCode: state.exitCode,
          })
        ) {
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, backoffMs(attempt)));
      }
      if (!state) return rejected("mr_subagent execute: no spawn result");
      return spawnResult(state);
    },
  });
}
