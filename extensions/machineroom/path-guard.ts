/**
 * path-guard — write/edit gate.
 *
 * Allowed without a prompt:
 *   - the directory Pi was launched in, and every subdirectory of it
 *   - ~/Work/ and its subdirectories
 *   - the explicit /tmp prefixes used by installers and tests
 *
 * Still blocked inside those trees: credential stores (~/.ssh, ~/.gnupg,
 * ~/.aws, ~/.kube, auth.json, mcp-auth.json). A symlink is judged by its
 * real path, so a link inside the launch directory cannot reach them.
 *
 * Everywhere else stays fail-closed: hard paths block, configuration files
 * confirm when a UI exists, and any other path asks or blocks.
 *
 * `decidePath` is the pure decision surface. The event handler only maps
 * its verdict back to the Pi tool pipeline.
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { existsSync, realpathSync } from "node:fs";
import { homedir } from "node:os";
import { basename, dirname, isAbsolute, resolve, sep } from "node:path";

export type Verdict = "allow" | "block" | "confirm";

export interface PathDecision {
  verdict: Verdict;
  reason?: string;
}

export interface PathGuardOptions {
  home?: string;
  work?: string;
  cwd?: string;
  hasUI?: boolean;
  allowPrefixes?: string[];
}

const SECRET_DIRS = [".ssh", ".gnupg", ".aws", ".kube"];
const HARD_DIRS = [".machineroom"];
const HARD_SEGMENTS = [".env", ".git", "node_modules"];
const CONFIRM_FILES = [
  [".pi", "agent", "settings.json"],
  [".pi", "agent", "mcp.json"],
  [".pi", "agent", "AGENTS.md"],
  [".bashrc"],
  [".bash_aliases"],
  [".profile"],
  [".config", "git", "ignore"],
  [".config", "gh", "hosts.yml"],
];
const DEFAULT_ALLOW_PREFIXES = ["/tmp/machineroom-", "/tmp/test-", "/tmp/ai-"];

function inside(root: string, target: string): boolean {
  const base = resolve(root);
  return target === base || target.startsWith(base + sep);
}

function expandHome(requested: string, home: string): string {
  if (requested === "~") return home;
  if (requested.startsWith("~/")) return resolve(home, requested.slice(2));
  return requested;
}

/** Resolve `..` and, when any ancestor exists, the real path behind symlinks. */
function canonicalize(absolute: string): string {
  let cursor = absolute;
  const suffix: string[] = [];
  while (!existsSync(cursor)) {
    const parent = dirname(cursor);
    if (parent === cursor) break;
    suffix.push(basename(cursor));
    cursor = parent;
  }
  if (existsSync(cursor)) {
    try {
      cursor = realpathSync(cursor);
    } catch {
      // Keep the resolved path when the kernel refuses the lookup.
    }
  }
  return suffix.length === 0 ? cursor : resolve(cursor, ...suffix.reverse());
}

export function decidePath(
  requested: string,
  options: PathGuardOptions = {}
): PathDecision {
  const home = options.home ?? homedir();
  const work = options.work ?? resolve(home, "Work");
  const cwd = options.cwd ?? "";
  const hasUI = options.hasUI ?? false;
  const allowPrefixes = options.allowPrefixes ?? DEFAULT_ALLOW_PREFIXES;

  const expanded = expandHome(requested, home);
  const absolute = isAbsolute(expanded)
    ? resolve(expanded)
    : resolve(cwd || process.cwd(), expanded);
  const target = canonicalize(absolute);

  const block = (reason: string): PathDecision => ({
    verdict: "block",
    reason,
  });
  const confirm = (reason: string): PathDecision =>
    hasUI ? { verdict: "confirm", reason } : block(`${reason} (no UI)`);

  if (target === home) {
    return block("refusing to write to the home root");
  }

  const secretDirs = SECRET_DIRS.map((dir) => resolve(home, dir));
  const secretFiles = [
    resolve(home, ".pi", "agent", "auth.json"),
    resolve(home, ".pi", "agent", "mcp-auth.json"),
  ];
  if (
    secretFiles.includes(target) ||
    secretDirs.some((dir) => target === dir || target.startsWith(dir + sep))
  ) {
    return block(
      "protected credential path; do not retry with variants, ask the operator"
    );
  }

  const launch = cwd ? resolve(cwd) : "";
  const openedByLaunch = launch !== "" && inside(launch, target);
  const openedByWork = inside(work, target);
  const openedByPrefix = allowPrefixes.some((prefix) =>
    target.startsWith(resolve(prefix))
  );
  if (openedByLaunch || openedByWork || openedByPrefix) {
    return { verdict: "allow" };
  }

  const hardDirs = [
    ...HARD_DIRS.map((dir) => resolve(home, dir)),
    resolve(home, ".pi", "agent", "extensions"),
    resolve(home, ".config", "hypr"),
  ];
  const confirmFiles = new Set(
    CONFIRM_FILES.map((parts) => resolve(home, ...parts))
  );

  if (HARD_SEGMENTS.some((segment) => target.split(sep).includes(segment))) {
    return block(
      "protected path segment; do not retry with ~, .. or symlinks, ask the operator"
    );
  }
  if (hardDirs.some((dir) => target === dir || target.startsWith(dir + sep))) {
    return block(
      "protected path; do not retry with variants, ask the operator"
    );
  }
  if (confirmFiles.has(target)) {
    return confirm("editing a configuration file");
  }
  return confirm(
    "path outside the launch directory and ~/Work requires confirmation"
  );
}

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "write" && event.toolName !== "edit")
      return undefined;
    const requested = String((event.input as { path?: unknown })?.path ?? "");
    const decision = decidePath(requested, { hasUI: ctx.hasUI, cwd: ctx.cwd });

    if (decision.verdict === "allow") return undefined;

    const reason = `path-guard: ${decision.reason}: ${requested}`;
    if (decision.verdict === "block") {
      if (ctx.hasUI)
        ctx.ui.notify(`Blocked protected path: ${requested}`, "warning");
      return { block: true, reason };
    }
    if (!ctx.hasUI) {
      return { block: true, reason: `${reason} (no UI to confirm)` };
    }
    const ok = await ctx.ui.confirm(
      "Write outside the launch directory and ~/Work?",
      requested
    );
    if (!ok)
      return {
        block: true,
        reason: `path-guard: blocked by the operator: ${requested}`,
      };
    return undefined;
  });
}
