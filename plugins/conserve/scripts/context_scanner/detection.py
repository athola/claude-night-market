"""Route, environment variable, middleware, and schema detection."""

from __future__ import annotations

import re
from pathlib import Path

from .models import (
    EXCLUDED_DIRS,
    TOKENS_PER_ENV_VAR,
    TOKENS_PER_FILE_SCANNED,
    TOKENS_PER_HOT_FILE,
    TOKENS_PER_ROUTE,
    EnvVarInfo,
    MiddlewareInfo,
    RouteInfo,
    ScanResult,
    SchemaModel,
    TokenEstimate,
    _walk_limited,
)

# ---------------------------------------------------------------------------
# Import graph source extensions (shared with import_graph module)
# ---------------------------------------------------------------------------

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


def detect_routes(root: Path) -> list[RouteInfo]:  # noqa: PLR0912, C901 - one branch per framework (FastAPI/Flask/Express)
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


def detect_env_vars(root: Path) -> list[EnvVarInfo]:  # noqa: PLR0912, C901 - branches per language and file type
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


def detect_schemas(root: Path) -> list[SchemaModel]:  # noqa: PLR0912, C901 - one branch per ORM framework (SQLAlchemy/Django/Pydantic/Prisma)
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
