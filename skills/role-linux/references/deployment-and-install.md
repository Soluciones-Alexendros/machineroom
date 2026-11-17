# Build, deployment and installation

The artifact is not shipped until it can be built reproducibly, deployed
predictably, installed idempotently and removed cleanly.

## Build

- **Reproducible:** no timestamps, absolute paths or build-host identifiers
  embedded in the artifact. Set `SOURCE_DATE_EPOCH` where the toolchain honours
  it.
- **Staged:** always install into a staging root (`DESTDIR`, `$pkgdir`,
  `--prefix` + `DESTDIR`) so the file list is inspectable before it touches a
  live system.
- **Minimal:** build dependencies must not leak into the runtime dependency set.
- **Named:** artifact name carries version and architecture
  (`myapp-1.2.3-x86_64.pkg.tar.zst`, `myapp_1.2.3_amd64.deb`) so a stale file is
  detectable.

Produce a file list (`dpkg -c`, `pacman -Ql`, or the staged tree) and treat it as
the contract of the deployment.

## Filesystem placement

| Content | Location |
| --- | --- |
| Executables | `/usr/bin` |
| Architecture-independent data | `/usr/share/<app>` |
| Libraries (shared) | `/usr/lib` |
| Documentation and licenses | `/usr/share/doc/<app>` |
| systemd user units | `/usr/lib/systemd/user` |
| `.desktop` entries | `/usr/share/applications` |
| Icons | `/usr/share/icons/hicolor/<size>/apps` |

Never `/usr/local` from a package, never `$HOME` from a package, never a path
outside the staging root.

## Deployment

- **Scope:** decide system-wide vs per-user before packaging. A per-user install
  must not write to `/usr`.
- **Upgrade path:** an upgrade replaces files and must not duplicate
  configuration. Ship defaults in `/usr/share` and never overwrite user config.
- **Configuration:** read from `/etc/<app>` (system) or
  `${XDG_CONFIG_HOME:-$HOME/.config}/<app>` (user). Do not mix.
- **State:** caches in `${XDG_CACHE_HOME}`, data in `${XDG_DATA_HOME}`, runtime in
  `${XDG_RUNTIME_DIR}`. Hardcoded `~/.myapp` is a defect.

## Installation

An installer must be:

1. **Idempotent** — running twice equals running once.
2. **Verifiable** — ends with a check (version output, file presence, service
   state) that can fail loudly.
3. **Reversible** — documents and implements uninstall.
4. **Non-interactive** where possible; prompts break automation.

For a script-based install, keep it thin: it should select the right native
package, not reimplement packaging.

## Deploy vs release

This role produces the artifact and its install path. Tagging, changelog,
publication and merge-watch belong to `project-status`. Conflating them is how
"it deployed" gets mistaken for "it was released with evidence".

## Verification checklist

- [ ] Build reproducible in a clean environment; no host paths embedded.
- [ ] Staged file list matches the documented placement table.
- [ ] Install twice in a row produces the same system state.
- [ ] Installer ends with a verifiable check.
- [ ] Upgrade preserves user configuration.
- [ ] Uninstall removes every owned file and no foreign one.
- [ ] No writes to `/usr/local`, `$HOME` or outside the staging root during
      build.
