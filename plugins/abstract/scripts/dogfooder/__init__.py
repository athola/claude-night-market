"""Dogfooder package - Makefile QA for documentation coverage.

Re-exports all public symbols so callers can do:
    from dogfooder import MakefileDogfooder
    from dogfooder import load_target_catalog
"""

from __future__ import annotations

from dogfooder.parser import (
    DocumentationCommandExtractor,
    MakefileAnalyzer,
    load_target_catalog,
)
from dogfooder.reporter import MakefileDogfooder, ProcessingConfig
from dogfooder.validator import (
    MakefileTargetGenerator,
    generate_makefile,
    run_preflight_checks,
    validate_working_directory,
)

__all__ = [
    "load_target_catalog",
    "DocumentationCommandExtractor",
    "MakefileAnalyzer",
    "MakefileTargetGenerator",
    "MakefileDogfooder",
    "ProcessingConfig",
    "generate_makefile",
    "run_preflight_checks",
    "validate_working_directory",
]
