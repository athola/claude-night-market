"""Analyzer lenses for the Insight Engine.

Each lens is a Python module with:
- LENS_META: dict with name, insight_types, weight, description
- analyze(context: AnalysisContext) -> list[Finding]

Lenses are auto-discovered by scanning this package for
modules matching the convention.
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Any

from insight_types import AnalysisContext, Finding


def discover_lenses(
    weight_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Discover all available lenses in this package.

    Args:
        weight_filter: If set, only return lenses matching
            this weight ("lightweight" or "deep").

    Returns:
        List of dicts with 'meta' and 'analyze' keys.

    """
    lenses: list[dict[str, Any]] = []
    package_path = Path(__file__).parent

    for _importer, modname, _ispkg in pkgutil.iter_modules([str(package_path)]):
        try:
            module = importlib.import_module(f"lenses.{modname}")
        except ImportError:
            continue

        meta = getattr(module, "LENS_META", None)
        analyze_fn = getattr(module, "analyze", None)

        if meta is None or analyze_fn is None:
            continue

        if weight_filter and meta.get("weight") != weight_filter:
            continue

        lenses.append(
            {
                "meta": meta,
                "analyze": analyze_fn,
                "module": modname,
            }
        )

    return lenses


def run_lenses(
    context: AnalysisContext,
    weight_filter: str | None = None,
) -> list[Finding]:
    """Run all matching lenses and collect findings.

    Args:
        context: Analysis context with metrics and history.
        weight_filter: Only run lenses of this weight.

    Returns:
        Combined list of findings from all lenses.

    """
    findings: list[Finding] = []
    for lens in discover_lenses(weight_filter=weight_filter):
        try:
            result = lens["analyze"](context)
            if result:
                findings.extend(result)
        except Exception as exc:
            sys.stderr.write(f"[lenses] {lens['meta']['name']} failed: {exc}\n")
            continue
    return findings
