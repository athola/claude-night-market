"""ADR + architecture documentation analysis (AR-01)."""

from __future__ import annotations

from typing import Any

from ._constants import MIN_ADR_SECTIONS


class DocumentationMixin:
    """Architectural decision record + documentation completeness checks."""

    def analyze_adrs(self, context: Any) -> dict[str, Any]:
        """Analyze Architectural Decision Records."""
        files = context.get_files()
        adr_files = [f for f in files if "adr" in f.lower() and f.endswith(".md")]

        total_adrs = len(adr_files)
        completeness_score = 0.0
        adrs = []

        if total_adrs > 0:
            complete_count = 0
            for adr_file in adr_files:
                content = context.get_file_content(adr_file)

                required_sections = ["Status", "Context", "Decision", "Consequences"]
                sections_found = sum(
                    1 for section in required_sections if section in content
                )

                adr_info = {
                    "file": adr_file,
                    "completeness": sections_found / len(required_sections),
                }
                adrs.append(adr_info)

                if sections_found >= MIN_ADR_SECTIONS:
                    complete_count += 1

            completeness_score = complete_count / total_adrs if total_adrs > 0 else 0.0

        return {
            "total_adrs": total_adrs,
            "completeness_score": completeness_score,
            "adrs": adrs,
        }

    def analyze_architecture_documentation(self, context: Any) -> dict[str, Any]:
        """Analyze architecture documentation completeness."""
        files = context.get_files()
        documentation_found = False
        missing_docs = []

        doc_patterns = {
            "architecture_overview": ["architecture.md", "overview.md", "readme.md"],
            "design_decisions": ["adr/", "decisions/", "design.md"],
            "component_diagrams": [".drawio", ".puml", "diagrams/", "architecture.png"],
            "api_documentation": ["api.md", "openapi", "swagger"],
        }

        found_docs = set()
        for doc_type, patterns in doc_patterns.items():
            if any(pattern.lower() in f.lower() for pattern in patterns for f in files):
                found_docs.add(doc_type)
                documentation_found = True

        for doc_type in doc_patterns:
            if doc_type not in found_docs:
                missing_docs.append(doc_type)

        return {
            "documentation_found": documentation_found,
            "missing_docs": missing_docs,
        }


__all__ = ["DocumentationMixin"]
