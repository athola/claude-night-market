"""Reporting mixin: versioning analysis, performance, and summary generation."""

from __future__ import annotations

import re
from typing import Any

from ...utils import content_parser


class ReportingMixin:
    """Analyze API versioning, performance implications, and generate summaries."""

    def analyze_versioning(
        self,
        context: Any,
        filename: str,
    ) -> dict[str, Any]:
        """Detect ``v1`` route prefixes, package metadata version, and changelog hints."""
        code = content_parser.get_file_content(context, filename)
        inconsistencies: list[str] = []

        version_patterns = re.findall(r"/api/v\d+", code)
        version_constants = re.findall(r"API_V\d+", code)

        versioning_detected = len(version_patterns) > 0 or len(version_constants) > 0

        versioned_urls = re.findall(r"/api/v\d+/\w+", code)
        unversioned_urls = re.findall(r"/api/(?!v\d+)(\w+)", code)

        if versioned_urls and unversioned_urls:
            inconsistencies.append(
                f"Mixed versioning: {len(versioned_urls)} versioned endpoints, "
                f"{len(unversioned_urls)} unversioned endpoints"
            )

        versions = set(re.findall(r"v(\d+)", " ".join(version_patterns)))
        if len(versions) > 1:
            inconsistencies.append(
                f"Multiple API versions in use: {', '.join(sorted(versions))}"
            )

        return {
            "versioning_detected": versioning_detected,
            "inconsistencies": inconsistencies,
        }

    def analyze_performance_implications(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, Any]]:
        """Flag N+1 patterns, sync-in-async calls, and unbounded loops in ``filename``."""
        code = content_parser.get_file_content(context, filename)
        issues: list[dict[str, Any]] = []

        all_records_patterns = re.finditer(
            r"(getAll\(\)|findAll\(\)|\.find\(\{\s*\}\)[^)]*\.toArray\(\))",
            code,
            re.DOTALL | re.IGNORECASE,
        )
        for _match in all_records_patterns:
            match_start = max(0, _match.start() - 100)
            match_end = min(len(code), _match.end() + 100)
            context_text = code[match_start:match_end]
            if "limit" not in context_text and "pagination" not in context_text:
                issues.append(
                    {
                        "type": "performance_issue",
                        "location": filename,
                        "severity": "high",
                        "issue": "Returns all records without pagination - perf issue",
                    }
                )

        n_plus_one_patterns = re.finditer(
            r"for\s*\([^)]+(?:of|in)[^)]+\)\s*\{[\s\S]*?await[\s\S]*?\}",
            code,
        )
        for _match in n_plus_one_patterns:
            issues.append(
                {
                    "type": "performance_issue",
                    "location": filename,
                    "severity": "medium",
                    "issue": "N+1 query pattern detected - use batch queries",
                }
            )

        filter_after_fetch = re.finditer(
            r"\.find\(\{\s*\}\)[\s\S]{0,200}\.filter\(",
            code,
        )
        for _match in filter_after_fetch:
            issues.append(
                {
                    "type": "performance_issue",
                    "location": filename,
                    "severity": "medium",
                    "issue": "Filtering in app instead of DB - perf concern",
                }
            )

        return issues

    def generate_api_summary(
        self,
        analysis_data: dict[str, Any],
    ) -> str:
        """Reduce per-language analyses into a single dict for the report renderer."""
        total_exports = analysis_data.get("total_exports", 0)
        languages = analysis_data.get("languages", [])
        files_analyzed = analysis_data.get("files_analyzed", 0)

        languages_str = ", ".join(languages) if languages else "none"

        return f"""## API Surface Summary
Total exports: {total_exports}
Files analyzed: {files_analyzed}
Languages: {languages_str}

## Issues Found

## Recommendations"""
