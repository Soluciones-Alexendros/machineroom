# Arch / Omarchy packaging

Native packaging for Arch-family systems (`pacman`, `makepkg`, AUR) and for
Omarchy desktop applications that must appear in the launcher.

## `PKGBUILD` structure

```bash
pkgname=myapp
pkgver=1.2.3
pkgrel=1
pkgdesc="One-line description"
arch=('x86_64' 'aarch64')
url="https://example.invalid"
license=('MIT')
depends=('glibc' 'gtk4')
makedepends=('cmake' 'ninja')
optdepends=('ffmpeg: video export')
source=("$pkgname-$pkgver.tar.gz::https://example.invalid/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
  cd "$pkgname-$pkgver"
  cmake -B build -S . -DCMAKE_BUILD_TYPE=None -DCMAKE_INSTALL_PREFIX=/usr
  cmake --build build
}

package() {
  cd "$pkgname-$pkgver"
  DESTDIR="$pkgdir" cmake --install build
}
```

Rules that matter:

- `pkgrel` increments on packaging changes, not on upstream version changes.
- `source` URLs must be pinned to an immutable artifact; `sha256sums` never
  `SKIP` for release packages (only acceptable for VCS sources, which then need
  `pkgver()` and a `-git` suffix).
- `depends` are runtime, `makedepends` build-only, `optdepends` optional features
  with a description after the colon.
- `$pkgdir` is the packaging root; everything must go through `DESTDIR="$pkgdir"`.
  Writing outside it corrupts the build environment.
- Never install into `/usr/local` from a package; that path belongs to the admin.

## Build and verify

```bash
makepkg -Cfsi          # clean build, sync deps, install
makepkg --verifysource # check sums before trusting
namcap PKGBUILD        # packaging lints
namcap myapp-*.pkg.tar.zst  # binary lints (deps, paths, permissions)
```

- `makepkg` refuses to build as root by design. Build in a clean chroot
  (`devtools`, `extra-x86_64-build`) when the dependencies must be honest.
- `namcap` findings about unused/missing deps are the main real-world defect;
  resolve them, do not suppress them.

## AUR submission

- AUR hosts `PKGBUILD`s, not binaries. `pkgname` for a release package, `-git`/
  `-bin` suffixes for variants.
- `.SRCINFO` is generated (`makepkg --printsrcinfo > .SRCINFO`) and must be
  committed; a stale `.SRCINFO` blocks adoption.
- No `sudo`, no network in `build()`/`package()`, no self-updating logic.
- Adopt/co-maintain rules apply; never silently take over an orphan without the
  documented process.

## Omarchy desktop application

An Omarchy app is a normal compiled binary plus a launcher entry; the packaging
is what makes it visible and themable.

1. Build into one binary (`/usr/bin/<app>`).
2. Ship `<app>.desktop` into `/usr/share/applications/` with `Name`, `Exec`,
   `Icon`, `Categories`.
3. Ship icons under `/usr/share/icons/hicolor/<size>/apps/`.
4. Follow the desktop theme at runtime (read the active theme, do not hardcode
   colors); the app must restyle without a rebuild.
5. Install as a package so the launcher picks it up, not as a stray binary in
   `$HOME`.

## Verification checklist

- [ ] `makepkg -Cfsi` builds and installs cleanly in a clean chroot.
- [ ] `namcap` clean on `PKGBUILD` and on the built package.
- [ ] `sha256sums` real for release packages.
- [ ] `pacman -Ql` file list matches intent; no files under `/usr/local`.
- [ ] `pacman -Rns` removes the package and owned files.
- [ ] For AUR: `.SRCINFO` regenerated and committed.
- [ ] For Omarchy: `.desktop` + icons present, launcher entry appears, theme
      follows the system.
