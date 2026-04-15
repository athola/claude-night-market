"""Context scanner subpackage - re-exports the full public API."""

# ruff: noqa: F401

# Models and constants
# Caching
from .cache import (
    compute_fingerprint,
    load_cache,
    save_cache,
)

# CLI
from .cli import main

# Detection (routes, env vars, middleware, schemas)
from .detection import (
    detect_env_vars,
    detect_middleware,
    detect_routes,
    detect_schemas,
    estimate_token_savings,
)

# Ecosystem detection
from .ecosystems import (
    ENTRY_POINT_PATTERNS,
    _extract_pkg_name,
    _extract_version,
    _parse_pyproject_deps,
    _parse_pyproject_scripts,
    _parse_requirements_txt,
    _walk_limited,
    detect_entry_points,
    detect_go,
    detect_java,
    detect_node,
    detect_python,
    detect_rust,
    scan_directory,
)

# Import graph analysis
from .import_graph import (
    blast_radius,
    build_import_graph,
    detect_hot_files,
)
from .models import (
    EXCLUDED_DIRS,
    EXTENSION_LANGUAGES,
    GO_FRAMEWORKS,
    NODE_FRAMEWORKS,
    PYTHON_FRAMEWORKS,
    RUST_FRAMEWORKS,
    TOKENS_PER_ENV_VAR,
    TOKENS_PER_FILE_SCANNED,
    TOKENS_PER_HOT_FILE,
    TOKENS_PER_ROUTE,
    BlastResult,
    Dependency,
    DirectoryInfo,
    EcosystemResult,
    EntryPoint,
    EnvVarInfo,
    FrameworkMatch,
    ImportGraph,
    MiddlewareInfo,
    RouteInfo,
    ScanResult,
    SchemaModel,
    TokenEstimate,
    TruncatedList,
    WikiArticle,
)

# Renderers
from .renderers import (
    _VALID_SECTIONS,
    _copy_result,
    _round_tokens,
    classify_topics,
    generate_wiki,
    render_blast_radius,
    render_json,
    render_markdown,
    render_section,
    summarize,
    summarize_dependencies,
)

__all__ = [
    # Models
    "BlastResult",
    "Dependency",
    "DirectoryInfo",
    "EcosystemResult",
    "EntryPoint",
    "EnvVarInfo",
    "FrameworkMatch",
    "ImportGraph",
    "MiddlewareInfo",
    "RouteInfo",
    "ScanResult",
    "SchemaModel",
    "TokenEstimate",
    "TruncatedList",
    "WikiArticle",
    # Constants
    "EXCLUDED_DIRS",
    "EXTENSION_LANGUAGES",
    "GO_FRAMEWORKS",
    "NODE_FRAMEWORKS",
    "PYTHON_FRAMEWORKS",
    "RUST_FRAMEWORKS",
    "TOKENS_PER_ENV_VAR",
    "TOKENS_PER_FILE_SCANNED",
    "TOKENS_PER_HOT_FILE",
    "TOKENS_PER_ROUTE",
    "ENTRY_POINT_PATTERNS",
    "_VALID_SECTIONS",
    # Ecosystem detection
    "scan_directory",
    "detect_python",
    "detect_node",
    "detect_rust",
    "detect_go",
    "detect_java",
    "detect_entry_points",
    "_walk_limited",
    "_parse_pyproject_deps",
    "_extract_pkg_name",
    "_extract_version",
    "_parse_requirements_txt",
    "_parse_pyproject_scripts",
    # Import graph
    "build_import_graph",
    "detect_hot_files",
    "blast_radius",
    # Cache
    "compute_fingerprint",
    "save_cache",
    "load_cache",
    # Detection
    "detect_routes",
    "detect_env_vars",
    "detect_middleware",
    "detect_schemas",
    "estimate_token_savings",
    # Renderers
    "render_markdown",
    "render_json",
    "render_blast_radius",
    "render_section",
    "summarize",
    "summarize_dependencies",
    "classify_topics",
    "generate_wiki",
    "_copy_result",
    "_round_tokens",
    # CLI
    "main",
]
