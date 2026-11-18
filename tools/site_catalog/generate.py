#!/usr/bin/env python3
"""Build the public site catalog from the live repository.

Reads declarations. Does not import the phase router and does not execute it.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from typing import Any, NamedTuple, cast

import yaml

DOMAINS = ("plan", "local", "project", "web", "role")
SKILL_FIELDS = (
    "name",
    "description",
    "domain",
    "type",
    "language",
    "keywords",
    "compatibility",
    "entry",
)
REQUIRED_SECTIONS = ("Overview", "When to Use")
LAYER_DIRS = (
    "skills",
    "tools",
    "stacks",
    "templates/product",
    "docs",
    ".github/workflows",
)
_FENCE = re.compile(r"```(?:bash|sh)?\n(.*?)```", re.DOTALL)
_PIN = re.compile(r"@v(\d+\.\d+\.\d+)|--version[ \t]+(\d+\.\d+\.\d+)|--branch[ \t]+v(\d+\.\d+\.\d+)")
_LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)\)")
_BARE_URL = re.compile(r"https?://[^\s<>)\]]+")
_COUNT = re.compile(r"\b(\d+)\s+(skills|dominios)\b", re.IGNORECASE)
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


class CatalogError(Exception):
    """A public source could not be published as declared."""


class _LinkScope(NamedTuple):
    root: Path
    published: dict[str, dict[str, Any]]
    consult: set[str]
    hosts: set[str]
    images: dict[str, str]
    sha: str


def build_catalog(root: Path, *, sha: str | None = None) -> dict[str, Any]:
    """Return the public catalog for ``root``. ``sha`` is the commit being built."""
    root = root.resolve()
    manifest = _load_manifest(root)
    commit = sha or _git_sha(root)
    version = _read_version(root / "package.json")
    scope = _scope(root, manifest, commit)
    skills = _public_skills(root, scope)
    phases = _public_phases(root)
    tools = _public_tools(root, {item["name"] for item in skills})
    docs = _public_docs(root, manifest, version, scope, len(skills))
    hero = _hero(root / "README.md", len(skills))
    _check_layers(root)
    return {
        "product_version": version,
        "source_sha": commit,
        "portal_sha": _portal_sha(root),
        "repo": "Soluciones-Alexendros/machineroom",
        "hero_markdown": hero,
        "skill_count": len(skills),
        "skills": skills,
        "phases": phases,
        "tools": tools,
        "dependencies": _dependencies(root),
        "layers": [f"{name}/" for name in LAYER_DIRS],
        "docs": docs,
        "allowed_hosts": manifest["allowed_hosts"],
    }


def write_catalog(root: Path, dest: Path, *, sha: str | None = None) -> dict[str, Any]:
    catalog = build_catalog(root, sha=sha)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return catalog


def _load_manifest(root: Path) -> dict[str, Any]:
    path = root / "site" / "manifest.yaml"
    if not path.is_file():
        raise CatalogError(f"falta {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CatalogError("site/manifest.yaml no es un objeto")
    hosts = data.get("allowed_hosts")
    docs = data.get("docs")
    if not isinstance(hosts, list) or not all(isinstance(item, str) for item in hosts):
        raise CatalogError("allowed_hosts debe ser una lista de hosts")
    if not isinstance(docs, list) or not docs:
        raise CatalogError("docs debe nombrar al menos la guía de instalación")
    slugs: set[str] = set()
    sources: set[str] = set()
    for entry in docs:
        if not isinstance(entry, dict):
            raise CatalogError("cada doc del manifiesto es un objeto")
        source = entry.get("source")
        slug = entry.get("slug")
        group = entry.get("group")
        lang = entry.get("lang")
        if not all(isinstance(value, str) and value for value in (source, slug, group, lang)):
            raise CatalogError(f"fila incompleta: {entry!r}")
        if slug in slugs:
            raise CatalogError(f"slug repetido: {slug}")
        if source in sources:
            raise CatalogError(f"source repetido: {source}")
        slugs.add(cast(str, slug))
        sources.add(cast(str, source))
        _safe_file(root, cast(str, source))
    consult = data.get("consult_on_github") or []
    if not isinstance(consult, list):
        raise CatalogError("consult_on_github debe ser una lista")
    for item in consult:
        if not isinstance(item, dict) or not isinstance(item.get("source"), str):
            raise CatalogError(f"consult_on_github inválido: {item!r}")
        _safe_file(root, item["source"])
    _image_map(root, data)
    return data


def _safe_file(root: Path, source: str) -> Path:
    if source.startswith(("/", "\\")) or "\\" in source or ".." in Path(source).parts:
        raise CatalogError(f"ruta fuera del árbol: {source}")
    path = (root / source).resolve()
    if not path.is_relative_to(root.resolve()):
        raise CatalogError(f"ruta fuera del árbol: {source}")
    if path.is_symlink():
        raise CatalogError(f"enlace simbólico no publicable: {source}")
    if not path.is_file():
        raise CatalogError(f"falta el archivo registrado: {source}")
    return path


def _read_version(path: Path) -> str:
    if not path.is_file():
        raise CatalogError(f"falta {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    version = data.get("version")
    if not isinstance(version, str) or not version:
        raise CatalogError(f"{path} no declara version")
    return version


def _portal_sha(root: Path) -> str:
    pin = root / "site" / "portal.pin"
    if not pin.is_file():
        raise CatalogError("falta site/portal.pin")
    data = yaml.safe_load(pin.read_text(encoding="utf-8"))
    sha = data.get("sha") if isinstance(data, dict) else None
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise CatalogError("site/portal.pin sha debe ser 40 hex")
    return sha


def _git_sha(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    sha = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise CatalogError("no se pudo leer el SHA de git; pasa sha al construir")
    return sha


def _public_skills(root: Path, scope: _LinkScope) -> list[dict[str, Any]]:
    raw = _skill_index(root)
    items = raw.get("skills")
    if not isinstance(items, list) or not items:
        raise CatalogError("el índice de skills salió vacío")
    public: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise CatalogError("una skill del índice no es un objeto")
        name = item.get("name")
        if not isinstance(name, str) or not name:
            raise CatalogError("skill sin name")
        if name in seen:
            raise CatalogError(f"skill repetida: {name}")
        seen.add(name)
        if item.get("domain") not in DOMAINS:
            raise CatalogError(f"dominio no cerrado: {name} {item.get('domain')!r}")
        entry = item.get("entry")
        if not isinstance(entry, str):
            raise CatalogError(f"skill sin entry: {name}")
        path = _safe_file(root, entry)
        sections = _sections(path.read_text(encoding="utf-8"), name)
        published_sections = {title: _publish_section(text, path, scope, entry) for title, text in sections.items()}
        public.append(
            {
                **{key: item.get(key) for key in SKILL_FIELDS},
                "overview_markdown": published_sections["Overview"],
                "when_to_use_markdown": published_sections["When to Use"],
                "source_url": _blob(scope.sha, entry),
            }
        )
    return public


def _skill_index(root: Path) -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "skill-index" / "generate.py"
    spec = importlib.util.spec_from_file_location("skill_index_generate", path)
    if spec is None or spec.loader is None:
        raise CatalogError("no se pudo cargar tools/skill-index/generate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    built = cast(Any, module).build_index(root)
    if not isinstance(built, dict):
        raise CatalogError("build_index no devolvió un objeto")
    return built


def _sections(text: str, name: str) -> dict[str, str]:
    parts = text.split("---", 2)
    body = parts[2] if text.startswith("---") and len(parts) == 3 else text
    found: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        match = re.match(r"^## (.+)$", line)
        if match:
            current = match.group(1).strip()
            found.setdefault(current, [])
            continue
        if current is not None and not line.startswith("## "):
            found[current].append(line)
    missing = [title for title in REQUIRED_SECTIONS if title not in found]
    if missing:
        raise CatalogError(f"{name} no tiene {', '.join(missing)}")
    return {title: "\n".join(found[title]).strip() for title in REQUIRED_SECTIONS}


def _hero(path: Path, skill_count: int) -> str:
    if not path.is_file():
        raise CatalogError("falta README.md")
    for paragraph in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")):
        if paragraph.lstrip().startswith("**Machineroom**"):
            text = " ".join(paragraph.split())
            _check_counts(text, skill_count, "titular")
            return text
    raise CatalogError("el README no tiene el párrafo que empieza por **Machineroom**")


def _check_counts(text: str, skill_count: int, where: str) -> None:
    for match in _COUNT.finditer(text):
        number = int(match.group(1))
        kind = match.group(2).lower()
        expected = skill_count if kind == "skills" else len(DOMAINS)
        if number != expected:
            raise CatalogError(f"{where} dice {number} {kind} y el catálogo tiene {expected}")


def _public_phases(root: Path) -> list[dict[str, Any]]:
    source = root / "tools" / "workspace-router" / "project_load.py"
    if not source.is_file():
        raise CatalogError(f"falta {source}")
    order = _parse_phases(source)
    resolutions = _parse_resolutions(source)
    template = _template_handoffs(root / "templates" / "harness" / "project.yaml")
    phases: list[dict[str, Any]] = []
    for phase_id in order:
        if phase_id not in resolutions:
            raise CatalogError(f"fase sin resolución literal: {phase_id}")
        spec = resolutions[phase_id]
        skill, fallback, key = _resolve(spec, template)
        others = _other_declarations(phase_id, key, template)
        phases.append(
            {
                "id": phase_id,
                "skill": skill,
                "template_key": key,
                "fallback": fallback,
                "others": others,
            }
        )
    return phases


def _parse_phases(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and _assigns(node, "PHASES"):
            value = node.value
            if not isinstance(value, ast.Tuple) or not value.elts:
                raise CatalogError(f"{path}: PHASES no es un tuple de cadenas")
            phases: list[str] = []
            for elt in value.elts:
                if not isinstance(elt, ast.Constant) or not isinstance(elt.value, str):
                    raise CatalogError(f"{path}: PHASES contiene un valor no literal")
                phases.append(elt.value)
            return phases
    raise CatalogError(f"{path}: no hay PHASES")


def _parse_resolutions(path: Path) -> dict[str, ast.expr]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    function = next(
        (node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "handoff_for_phase"),
        None,
    )
    if function is None:
        raise CatalogError(f"{path}: no hay handoff_for_phase")
    for stmt in function.body:
        if isinstance(stmt, ast.Assign) and _assigns(stmt, "mapping") and isinstance(stmt.value, ast.Dict):
            found: dict[str, ast.expr] = {}
            for key, value in zip(stmt.value.keys, stmt.value.values, strict=True):
                if not isinstance(key, ast.Constant) or not isinstance(key.value, str) or value is None:
                    raise CatalogError(f"{path}: clave de mapping no literal")
                _require_resolution_shape(value, key.value, path)
                found[key.value] = value
            return found
    raise CatalogError(f"{path}: handoff_for_phase no asigna mapping")


def _require_resolution_shape(expr: ast.expr, phase: str, path: Path) -> None:
    try:
        _describe(expr)
    except CatalogError as exc:
        raise CatalogError(f"{path}: fase {phase}: {exc}") from exc


def _describe(expr: ast.expr) -> tuple[str, list[str], str | None]:
    """Return kind, template keys in order, and the literal fallback."""
    if isinstance(expr, ast.Call):
        key, default = _describe_get(expr, default_required=True)
        return "get", [key], default
    if isinstance(expr, ast.BoolOp) and isinstance(expr.op, ast.Or):
        keys: list[str] = []
        fallback: str | None = None
        for value in expr.values:
            if isinstance(value, ast.Call):
                key, _ = _describe_get(value, default_required=False)
                keys.append(key)
            elif isinstance(value, ast.Constant) and isinstance(value.value, str):
                fallback = value.value
            else:
                raise CatalogError("la cadena or no es literal")
        if not keys or fallback is None:
            raise CatalogError("la cadena or no termina en una skill literal")
        return "or", keys, fallback
    raise CatalogError("la resolución no es h.get ni una cadena or")


def _describe_get(call: ast.Call, *, default_required: bool) -> tuple[str, str | None]:
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr != "get" or not isinstance(func.value, ast.Name):
        raise CatalogError("la llamada no es h.get")
    if not call.args or not isinstance(call.args[0], ast.Constant) or not isinstance(call.args[0].value, str):
        raise CatalogError("h.get sin clave literal")
    default: str | None = None
    if len(call.args) > 1:
        if not isinstance(call.args[1], ast.Constant) or not isinstance(call.args[1].value, str):
            raise CatalogError("el respaldo de h.get no es una cadena")
        default = call.args[1].value
    elif default_required:
        raise CatalogError("h.get sin respaldo literal")
    return call.args[0].value, default


def _resolve(expr: ast.expr, handoffs: dict[str, str]) -> tuple[str, str | None, str]:
    kind, keys, default = _describe(expr)
    if kind == "get":
        chosen = handoffs.get(keys[0]) or default or ""
        fallback = default if chosen != default else None
        return chosen, fallback, keys[0]
    for key in keys:
        value = handoffs.get(key)
        if isinstance(value, str) and value:
            fallback = default if value != default else None
            return value, fallback, key
    if default is None:
        raise CatalogError("la cadena or no termina en una skill literal")
    return default, None, keys[-1]


def _other_declarations(phase_id: str, winning_key: str, handoffs: dict[str, str]) -> list[dict[str, str]]:
    if phase_id != "IMPLEMENT":
        return []
    others: list[dict[str, str]] = []
    for key in ("implement_front", "implement_linux"):
        skill = handoffs.get(key)
        if key != winning_key and isinstance(skill, str) and skill:
            others.append(
                {
                    "key": key,
                    "skill": skill,
                    "note": "declarada en la plantilla, no la devuelve el router de fase",
                }
            )
    return others


def _template_handoffs(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise CatalogError(f"falta {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    handoffs = data.get("handoffs") if isinstance(data, dict) else None
    if not isinstance(handoffs, dict):
        raise CatalogError(f"{path} no tiene handoffs")
    clean: dict[str, str] = {}
    for key, value in handoffs.items():
        if not isinstance(key, str) or not isinstance(value, str) or not value:
            raise CatalogError(f"handoff no literal en {path}: {key!r}")
        clean[key] = value
    return clean


def _assigns(node: ast.Assign, name: str) -> bool:
    return any(isinstance(target, ast.Name) and target.id == name for target in node.targets)


def _public_tools(root: Path, skills: set[str]) -> list[dict[str, Any]]:
    path = root / "tools" / "execution" / "registry.yaml"
    if not path.is_file():
        raise CatalogError(f"falta {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw_tools = data.get("tools") if isinstance(data, dict) else None
    if not isinstance(raw_tools, list):
        raise CatalogError("registry.yaml no tiene tools")
    public: list[dict[str, Any]] = []
    seen: set[str] = set()
    for tool in raw_tools:
        if not isinstance(tool, dict):
            raise CatalogError("una herramienta del registro no es un objeto")
        tool_id = tool.get("tool_id")
        skill = tool.get("skill")
        if not isinstance(tool_id, str) or not isinstance(skill, str):
            raise CatalogError("herramienta sin tool_id o skill")
        if tool_id in seen:
            raise CatalogError(f"tool_id repetido: {tool_id}")
        seen.add(tool_id)
        if skill not in skills:
            raise CatalogError(f"herramienta {tool_id} cita la skill ausente {skill}")
        operations = []
        for operation in tool.get("operations") or []:
            if not isinstance(operation, dict):
                raise CatalogError(f"{tool_id} tiene una operación que no es un objeto")
            op_id = operation.get("id")
            effect = operation.get("effect")
            if not isinstance(op_id, str) or not isinstance(effect, str):
                raise CatalogError(f"{tool_id} operación sin id o effect")
            approval = operation.get("approval_required")
            dry_run = operation.get("dry_run")
            if not isinstance(approval, bool) or not isinstance(dry_run, str):
                raise CatalogError(f"{tool_id}.{op_id} no declara aprobación y dry_run")
            operations.append(
                {
                    "id": op_id,
                    "effect": effect,
                    "approval_required": approval,
                    "dry_run": dry_run,
                }
            )
        public.append({"tool_id": tool_id, "skill": skill, "operations": operations})
    return public


def _dependencies(root: Path) -> dict[str, list[dict[str, str]]]:
    return {
        "root": _npm_deps(root / "package.json"),
        "tools": _python_deps(root / "tools" / "pyproject.toml"),
        "site": _npm_deps(root / "site" / "package.json"),
    }


def _npm_deps(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    found: list[dict[str, str]] = []
    for kind, key in (("directa", "dependencies"), ("desarrollo", "devDependencies")):
        block = data.get(key) or {}
        if not isinstance(block, dict):
            raise CatalogError(f"{path} {key} no es un objeto")
        for name, spec in sorted(block.items()):
            if isinstance(name, str) and isinstance(spec, str):
                found.append({"name": name, "spec": spec, "kind": kind})
    return found


def _python_deps(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    table = re.search(r"(?ms)^\[project\]\s*(.*?)(?=^\[|\Z)", text)
    if table is None:
        return []
    match = re.search(r"(?ms)^dependencies\s*=\s*\[(.*?)\]", table.group(1))
    if match is None:
        return []
    names = re.findall(r'"([^"]+)"', match.group(1))
    return [{"name": item, "spec": item, "kind": "directa"} for item in names]


def _check_layers(root: Path) -> None:
    for name in LAYER_DIRS:
        if not (root / name).is_dir():
            raise CatalogError(f"falta el directorio de capa {name}")


def _public_docs(
    root: Path,
    manifest: dict[str, Any],
    version: str,
    scope: _LinkScope,
    skill_count: int,
) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for entry in manifest["docs"]:
        path = _safe_file(root, entry["source"])
        text = path.read_text(encoding="utf-8")
        if "/home/" in text:
            raise CatalogError(f"{entry['source']} contiene una ruta /home/")
        if entry["source"].endswith("harness-setup.md"):
            _check_install_pins(text, version)
            _check_counts(_install_lead(text), skill_count, entry["source"])
        markdown = _rewrite_links(text, path, scope, entry["source"])
        docs.append(
            {
                "source": entry["source"],
                "slug": entry["slug"],
                "group": entry["group"],
                "lang": entry["lang"],
                "title": _title(markdown, entry["source"]),
                "markdown": markdown,
                "source_url": _blob(scope.sha, entry["source"]),
            }
        )
    return docs


def _install_lead(text: str) -> str:
    """The public opening, before the machine-runtime procedure."""
    marker = "## Machine runtime"
    at = text.find(marker)
    if at == -1:
        return text
    return text[:at]


def _check_install_pins(text: str, version: str) -> None:
    for fence in _FENCE.finditer(text):
        block = fence.group(1)
        for match in _PIN.finditer(block):
            found = next(group for group in match.groups() if group)
            if found != version:
                raise CatalogError(f"la guía fija {found} y package.json es {version}")
        if "/path/to/project" in block:
            before = text[max(0, fence.start() - 400) : fence.start()]
            if "your project" not in before:
                raise CatalogError("un bloque usa /path/to/project sin decir que es el del lector")


def _scope(root: Path, manifest: dict[str, Any], sha: str) -> _LinkScope:
    return _LinkScope(
        root=root,
        published={entry["source"]: entry for entry in manifest["docs"]},
        consult={item["source"] for item in manifest.get("consult_on_github") or []},
        hosts=set(manifest["allowed_hosts"]),
        images=_image_map(root, manifest),
        sha=sha,
    )


def _image_map(root: Path, manifest: dict[str, Any]) -> dict[str, str]:
    raw = manifest.get("images") or []
    if not isinstance(raw, list):
        raise CatalogError("images debe ser una lista")
    found: dict[str, str] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise CatalogError(f"imagen inválida: {item!r}")
        source = item.get("source")
        href = item.get("href")
        if not isinstance(source, str) or not isinstance(href, str):
            raise CatalogError(f"imagen inválida: {item!r}")
        if not href.startswith("/") or href.startswith("//"):
            raise CatalogError(f"la imagen debe servirse en este origen: {href}")
        _safe_file(root, source)
        if source in found:
            raise CatalogError(f"imagen repetida: {source}")
        found[source] = href
    return found


def _publish_section(text: str, path: Path, scope: _LinkScope, source: str) -> str:
    if "/home/" in text:
        raise CatalogError(f"{source} contiene una ruta /home/")
    return _rewrite_links(text, path, scope, source)


def _rewrite_links(text: str, path: Path, scope: _LinkScope, source: str) -> str:
    def replace(match: re.Match[str]) -> str:
        bang, label, dest = match.group(1), match.group(2), match.group(3)
        rewritten = _classify(dest, path, scope, source, image=bool(bang))
        return f"{bang}[{label}]({rewritten})"

    rewritten = _LINK.sub(replace, text)
    for bare in _BARE_URL.findall(rewritten):
        _require_host(bare, scope.hosts, source)
    return rewritten


def _classify(
    dest: str,
    path: Path,
    scope: _LinkScope,
    source: str,
    *,
    image: bool,
) -> str:
    if image and dest.startswith(("http://", "https://", "mailto:")):
        raise CatalogError(f"{source} enlaza una imagen de otro origen: {dest}")
    if dest.startswith(("http://", "https://")):
        _require_host(dest, scope.hosts, source)
        return dest
    if dest.startswith("mailto:"):
        raise CatalogError(f"{source} enlaza un mailto no permitido: {dest}")
    fragment = ""
    bare = dest
    if "#" in dest:
        bare, fragment = dest.split("#", 1)
        fragment = "#" + fragment
    if not bare:
        return dest
    target = _resolve_link(path, scope.root, bare, source)
    rel = str(target.relative_to(scope.root))
    if image:
        href = scope.images.get(rel)
        if href is None:
            raise CatalogError(f"{source} enlaza una imagen no nombrada en el manifiesto: {dest}")
        return href + fragment
    if rel in scope.published:
        slug = scope.published[rel]["slug"]
        return f"/docs/{slug}/{fragment}"
    if rel in scope.consult:
        return _blob(scope.sha, rel) + fragment
    raise CatalogError(f"{source} enlaza {dest}: destino no publicado")


def _resolve_link(path: Path, root: Path, bare: str, source: str) -> Path:
    if bare.startswith(("/", "\\")) or "\\" in bare:
        raise CatalogError(f"{source} enlaza fuera del árbol: {bare}")
    candidate = (path.parent / bare).resolve()
    if not candidate.is_relative_to(root):
        raise CatalogError(f"{source} enlaza fuera del árbol: {bare}")
    if not candidate.is_file():
        raise CatalogError(f"{source} enlaza un archivo inexistente: {bare}")
    return candidate


def _require_host(url: str, hosts: set[str], source: str) -> None:
    match = re.match(r"https?://([^/]+)", url)
    host = match.group(1).lower() if match else ""
    if host.startswith("www."):
        host = host[4:]
    if host not in hosts:
        raise CatalogError(f"{source} enlaza un host no permitido: {host or url}")


def _blob(sha: str, source: str) -> str:
    return f"https://github.com/Soluciones-Alexendros/machineroom/blob/{sha}/{source}"


def _title(markdown: str, source: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    if not match:
        raise CatalogError(f"{source} no tiene título")
    return match.group(1).strip()


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    dest = root / "site" / "src" / "generated" / "catalog.json"
    write_catalog(root, dest)
    print(f"catalog: {dest}")


if __name__ == "__main__":
    main()
