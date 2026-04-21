"""Shared data structures and constants for context_scanner."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Section(str, Enum):
    """Valid section identifiers for render_section()."""

    STRUCTURE = "structure"
    DEPS = "deps"
    ROUTES = "routes"
    HOT_FILES = "hot-files"
    ENV = "env"
    MIDDLEWARE = "middleware"
    MODELS = "models"
    FRAMEWORKS = "frameworks"


# ---------------------------------------------------------------------------
# Constants
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

# Token savings estimation constants
TOKENS_PER_ROUTE = 400
TOKENS_PER_HOT_FILE = 150
TOKENS_PER_ENV_VAR = 100
TOKENS_PER_FILE_SCANNED = 80


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


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
# File-system helpers (no sibling imports — safe for all modules)
# ---------------------------------------------------------------------------


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

        dirs: list[str] = []
        files: list[str] = []
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
