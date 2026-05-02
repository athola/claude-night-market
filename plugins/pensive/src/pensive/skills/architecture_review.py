"""Analyze system design and patterns using an architecture review skill.

This skill evaluates architectural patterns, SOLID principles, coupling/cohesion,
ADR compliance, and generates architecture quality reports.
"""

from __future__ import annotations

import ast
import logging
import re
import textwrap
from typing import Any, ClassVar

from .base import BaseReviewSkill

logger = logging.getLogger(__name__)

# Architecture detection thresholds
MIN_LAYERS_FOR_LAYERED = 3  # Minimum layers to detect layered architecture
MIN_SERVICES_FOR_MICROSERVICES = 2  # Minimum services to detect microservices
MIN_EVENT_COMPONENTS = 3  # Minimum event components for event-driven
MIN_RESPONSIBILITIES_FOR_LOW_COHESION = 3  # Threshold for cohesion calculation
MIN_VIOLATIONS_TO_REPORT = 2  # Minimum violations before flagging
MIN_ADR_SECTIONS = 3  # Minimum ADR sections for completeness

# Coupling score calculation
COUPLING_DEPENDENCY_SCALE = 10.0
COUPLING_VIOLATION_WEIGHT = 0.5

# Cohesion score thresholds
COHESION_SCORE_MEDIUM = 0.7
COHESION_SCORE_HIGH = 0.9
MIN_RESPONSIBILITIES_FOR_MEDIUM_COHESION = 2

# SRP keyword detection
_SRP_KEYWORDS = frozenset(
    ["user", "email", "report", "backup", "send", "generate", "create"]
)


