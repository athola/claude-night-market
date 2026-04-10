#!/usr/bin/env python3
"""Project context map generator for token conservation.

Pre-scans a codebase and generates a compressed context map that gives
AI assistants a project overview without expensive exploratory reads.

Usage:
    python context_scanner.py [path] [--format md|json] [--max-tokens N]
    python context_scanner.py . --format json
    python context_scanner.py /project --output context-map.md
"""

from __future__ import annotations

# ruff: noqa: PLR0912, PLR0915, PLR2004, C901
import argparse
import copy
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict, deque
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

EXTENSION_LANGUAGES: dict[str, str] = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".toml": "TOML",
    ".json": "JSON",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sh": "Shell",
    ".sql": "SQL",
}

EXCLUDED_DIRS: set[str] = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".eggs",
    "target",  # Rust/Java build output
    ".next",
    ".nuxt",
    ".cache",
    "coverage",
    ".coverage",
    ".idea",
    ".vscode",
    ".uv-tools",
    ".uv-cache",
    ".typecheck-venv",
    ".xdg-cache",
    "htmlcov",
    "site-packages",
}

# Frameworks identified by dependency name
PYTHON_FRAMEWORKS: dict[str, str] = {
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "starlette": "Starlette",
    "tornado": "Tornado",
    "aiohttp": "aiohttp",
    "sqlalchemy": "SQLAlchemy",
    "pydantic": "Pydantic",
    "pytest": "Pytest",
    "celery": "Celery",
    "click": "Click",
    "typer": "Typer",
    "rich": "Rich",
    "httpx": "HTTPX",
    "requests": "Requests",
}

NODE_FRAMEWORKS: dict[str, str] = {
    "express": "Express",
    "next": "Next.js",
    "react": "React",
    "vue": "Vue",
    "angular": "Angular",
    "svelte": "Svelte",
    "nestjs": "NestJS",
    "@nestjs/core": "NestJS",
    "prisma": "Prisma",
    "drizzle-orm": "Drizzle",
    "zod": "Zod",
    "vitest": "Vitest",
    "jest": "Jest",
    "tailwindcss": "Tailwind CSS",
    "typescript": "TypeScript",
}

RUST_FRAMEWORKS: dict[str, str] = {
    "tokio": "Tokio",
    "axum": "Axum",
    "actix-web": "Actix",
    "rocket": "Rocket",
    "serde": "Serde",
    "sqlx": "SQLx",
    "diesel": "Diesel",
    "clap": "Clap",
    "tracing": "Tracing",
}

GO_FRAMEWORKS: dict[str, str] = {
    "github.com/gin-gonic/gin": "Gin",
    "github.com/labstack/echo": "Echo",
    "github.com/gofiber/fiber": "Fiber",
    "github.com/gorilla/mux": "Gorilla Mux",
    "github.com/spf13/cobra": "Cobra",
    "github.com/jmoiron/sqlx": "SQLx",
    "gorm.io/gorm": "GORM",
}


@dataclass
class DirectoryInfo:
    """Summary of a top-level directory."""

    path: str
    file_count: int
    primary_language: str | None = None


@dataclass
class Dependency:
    """A project dependency."""

    name: str
    version: str | None = None
    category: str = "runtime"  # "runtime" | "dev"


@dataclass
class FrameworkMatch:
    """A detected framework or notable library."""

    name: str
    locations: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class EntryPoint:
    """A detected application entry point."""

    path: str
    kind: str = "main"  # "main" | "cli" | "app" | "server"


@dataclass
class EcosystemResult:
    """Results from a single ecosystem detector."""

    name: str  # "Python", "Node", "Rust", "Go", "Java"
    package_manager: str | None = None
    dependencies: list[Dependency] = field(default_factory=list)
    frameworks: list[FrameworkMatch] = field(default_factory=list)
    entry_points: list[EntryPoint] = field(default_factory=list)


@dataclass
class TruncatedList:
    """A list with truncation metadata."""

    shown: list = field(default_factory=list)
    remaining: int = 0


@dataclass
class ImportGraph:
    """Import relationship graph between project files."""

    edges: list[tuple[str, str]] = field(default_factory=list)
    imports: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    imported_by: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))

    def add_edge(self, source: str, target: str) -> None:
        """Record that source imports target."""
        self.edges.append((source, target))
        self.imports[source].add(target)
        self.imported_by[target].add(source)


@dataclass
class RouteInfo:
    """A detected API route."""

    method: str
    path: str
    file: str


@dataclass
class EnvVarInfo:
    """A detected environment variable reference."""

    name: str
    file: str
    has_default: bool = False


@dataclass
class MiddlewareInfo:
    """A detected middleware pattern."""

    name: str
    kind: str  # "auth" | "cors" | "rate-limit" | "logging" | "validation"
    file: str


@dataclass
class TokenEstimate:
    """Estimated tokens saved by pre-compiling context."""

    route_tokens: int = 0
    hot_file_tokens: int = 0
    env_var_tokens: int = 0
    file_scan_tokens: int = 0

    @property
    def total(self) -> int:
        """Sum of all token estimate components."""
        return (
            self.route_tokens
            + self.hot_file_tokens
            + self.env_var_tokens
            + self.file_scan_tokens
        )


@dataclass
class BlastResult:
    """Result of a per-file blast radius analysis."""

    target: str
    direct: list[str] = field(default_factory=list)
    transitive: list[tuple[str, str]] = field(default_factory=list)

    @property
    def total_affected(self) -> int:
        """Count of all files affected (direct + transitive)."""
        return len(self.direct) + len(self.transitive)


@dataclass
class SchemaModel:
    """A detected ORM model or schema definition."""

    name: str
    file: str
    field_count: int = 0
    framework: str = ""  # "SQLAlchemy" | "Django" | "Pydantic" | "Prisma"


@dataclass
class WikiArticle:
    """A generated wiki knowledge article."""

    topic: str
    title: str
    files: list[str] = field(default_factory=list)
    content: str = ""


@dataclass
class ScanResult:
    """Complete project scan result."""

    project_name: str
    total_files: int
    directories: list[DirectoryInfo] = field(default_factory=list)
    ecosystems: list[EcosystemResult] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    truncated_dirs: int = 0
    # Extended analysis fields
    import_graph: ImportGraph | None = None
    hot_files: list[str] = field(default_factory=list)
    hot_file_counts: dict[str, int] = field(default_factory=dict)
    routes: list[RouteInfo] = field(default_factory=list)
    env_vars: list[EnvVarInfo] = field(default_factory=list)
    middleware: list[MiddlewareInfo] = field(default_factory=list)
    schemas: list[SchemaModel] = field(default_factory=list)
    token_estimate: TokenEstimate | None = None

    @property
    def all_dependencies(self) -> list[Dependency]:
        """Flatten dependencies from all ecosystems."""
        deps = []
        for eco in self.ecosystems:
            deps.extend(eco.dependencies)
        return deps

    @property
    def all_frameworks(self) -> list[FrameworkMatch]:
        """Flatten framework matches from all ecosystems."""
        fws = []
        for eco in self.ecosystems:
            fws.extend(eco.frameworks)
        return fws

    @property
    def all_entry_points(self) -> list[EntryPoint]:
        """Flatten entry points from all ecosystems."""
        eps = []
        for eco in self.ecosystems:
            eps.extend(eco.entry_points)
        return eps


