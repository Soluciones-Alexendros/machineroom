"""Checks on the built site directory, then writes the artifact fingerprint."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

EXCLUDED_SENTINEL = "Si se filtra un token de GitHub"
_TEXT = {".html", ".css", ".js", ".json", ".svg", ".txt", ".xml"}


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.inline_script = False
        self.inline_style = False
        self._script = False
        self._script_src = False
        self._script_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        found = {key: value for key, value in attrs}
        element_id = found.get("id")
        if element_id:
            self.ids.add(element_id)
        if tag == "a":
            href = found.get("href")
            if href:
                self.hrefs.append(href)
        if found.get("style") is not None:
            self.inline_style = True
        if tag == "style":
            self.inline_style = True
        if tag == "script":
            self._script = True
            self._script_src = found.get("src") is not None
            self._script_text = []

    def handle_data(self, data: str) -> None:
        if self._script:
            self._script_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._script:
            if "".join(self._script_text).strip() and not self._script_src:
                self.inline_script = True
            self._script = False


def contains_excluded_sentinel(root: Path) -> bool:
    """True when the excluded-doc phrase appears anywhere under ``root``."""
    if not root.exists():
        return False
    paths = [root] if root.is_file() else [path for path in root.rglob("*") if path.is_file()]
    return any(EXCLUDED_SENTINEL in path.read_bytes().decode("utf-8", errors="ignore") for path in paths)


def fingerprint_tree(dist: Path) -> str:
    """SHA-256 of every file except build-identity.json."""
    digest = hashlib.sha256()
    files = sorted(path for path in dist.rglob("*") if path.is_file() and path.name != "build-identity.json")
    for path in files:
        digest.update(path.relative_to(dist).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _html_files(dist: Path) -> list[Path]:
    return [path.resolve() for path in dist.rglob("*.html") if path.is_file()]


def _denylist_api() -> Any:
    path = Path(__file__).resolve().parents[1] / "validate" / "private_denylist.py"
    spec = importlib.util.spec_from_file_location("site_private_denylist", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("no se pudo cargar private_denylist")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse(path: Path) -> _Page:
    page = _Page()
    page.feed(path.read_text(encoding="utf-8"))
    return page


def _target(dist: Path, current: Path, href: str) -> tuple[Path | None, str]:
    bare, _, fragment = href.partition("#")
    if bare.startswith(("http://", "https://", "mailto:")):
        return None, ""
    if not bare:
        return current, fragment
    if bare.startswith("/"):
        if bare == "/":
            return dist / "index.html", fragment
        relative = bare.strip("/")
        if bare.endswith("/"):
            return dist / relative / "index.html", fragment
        return dist / relative, fragment
    return (current.parent / bare).resolve(), fragment


def unwrapped_tables(text: str) -> int:
    """Tables scroll inside the portal wrap. A bare table widens the page."""
    count = 0
    for match in re.finditer(r"<table\b", text):
        window = text[max(0, match.start() - 160) : match.start()]
        if "table-wrap" not in window:
            count += 1
    return count


def audit(dist: Path, catalog: dict[str, Any]) -> list[str]:
    """Return human-readable failures. Empty means the directory matches the catalog."""
    errors: list[str] = []
    if not dist.is_dir():
        return [f"falta {dist}"]
    pages = {path: _parse(path) for path in _html_files(dist)}
    if not pages:
        errors.append("el directorio no tiene HTML")

    for path in dist.rglob("*"):
        if path.is_file() and (path.suffix == ".md" or path.name == "registry.yaml"):
            errors.append(f"archivo no publicable: {path.relative_to(dist)}")

    if contains_excluded_sentinel(dist):
        errors.append("el artefacto contiene el centinela de un documento excluido")
    if not any(path.suffix == ".woff2" for path in dist.rglob("*") if path.is_file()):
        errors.append("no hay fuentes woff2")
    if not (dist / "404.html").is_file():
        errors.append("falta 404.html")

    home = pages.get(dist / "index.html")
    home_text = (dist / "index.html").read_text(encoding="utf-8") if home else ""
    if home is None:
        errors.append("falta index.html")
    else:
        if "/docs/instalar/" not in home.hrefs or "/cableado/" not in home.hrefs:
            errors.append("la portada no enlaza instalar y cableado")
        if "pi install" in home_text or "<pre" in home_text:
            errors.append("la portada contiene una orden")
        for name, value in (
            ("machineroom-sha", catalog.get("source_sha")),
            ("portal-sha", catalog.get("portal_sha")),
        ):
            needle = f'name="{name}" content="{value}"'
            if needle not in home_text:
                errors.append(f"falta la meta {name}")
        theme = re.search(r"<script\b([^>]*\bsrc=\"/theme-init\.js\"[^>]*)>", home_text)
        if theme is None or "async" in theme.group(1) or "defer" in theme.group(1):
            errors.append("theme-init.js no bloquea el análisis")

    cable = dist / "cableado" / "index.html"
    cable_text = cable.read_text(encoding="utf-8") if cable.is_file() else ""
    if not cable_text:
        errors.append("falta cableado")
    else:
        phase = next((item for item in catalog.get("phases", []) if item.get("id") == "IMPLEMENT"), None)
        if not isinstance(phase, dict):
            errors.append("el catálogo no tiene IMPLEMENT")
        else:
            skill = phase.get("skill")
            if not isinstance(skill, str) or skill not in cable_text:
                errors.append("IMPLEMENT no muestra la skill resuelta")
            for other in phase.get("others") or []:
                if not isinstance(other, dict):
                    continue
                other_skill = other.get("skill")
                note = other.get("note")
                if not isinstance(other_skill, str) or other_skill not in cable_text:
                    errors.append("falta una declaración de plantilla")
                if not isinstance(note, str) or note not in cable_text:
                    errors.append("falta la nota de la plantilla")
        if "Dependencias directas declaradas" not in cable_text:
            errors.append("falta el título de dependencias")

    css = "\n".join(
        path.read_bytes().decode("utf-8", errors="ignore") for path in dist.rglob("*.css") if path.is_file()
    )
    if ".site-nav" not in css:
        errors.append("el CSS del sitio no entró en el artefacto")

    vercel = dist / "vercel.json"
    if not vercel.is_file():
        errors.append("falta vercel.json en la raíz del artefacto")
    else:
        policy = vercel.read_text(encoding="utf-8")
        if "unsafe-inline" in policy or "script-src 'self'" not in policy:
            errors.append("la CSP no queda en 'self'")

    for path, page in pages.items():
        if unwrapped_tables(path.read_text(encoding="utf-8")):
            errors.append(f"tabla sin desplazamiento: {path.relative_to(dist)}")
        if page.inline_script or page.inline_style:
            errors.append(f"estilo o script en línea: {path.relative_to(dist)}")
        for href in page.hrefs:
            target, fragment = _target(dist, path, href)
            if target is None:
                continue
            target = target.resolve()
            if not target.is_file():
                errors.append(f"{path.relative_to(dist)} enlaza un archivo ausente: {href}")
                continue
            parsed = pages.get(target)
            if fragment and (parsed is None or fragment not in parsed.ids):
                errors.append(f"{path.relative_to(dist)} enlaza #{fragment} y no existe")
    return errors


def _denylist(dist: Path) -> str:
    raw: str | None = None
    found = False
    for key in ("MACHINEROOM_PRIVATE_PATTERNS", "HYGIENE_DENYLIST"):
        if key in os.environ:
            found = True
            raw = os.environ.get(key)
            break
    if not found or raw is None or not raw.strip():
        print("denylist: NOT_RUN")
        return "NOT_RUN"
    api = _denylist_api()
    patterns, error = api._parse_patterns(raw)
    if error is not None or patterns is None:
        print("denylist: FAIL")
        return "FAIL"
    files = [path.relative_to(dist).as_posix() for path in dist.rglob("*") if path.is_file() and path.suffix in _TEXT]
    if api._scan_files(dist, files, patterns) != "CLEAR":
        print("denylist: FAIL")
        return "FAIL"
    print("denylist: CLEAR")
    return "CLEAR"


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    dist = root / "site" / "dist"
    catalog_path = root / "site" / "src" / "generated" / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    errors = audit(dist, catalog)
    if errors:
        for item in errors:
            print(item)
        raise SystemExit(1)
    digest = fingerprint_tree(dist)
    identity = {
        "machineroom_sha": catalog["source_sha"],
        "portal_sha": catalog["portal_sha"],
        "artifact_sha256": digest,
    }
    (dist / "build-identity.json").write_text(
        json.dumps(identity, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if fingerprint_tree(dist) != digest:
        raise SystemExit("la huella cambió al escribir build-identity.json")
    if _denylist(dist) == "FAIL":
        raise SystemExit(1)
    print(f"artifact {digest}")


if __name__ == "__main__":
    main()
