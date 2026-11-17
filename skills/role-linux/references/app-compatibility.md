# Compatibility and ABI — Linux application surface

What "works on Linux" means once you stop meaning "it compiled on my machine".

## Target contract

Declare, in the repository, exactly this and keep it honest:

| Claim | Evidence required |
| --- | --- |
| Supported distros and versions | CI matrix or a documented manual build log |
| glibc floor | `objdump -T`/`readelf` symbol versions of the built binary |
| Kernel feature floor | minimum version for each syscall/cgroup/namespace used |
| Desktop environment support | tested session (GNOME, KDE, Hyprland/Omarchy) |
| Architecture | `x86_64`, `aarch64`, packaged per target |

A distro list without evidence is a wish. If a target is untested, mark it
`not_run` with a reason instead of implying support.

## glibc and symbol versioning

- A binary built on a newer glibc does not run on an older one. Build on the
  oldest supported target, or pin the toolchain to that sysroot.
- `readelf --dyn-syms` and `objdump -T` show the `GLIBC_x.y` version tags
  actually required. Check the maximum, not the average.
- Static linking of glibc is not a portable answer (NSS, `dlopen`, locale paths).
  Prefer musl for static artifacts, or accept a glibc floor.

## Shared libraries vs vendored code

- **Shared from the distro** when the library has a stable ABI and a security
  owner in that distro. This keeps CVE response with the distro.
- **Vendored/bundled** when the library is unstable or the app cannot tolerate a
  distro upgrade. Bundling transfers CVE responsibility to you and must be
  declared in the SBOM.
- Never mix: a vendored copy that shadows the system one produces two versions
  in one process.

## Runtime degradation

Optional integrations (portals, tray, notifications, audio, GPU) must fail soft:

1. Detect availability.
2. Degrade to a documented alternative.
3. Tell the user once, without blocking the main flow.

A hard dependency on a desktop-only service breaks the CLI and headless case.

## Sandboxing and permissions

- Prefer portals (`xdg-desktop-portal`) over direct privileged access.
- Flatpak/Snap change the filesystem and ABI assumptions: paths, `$HOME`
  redirection, missing host libraries. Test inside the sandbox, not only on the
  host.
- Linux capabilities and `setuid` are a last resort; both are an audit surface.

## Verification checklist

- [ ] Build on the oldest supported distro/image succeeds.
- [ ] `readelf`/`objdump` glibc floor matches the declared contract.
- [ ] Binary runs with the minimal dependency set (no accidental dev packages).
- [ ] Optional features degrade with a clear message when absent.
- [ ] `ldd` shows no unresolved or accidental vendored paths.
- [ ] Uninstall/remove leaves no owned files behind.
