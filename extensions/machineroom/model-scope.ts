/**
 * Pi model allowlist. Same file the Python orchestrator loads
 * (`model-scope.json`). `*` does not cross `/`.
 */
import fs from "node:fs";
import path from "node:path";

export interface ModelScope {
  defaultModel: string;
  patterns: string[];
}

const RELATIVE = path.join("extensions", "machineroom", "model-scope.json");
const GLOB = /[*?[\]]/;

export function loadModelScope(root: string): ModelScope {
  const raw = JSON.parse(
    fs.readFileSync(path.join(root, RELATIVE), "utf8")
  ) as { defaultModel?: unknown; patterns?: unknown };
  const defaultModel = String(raw.defaultModel ?? "").trim();
  if (
    !Array.isArray(raw.patterns) ||
    raw.patterns.length === 0 ||
    !defaultModel
  ) {
    throw new Error("model scope needs defaultModel and patterns");
  }
  const patterns = raw.patterns.map((item) => String(item).trim());
  if (patterns.some((item) => !item)) {
    throw new Error("model scope patterns must be non-empty strings");
  }
  const scope = { defaultModel, patterns };
  if (!modelInScope(defaultModel, scope)) {
    throw new Error(`default model is outside the scope: ${defaultModel}`);
  }
  return scope;
}

function globToRegExp(pattern: string): RegExp {
  let source = "^";
  for (const char of pattern) {
    source +=
      char === "*" ? "[^/]*" : char.replace(/[.+^${}()|[\]\\]/g, "\\$&");
  }
  return new RegExp(`${source}$`, "i");
}

/** True for one concrete provider/id. Glob characters in the reference are rejected. */
export function modelInScope(reference: string, scope: ModelScope): boolean {
  const candidate = reference.trim();
  if (!candidate || GLOB.test(candidate) || /\s/.test(candidate)) return false;
  const slash = candidate.indexOf("/");
  if (slash <= 0 || slash === candidate.length - 1) return false;
  const modelId = candidate.slice(slash + 1);
  for (const pattern of scope.patterns) {
    if (GLOB.test(pattern)) {
      const regex = globToRegExp(pattern);
      if (regex.test(candidate) || regex.test(modelId)) return true;
    } else if (candidate.toLowerCase() === pattern.toLowerCase()) {
      return true;
    }
  }
  return false;
}

/** Blank means the scope default. Anything outside the scope throws. */
export function resolveSubagentModel(
  raw: string | undefined,
  scope: ModelScope
): string {
  const candidate = (raw ?? "").trim();
  if (!candidate) return scope.defaultModel;
  if (!modelInScope(candidate, scope)) {
    throw new Error(`model out of scope: ${candidate}`);
  }
  return candidate;
}
