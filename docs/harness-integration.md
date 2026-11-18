# Harness integration status

Cursor, OpenCode (V2) and Pi are the supported harnesses. All sit at level A: the deterministic symlink gate. CI does not require any harness binary.

| Harness  | Level | Evidence                                                                        |
| -------- | ----- | ------------------------------------------------------------------------------- |
| Cursor   | A     | `bash scripts/install-cursor.sh --target <dir>` symlinks each `skills/<name>`   |
| OpenCode | A     | `bash scripts/install-opencode.sh --target <dir>` symlinks each `skills/<name>` |
| Pi       | A     | `bash scripts/install-pi.sh --target <dir>` symlinks each `skills/<name>`       |

## Level A

- Symlinks are absolute and resolve to `skills/<name>`.
- `--target` does not write `$HOME`. `--user` is the only path that writes the user skills directory.
- Dry-run creates neither the destination nor the manifest.
- `scripts/tests/test_install.sh` and `scripts/tests/test_execution_e2e.sh` cover the gate. The E2E script does not invoke a harness binary.

## OpenCode contract surfaces

- Project skills: `<project>/.opencode/skills/<name>/SKILL.md` (absolute links).
- User skills: `${XDG_CONFIG_HOME:-$HOME/.config}/opencode/skills/<name>/SKILL.md` (relative links from a verified `$HOME/.machineroom` runtime).
- `scripts/install.sh --harness opencode` is the AI wrapper; `--components full` is rejected because OpenCode has no versioned hooks/rules/agents in this repository.
- `uv run --project tools python3 tools/harness/doctor.py --harness opencode --json` verifies level A links plus `opencode-source-collision`. An explicit `skills` entry in `opencode.json` wins by precedence, so a second catalog with the same ids is a `fail`, never a silent shadow.
- OpenCode V2 ignores frontmatter `compatibility` and `allowed-tools`; it derives skill ids from paths. `disable-model-invocation: true` behaves as `opencode/autoinvoke: false` and is kept on host-mutating skills.
- Level B is opt-in only: `MR_OPENCODE_NATIVE_OPT_IN=1` plus a real OpenCode V2 binary. The check calls `opencode api get /api/skill` and requires all 14 catalog ids. Without the binary or opt-in it reports `not_run` (exit 3); a V1 binary is `blocked`. The CLI talks to the operator's running service, so B proves discovery in the active context, not the provenance of a specific target — source links are proven by level A. `scripts/tests/test_opencode_native.sh` covers A/B and both negative lanes.
- Level C (permissions) is out of scope: loading a skill does not authorize Bash, network, secrets or paths outside the project. No permission widening is installed.

## Cursor contract surfaces

Versioned under `.cursor/` (skills symlinks are **not** committed; run `install-cursor.sh`):

- `.cursor/rules/machineroom.mdc` (`alwaysApply: true`)
- `.cursor/hooks.json`, `.cursor/hooks/session_start.py`, `.cursor/hooks/shell_gate.py`
- `.cursor/agents/mr-verifier.md`
- `tools/validate/tests/test_shell_gate.py`

Surfaces are scope-aware under `--user`: the catalog is `$HOME/.machineroom`, and every owned path under `~/.cursor` / `~/.pi/agent` is a relative symlink into that runtime. The project rule is omitted because Cursor keeps user rules in Settings. `hooks.json` is rewritten in the runtime with `hooks/...` commands (user hooks run from `~/.cursor`) and linked from `~/.cursor/hooks.json`. `doctor.py --full` accepts both scopes.

Levels beyond A:

- **B (native discovery/load):** Customize → Skills lists all 14; `/project-status` routes. Human IDE only → **`not_run` in CI**.
- **C (shell gate in IDE):** an agent-proposed host-mutating shell (e.g. `apt-get upgrade`) is `deny` or `ask`. The `beforeShellExecution` matcher is whole-word, so it covers host mutation and outbound network only; ordinary commands (`python`, `git`, `npm`, `pytest`) stay open even when their text contains substrings such as `chapter`, `adapter` or `curly`. Human IDE only → **`not_run` in CI**.

## Pi model scope

Product calls (orchestrator, `PiSubagentAdapter`, and the extension's `mr_subagent`)
pass `--model` from `extensions/machineroom/model-scope.json`. The default is
`opencode-go/deepseek-v4.1-flash`. The keep set is that model,
`opencode-go/deepseek-v4-pro`, free OpenCode models (`opencode/*free*`) and NVIDIA
Nemotron models (`nvidia/*nemotron*`). `MR_PI_MODEL` may select another kept model.
A reference outside the scope fails before a process starts. Interactive Pi still
applies the same keep set through the operator's `enabledModels`.

## Permissions

Loading a skill does not authorize Bash, network, secrets, or paths outside the project, in any harness. Product restrictions (`DenyProvider`, `run_registered`, evidence binding) remain even when the harness can load the skill file. OpenCode V2 permission rules in `opencode.json` are operator-owned and are never written by these installers.

## Execution API (product)

- Callers use `run_registered(operation_id, params)` only. Free-form `run_operation(..., argv=..., effect=...)` is rejected.
- Evidence uses content digests (SHA-256 of bytes), UUID `run_id`, and phase/skill/target binding before `--complete`.
- Status advances under a full read→validate→write lock with idempotent replay of the same `run_id`.

## MCP servers (canonical list)

Secrets never live in this repository. Every entry that needs a token, header or
OAuth session is declared in the **user** files (`~/.pi/agent/mcp.json`,
`~/.cursor/mcp.json`), never in `.pi/mcp.json` or `.cursor/mcp.json` committed
here. `.pi/mcp.json` is optional and may only declare servers with no secret.

| Server            | Secrets         | Pi exposure | Purpose                                                |
| ----------------- | --------------- | ----------- | ------------------------------------------------------ |
| `github`          | `gh auth token` | `deferred`  | Repos, PRs, issues, Actions logs, secret scanning      |
| `context7`        | none            | `codemode`  | Up-to-date library/framework docs                      |
| `playwright`      | none            | `codemode`  | Browser driving: a11y snapshot, clicks, screenshots    |
| `chrome-devtools` | none            | `codemode`  | Performance traces, Core Web Vitals, network waterfall |
| `notion`          | OAuth           | `deferred`  | Workspace search, pages, databases, comments           |

Rules:

- Exposure is `codemode` by default so tools are reached from scripts; `deferred`
  keeps large servers behind `tool_search`. Set `toolExposure` per tool to make a
  few direct and to hide destructive ones (`delete_file`, `fork_repository`, ...).
- Pi reads `~/.pi/agent/mcp.json` (user) and `.pi/mcp.json` (project, trusted
  only). Cursor reads `~/.cursor/mcp.json` (user). Aligning Cursor is a host
  step: it is not part of this repository's diff.
- Documenting a server here does not authorize it. Network access still needs
  the operator's approval through the execution layer.
- Verify with `pi mcp list` (Pi) or Customize → MCP (Cursor). Both are
  `not_run` in CI: a local client is required.