class ArchitectureReviewSkill(BaseReviewSkill):
    """Review software architecture and design patterns."""

    skill_name = "architecture_review"
    supported_languages: ClassVar[list[str]] = [
        "python",
        "typescript",
        "javascript",
        "java",
        "rust",
        "go",
    ]

    def detect_architecture_pattern(self, context: Any) -> dict[str, Any]:
        """Detect architectural patterns in the codebase.

        Args:
            context: Skill context with file access methods

        Returns:
            Dict with detected patterns, layers, components, and services
        """
        files = context.get_files()
        patterns = []
        layers = []
        components = {}
        services = []

        # Detect layered architecture
        layer_names = ["controllers", "services", "repositories", "models"]
        detected_layers = []
        for layer in layer_names:
            if any(layer in f.lower() for f in files):
                detected_layers.append(layer)

        if len(detected_layers) >= MIN_LAYERS_FOR_LAYERED:
            patterns.append("layered")
            layers.extend(detected_layers)

        # Detect hexagonal architecture
        has_ports = any("ports" in f.lower() for f in files)
        has_adapters = any("adapters" in f.lower() for f in files)
        has_domain = any("domain" in f.lower() or "core" in f.lower() for f in files)

        if has_ports and has_adapters:
            patterns.append("hexagonal")
            components["ports"] = True
            components["adapters"] = True
            if has_domain:
                components["domain"] = True

        # Detect microservices architecture
        service_dirs = set()
        for f in files:
            parts = f.split("/")
            # Look for various service patterns
            for i, part in enumerate(parts):
                # Match pattern like "services/user-service"
                if part == "services" and i + 1 < len(parts):
                    service_dirs.add(parts[i + 1])
                # Match pattern like "user-service/src" or "api-gateway/src"
                elif "-service" in part or (part == "api-gateway" and i == 0):
                    service_dirs.add(part)

        if len(service_dirs) >= MIN_SERVICES_FOR_MICROSERVICES:
            patterns.append("microservices")
            for service_name in service_dirs:
                services.append({"name": service_name})

        # Detect event-driven architecture
        event_keywords = ["events", "handlers", "publishers", "subscribers"]
        detected_event_components = []
        for keyword in event_keywords:
            if any(keyword in f.lower() for f in files):
                detected_event_components.append(keyword)

        if len(detected_event_components) >= MIN_EVENT_COMPONENTS:
            patterns.append("event_driven")
            for component in detected_event_components:
                components[component] = True

        return {
            "patterns": patterns,
            "layers": layers,
            "components": components,
            "services": services,
        }

    def analyze_coupling(self, context: Any) -> dict[str, Any]:
        """Analyze coupling between modules.

        Args:
            context: Skill context with dependency analysis methods

        Returns:
            Dict with coupling score and violations
        """
        dependencies = context.analyze_dependencies()
        violations = []
        coupling_score = 0.0

        # Detect layering violations (e.g., controller -> database direct)
        for dep in dependencies:
            from_module = dep.get("from", "")
            to_module = dep.get("to", "")

            # Check for controller directly accessing database
            if "controller" in from_module.lower() and "database" in to_module.lower():
                violations.append(
                    {
                        "type": "layering_violation",
                        "from": from_module,
                        "to": to_module,
                        "issue": "Controller accesses DB, bypassing service layer",
                    }
                )

            # Check for repository directly accessed by controller
            if (
                "controller" in from_module.lower()
                and "repository" in to_module.lower()
            ):
                violations.append(
                    {
                        "type": "layering_violation",
                        "from": from_module,
                        "to": to_module,
                        "issue": "Controller accesses repo, should use service layer",
                    }
                )

        # Calculate coupling score based on dependencies and violations
        if dependencies:
            coupling_score = len(dependencies) / COUPLING_DEPENDENCY_SCALE
            if violations:
                coupling_score += len(violations) * COUPLING_VIOLATION_WEIGHT

        return {
            "coupling_score": coupling_score,
            "violations": violations,
        }

    def analyze_cohesion(
        self,
        context: Any,
        module_path: str,
    ) -> dict[str, Any]:
        """Analyze cohesion within a module.

        Args:
            context: Skill context with file content access
            module_path: Path to the module to analyze

        Returns:
            Dict with cohesion score and identified responsibilities
        """
        content = context.get_file_content(module_path)
        content_lower = content.lower()
        responsibilities = []
        cohesion_score = 1.0

        # Detect different responsibilities based on method names and keywords
        responsibility_keywords = {
            "user_management": [
                "create_user",
                "update_user",
                "delete_user",
                "get_user",
            ],
            "notification": ["send_notification", "send_email", "notify"],
            "billing": ["calculate_invoice", "process_payment", "charge"],
            "validation": ["validate_", "check_", "verify_"],
            "authentication": ["authenticate", "login", "logout"],
            "authorization": ["authorize", "has_permission", "check_role"],
        }

        for responsibility, keywords in responsibility_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                responsibilities.append(responsibility)

        # Calculate cohesion score - lower score for more diverse responsibilities
        if len(responsibilities) >= MIN_RESPONSIBILITIES_FOR_LOW_COHESION:
            cohesion_score = 1.0 / len(responsibilities)
        elif len(responsibilities) >= MIN_RESPONSIBILITIES_FOR_MEDIUM_COHESION:
            cohesion_score = COHESION_SCORE_MEDIUM
        else:
            cohesion_score = COHESION_SCORE_HIGH

        return {
            "cohesion_score": cohesion_score,
            "responsibilities": responsibilities,
        }

    def check_separation_of_concerns(
        self,
        context: Any,
        file_path: str,
    ) -> list[dict[str, Any]]:
        """Check for separation of concerns violations.

        Args:
            context: Skill context with file content access
            file_path: Path to the file to analyze

        Returns:
            List of SoC violations with type and details
        """
        content = context.get_file_content(file_path)
        violations = []

        # Check for data access concerns (SQL, database connections)
        data_access_patterns = [
            "sqlite3.connect",
            "cursor.execute",
            "db_connection",
            "INSERT INTO",
            "SELECT FROM",
            "UPDATE SET",
        ]
        if any(pattern in content for pattern in data_access_patterns):
            violations.append(
                {
                    "type": "data_access",
                    "issue": "Data access logic mixed with other concerns",
                    "location": file_path,
                }
            )

        # Check for business logic concerns
        business_logic_patterns = [
            "validate_user",
            "validate_",
            "process_",
            "calculate_",
        ]
        if any(pattern in content for pattern in business_logic_patterns):
            violations.append(
                {
                    "type": "business_logic",
                    "issue": "Business logic present in file",
                    "location": file_path,
                }
            )

        # Check for presentation concerns (HTTP, response formatting)
        presentation_patterns = [
            "Response(",
            "status=",
            "render_template",
            "jsonify",
        ]
        if any(pattern in content for pattern in presentation_patterns):
            violations.append(
                {
                    "type": "presentation",
                    "issue": "Presentation logic mixed with other concerns",
                    "location": file_path,
                }
            )

        # Check for logging concerns
        logging_patterns = ["print(", "logger.", "logging."]
        if any(pattern in content for pattern in logging_patterns):
            # Only flag if other concerns are also present
            if len(violations) > 0:
                violations.append(
                    {
                        "type": "logging",
                        "issue": "Logging mixed with other concerns",
                        "location": file_path,
                    }
                )

        # Only return violations if we found multiple concerns mixed together
        if len(violations) >= MIN_VIOLATIONS_TO_REPORT:
            return violations
        return []

    def check_dependency_inversion(
        self,
        context: Any,
        file_path: str,
    ) -> list[dict[str, Any]]:
        """Check for dependency inversion principle violations.

        Args:
            context: Skill context with file content access
            file_path: Path to the file to analyze

        Returns:
            List of DIP violations with issue descriptions
        """
        content = context.get_file_content(file_path)
        violations = []

        # Check for direct instantiation of infrastructure classes in
        # business logic using general patterns rather than hardcoded names.
        concrete_patterns = [
            r"\b\w+Database\(",
            r"\b\w+Repository\(",
            r"\b\w+Service\(",
            r"\b\w+Client\(",
            r"\bnew\s+\w+(Database|Repository|Service|Client)",
        ]

        for pattern in concrete_patterns:
            for match in re.finditer(pattern, content):
                matched_text = match.group(0).rstrip("(")
                violations.append(
                    {
                        "type": "concrete_dependency",
                        "issue": f"Depends on concrete class {matched_text}",
                        "location": file_path,
                        "suggestion": (
                            f"Inject {matched_text} through interface/protocol"
                        ),
                    }
                )

        # Check for direct instantiation in __init__ methods
        if "def __init__(" in content:
            # Look for patterns like: self.something = ConcreteClass()
            init_pattern = r"self\.\w+\s*=\s*([A-Z]\w+)\(\)"
            matches = re.findall(init_pattern, content)
            for class_name in matches:
                # Skip if it's a basic type or common exceptions
                if class_name not in ["Exception", "ValueError", "TypeError"]:
                    violations.append(
                        {
                            "type": "concrete_dependency",
                            "issue": f"Depends on concrete class {class_name}",
                            "location": file_path,
                            "suggestion": "Use dependency injection instead",
                        }
                    )

        return violations

    def analyze_solid_principles(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze SOLID principles compliance.

        Args:
            context: Skill context with file content access
            file_path: Path to the file to analyze

        Returns:
            Dict with analysis for each SOLID principle
        """
        content = context.get_file_content(file_path)

        # Single Responsibility Principle
        srp_violations = 0
        srp_issues = []

        # Use AST to extract classes and their methods, fall back to regex
        try:
            tree = ast.parse(content)
        except SyntaxError:
            try:
                tree = ast.parse(textwrap.dedent(content))
            except SyntaxError:
                tree = None

        if tree is not None:
            class_methods_map = {
                node.name: [
                    n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)
                ]
                for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef)
            }
        else:
            # Regex fallback for code that doesn't parse cleanly
            class_pattern = r"class\s+(\w+).*?(?=class\s+\w+|$)"
            method_pattern = r"def\s+(\w+)\s*\("
            class_methods_map = {}
            for class_match in re.finditer(class_pattern, content, re.DOTALL):
                class_name = class_match.group(1)
                class_text = class_match.group(0)
                class_methods_map[class_name] = re.findall(method_pattern, class_text)

        for _class_name, methods in class_methods_map.items():
            # Set-based keyword scan for diverse responsibilities
            method_names_lower = {m.lower() for m in methods}
            found_keywords = {
                kw for kw in _SRP_KEYWORDS if any(kw in m for m in method_names_lower)
            }
            responsibility_types = len(found_keywords)

            if responsibility_types >= MIN_RESPONSIBILITIES_FOR_LOW_COHESION:
                srp_violations += 1
                srp_issues.append("Class has multiple responsibilities")

        # Open/Closed Principle
        ocp_violations = 0
        ocp_issues = []

        # Check for type checking in methods (indicates OCP violation)
        type_check_patterns = [
            r"if.*\.type\s*==",
            r"if.*isinstance\(",
            r"elif.*\.type\s*==",
        ]

        for pattern in type_check_patterns:
            if re.search(pattern, content):
                ocp_violations += 1
                ocp_issues.append("Type checking in code - should use polymorphism")
                break

        # Liskov Substitution Principle
        lsp_violations = 0
        lsp_issues = []

        # Detect inheritance and check for overridden methods that change behavior
        # Look for classes that inherit and have set_width/set_height pattern
        if re.search(r"class\s+Square.*\(.*Rectangle.*\)", content):
            if "set_width" in content or "set_height" in content:
                lsp_violations += 1
                lsp_issues.append("Square inherits Rectangle but violates LSP")

        # Generic check: if a class overrides a method and changes both width/height
        # when only one should change
        if re.search(r"def\s+set_width.*self\.height\s*=", content):
            lsp_violations += 1
            lsp_issues.append("Overridden method changes behavior unexpectedly")

        return {
            "single_responsibility": {
                "violations": srp_violations,
                "issues": srp_issues,
            },
            "open_closed": {
                "violations": ocp_violations,
                "issues": ocp_issues,
            },
            "liskov_substitution": {
                "violations": lsp_violations,
                "issues": lsp_issues,
            },
        }

    def analyze_adrs(self, context: Any) -> dict[str, Any]:
        """Analyze Architectural Decision Records.

        Args:
            context: Skill context with file access methods

        Returns:
            Dict with ADR count and completeness score
        """
        files = context.get_files()
        adr_files = [f for f in files if "adr" in f.lower() and f.endswith(".md")]

        total_adrs = len(adr_files)
        completeness_score = 0.0
        adrs = []

        if total_adrs > 0:
            complete_count = 0
            for adr_file in adr_files:
                content = context.get_file_content(adr_file)

                # Check for required ADR sections
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

    def analyze_data_flow(self, context: Any) -> dict[str, Any]:
        """Analyze data flow architecture patterns.

        Args:
            context: Skill context with file access methods

        Returns:
            Dict with detected pattern and flow components
        """
        files = context.get_files()
        pattern_detected = None
        flow_components = []

        # Detect pipes and filters pattern
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

        # Detect batch sequential pattern
        batch_keywords = ["batch", "sequential", "stages"]
        if any(keyword in f.lower() for keyword in batch_keywords for f in files):
            if pattern_detected is None:
                pattern_detected = "batch_sequential"

        # Detect stream processing pattern
        stream_keywords = ["stream", "streaming", "kafka", "kinesis"]
        if any(keyword in f.lower() for keyword in stream_keywords for f in files):
            if pattern_detected is None:
                pattern_detected = "streams"

        return {
            "pattern_detected": pattern_detected,
            "flow_components": flow_components,
        }

    def _get_any_content(self, context: Any) -> str:
        """Fetch file content from context, trying all available files as fallback."""
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
        """Analyze scalability patterns and bottlenecks.

        Args:
            context: Skill context with file content access

        Returns:
            Dict with scalability score and identified bottlenecks
        """
        bottlenecks = []
        scalability_score = 10.0  # Start with perfect score

        content = self._get_any_content(context)

        # Check for stateful singletons
        if "_instance" in content and "cls._instance" in content:
            bottlenecks.append(
                {
                    "type": "stateful_singleton",
                    "location": "code",
                    "issue": "Stateful singleton limits horizontal scaling",
                }
            )
            scalability_score -= 2.0

        # Check for in-memory caching
        if "cache = {}" in content or "self.cache" in content:
            bottlenecks.append(
                {
                    "type": "in_memory_state",
                    "location": "code",
                    "issue": "In-memory cache prevents horizontal scaling",
                }
            )
            scalability_score -= 1.5

        # Check for sequential processing with expensive operations
        # Look for nested loops or known sequential patterns, not just any
        # iteration.  A bare "for item in" matches too many benign loops.
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
        """Analyze security architecture patterns.

        Args:
            context: Skill context with file content access

        Returns:
            Dict with security score and vulnerabilities
        """
        vulnerabilities = []
        security_score = 10.0  # Start with perfect score

        content = self._get_any_content(context)

        # Check for missing authorization on sensitive operations
        sensitive_operations = ["def delete_all", "def delete_user", "def remove_all"]
        for operation in sensitive_operations:
            if operation in content:
                # Extract the method and check for auth
                method_start = content.find(operation)
                # Find the end of this method (next def or end of class/file)
                method_end = content.find("\n    def ", method_start + len(operation))
                if method_end == -1:
                    method_end = content.find("\nclass ", method_start + len(operation))
                if method_end == -1:
                    method_end = len(content)

                method_content = content[method_start:method_end]

                # Remove comments from method content before checking
                method_without_comments = re.sub(r"#.*", "", method_content)

                # Check for actual authorization code (not just in comments)
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
                    break  # Only report once

        # Check for sensitive data logging
        if "password" in content.lower() and "logger" in content.lower():
            vulnerabilities.append(
                {
                    "type": "data_exposure",
                    "location": "code",
                    "issue": "Potential sensitive data logging",
                }
            )
            security_score -= 2.0

        # Check for SQL injection risks
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

    def detect_architectural_drift(self, context: Any) -> dict[str, Any]:
        """Detect architectural drift from intended design.

        Args:
            context: Skill context with architecture comparison methods

        Returns:
            Dict with drift detection status and deviations
        """
        intended_patterns = context.get_intended_architecture()
        detected_patterns = context.get_detected_patterns()

        deviations = []
        drift_detected = False

        # Find patterns that exist but weren't intended
        for pattern in detected_patterns:
            if pattern not in intended_patterns:
                deviations.append(
                    {
                        "pattern": pattern,
                        "type": "unintended",
                        "issue": f"Pattern '{pattern}' detected but not intended",
                    }
                )
                drift_detected = True

        # Find patterns that should exist but don't
        for pattern in intended_patterns:
            if pattern not in detected_patterns:
                deviations.append(
                    {
                        "pattern": pattern,
                        "type": "missing",
                        "issue": f"Pattern '{pattern}' intended but not detected",
                    }
                )
                drift_detected = True

        return {
            "drift_detected": drift_detected,
            "deviations": deviations,
        }

    def generate_recommendations(
        self,
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate actionable architecture recommendations.

        Args:
            findings: List of architecture findings

        Returns:
            List of recommendations with priority, action, and rationale
        """
        recommendations = []
        for finding in findings:
            recommendations.append(
                {
                    "priority": finding.get("severity", "medium"),
                    "action": f"Address {finding.get('type', 'issue')}",
                    "rationale": finding.get("issue", "Improve architecture quality"),
                }
            )
        return recommendations

    def analyze_architecture_documentation(self, context: Any) -> dict[str, Any]:
        """Analyze architecture documentation completeness.

        Args:
            context: Skill context with file access methods

        Returns:
            Dict with documentation status and missing docs
        """
        files = context.get_files()
        documentation_found = False
        missing_docs = []

        # Check for common architecture documentation files
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

        # Determine what's missing
        for doc_type in doc_patterns:
            if doc_type not in found_docs:
                missing_docs.append(doc_type)

        return {
            "documentation_found": documentation_found,
            "missing_docs": missing_docs,
        }

    def analyze_technical_debt(
        self,
        debt_indicators: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze technical debt impact.

        Args:
            debt_indicators: List of debt indicators with type, count, and impact

        Returns:
            Dict with overall score, priority areas, and remediation effort
        """
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

    def create_architecture_report(self, analysis_results: dict[str, Any]) -> str:
        """Create a structured architecture quality report.

        Args:
            analysis_results: Results from architecture analysis

        Returns:
            Formatted markdown report
        """
        patterns = analysis_results.get("patterns_detected", [])
        score = analysis_results.get("architecture_score", 0.0)
        violations = analysis_results.get("violations", [])
        recommendations = analysis_results.get("recommendations", [])
        debt_score = analysis_results.get("technical_debt_score", 0.0)

        report_lines = [
            "# Architecture Quality Report",
            "",
            "## Architecture Assessment",
            "",
            f"**Overall Score:** {score}/10",
            f"**Technical Debt Score:** {debt_score}/10",
            "",
            "## Patterns Identified",
            "",
        ]

        if patterns:
            for pattern in patterns:
                report_lines.append(f"- {pattern}")
        else:
            report_lines.append("- No clear patterns detected")

        report_lines.extend(
            [
                "",
                "## Issues Found",
                "",
            ]
        )

        if violations:
            for violation in violations:
                severity = violation.get("severity", "unknown")
                message = violation.get("message", "No description")
                report_lines.append(f"- [{severity.upper()}] {message}")
        else:
            report_lines.append("- No issues found")

        report_lines.extend(
            [
                "",
                "## Recommendations",
                "",
            ]
        )

        if recommendations:
            for rec in recommendations:
                report_lines.append(f"- {rec}")
        else:
            report_lines.append("- Continue following current architecture patterns")

        report_lines.extend(
            [
                "",
                "## Summary",
                "",
                "This report provides an overview of the architecture quality. "
                "Address high-priority issues first and maintain architectural "
                "consistency across the codebase.",
                "",
            ]
        )

        return "\n".join(report_lines)

    def _impact_weight(self, impact: str) -> float:
        """Convert impact level to numeric weight.

        Args:
            impact: Impact level (low, medium, high)

        Returns:
            Numeric weight
        """
        weights = {
            "low": 1.0,
            "medium": 2.5,
            "high": 5.0,
        }
        return weights.get(impact.lower(), 1.0)
