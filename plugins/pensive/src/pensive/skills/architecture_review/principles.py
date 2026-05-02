"""SoC, dependency inversion, and SOLID principle checks (AR-01)."""

from __future__ import annotations

import ast
import re
import textwrap
from typing import Any

from ._constants import (
    MIN_RESPONSIBILITIES_FOR_LOW_COHESION,
    MIN_VIOLATIONS_TO_REPORT,
    _BUILTIN_EXC_NAMES,
    _SRP_KEYWORDS,
)


class PrinciplesMixin:
    """Separation of concerns, dependency inversion, and SOLID checks."""

    def check_separation_of_concerns(
        self,
        context: Any,
        file_path: str,
    ) -> list[dict[str, Any]]:
        """Check for separation of concerns violations."""
        content = context.get_file_content(file_path)
        violations = []

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

        logging_patterns = ["print(", "logger.", "logging."]
        if any(pattern in content for pattern in logging_patterns):
            if len(violations) > 0:
                violations.append(
                    {
                        "type": "logging",
                        "issue": "Logging mixed with other concerns",
                        "location": file_path,
                    }
                )

        if len(violations) >= MIN_VIOLATIONS_TO_REPORT:
            return violations
        return []

    def check_dependency_inversion(
        self,
        context: Any,
        file_path: str,
    ) -> list[dict[str, Any]]:
        """Check for dependency inversion principle violations."""
        content = context.get_file_content(file_path)
        violations = []

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

        if "def __init__(" in content:
            init_pattern = r"self\.\w+\s*=\s*([A-Z]\w+)\(\)"
            matches = re.findall(init_pattern, content)
            for class_name in matches:
                if class_name not in _BUILTIN_EXC_NAMES:
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
        """Analyze SOLID principles compliance."""
        content = context.get_file_content(file_path)

        # Single Responsibility Principle
        srp_violations = 0
        srp_issues = []

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
            class_pattern = r"class\s+(\w+).*?(?=class\s+\w+|$)"
            method_pattern = r"def\s+(\w+)\s*\("
            class_methods_map = {}
            for class_match in re.finditer(class_pattern, content, re.DOTALL):
                class_name = class_match.group(1)
                class_text = class_match.group(0)
                class_methods_map[class_name] = re.findall(method_pattern, class_text)

        for _class_name, methods in class_methods_map.items():
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

        if re.search(r"class\s+Square.*\(.*Rectangle.*\)", content):
            if "set_width" in content or "set_height" in content:
                lsp_violations += 1
                lsp_issues.append("Square inherits Rectangle but violates LSP")

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


__all__ = ["PrinciplesMixin"]
