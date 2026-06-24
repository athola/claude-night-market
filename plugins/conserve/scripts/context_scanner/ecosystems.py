"""Language and framework ecosystem detection functions."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from .detection import (
    detect_env_vars,
    detect_middleware,
    detect_routes,
    detect_schemas,
    estimate_token_savings,
)
from .import_graph import build_import_graph, detect_hot_files
from .models import (
    EXCLUDED_DIRS,
    EXTENSION_LANGUAGES,
    GO_FRAMEWORKS,
    NODE_FRAMEWORKS,
    PYTHON_FRAMEWORKS,
    RUST_FRAMEWORKS,
    Dependency,
    DirectoryInfo,
    EcosystemResult,
    EntryPoint,
    FrameworkMatch,
    ScanResult,
    _walk_limited,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_WALK_DEPTH = 8
_MIN_MODULE_PARTS = 2

# ---------------------------------------------------------------------------
# T001: File Tree Walker
# ---------------------------------------------------------------------------


_CONFIG_PATTERNS = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".env.example",
    "tsconfig.json",
    "vite.config.ts",
    "vite.config.js",
    "webpack.config.js",
    "next.config.js",
    "next.config.mjs",
}


def _scan_directory_structure(root: Path) -> ScanResult:
    """Walk the directory tree and build the ScanResult skeleton.

    Populates project_name, total_files, directories, and config_files.
    Does not run ecosystem or analysis detectors.
    """
    root = root.resolve()
    dir_files: dict[str, list[str]] = {}
    root_files: list[str] = []
    config_files: list[str] = []
    total_files = 0

    def _walk(path: Path, depth: int, top_dir: str | None) -> None:
        nonlocal total_files
        if depth > _MAX_WALK_DEPTH:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda e: e.name)
        except PermissionError:
            return

        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name in EXCLUDED_DIRS:
                    continue
                if entry.name.endswith(".egg-info"):
                    continue
                current_top = top_dir if top_dir else entry.name
                _walk(entry, depth + 1, current_top)
            elif entry.is_file():
                total_files += 1
                rel = str(entry.relative_to(root))
                if entry.name in _CONFIG_PATTERNS:
                    config_files.append(rel)
                if top_dir:
                    if top_dir not in dir_files:
                        dir_files[top_dir] = []
                    dir_files[top_dir].append(entry.name)
                else:
                    root_files.append(entry.name)

    _walk(root, 0, None)

    directories: list[DirectoryInfo] = []
    for dirname, files in dir_files.items():
        ext_counts: Counter = Counter()
        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext:
                ext_counts[ext] += 1
        primary_lang = None
        if ext_counts:
            top_ext = ext_counts.most_common(1)[0][0]
            primary_lang = EXTENSION_LANGUAGES.get(top_ext)
        directories.append(
            DirectoryInfo(
                path=dirname,
                file_count=len(files),
                primary_language=primary_lang,
            )
        )
    directories.sort(key=lambda d: d.file_count, reverse=True)

    return ScanResult(
        project_name=root.name,
        total_files=total_files,
        directories=directories,
        config_files=config_files,
    )


def _enrich_with_detectors(root: Path, result: ScanResult) -> None:
    """Run ecosystem and analysis detectors, populating extended ScanResult fields."""
    for detector in [detect_python, detect_node, detect_rust, detect_go, detect_java]:
        eco = detector(root)
        if eco is not None:
            result.ecosystems.append(eco)

    file_entry_points = detect_entry_points(root, result.all_entry_points)
    if file_entry_points:
        if not result.ecosystems:
            result.ecosystems.append(
                EcosystemResult(name="Generic", entry_points=file_entry_points)
            )
        else:
            existing_paths = {e.path for e in result.all_entry_points}
            for ep in file_entry_points:
                if ep.path not in existing_paths:
                    result.ecosystems[0].entry_points.append(ep)

    result.import_graph = build_import_graph(root)
    result.hot_files = detect_hot_files(result.import_graph)
    result.hot_file_counts = {
        hf: len(result.import_graph.imported_by.get(hf, set()))
        for hf in result.hot_files
    }
    result.routes = detect_routes(root)
    result.env_vars = detect_env_vars(root)
    result.middleware = detect_middleware(root)
    result.schemas = detect_schemas(root)
    result.token_estimate = estimate_token_savings(result)


def scan_directory(root: Path) -> ScanResult:
    """Walk a project directory and collect structure metadata."""
    result = _scan_directory_structure(root.resolve())
    _enrich_with_detectors(root.resolve(), result)
    return result


# ---------------------------------------------------------------------------
# T002: Python Ecosystem Detector
# ---------------------------------------------------------------------------


def _parse_optional_group_line(
    stripped: str, current_group: str
) -> tuple[str, list[Dependency]]:
    """Parse one inline group assignment: ``group = ["pkg1", "pkg2"]``.

    Returns the resolved group name and any dependencies found on this line.
    """
    deps: list[Dependency] = []
    if "=" not in stripped or "[" not in stripped:
        return current_group, deps
    group = stripped.split("=")[0].strip()
    items_part = stripped.split("[", 1)[1]
    if "]" in items_part:
        items_part = items_part.split("]")[0]
    for item in items_part.split(","):
        name = _extract_pkg_name(item.strip().strip("\"' "))
        if name:
            cat = "dev" if group in ("dev", "test", "testing") else "runtime"
            deps.append(Dependency(name, _extract_version(item), cat))
    return group, deps


def _parse_project_deps(text: str) -> tuple[list[Dependency], list[Dependency]]:
    """Parse [project.dependencies] and optional-dependency groups."""
    runtime_deps: list[Dependency] = []
    dev_deps: list[Dependency] = []

    in_deps = False
    in_optional = False
    current_group = ""

    for line in text.splitlines():
        stripped = line.strip()

        if stripped == "dependencies = [" or stripped.startswith("dependencies = ["):
            in_deps = True
            if stripped.endswith("]") and stripped != "dependencies = [":
                items = stripped.split("[", 1)[1].rstrip("]")
                for item in items.split(","):
                    name = _extract_pkg_name(item.strip().strip("\"'"))
                    if name:
                        runtime_deps.append(
                            Dependency(name, _extract_version(item), "runtime")
                        )
                in_deps = False
            continue
        if stripped.startswith(
            "[project.optional-dependencies]"
        ) or stripped.startswith("[tool.poetry.group"):
            in_optional = True
            in_deps = False
            continue
        if stripped.startswith("[") and not stripped.startswith("[["):
            in_deps = False
            in_optional = False
            continue

        if in_deps and stripped == "]":
            in_deps = False
            continue

        if in_deps:
            name = _extract_pkg_name(stripped.strip("\"', "))
            if name:
                runtime_deps.append(
                    Dependency(name, _extract_version(stripped), "runtime")
                )

        if in_optional:
            current_group, found = _parse_optional_group_line(stripped, current_group)
            dev_deps.extend(found)

    return runtime_deps, dev_deps


def _parse_poetry_deps(text: str) -> list[Dependency]:
    """Parse [tool.poetry.dependencies] from pyproject.toml text."""
    deps: list[Dependency] = []
    match = re.search(
        r"\[tool\.poetry\.dependencies\](.*?)(?=\n\[|\Z)", text, re.DOTALL
    )
    if match:
        for line in match.group(1).splitlines():
            if "=" in line and not line.strip().startswith("#"):
                parts = line.strip().split("=", 1)
                name = parts[0].strip()
                if name and name != "python":
                    version = parts[1].strip().strip("\"'{}^ ")
                    deps.append(Dependency(name, version, "runtime"))
    return deps


def _parse_pyproject_deps(text: str) -> tuple[list[Dependency], list[Dependency]]:
    """Extract dependencies from pyproject.toml text."""
    runtime_deps, dev_deps = _parse_project_deps(text)
    runtime_deps.extend(_parse_poetry_deps(text))
    return runtime_deps, dev_deps


def _extract_pkg_name(s: str) -> str | None:
    """Extract package name from a dependency spec like 'fastapi>=0.104.0'."""
    s = s.strip().strip("\"'")
    if not s or s.startswith("#") or s == "]":
        return None
    # Handle extras: package[extra]
    name = re.split(r"[>=<!~\[\s;]", s)[0].strip()
    return name.lower() if name else None


def _extract_version(s: str) -> str | None:
    """Extract version from a dependency spec."""
    match = re.search(r"[>=<!~]=?\s*([\d][^\s,\"']*)", s)
    return match.group(1) if match else None


def _parse_requirements_txt(text: str) -> list[Dependency]:
    """Extract dependencies from requirements.txt."""
    deps = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        name = _extract_pkg_name(line)
        if name:
            deps.append(Dependency(name, _extract_version(line), "runtime"))
    return deps


def _parse_pyproject_scripts(text: str) -> list[EntryPoint]:
    """Extract [project.scripts] entry points from pyproject.toml."""
    entry_points = []
    in_scripts = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[project.scripts]":
            in_scripts = True
            continue
        if in_scripts and stripped.startswith("["):
            break
        if in_scripts and "=" in stripped:
            entry_points.append(EntryPoint(path=stripped, kind="cli"))
    return entry_points


def detect_python(root: Path) -> EcosystemResult | None:
    """Detect Python ecosystem from project files."""
    pyproject = root / "pyproject.toml"
    requirements = root / "requirements.txt"
    setup_py = root / "setup.py"

    if not (pyproject.exists() or requirements.exists() or setup_py.exists()):
        return None

    deps: list[Dependency] = []
    dev_deps: list[Dependency] = []
    entry_points: list[EntryPoint] = []

    if pyproject.exists():
        text = pyproject.read_text(errors="replace")
        runtime, dev = _parse_pyproject_deps(text)
        deps.extend(runtime)
        dev_deps.extend(dev)
        entry_points.extend(_parse_pyproject_scripts(text))

    if requirements.exists() and not deps:
        text = requirements.read_text(errors="replace")
        deps.extend(_parse_requirements_txt(text))

    all_deps = deps + dev_deps

    # Detect package manager
    pm = "pip"
    if (root / "uv.lock").exists():
        pm = "uv"
    elif (root / "poetry.lock").exists():
        pm = "poetry"
    elif (root / "Pipfile.lock").exists():
        pm = "pipenv"

    # Detect frameworks
    frameworks = []
    dep_names = {d.name for d in all_deps}
    for pkg, fw_name in PYTHON_FRAMEWORKS.items():
        if pkg in dep_names:
            frameworks.append(FrameworkMatch(name=fw_name))

    return EcosystemResult(
        name="Python",
        package_manager=pm,
        dependencies=all_deps,
        frameworks=frameworks,
        entry_points=entry_points,
    )


# ---------------------------------------------------------------------------
# T003: Multi-Ecosystem Detectors
# ---------------------------------------------------------------------------


def detect_node(root: Path) -> EcosystemResult | None:  # noqa: PLR0912 - branches per framework and entry-point detection pattern
    """Detect Node.js ecosystem from package.json."""
    pkg_json = root / "package.json"
    if not pkg_json.exists():
        return None

    try:
        data = json.loads(pkg_json.read_text(errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None

    deps: list[Dependency] = []
    frameworks: list[FrameworkMatch] = []
    entry_points: list[EntryPoint] = []

    # Runtime dependencies
    for name, version in data.get("dependencies", {}).items():
        deps.append(Dependency(name, version.lstrip("^~>="), "runtime"))

    # Dev dependencies
    for name, version in data.get("devDependencies", {}).items():
        deps.append(Dependency(name, version.lstrip("^~>="), "dev"))

    # Detect frameworks
    all_dep_names = {d.name for d in deps}
    for pkg, fw_name in NODE_FRAMEWORKS.items():
        if pkg in all_dep_names:
            frameworks.append(FrameworkMatch(name=fw_name))

    # Entry points
    if "main" in data:
        entry_points.append(EntryPoint(path=data["main"], kind="main"))
    if "bin" in data:
        if isinstance(data["bin"], str):
            entry_points.append(EntryPoint(path=data["bin"], kind="cli"))
        elif isinstance(data["bin"], dict):
            for _name, path in data["bin"].items():
                entry_points.append(EntryPoint(path=path, kind="cli"))

    # Package manager
    pm = "npm"
    if (root / "yarn.lock").exists():
        pm = "yarn"
    elif (root / "pnpm-lock.yaml").exists():
        pm = "pnpm"
    elif (root / "bun.lockb").exists():
        pm = "bun"

    return EcosystemResult(
        name="Node",
        package_manager=pm,
        dependencies=deps,
        frameworks=frameworks,
        entry_points=entry_points,
    )


def detect_rust(root: Path) -> EcosystemResult | None:
    """Detect Rust ecosystem from Cargo.toml."""
    cargo = root / "Cargo.toml"
    if not cargo.exists():
        return None

    text = cargo.read_text(errors="replace")
    deps: list[Dependency] = []
    frameworks: list[FrameworkMatch] = []

    # Parse [dependencies] section
    in_deps = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[dependencies]":
            in_deps = True
            continue
        if stripped.startswith("[") and in_deps:
            in_deps = False
            continue
        if in_deps and "=" in stripped and not stripped.startswith("#"):
            parts = stripped.split("=", 1)
            name = parts[0].strip()
            # Handle both `name = "version"` and `name = { version = "..." }`
            val = parts[1].strip()
            version = None
            ver_match = re.search(r'"([^"]*)"', val)
            if ver_match:
                version = ver_match.group(1)
            deps.append(Dependency(name, version, "runtime"))

    # Detect frameworks
    dep_names = {d.name for d in deps}
    for pkg, fw_name in RUST_FRAMEWORKS.items():
        if pkg in dep_names:
            frameworks.append(FrameworkMatch(name=fw_name))

    return EcosystemResult(
        name="Rust",
        package_manager="cargo",
        dependencies=deps,
        frameworks=frameworks,
    )


def detect_go(root: Path) -> EcosystemResult | None:
    """Detect Go ecosystem from go.mod."""
    gomod = root / "go.mod"
    if not gomod.exists():
        return None

    text = gomod.read_text(errors="replace")
    deps: list[Dependency] = []
    frameworks: list[FrameworkMatch] = []

    # Parse require block
    in_require = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_require = True
            continue
        if stripped == ")" and in_require:
            in_require = False
            continue
        if in_require and stripped and not stripped.startswith("//"):
            parts = stripped.split()
            if len(parts) >= _MIN_MODULE_PARTS:
                mod_path = parts[0]
                version = parts[1]
                # Use last segment as display name
                short_name = mod_path.rsplit("/", 1)[-1]
                deps.append(Dependency(short_name, version, "runtime"))

                # Check frameworks by full module path
                for mod_prefix, fw_name in GO_FRAMEWORKS.items():
                    if mod_path.startswith(mod_prefix):
                        frameworks.append(FrameworkMatch(name=fw_name))

    return EcosystemResult(
        name="Go",
        package_manager="go modules",
        dependencies=deps,
        frameworks=frameworks,
    )


def detect_java(root: Path) -> EcosystemResult | None:
    """Detect Java/Kotlin ecosystem from build files."""
    pom = root / "pom.xml"
    gradle = root / "build.gradle"
    gradle_kts = root / "build.gradle.kts"

    if not (pom.exists() or gradle.exists() or gradle_kts.exists()):
        return None

    pm = "maven" if pom.exists() else "gradle"
    return EcosystemResult(name="Java", package_manager=pm)


# ---------------------------------------------------------------------------
# T004: Entry Point Detection
# ---------------------------------------------------------------------------

ENTRY_POINT_PATTERNS: list[tuple[str, str]] = [
    # (glob pattern relative to root, kind)
    ("main.py", "main"),
    ("app.py", "app"),
    ("cli.py", "cli"),
    ("server.py", "server"),
    ("manage.py", "cli"),
    ("index.ts", "main"),
    ("index.js", "main"),
    ("main.ts", "main"),
    ("main.js", "main"),
    ("server.ts", "server"),
    ("server.js", "server"),
    ("app.ts", "app"),
    ("app.js", "app"),
    ("main.go", "main"),
    ("main.rs", "main"),
]


def detect_entry_points(root: Path, existing: list[EntryPoint]) -> list[EntryPoint]:
    """Detect entry points from well-known file patterns."""
    existing_paths = {e.path for e in existing}
    found: list[EntryPoint] = []

    target_names = {pat for pat, _ in ENTRY_POINT_PATTERNS}

    for dirpath, _dirnames, filenames in _walk_limited(root, max_depth=3):
        for fname in filenames:
            if fname in target_names:
                rel = str(Path(dirpath).relative_to(root) / fname)
                # Normalize to forward slashes
                rel = rel.replace("\\", "/")
                if rel.startswith("./"):
                    rel = rel[2:]
                if rel not in existing_paths:
                    kind = next(k for p, k in ENTRY_POINT_PATTERNS if p == fname)
                    found.append(EntryPoint(path=rel, kind=kind))

    # Also look for __main__.py
    for dirpath, _dirnames, filenames in _walk_limited(root, max_depth=3):
        for fname in filenames:
            if fname == "__main__.py":
                rel = str(Path(dirpath).relative_to(root) / fname)
                rel = rel.replace("\\", "/")
                if rel.startswith("./"):
                    rel = rel[2:]
                if rel not in existing_paths and rel not in {e.path for e in found}:
                    found.append(EntryPoint(path=rel, kind="main"))

    return found
