# Debian / Ubuntu packaging

Native packaging for Debian-family distributions. Targets `dpkg`, `apt` and PPA
distribution.

## `debian/` layout

```text
debian/
  control          # binary and source package metadata
  rules            # build recipe (executable, makefile syntax)
  changelog        # Debian changelog (dpkg format, not Keep a Changelog)
  copyright        # machine-readable copyright + license
  compat           # debhelper compat level (or Build-Depends: debhelper-compat)
  install          # files to install per package
  source/format    # 3.0 (quilt) or 3.0 (native)
  patches/         # only with 3.0 (quilt)
  postinst prerm postrm preinst   # maintainer scripts, only when justified
```

Generate the skeleton with `dh_make` and remove what does not apply; a copied
template with unused stanzas is a smell.

## `debian/control`

Two stanzas minimum: source and binary.

```text
Source: myapp
Section: utils
Priority: optional
Maintainer: Name <email>
Build-Depends: debhelper-compat (= 13), <build tool deps>
Standards-Version: <current Debian policy version>
Homepage: https://example.invalid

Package: myapp
Architecture: any
Depends: ${shlibs:Depends}, ${misc:Depends}
Description: one-line summary
 Longer description, indented by one space.
```

Rules that matter:

- `Depends` lists hard runtime requirements; `Recommends` is installed by default
  and should still degrade; `Suggests` is optional. Do not put optional features
  in `Depends`.
- `${shlibs:Depends}` comes from actual linked libraries. Hand-writing library
  versions drifts.
- `Architecture: any` for compiled packages, `all` for scripts/docs.
- Description first line is a summary, not a repeat of the package name.

## `debian/rules`

Modern minimal form with `dh`:

```make
#!/usr/bin/make -f
%:
	dh $@
```

Override only what the upstream build needs (`override_dh_auto_configure`,
`override_dh_auto_build`, `override_dh_auto_install`). Every override is a
deviation from the default that a reviewer must be able to justify.

## Maintainer scripts

`postinst`/`prerm`/`postrm` run as root and are the highest-risk part of a
package. Rules:

- Idempotent: re-running must not corrupt state.
- Never start a long-running service synchronously; use `deb-systemd-helper` /
  `deb-systemd-invoke` semantics.
- Never download or execute remote content.
- Guard with `[ -x /usr/bin/x ]` style checks when calling external tools.
- If the script is empty or trivial, delete it.

## Quality gates

- `lintian` clean or every tag explained.
- `dpkg-buildpackage -b -us -uc` reproducible in a clean chroot (`pbuilder`,
  `sbuild`, or a container).
- `dpkg -c` shows exactly the expected file list; no build residue, no `.git`.
- `dpkg -i` → run → `apt remove` → `apt purge` leaves no owned files.

## PPA and repository distribution

- A PPA is Ubuntu-specific and needs source packages for each supported series;
  decide the series matrix before promising it.
- For a private/self-hosted `apt` repository: sign `Release` (`InRelease`), pin
  the key, and document key rotation.
- Keep `debian/changelog` version and the upstream tag in sync; a mismatch is the
  most common packaging break.

## Verification checklist

- [ ] `debian/control` deps match real runtime needs (`${shlibs:Depends}` used).
- [ ] `debian/rules` has no unexplained override.
- [ ] Maintainer scripts idempotent, root-safe, no network.
- [ ] `lintian` clean or tags justified.
- [ ] Install → run → remove → purge round trip verified.
- [ ] Package built in a clean chroot, not on the dev machine.