# ---------------------------------------------------------------------------
# T001: File Tree Walker
# ---------------------------------------------------------------------------


def scan_directory(root: Path) -> ScanResult:
    """Walk a project directory and collect structure metadata."""
    root = root.resolve()
    project_name = root.name

    # Collect files per top-level directory
    dir_files: dict[str, list[str]] = defaultdict(list)
    root_files: list[str] = []
    config_files: list[str] = []
    total_files = 0

    config_patterns = {
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

    def _walk(path: Path, depth: int, top_dir: str | None) -> None:
        nonlocal total_files
        if depth > 8:
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
                if entry.name in config_patterns:
                    config_files.append(rel)
                if top_dir:
                    dir_files[top_dir].append(entry.name)
                else:
                    root_files.append(entry.name)

    _walk(root, 0, None)

    # Build DirectoryInfo list
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

    result = ScanResult(
        project_name=project_name,
        total_files=total_files,
        directories=directories,
        config_files=config_files,
    )

    # Run ecosystem detectors
    for detector in [detect_python, detect_node, detect_rust, detect_go, detect_java]:
        eco = detector(root)
        if eco is not None:
            result.ecosystems.append(eco)

    # Detect additional entry points from file patterns
    file_entry_points = detect_entry_points(root, result.all_entry_points)
    if file_entry_points:
        if not result.ecosystems:
            result.ecosystems.append(
                EcosystemResult(name="Generic", entry_points=file_entry_points)
            )
        else:
            # Add file-based entry points to first ecosystem
            existing_paths = {e.path for e in result.all_entry_points}
            for ep in file_entry_points:
                if ep.path not in existing_paths:
                    result.ecosystems[0].entry_points.append(ep)

    # Extended analysis detectors
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

    return result


# ---------------------------------------------------------------------------
# T002: Python Ecosystem Detector
# ---------------------------------------------------------------------------


def _parse_pyproject_deps(text: str) -> tuple[list[Dependency], list[Dependency]]:
    """Extract dependencies from pyproject.toml text."""
    runtime_deps: list[Dependency] = []
    dev_deps: list[Dependency] = []

    # Parse [project.dependencies] array
    in_deps = False
    in_optional = False
    current_group = ""

    for line in text.splitlines():
        stripped = line.strip()

        # Section headers
        if stripped == "dependencies = [" or stripped.startswith("dependencies = ["):
            in_deps = True
            # Check if single-line
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
            if stripped == "[project.scripts]":
                in_deps = False
                in_optional = False
            elif stripped.startswith("[project") or stripped.startswith("[tool"):
                in_deps = False
                in_optional = False
            else:
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
            # Look for group = ["pkg1", "pkg2"] pattern
            if "=" in stripped and "[" in stripped:
                current_group = stripped.split("=")[0].strip()
                items_part = stripped.split("[", 1)[1]
                if "]" in items_part:
                    items_part = items_part.split("]")[0]
                for item in items_part.split(","):
                    name = _extract_pkg_name(item.strip().strip("\"' "))
                    if name:
                        cat = (
                            "dev"
                            if current_group in ("dev", "test", "testing")
                            else "runtime"
                        )
                        dev_deps.append(Dependency(name, _extract_version(item), cat))

    # Parse [tool.poetry.dependencies] style
    poetry_deps_match = re.search(
        r"\[tool\.poetry\.dependencies\](.*?)(?=\n\[|\Z)", text, re.DOTALL
    )
    if poetry_deps_match:
        for line in poetry_deps_match.group(1).splitlines():
            if "=" in line and not line.strip().startswith("#"):
                parts = line.strip().split("=", 1)
                name = parts[0].strip()
                if name and name != "python":
                    version = parts[1].strip().strip("\"'{}^ ")
                    runtime_deps.append(Dependency(name, version, "runtime"))

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


def detect_node(root: Path) -> EcosystemResult | None:
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
            if len(parts) >= 2:
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


def _walk_limited(
    root: Path, max_depth: int = 3
) -> Iterator[tuple[str, list[str], list[str]]]:
    """Walk directory tree with depth limit, respecting exclusions."""

    def _recurse(path: Path, depth: int) -> Iterator[tuple[str, list[str], list[str]]]:
        if depth > max_depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda e: e.name)
        except PermissionError:
            return

        dirs = []
        files = []
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name not in EXCLUDED_DIRS and not entry.name.endswith(
                    ".egg-info"
                ):
                    dirs.append(entry.name)
            elif entry.is_file():
                files.append(entry.name)

        yield str(path), dirs, files

        for dname in dirs:
            yield from _recurse(path / dname, depth + 1)

    yield from _recurse(root, 0)


# ---------------------------------------------------------------------------
# T008: Import Graph + Hot File Detection
# ---------------------------------------------------------------------------

# Language-specific import patterns (compiled once)
_PY_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE
)
_JS_IMPORT_RE = re.compile(
    r"""(?:import\s+.*?\s+from\s+['"]([^'"]+)['"]|"""
    r"""import\s+['"]([^'"]+)['"]|"""
    r"""require\s*\(\s*['"]([^'"]+)['"]\s*\))""",
    re.MULTILINE,
)
_GO_IMPORT_RE = re.compile(r'^\s*"([^"]+)"', re.MULTILINE)
_RUST_USE_RE = re.compile(r"^\s*(?:use|mod)\s+([\w:]+)", re.MULTILINE)

_SOURCE_EXTS: set[str] = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".rb",
    ".php",
}


def _extract_imports_from_file(filepath: Path, root: Path) -> list[str]:
    """Extract import targets from a single source file.

    Returns relative module names (not resolved to disk paths).
    """
    ext = filepath.suffix.lower()
    try:
        text = filepath.read_text(errors="replace")
    except OSError:
        return []

    raw: list[str] = []

    if ext in (".py", ".pyi"):
        for m in _PY_IMPORT_RE.finditer(text):
            raw.append(m.group(1) or m.group(2))
    elif ext in (".js", ".jsx", ".ts", ".tsx"):
        for m in _JS_IMPORT_RE.finditer(text):
            raw.append(m.group(1) or m.group(2) or m.group(3))
    elif ext == ".go":
        for m in _GO_IMPORT_RE.finditer(text):
            raw.append(m.group(1))
    elif ext == ".rs":
        for m in _RUST_USE_RE.finditer(text):
            raw.append(m.group(1))

    return raw


