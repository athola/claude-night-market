"""Data flow, scalability, security, technical-debt analyses (AR-01)."""

from __future__ import annotations

import re
from typing import Any

from ._constants import logger


class QualityMixin:
    """Data flow + scalability + security + technical-debt analyses."""

    def analyze_data_flow(self, context: Any) -> dict[str, Any]:
        """Analyze data flow architecture patterns."""
        files = context.get_files()
        pattern_detected = None
        flow_components = []

        pipes_keywords = ["pipes", "pipe", "filters", "filter"]
        if any(keyword in f.lower() for keyword in pipes_keywords for f in files):
            pattern_detected = "pipes_filters"
            flow_components.extend(
                [
                    comp
                    for comp in ["pipes", "filters", "transforms", "sinks"]
                    if any(comp in f.lower() for f in files)
                ]
            )

        batch_keywords = ["batch", "sequential", "stages"]
        if any(keyword in f.lower() for keyword in batch_keywords for f in files):
            if pattern_detected is None:
                pattern_detected = "batch_sequential"

        stream_keywords = ["stream", "streaming", "kafka", "kinesis"]
        if any(keyword in f.lower() for keyword in stream_keywords for f in files):
            if pattern_detected is None:
                pattern_detected = "streams"

        return {
            "pattern_detected": pattern_detected,
            "flow_components": flow_components,
        }

    def _get_any_content(self, context: Any) -> str:
        """Fetch file content from context, trying all available files."""
        try:
            content = context.get_file_content("") or ""
            if content:
                return content
        except OSError:
            pass
        except NotImplementedError as exc:
            logger.debug("context does not support get_file_content(''): %s", exc)
        try:
            for file_path in context.get_files():
                try:
                    content = context.get_file_content(file_path)
                    if content:
                        return str(content)
                except OSError:
                    continue
        except OSError:
            pass
        except NotImplementedError as exc:
            logger.debug("context does not support get_files()/per-file fetch: %s", exc)
        return ""

    def analyze_scalability_patterns(self, context: Any) -> dict[str, Any]:
        """Analyze scalability patterns and bottlenecks."""
        bottlenecks = []
        scalability_score = 10.0

        content = self._get_any_content(context)

        if "_instance" in content and "cls._instance" in content:
            bottlenecks.append(
                {
                    "type": "stateful_singleton",
                    "location": "code",
                    "issue": "Stateful singleton limits horizontal scaling",
                }
            )
            scalability_score -= 2.0

        if "cache = {}" in content or "self.cache" in content:
            bottlenecks.append(
                {
                    "type": "in_memory_state",
                    "location": "code",
                    "issue": "In-memory cache prevents horizontal scaling",
                }
            )
            scalability_score -= 1.5

        sequential_patterns = [
            re.compile(r"for\s+\w+\s+in\s+.*:\s*\n\s+for\s+\w+\s+in\s+"),
            re.compile(
                r"for\s+\w+\s+in\s+.*:\s*\n(?:.*\n)*?\s+(?:time\.sleep|requests\.\w+|db\.|cursor\.)"
            ),
        ]
        if any(p.search(content) for p in sequential_patterns):
            bottlenecks.append(
                {
                    "type": "sequential_processing",
                    "location": "code",
                    "issue": "Sequential processing limits throughput",
                }
            )
            scalability_score -= 1.0

        scalability_score = max(scalability_score, 0.0)

        return {
            "scalability_score": scalability_score,
            "bottlenecks": bottlenecks,
        }

    def analyze_security_architecture(self, context: Any) -> dict[str, Any]:
        """Analyze security architecture patterns."""
        vulnerabilities = []
        security_score = 10.0

        content = self._get_any_content(context)

        sensitive_operations = ["def delete_all", "def delete_user", "def remove_all"]
        for operation in sensitive_operations:
            if operation in content:
                method_start = content.find(operation)
                method_end = content.find("\n    def ", method_start + len(operation))
                if method_end == -1:
                    method_end = content.find("\nclass ", method_start + len(operation))
                if method_end == -1:
                    method_end = len(content)

                method_content = content[method_start:method_end]
                method_without_comments = re.sub(r"#.*", "", method_content)

                has_auth = (
                    "admin" in method_without_comments.lower()
                    or "role" in method_without_comments.lower()
                    or "authorize" in method_without_comments.lower()
                    or "permission" in method_without_comments.lower()
                )

                if not has_auth:
                    vulnerabilities.append(
                        {
                            "type": "authorization",
                            "location": "code",
                            "issue": "Sensitive operation without authorization check",
                        }
                    )
                    security_score -= 2.5
                    break

        if "password" in content.lower() and "logger" in content.lower():
            vulnerabilities.append(
                {
                    "type": "data_exposure",
                    "location": "code",
                    "issue": "Potential sensitive data logging",
                }
            )
            security_score -= 2.0

        if "execute(" in content and ('f"' in content or "%" in content):
            vulnerabilities.append(
                {
                    "type": "sql_injection",
                    "location": "code",
                    "issue": "Potential SQL injection vulnerability",
                }
            )
            security_score -= 3.0

        security_score = max(security_score, 0.0)

        return {
            "security_score": security_score,
            "vulnerabilities": vulnerabilities,
        }

    def analyze_technical_debt(
        self,
        debt_indicators: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze technical debt impact."""
        high_debt_threshold = 20
        total_impact = sum(
            indicator.get("count", 0)
            * self._impact_weight(indicator.get("impact", "low"))
            for indicator in debt_indicators
        )

        priority_areas = [
            indicator["type"]
            for indicator in debt_indicators
            if indicator.get("impact") == "high"
        ]

        return {
            "overall_score": min(total_impact / 10.0, 10.0),
            "priority_areas": priority_areas,
            "remediation_effort": (
                "high" if total_impact > high_debt_threshold else "medium"
            ),
        }

    def _impact_weight(self, impact: str) -> float:
        """Convert impact level to numeric weight."""
        weights = {
            "low": 1.0,
            "medium": 2.5,
            "high": 5.0,
        }
        return weights.get(impact.lower(), 1.0)


__all__ = ["QualityMixin"]
