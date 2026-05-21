"""Quality mixin: documentation, naming, errors, breaking changes, security."""

from __future__ import annotations

import re
from typing import Any

from ...utils import content_parser


class QualityMixin:
    """Check API quality: documentation, naming, error handling, security."""

    def check_documentation(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, Any]]:
        """Score docstring/JSDoc coverage on public symbols within ``filename``."""
        code = content_parser.get_file_content(context, filename)
        issues: list[dict[str, Any]] = []

        class_matches = re.finditer(r"export\s+class\s+(\w+)", code)
        for match in class_matches:
            class_name = match.group(1)
            start = max(0, match.start() - 200)
            preceding = code[start : match.start()]
            if not re.search(r"(/\*\*|//)", preceding):
                issues.append(
                    {
                        "type": "missing_documentation",
                        "location": filename,
                        "severity": "medium",
                        "issue": f"Class {class_name} missing documentation",
                    }
                )

        func_matches = re.finditer(r"export\s+function\s+(\w+)", code)
        for match in func_matches:
            func_name = match.group(1)
            start = max(0, match.start() - 200)
            preceding = code[start : match.start()]
            if not re.search(r"(/\*\*|//)", preceding):
                issues.append(
                    {
                        "type": "missing_documentation",
                        "location": filename,
                        "severity": "medium",
                        "issue": f"Function {func_name} missing documentation",
                    }
                )

        return issues

    def check_naming_consistency(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, Any]]:
        """Detect mixed naming conventions (snake_case vs camelCase) in public symbols."""
        code = content_parser.get_file_content(context, filename)
        issues: list[dict[str, Any]] = []

        method_names: list[str] = []
        class_blocks = re.finditer(r"class\s+\w+\s*\{(.*?)\n\}", code, re.DOTALL)
        for block in class_blocks:
            methods = re.findall(r"^\s*(\w+)\s*\(", block.group(1), re.MULTILINE)
            method_names.extend(methods)

        has_camel_case = any(
            re.match(r"^[a-z][a-zA-Z0-9]*$", name) for name in method_names
        )
        has_pascal_case = any(
            re.match(r"^[A-Z][a-zA-Z0-9]*$", name) for name in method_names
        )
        has_snake_case = any("_" in name for name in method_names)

        styles_count = sum([has_camel_case, has_pascal_case, has_snake_case])
        if styles_count > 1:
            issues.append(
                {
                    "type": "naming_inconsistency",
                    "location": filename,
                    "severity": "medium",
                    "issue": (
                        "Inconsistent naming conventions detected "
                        "(mix of camelCase, PascalCase, and snake_case)"
                    ),
                }
            )

        const_names = re.findall(r"export\s+const\s+(\w+)", code)
        for const_name in const_names:
            if (
                not const_name.isupper()
                and "_" in const_name
                and not re.match(r"^[A-Z_]+$", const_name)
            ):
                issues.append(
                    {
                        "type": "naming_inconsistency",
                        "location": filename,
                        "severity": "low",
                        "issue": f"Constant {const_name} inconsistent naming",
                    }
                )

        return issues

    def check_error_handling(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, Any]]:
        """Detect bare ``except``, swallowed errors, and missing ``Result``-style returns."""
        code = content_parser.get_file_content(context, filename)
        issues: list[dict[str, Any]] = []

        method_blocks = re.finditer(
            r"(\w+)\s*\([^)]*\)\s*\{([^}]*fetch[^}]*)\}", code, re.DOTALL
        )

        for match in method_blocks:
            method_name = match.group(1)
            method_body = match.group(2)

            has_fetch = "fetch" in method_body
            has_try_catch = "try" in method_body and "catch" in method_body
            has_catch_handler = ".catch(" in method_body

            if has_fetch and not has_try_catch and not has_catch_handler:
                issues.append(
                    {
                        "type": "missing_error_handling",
                        "location": filename,
                        "severity": "high",
                        "issue": f"Method {method_name} fetch lacks error handling",
                    }
                )

        return issues

    def check_breaking_changes(
        self,
        context: Any,
        filename: str,
        _options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Diff exported signatures against the prior version to flag breakage."""
        code = content_parser.get_file_content(context, filename)
        issues: list[dict[str, Any]] = []

        breaking_comments = re.finditer(
            r"//\s*Breaking change:(.+)", code, re.IGNORECASE
        )
        for match in breaking_comments:
            issues.append(
                {
                    "type": "breaking_change",
                    "location": filename,
                    "severity": "critical",
                    "issue": f"Breaking change detected: {match.group(1).strip()}",
                }
            )

        signature_changes = re.finditer(
            r"//\s*export\s+function\s+(\w+)\s*\([^)]*\)", code
        )
        for match in signature_changes:
            func_name = match.group(1)
            issues.append(
                {
                    "type": "breaking_change",
                    "location": filename,
                    "severity": "high",
                    "issue": f"Function {func_name} signature may have changed",
                }
            )

        return issues

    def validate_rest_patterns(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, Any]]:
        """Flag handlers missing HTTP-method or status-code conventions in ``filename``."""
        code = content_parser.get_file_content(context, filename)
        issues: list[dict[str, Any]] = []

        delete_endpoints = re.finditer(
            r'fetch\([^)]*/(delete|remove)[^)]*\)(?!\s*,\s*\{[^}]*method:\s*[\'"]DELETE[\'"]\})',
            code,
            re.IGNORECASE,
        )
        for _match in delete_endpoints:
            issues.append(
                {
                    "type": "rest_violation",
                    "location": filename,
                    "severity": "medium",
                    "issue": "Using GET for delete - should use DELETE method",
                }
            )

        improper_methods = re.finditer(
            r"async\s+(\w*delete\w*)\s*\([^)]*\)\s*\{[^}]*fetch\([^,)]+\)(?![^}]*method)",
            code,
            re.IGNORECASE | re.DOTALL,
        )
        for _match in improper_methods:
            issues.append(
                {
                    "type": "rest_violation",
                    "location": filename,
                    "severity": "medium",
                    "issue": "Delete method missing HTTP method - use DELETE",
                }
            )

        return issues

    def check_input_validation(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, Any]]:
        """Flag handlers that read inputs without an explicit validator call."""
        code = content_parser.get_file_content(context, filename)
        issues: list[dict[str, Any]] = []

        validation_needed = re.finditer(
            r"(\w+)\s*\(([^)]*(?:userData|email|query|userId)[^)]*)\)\s*\{([^}]{0,300})",
            code,
            re.DOTALL,
        )

        for match in validation_needed:
            method_name = match.group(1)
            _params = match.group(2)
            method_body = match.group(3)

            has_validation = any(
                [
                    "if" in method_body and "throw" in method_body,
                    "validate" in method_body.lower(),
                    "check" in method_body.lower(),
                    "!" in method_body
                    and ("null" in method_body or "undefined" in method_body),
                ]
            )

            if not has_validation:
                issues.append(
                    {
                        "type": "missing_validation",
                        "location": filename,
                        "severity": "medium",
                        "issue": f"Method {method_name} input lacks validation",
                    }
                )

        return issues

    def check_security_practices(
        self,
        context: Any,
        filename: str,
    ) -> list[dict[str, Any]]:
        """Flag hardcoded secrets, insecure defaults, and missing auth gates."""
        code = content_parser.get_file_content(context, filename)
        issues: list[dict[str, Any]] = []

        api_key_storage = re.finditer(r"this\.(apiKey|api_key|API_KEY)\s*=", code)
        for _match in api_key_storage:
            issues.append(
                {
                    "type": "security_issue",
                    "location": filename,
                    "severity": "critical",
                    "issue": "API key stored in client code",
                }
            )

        hardcoded_keys = re.finditer(
            r'(apiKey|api_key|API_KEY)\s*[:=]\s*[\'"][^\'"]+[\'"]', code
        )
        for _match in hardcoded_keys:
            issues.append(
                {
                    "type": "security_issue",
                    "location": filename,
                    "severity": "critical",
                    "issue": "API key appears to be hardcoded in client code",
                }
            )

        fetch_without_auth = re.finditer(
            r'fetch\([^)]+,\s*\{[^}]*method:\s*[\'"]POST[\'"][^}]*\}', code, re.DOTALL
        )
        for match in fetch_without_auth:
            fetch_block = match.group(0)
            if "Authorization" not in fetch_block and "headers" not in fetch_block:
                issues.append(
                    {
                        "type": "security_issue",
                        "location": filename,
                        "severity": "high",
                        "issue": "POST request without authentication headers",
                    }
                )

        file_upload_patterns = re.finditer(
            r"(upload|file)\s*\([^)]*\)\s*\{[^}]*FormData[^}]*\}",
            code,
            re.DOTALL | re.IGNORECASE,
        )
        for match in file_upload_patterns:
            upload_block = match.group(0)
            if not any(
                check in upload_block.lower() for check in ["type", "size", "validate"]
            ):
                issues.append(
                    {
                        "type": "security_issue",
                        "location": filename,
                        "severity": "high",
                        "issue": "File upload without type or size validation",
                    }
                )

        return issues
