"""Scan result caching logic."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .models import (
    EXCLUDED_DIRS,
    Dependency,
    DirectoryInfo,
    EcosystemResult,
    EntryPoint,
    EnvVarInfo,
    FrameworkMatch,
    MiddlewareInfo,
    RouteInfo,
    ScanResult,
    SchemaModel,
    TokenEstimate,
    _walk_limited,
)
from .renderers import render_json

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