def _resolve_import(
    raw_import: str,
    source_file: Path,
    root: Path,
    file_index: dict[str, str],
) -> str | None:
    """Resolve an import string to a project-relative file path.

    Uses a filename index for fast lookup. Returns None for
    external/stdlib imports.
    """
    # Skip stdlib and external packages (match top-level module exactly)
    _top = raw_import.split(".")[0]
    if _top in {
        "os",
        "sys",
        "re",
        "json",
        "typing",
        "collections",
        "pathlib",
        "datetime",
        "dataclasses",
        "abc",
        "functools",
        "itertools",
        "logging",
        "unittest",
        "io",
        "math",
        "hashlib",
        "http",
        "urllib",
        "socket",
        "subprocess",
    }:
        return None

    # For relative imports (Python . prefix), resolve against source dir
    clean = raw_import.lstrip(".")

    # JS/TS relative imports start with ./  or ../
    if raw_import.startswith(("./", "../")):
        source_dir = source_file.parent
        candidate = (source_dir / raw_import).resolve()
        # Try with and without extensions
        for ext in ("", ".js", ".ts", ".tsx", ".jsx"):
            test_path = candidate.parent / (candidate.name + ext)
            if test_path.exists() and test_path.is_file():
                try:
                    rel = str(test_path.relative_to(root))
                    return rel
                except ValueError:
                    continue
        # Try index file in directory
        if candidate.is_dir():
            for idx in ("index.js", "index.ts"):
                idx_path = candidate / idx
                if idx_path.exists():
                    return str(idx_path.relative_to(root))
        return None

    # Module name -> filename heuristic
    parts = clean.rsplit(".", 1)
    stem = parts[-1] if parts else clean
    # Also try the first part (top-level module)
    top_module = clean.split(".")[0] if "." in clean else clean

    for candidate_stem in (stem, top_module):
        for ext in (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs"):
            key = candidate_stem + ext
            if key in file_index:
                return file_index[key]

    return None


def build_import_graph(root: Path) -> ImportGraph:
    """Build an import graph from source files in the project."""
    root = root.resolve()
    graph = ImportGraph()

    # First pass: index all source files by name for resolution
    file_index: dict[str, str] = {}  # filename -> relative path
    source_files: list[Path] = []

    for dirpath, _dirs, files in _walk_limited(root, max_depth=8):
        for fname in files:
            fpath = Path(dirpath) / fname
            if fpath.suffix.lower() in _SOURCE_EXTS:
                rel = str(fpath.relative_to(root))
                file_index.setdefault(fname, rel)
                source_files.append(fpath)

    # Second pass: extract imports and resolve to project files
    for fpath in source_files:
        source_rel = str(fpath.relative_to(root))
        raw_imports = _extract_imports_from_file(fpath, root)
        for raw in raw_imports:
            target = _resolve_import(raw, fpath, root, file_index)
            if target and target != source_rel:
                graph.add_edge(source_rel, target)

    return graph


def detect_hot_files(graph: ImportGraph, threshold: int = 3) -> list[str]:
    """Identify files imported by threshold or more other files.

    Returns paths sorted by import count (descending).
    """
    hot = [
        (path, len(importers))
        for path, importers in graph.imported_by.items()
        if len(importers) >= threshold
    ]
    hot.sort(key=lambda x: x[1], reverse=True)
    return [path for path, _count in hot]


def blast_radius(graph: ImportGraph, target: str) -> BlastResult:
    """BFS over imported_by to find all files affected by changing target.

    Returns direct dependents (depth 1) and transitive dependents
    (depth 2+) with the intermediate file they're reached through.
    """
    result = BlastResult(target=target)

    if target not in graph.imported_by:
        return result

    # BFS (deque for O(1) popleft)
    visited: set[str] = {target}
    # queue entries: (file, depth, via_file)
    queue: deque[tuple[str, int, str]] = deque(
        (dep, 1, target) for dep in sorted(graph.imported_by.get(target, set()))
    )

    while queue:
        current, depth, via = queue.popleft()
        if current in visited:
            continue
        visited.add(current)

        if depth == 1:
            result.direct.append(current)
        else:
            result.transitive.append((current, via))

        for next_dep in sorted(graph.imported_by.get(current, set())):
            if next_dep not in visited:
                queue.append((next_dep, depth + 1, current))

    result.direct.sort()
    result.transitive.sort()
    return result


# ---------------------------------------------------------------------------
# T003: Scan Caching
# ---------------------------------------------------------------------------

_CACHE_VERSION = 1
_CACHE_FILENAME = ".codesight-cache.json"


def compute_fingerprint(root: Path) -> str:
    """Compute a cheap fingerprint for cache invalidation.

    Hashes: file count, max mtime, sorted top-level dir names.
    """
    root = root.resolve()
    file_count = 0
    max_mtime = 0.0
    top_dirs: list[str] = []

    for entry in sorted(root.iterdir()):
        if entry.name in EXCLUDED_DIRS or entry.name.startswith("."):
            continue
        if entry.is_dir():
            top_dirs.append(entry.name)
            for dirpath, dirs, files in _walk_limited(entry, max_depth=6):
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
                file_count += len(files)
                for f in files:
                    try:
                        mt = (Path(dirpath) / f).stat().st_mtime
                        max_mtime = max(max_mtime, mt)
                    except OSError:
                        pass
        elif entry.is_file():
            file_count += 1
            try:
                mt = entry.stat().st_mtime
                max_mtime = max(max_mtime, mt)
            except OSError:
                pass

    raw = f"{file_count}:{max_mtime:.6f}:{','.join(top_dirs)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def save_cache(root: Path, result: ScanResult) -> None:
    """Save scan result to cache file."""
    root = root.resolve()
    cache_path = root / _CACHE_FILENAME
    fingerprint = compute_fingerprint(root)

    data = {
        "version": _CACHE_VERSION,
        "fingerprint": fingerprint,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scan_result": json.loads(render_json(result)),
    }
    cache_path.write_text(json.dumps(data, indent=2))


def _rebuild_scan_result(data: dict) -> ScanResult:
    """Reconstruct a ScanResult from cached JSON data."""
    sr = data["scan_result"]
    directories = [
        DirectoryInfo(
            path=d["path"],
            file_count=d["file_count"],
            primary_language=d.get("primary_language"),
        )
        for d in sr.get("directories", [])
    ]
    ecosystems = []
    for eco in sr.get("ecosystems", []):
        ecosystems.append(
            EcosystemResult(
                name=eco["name"],
                package_manager=eco.get("package_manager"),
                dependencies=[
                    Dependency(
                        name=d["name"],
                        version=d.get("version"),
                        category=d.get("category", "runtime"),
                    )
                    for d in eco.get("dependencies", [])
                ],
                frameworks=[
                    FrameworkMatch(
                        name=f["name"],
                        locations=f.get("locations", []),
                        confidence=f.get("confidence", 1.0),
                    )
                    for f in eco.get("frameworks", [])
                ],
                entry_points=[
                    EntryPoint(path=e["path"], kind=e.get("kind", "main"))
                    for e in eco.get("entry_points", [])
                ],
            )
        )
    routes = [
        RouteInfo(method=r["method"], path=r["path"], file=r["file"])
        for r in sr.get("routes", [])
    ]
    env_vars = [
        EnvVarInfo(
            name=v["name"], file=v["file"], has_default=v.get("has_default", False)
        )
        for v in sr.get("env_vars", [])
    ]
    middleware = [
        MiddlewareInfo(name=m["name"], kind=m["kind"], file=m["file"])
        for m in sr.get("middleware", [])
    ]
    schemas = [
        SchemaModel(
            name=s["name"],
            file=s["file"],
            field_count=s.get("field_count", 0),
            framework=s.get("framework", ""),
        )
        for s in sr.get("schemas", [])
    ]
    te_data = sr.get("token_savings", {})
    token_estimate = TokenEstimate(
        route_tokens=te_data.get("route_tokens", 0),
        hot_file_tokens=te_data.get("hot_file_tokens", 0),
        env_var_tokens=te_data.get("env_var_tokens", 0),
        file_scan_tokens=te_data.get("file_scan_tokens", 0),
    )
    hot_files = sr.get("hot_files", [])

    return ScanResult(
        project_name=sr["project_name"],
        total_files=sr["total_files"],
        directories=directories,
        ecosystems=ecosystems,
        config_files=sr.get("config_files", []),
        hot_files=hot_files,
        hot_file_counts=sr.get("hot_file_counts", {}),
        routes=routes,
        env_vars=env_vars,
        middleware=middleware,
        schemas=schemas,
        token_estimate=token_estimate,
    )


def load_cache(root: Path) -> ScanResult | None:
    """Load cached scan result if fingerprint matches."""
    root = root.resolve()
    cache_path = root / _CACHE_FILENAME

    if not cache_path.exists():
        return None

    try:
        data = json.loads(cache_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    if data.get("version") != _CACHE_VERSION:
        return None

    current_fp = compute_fingerprint(root)
    if data.get("fingerprint") != current_fp:
        return None

    return _rebuild_scan_result(data)


# ---------------------------------------------------------------------------
# T009: Route Detection
# ---------------------------------------------------------------------------

# FastAPI/Starlette: @app.get("/path") or @router.post("/path")
_FASTAPI_ROUTE_RE = re.compile(
    r"@\w+\.(get|post|put|delete|patch|options|head)\s*\(\s*"
    r"""["']([^"']+)["']""",
    re.IGNORECASE,
)

# Flask: @app.route("/path") or @bp.route("/path", methods=["GET"])
_FLASK_ROUTE_RE = re.compile(
    r"@\w+\.route\s*\(\s*"
    r"""["']([^"']+)["']""",
)

# Express/Hono/Koa: app.get('/path', ...) or router.post('/path', ...)
_EXPRESS_ROUTE_RE = re.compile(
    r"\b\w+\.(get|post|put|delete|patch|all|use)\s*\(\s*"
    r"""["'](/[^"']*?)["']""",
)


def _is_test_file(fname: str, rel_path: str) -> bool:
    """Check if a file is a test file (should skip for route detection)."""
    return (
        fname.startswith("test_")
        or fname.endswith("_test.py")
        or fname.endswith(".test.ts")
        or fname.endswith(".test.js")
        or fname.endswith(".spec.ts")
        or fname.endswith(".spec.js")
        or "/tests/" in rel_path
        or "/test/" in rel_path
        or "/__tests__/" in rel_path
    )


def detect_routes(root: Path) -> list[RouteInfo]:
    """Detect API routes from framework-specific patterns."""
    root = root.resolve()
    routes: list[RouteInfo] = []
    seen: set[tuple[str, str]] = set()  # (method, path) dedup

    for dirpath, _dirs, files in _walk_limited(root, max_depth=6):
        for fname in files:
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower()
            if ext not in (".py", ".js", ".ts", ".jsx", ".tsx"):
                continue
            rel = str(fpath.relative_to(root))
            # Skip test files - they contain example routes, not real ones
            if _is_test_file(fname, rel):
                continue

            try:
                raw_text = fpath.read_text(errors="replace")
            except OSError:
                continue

            # Strip comment lines to avoid matching example code
            text = "\n".join(
                line
                for line in raw_text.splitlines()
                if not line.lstrip().startswith(("#", "//", "*", "///"))
            )

            # FastAPI / Starlette
            for m in _FASTAPI_ROUTE_RE.finditer(text):
                method = m.group(1).upper()
                path = m.group(2)
                key = (method, path)
                if key not in seen:
                    seen.add(key)
                    routes.append(RouteInfo(method, path, rel))

            # Flask
            for m in _FLASK_ROUTE_RE.finditer(text):
                path = m.group(1)
                # Flask uses methods= kwarg; default is GET
                method = "GET"
                methods_match = re.search(
                    r"methods\s*=\s*\[([^\]]+)\]",
                    text[m.start() : m.start() + 200],
                )
                if methods_match:
                    method = (
                        methods_match.group(1).strip("\"' ").split(",")[0].strip("\"' ")
                    )
                key = (method.upper(), path)
                if key not in seen:
                    seen.add(key)
                    routes.append(RouteInfo(method.upper(), path, rel))

            # Express / Hono / Koa (JS/TS only)
            if ext in (".js", ".ts", ".jsx", ".tsx"):
                for m in _EXPRESS_ROUTE_RE.finditer(text):
                    method = m.group(1).upper()
                    path = m.group(2)
                    if method == "USE":
                        method = "MW"  # middleware mount
                    key = (method, path)
                    if key not in seen:
                        seen.add(key)
                        routes.append(RouteInfo(method, path, rel))

    return routes


# ---------------------------------------------------------------------------
# T010: Environment Variable Detection
# ---------------------------------------------------------------------------

_PY_ENVIRON_RE = re.compile(
    r"""os\.(?:environ\[["'](\w+)["']\]|"""
    r"""getenv\(["'](\w+)["']|"""
    r"""environ\.get\(["'](\w+)["'])""",
)
_JS_PROCESS_ENV_RE = re.compile(
    r"""process\.env\.(\w+)|process\.env\[["'](\w+)["']\]""",
)
_DOTENV_LINE_RE = re.compile(r"^([A-Z][A-Z0-9_]+)\s*=", re.MULTILINE)


def detect_env_vars(root: Path) -> list[EnvVarInfo]:
    """Detect environment variable references across the project."""
    root = root.resolve()
    found: dict[str, EnvVarInfo] = {}  # name -> info (dedup)

    for dirpath, _dirs, files in _walk_limited(root, max_depth=6):
        for fname in files:
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower()

            # .env / .env.example files
            if fname.startswith(".env"):
                try:
                    text = fpath.read_text(errors="replace")
                except OSError:
                    continue
                rel = str(fpath.relative_to(root))
                for m in _DOTENV_LINE_RE.finditer(text):
                    name = m.group(1)
                    if name not in found:
                        found[name] = EnvVarInfo(name, rel)
                continue

            if ext not in _SOURCE_EXTS:
                continue

            try:
                text = fpath.read_text(errors="replace")
            except OSError:
                continue

            rel = str(fpath.relative_to(root))

            # Python: os.environ, os.getenv, os.environ.get
            if ext == ".py":
                for m in _PY_ENVIRON_RE.finditer(text):
                    name = m.group(1) or m.group(2) or m.group(3)
                    has_default = "getenv" in m.group(0) or "get(" in m.group(0)
                    if name not in found:
                        found[name] = EnvVarInfo(name, rel, has_default)

            # JS/TS: process.env.VAR
            if ext in (".js", ".ts", ".jsx", ".tsx"):
                for m in _JS_PROCESS_ENV_RE.finditer(text):
                    name = m.group(1) or m.group(2)
                    if name not in found:
                        found[name] = EnvVarInfo(name, rel)

    return sorted(found.values(), key=lambda v: v.name)


# ---------------------------------------------------------------------------
# T011: Middleware Detection
# ---------------------------------------------------------------------------

_MIDDLEWARE_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    ("CORS", "cors", re.compile(r"cors|CORSMiddleware|cross.origin", re.IGNORECASE)),
    (
        "Authentication",
        "auth",
        re.compile(
            r"authenticat|require_auth|jwt|oauth|bearer|verify_token|"
            r"@login_required|@auth_required|passport\.authenticate",
            re.IGNORECASE,
        ),
    ),
    (
        "Rate Limiting",
        "rate-limit",
        re.compile(
            r"rate.?limit|throttl|Limiter|slowapi|express.rate.limit",
            re.IGNORECASE,
        ),
    ),
    (
        "Logging",
        "logging",
        re.compile(
            r"request.?log|access.?log|morgan|pino|structlog.*middleware",
            re.IGNORECASE,
        ),
    ),
    (
        "Validation",
        "validation",
        re.compile(
            r"validate.?request|celebrate|express.validator|"
            r"@validate|request.?validation",
            re.IGNORECASE,
        ),
    ),
]


def detect_middleware(root: Path) -> list[MiddlewareInfo]:
    """Detect middleware patterns in the project."""
    root = root.resolve()
    found: dict[str, MiddlewareInfo] = {}  # kind -> info (dedup)

    for dirpath, _dirs, files in _walk_limited(root, max_depth=6):
        for fname in files:
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower()
            if ext not in _SOURCE_EXTS:
                continue
            # Skip test files, tool scripts, and hook scripts
            rel = str(fpath.relative_to(root))
            if _is_test_file(fname, rel):
                continue
            if "/scripts/" in rel or "/hooks/" in rel:
                continue

            try:
                text = fpath.read_text(errors="replace")
            except OSError:
                continue

            # Strip comments and regex/string definitions
            code_lines = [
                line
                for line in text.splitlines()
                if not line.lstrip().startswith(("#", "//", "*"))
                and "re.compile" not in line
                and "_RE = " not in line
                and "_PATTERNS" not in line
            ]
            code_text = "\n".join(code_lines)

            for display_name, kind, pattern in _MIDDLEWARE_PATTERNS:
                if kind not in found and pattern.search(code_text):
                    found[kind] = MiddlewareInfo(display_name, kind, rel)

    return sorted(found.values(), key=lambda m: m.kind)


# ---------------------------------------------------------------------------
# T012: Token Savings Estimation
# ---------------------------------------------------------------------------

TOKENS_PER_ROUTE = 400
TOKENS_PER_HOT_FILE = 150
TOKENS_PER_ENV_VAR = 100
TOKENS_PER_FILE_SCANNED = 80


def estimate_token_savings(result: ScanResult) -> TokenEstimate:
    """Estimate exploration tokens saved by the context map.

    Estimated costs: each route costs ~400 tokens
    of manual discovery, each hot file ~150, each env var ~100,
    and each file scanned ~80 tokens of glob/grep overhead.
    """
    return TokenEstimate(
        route_tokens=len(result.routes) * TOKENS_PER_ROUTE,
        hot_file_tokens=len(result.hot_files) * TOKENS_PER_HOT_FILE,
        env_var_tokens=len(result.env_vars) * TOKENS_PER_ENV_VAR,
        file_scan_tokens=result.total_files * TOKENS_PER_FILE_SCANNED,
    )


# ---------------------------------------------------------------------------
# T005: Strategic Summarizer
# ---------------------------------------------------------------------------


def summarize(
    result: ScanResult,
    max_dirs: int = 8,
    max_deps: int = 8,
    max_frameworks: int = 6,
    max_entry_points: int = 5,
) -> ScanResult:
    """Apply truncation limits to scan result in-place."""
    if len(result.directories) > max_dirs:
        result.truncated_dirs = len(result.directories) - max_dirs
        result.directories = result.directories[:max_dirs]

    for eco in result.ecosystems:
        if len(eco.dependencies) > max_deps:
            eco.dependencies = eco.dependencies[:max_deps]
        if len(eco.frameworks) > max_frameworks:
            eco.frameworks = eco.frameworks[:max_frameworks]
        if len(eco.entry_points) > max_entry_points:
            eco.entry_points = eco.entry_points[:max_entry_points]

    return result


def summarize_dependencies(deps: list[Dependency], max_items: int = 8) -> TruncatedList:
    """Truncate a dependency list with remaining count."""
    if len(deps) <= max_items:
        return TruncatedList(shown=deps, remaining=0)
    return TruncatedList(shown=deps[:max_items], remaining=len(deps) - max_items)


# ---------------------------------------------------------------------------
# Schema/Model Extraction
# ---------------------------------------------------------------------------

_PYTHON_MODEL_BASES = {
    "Base": "SQLAlchemy",
    "db.Model": "SQLAlchemy",
    "DeclarativeBase": "SQLAlchemy",
    "models.Model": "Django",
    "Model": "Django",
    "BaseModel": "Pydantic",
}

_PYTHON_MODEL_RE = re.compile(
    r"^class\s+(\w+)\s*\(\s*("
    + "|".join(re.escape(b) for b in _PYTHON_MODEL_BASES)
    + r")\s*\)\s*:",
    re.MULTILINE,
)

_PRISMA_MODEL_RE = re.compile(r"^model\s+(\w+)\s*\{", re.MULTILINE)

_PYTHON_FIELD_RE = re.compile(
    r"^\s+(\w+)\s*[=:]\s*"
    r"(Column|Field|models\.\w+Field|mapped_column"
    r"|Mapped\[|Optional\[|str|int|float|bool|list\[)",
    re.MULTILINE,
)
_PRISMA_FIELD_RE = re.compile(r"^\s+(\w+)\s+\w+", re.MULTILINE)


def _count_fields_python(body: str) -> int:
    """Count field definitions in a Python class body."""
    return len(_PYTHON_FIELD_RE.findall(body))


_PRISMA_FIELD_STRIPPED_RE = re.compile(r"^(\w+)\s+\w+")


def _count_fields_prisma(body: str) -> int:
    """Count field definitions in a Prisma model body."""
    count = 0
    for line in body.strip().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("@@"):
            continue
        if _PRISMA_FIELD_STRIPPED_RE.match(stripped):
            count += 1
    return count


def detect_schemas(root: Path) -> list[SchemaModel]:
    """Detect ORM model and schema definitions in the project."""
    root = root.resolve()
    schemas: list[SchemaModel] = []

    for dirpath, dirs, files in _walk_limited(root, max_depth=6):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for fname in files:
            fpath = Path(dirpath) / fname
            rel = str(fpath.relative_to(root))

            if _is_test_file(fname, rel):
                continue

            if fpath.suffix == ".prisma":
                try:
                    content = fpath.read_text(errors="replace")
                except OSError:
                    continue
                for match in _PRISMA_MODEL_RE.finditer(content):
                    name = match.group(1)
                    start = match.end()
                    brace_depth = 1
                    end = start
                    while end < len(content) and brace_depth > 0:
                        if content[end] == "{":
                            brace_depth += 1
                        elif content[end] == "}":
                            brace_depth -= 1
                        end += 1
                    body = content[start : end - 1]
                    schemas.append(
                        SchemaModel(
                            name=name,
                            file=rel,
                            field_count=_count_fields_prisma(body),
                            framework="Prisma",
                        )
                    )

            elif fpath.suffix in (".py", ".pyi"):
                try:
                    content = fpath.read_text(errors="replace")
                except OSError:
                    continue
                for match in _PYTHON_MODEL_RE.finditer(content):
                    name = match.group(1)
                    base = match.group(2)
                    framework = _PYTHON_MODEL_BASES.get(base, "Unknown")
                    start = match.end()
                    next_class = re.search(r"\n(?=class\s)", content[start:])
                    if next_class:
                        body = content[start : start + next_class.start()]
                    else:
                        body = content[start:]
                    schemas.append(
                        SchemaModel(
                            name=name,
                            file=rel,
                            field_count=_count_fields_python(body),
                            framework=framework,
                        )
                    )

    # Drop abstract base classes with no fields (e.g. class Base(DeclarativeBase): pass)
    schemas = [s for s in schemas if s.field_count > 0]
    schemas.sort(key=lambda s: s.name)
    return schemas


# ---------------------------------------------------------------------------
# Wiki Knowledge Articles
# ---------------------------------------------------------------------------

_TOPIC_PATTERNS: list[tuple[str, str, list[str], list[str]]] = [
    (
        "auth",
        "Authentication & Authorization",
        ["auth", "login", "session", "permission", "jwt", "oauth", "token"],
        ["jwt", "oauth", "passlib", "bcrypt", "flask_login", "authlib"],
    ),
    (
        "database",
        "Database & Models",
        ["model", "schema", "migration", "orm", "database", "db"],
        [
            "sqlalchemy",
            "django.db",
            "prisma",
            "sqlx",
            "diesel",
            "gorm",
            "drizzle",
            "mongoose",
            "sequelize",
            "typeorm",
        ],
    ),
    (
        "api",
        "API Routes & Endpoints",
        ["route", "endpoint", "handler", "controller", "view", "api"],
        [],
    ),
    (
        "config",
        "Configuration & Environment",
        ["config", "setting", "env", ".env"],
        ["dotenv", "pydantic_settings", "decouple", "environ"],
    ),
    (
        "testing",
        "Testing",
        ["test", "spec", "fixture", "conftest", "factory"],
        ["pytest", "unittest", "jest", "vitest", "mocha"],
    ),
]


def classify_topics(
    result: ScanResult,
) -> dict[str, list[str]]:
    """Classify project files into topic clusters."""
    topics: dict[str, list[str]] = defaultdict(list)

    # Classify files by route presence
    route_files = {r.file for r in result.routes}
    for rf in route_files:
        topics["api"].append(rf)

    # Classify files by env var presence
    env_files = {v.file for v in result.env_vars}
    for ef in env_files:
        if ef not in topics["config"]:
            topics["config"].append(ef)

    # Classify by middleware
    for mw in result.middleware:
        if mw.kind in ("auth", "session"):
            topics["auth"].append(mw.file)
        elif mw.kind == "logging":
            topics["config"].append(mw.file)

    # Classify schemas
    for s in getattr(result, "schemas", []):
        if s.file not in topics["database"]:
            topics["database"].append(s.file)

    # Classify hot files by path patterns
    for hf in result.hot_files:
        hf_lower = hf.lower()
        for topic, _title, path_pats, _imp_pats in _TOPIC_PATTERNS:
            if any(pat in hf_lower for pat in path_pats):
                if hf not in topics[topic]:
                    topics[topic].append(hf)

    # Deduplicate and sort
    for topic, files in topics.items():
        topics[topic] = sorted(set(files))

    # Remove empty topics
    return {k: v for k, v in topics.items() if v}


def _render_wiki_article(
    topic: str, title: str, files: list[str], result: ScanResult
) -> str:
    """Render a single wiki article as markdown."""
    lines = [f"# {title}", ""]

    if topic == "api" and result.routes:
        by_file: dict[str, list[RouteInfo]] = defaultdict(list)
        for r in result.routes:
            by_file[r.file].append(r)
        for rfile, routes in sorted(by_file.items()):
            lines.append(f"## {rfile}")
            for r in routes:
                lines.append(f"  {r.method:<7} {r.path}")
            lines.append("")
    elif topic == "database" and getattr(result, "schemas", []):
        for s in result.schemas:
            fields = f" ({s.field_count} fields)" if s.field_count else ""
            lines.append(f"  - {s.name}: {s.file}{fields}")
        lines.append("")

    if topic == "config" and result.env_vars:
        lines.append("## Environment Variables")
        for v in result.env_vars[:20]:
            default = " (has default)" if v.has_default else " (required)"
            lines.append(f"  - {v.name}{default}")
        if len(result.env_vars) > 20:
            lines.append(f"  ...{len(result.env_vars) - 20} more")
        lines.append("")

    lines.append("## Related Files")
    lines.append("")
    for f in files[:20]:
        lines.append(f"  - {f}")
    if len(files) > 20:
        lines.append(f"  ...{len(files) - 20} more")
    lines.append("")

    return "\n".join(lines)


def generate_wiki(root: Path, result: ScanResult) -> None:
    """Generate .codesight/ wiki directory with per-topic articles."""
    root = root.resolve()
    topics = classify_topics(result)

    if not topics:
        return

    wiki_dir = root / ".codesight"
    wiki_dir.mkdir(exist_ok=True)

    generated: list[tuple[str, str]] = []
    for topic, files in sorted(topics.items()):
        title = topic
        for t_name, t_title, _pats, _imps in _TOPIC_PATTERNS:
            if t_name == topic:
                title = t_title
                break
        content = _render_wiki_article(topic, title, files, result)
        article_path = wiki_dir / f"{topic}.md"
        article_path.write_text(content)
        generated.append((topic, title))

    index_lines = [
        f"# Context Wiki: {result.project_name}",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Topics",
        "",
    ]
    for topic, title in generated:
        count = len(topics[topic])
        index_lines.append(f"  - [{title}]({topic}.md) ({count} files)")
    index_lines.append("")

    (wiki_dir / "INDEX.md").write_text("\n".join(index_lines))


# ---------------------------------------------------------------------------
# T006: Markdown and JSON Renderers
# ---------------------------------------------------------------------------


def render_markdown(
    result: ScanResult,
    max_dirs: int = 8,
    max_deps: int = 8,
    include_timestamp: bool = True,
) -> str:
    """Render scan result as markdown context map."""
    result = summarize(result, max_dirs=max_dirs, max_deps=max_deps)

    lines: list[str] = []
    ts = (
        datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        if include_timestamp
        else ""
    )
    header_parts = [f"# Context Map: {result.project_name}"]
    meta_parts = []
    if ts:
        meta_parts.append(f"Generated: {ts}")
    meta_parts.append(f"Files: {result.total_files}")
    if meta_parts:
        header_parts.append(" | ".join(meta_parts))
    lines.extend(header_parts)
    lines.append("")

    # Structure section
    if result.directories:
        lines.append("## Structure")
        lines.append("")
        for d in result.directories:
            lang = f" ({d.primary_language})" if d.primary_language else ""
            lines.append(f"  {d.path:<20s} {d.file_count:>4d} files{lang}")
        if result.truncated_dirs > 0:
            lines.append(f"  ...{result.truncated_dirs} more directories")
        lines.append("")

    # Ecosystems
    for eco in result.ecosystems:
        if eco.name == "Generic":
            continue
        # Dependencies
        if eco.dependencies:
            lines.append(f"## Dependencies ({eco.name})")
            if eco.package_manager:
                lines.append(f"Package manager: {eco.package_manager}")
            lines.append("")
            shown_deps = summarize_dependencies(eco.dependencies, max_items=max_deps)
            for dep in shown_deps.shown:
                ver = f" {dep.version}" if dep.version else ""
                cat = " (dev)" if dep.category == "dev" else ""
                lines.append(f"  - {dep.name}{ver}{cat}")
            if shown_deps.remaining > 0:
                lines.append(f"  ...{shown_deps.remaining} more")
            lines.append("")

    # Frameworks (combined across ecosystems)
    all_frameworks = result.all_frameworks
    if all_frameworks:
        lines.append("## Frameworks Detected")
        lines.append("")
        seen = set()
        for fw in all_frameworks:
            if fw.name not in seen:
                seen.add(fw.name)
                lines.append(f"  - {fw.name}")
        lines.append("")

    # Entry points (combined)
    all_eps = result.all_entry_points
    if all_eps:
        lines.append("## Entry Points")
        lines.append("")
        for ep in all_eps:
            lines.append(f"  - {ep.path} ({ep.kind})")
        lines.append("")

    # Routes
    if result.routes:
        lines.append("## Routes")
        lines.append("")
        for r in result.routes[:15]:
            lines.append(f"  {r.method:<6s} {r.path}  ({r.file})")
        if len(result.routes) > 15:
            lines.append(f"  ...{len(result.routes) - 15} more")
        lines.append("")

    # Hot files
    if result.hot_files:
        lines.append("## Hot Files (high blast radius)")
        lines.append("")
        graph = result.import_graph
        for hf in result.hot_files[:8]:
            if graph and hf in graph.imported_by:
                count = len(graph.imported_by[hf])
            else:
                count = result.hot_file_counts.get(hf, 0)
            lines.append(f"  - {hf} ({count} importers)")
        if len(result.hot_files) > 8:
            lines.append(f"  ...{len(result.hot_files) - 8} more")
        lines.append("")

    # Environment variables
    if result.env_vars:
        lines.append("## Environment Variables")
        lines.append("")
        for ev in result.env_vars[:12]:
            default_mark = " (has default)" if ev.has_default else " (required)"
            lines.append(f"  - {ev.name}{default_mark}")
        if len(result.env_vars) > 12:
            lines.append(f"  ...{len(result.env_vars) - 12} more")
        lines.append("")

    # Middleware
    if result.middleware:
        lines.append("## Middleware")
        lines.append("")
        for mw in result.middleware:
            lines.append(f"  - {mw.name} ({mw.file})")
        lines.append("")

    # Schemas section
    if result.schemas:
        lines.append("## Models/Schemas")
        lines.append("")
        shown = result.schemas[:8]
        for s in shown:
            fields = f"({s.field_count} fields)" if s.field_count else ""
            lines.append(f"  {s.name:<16} {s.file} {fields}")
        if len(result.schemas) > 8:
            lines.append(f"  ...{len(result.schemas) - 8} more")
        lines.append("")

    # Config files
    if result.config_files:
        lines.append("## Configuration")
        lines.append("")
        for cf in result.config_files[:6]:
            lines.append(f"  - {cf}")
        if len(result.config_files) > 6:
            lines.append(f"  ...{len(result.config_files) - 6} more")
        lines.append("")

    # Token savings estimate
    if result.token_estimate and result.token_estimate.total > 0:
        est = result.token_estimate
        lines.append(f"## Token Savings: ~{_round_tokens(est.total)} tokens saved")
        lines.append("")
        if est.route_tokens:
            lines.append(f"  Routes: ~{_round_tokens(est.route_tokens)}")
        if est.hot_file_tokens:
            lines.append(f"  Hot files: ~{_round_tokens(est.hot_file_tokens)}")
        if est.env_var_tokens:
            lines.append(f"  Env vars: ~{_round_tokens(est.env_var_tokens)}")
        if est.file_scan_tokens:
            lines.append(f"  File scanning: ~{_round_tokens(est.file_scan_tokens)}")
        lines.append("")

    output = "\n".join(lines)

    # Replace token estimate in header
    output_tokens = len(output) // 4
    output = output.replace("~calculating", f"~{_round_tokens(output_tokens)} tokens")

    return output


def _round_tokens(n: int) -> str:
    """Round token count to nearest 100 for stable output."""
    if n < 100:
        return str(n)
    rounded = round(n / 100) * 100
    return f"{rounded:,}"


def _copy_result(result: ScanResult) -> ScanResult:
    """Deep copy to prevent mutation of nested lists during rendering."""
    return copy.deepcopy(result)


def render_json(result: ScanResult) -> str:
    """Render scan result as JSON."""
    data = {
        "project_name": result.project_name,
        "total_files": result.total_files,
        "directories": [
            {
                "path": d.path,
                "file_count": d.file_count,
                "primary_language": d.primary_language,
            }
            for d in result.directories
        ],
        "ecosystems": [
            {
                "name": eco.name,
                "package_manager": eco.package_manager,
                "dependencies": [
                    {"name": d.name, "version": d.version, "category": d.category}
                    for d in eco.dependencies
                ],
                "frameworks": [{"name": f.name} for f in eco.frameworks],
                "entry_points": [
                    {"path": e.path, "kind": e.kind} for e in eco.entry_points
                ],
            }
            for eco in result.ecosystems
        ],
        "config_files": result.config_files,
        "routes": [
            {"method": r.method, "path": r.path, "file": r.file} for r in result.routes
        ],
        "hot_files": result.hot_files,
        "hot_file_counts": result.hot_file_counts,
        "env_vars": [
            {"name": v.name, "file": v.file, "has_default": v.has_default}
            for v in result.env_vars
        ],
        "middleware": [
            {"name": m.name, "kind": m.kind, "file": m.file} for m in result.middleware
        ],
        "schemas": [
            {
                "name": s.name,
                "file": s.file,
                "field_count": s.field_count,
                "framework": s.framework,
            }
            for s in result.schemas
        ],
        "token_savings": {
            "route_tokens": result.token_estimate.route_tokens
            if result.token_estimate
            else 0,
            "hot_file_tokens": result.token_estimate.hot_file_tokens
            if result.token_estimate
            else 0,
            "env_var_tokens": result.token_estimate.env_var_tokens
            if result.token_estimate
            else 0,
            "file_scan_tokens": result.token_estimate.file_scan_tokens
            if result.token_estimate
            else 0,
            "total": result.token_estimate.total if result.token_estimate else 0,
        },
        "estimated_tokens": len(
            render_markdown(
                _copy_result(result),
                include_timestamp=False,
            )
        )
        // 4,
    }
    return json.dumps(data, indent=2)


def render_blast_radius(result: BlastResult) -> str:
    """Render blast radius result as markdown."""
    lines = [
        f"# Blast Radius: {result.target}",
        f"Direct dependents: {len(result.direct)}"
        f" | Transitive: {len(result.transitive)}",
        "",
    ]

    if result.direct:
        lines.append("## Direct (imported by)")
        for f in result.direct:
            lines.append(f"  {f}")
        lines.append("")

    if result.transitive:
        lines.append("## Transitive (2nd+ degree)")
        for f, via in result.transitive:
            lines.append(f"  {f} (via {via})")
        lines.append("")

    if result.total_affected == 0:
        lines.append("No dependents found.")

    return "\n".join(lines)


_VALID_SECTIONS = {
    "structure",
    "deps",
    "routes",
    "hot-files",
    "env",
    "middleware",
    "models",
    "frameworks",
}


def render_section(result: ScanResult, section: str) -> str | None:
    """Render a single section of the context map.

    Returns None if the section name is invalid.
    """
    if section not in _VALID_SECTIONS:
        return None

    lines: list[str] = []

    if section == "structure":
        for d in result.directories[:12]:
            lang = f" ({d.primary_language})" if d.primary_language else ""
            lines.append(f"  {d.path:<20} {d.file_count} files{lang}")
        if result.truncated_dirs:
            lines.append(f"  ...{result.truncated_dirs} more directories")

    elif section == "deps":
        for eco in result.ecosystems:
            pm = f" ({eco.package_manager})" if eco.package_manager else ""
            lines.append(f"## {eco.name}{pm}")
            for dep in eco.dependencies[:12]:
                ver = f" {dep.version}" if dep.version else ""
                lines.append(f"  - {dep.name}{ver}")
            remaining = len(eco.dependencies) - 12
            if remaining > 0:
                lines.append(f"  ...{remaining} more")
            lines.append("")

    elif section == "routes":
        for r in result.routes[:20]:
            lines.append(f"  {r.method:<7} {r.path:<30} ({r.file})")
        if len(result.routes) > 20:
            lines.append(f"  ...{len(result.routes) - 20} more")

    elif section == "hot-files":
        graph = result.import_graph
        for hf in result.hot_files[:15]:
            if graph and hf in graph.imported_by:
                count = len(graph.imported_by[hf])
            else:
                count = result.hot_file_counts.get(hf, 0)
            lines.append(f"  - {hf} ({count} importers)")
        if len(result.hot_files) > 15:
            lines.append(f"  ...{len(result.hot_files) - 15} more")

    elif section == "env":
        for v in result.env_vars[:20]:
            default = " (has default)" if v.has_default else " (required)"
            lines.append(f"  - {v.name}{default}")
        if len(result.env_vars) > 20:
            lines.append(f"  ...{len(result.env_vars) - 20} more")

    elif section == "middleware":
        for m in result.middleware:
            lines.append(f"  - {m.name} [{m.kind}] ({m.file})")

    elif section == "models":
        schemas = getattr(result, "schemas", [])
        for s in schemas[:12]:
            fields = f" ({s.field_count} fields)" if s.field_count else ""
            lines.append(f"  {s.name:<16} {s.file}{fields}")
        if len(schemas) > 12:
            lines.append(f"  ...{len(schemas) - 12} more")

    elif section == "frameworks":
        for fw in result.all_frameworks:
            locs = ", ".join(fw.locations[:3])
            lines.append(f"  - {fw.name} ({locs})")

    return "\n".join(lines) if lines else "(empty)"


# ---------------------------------------------------------------------------
# T007: CLI Interface
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a compressed context map for a project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["md", "json"],
        default="md",
        help="Output format (default: md)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=5000,
        help="Target maximum token count (default: 5000)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Write output to file instead of stdout",
    )
    parser.add_argument(
        "--blast",
        type=str,
        default=None,
        metavar="FILE",
        help="Show blast radius for a specific file",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        default=False,
        help="Force fresh scan, ignore cached results",
    )
    parser.add_argument(
        "--no-wiki",
        action="store_true",
        default=False,
        help="Skip wiki article generation",
    )
    parser.add_argument(
        "--wiki-only",
        action="store_true",
        default=False,
        help="Generate wiki articles only, no stdout output",
    )
    parser.add_argument(
        "--section",
        type=str,
        default=None,
        metavar="NAME",
        help=("Output a single section: " + ", ".join(sorted(_VALID_SECTIONS))),
    )

    args = parser.parse_args(argv)
    root = Path(args.path).resolve()

    if not root.is_dir():
        print(f"Error: '{args.path}' is not a valid directory", file=sys.stderr)
        return 1

    if args.blast:
        graph = build_import_graph(root)
        blast_file = args.blast
        br = blast_radius(graph, blast_file)
        output = render_blast_radius(br)
        if args.output:
            Path(args.output).write_text(output)
        else:
            print(output)
        return 0

    # Try cache first
    result = None
    if not args.no_cache:
        result = load_cache(root)

    if result is None:
        result = scan_directory(root)
        try:
            save_cache(root, result)
        except OSError:
            pass  # read-only filesystem (CI, Docker) — scan result is still valid

    if args.section:
        section_out = render_section(result, args.section)
        if section_out is None:
            print(
                f"Error: unknown section '{args.section}'. "
                f"Valid: {', '.join(sorted(_VALID_SECTIONS))}",
                file=sys.stderr,
            )
            return 1
        if args.output:
            Path(args.output).write_text(section_out)
        else:
            print(section_out)
        return 0

    # Wiki generation
    if not args.no_wiki or args.wiki_only:
        try:
            generate_wiki(root, result)
        except OSError as e:
            print(f"Warning: wiki generation failed: {e}", file=sys.stderr)

    if args.wiki_only:
        return 0

    # Adjust limits based on max-tokens target
    max_deps = max(4, min(12, args.max_tokens // 500))
    max_dirs = max(4, min(12, args.max_tokens // 400))

    if args.format == "json":
        output = render_json(result)
    else:
        output = render_markdown(result, max_dirs=max_dirs, max_deps=max_deps)

    if args.output:
        Path(args.output).write_text(output)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
