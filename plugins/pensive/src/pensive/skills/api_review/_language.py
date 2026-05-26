"""Language mixin: TypeScript, JavaScript, Python, Rust API surface analysis."""

from __future__ import annotations

import re
from typing import Any

from ...utils import content_parser


class LanguageMixin:
    """Analyze API surface for TypeScript, JavaScript, Python, and Rust files."""

    def analyze_typescript_api(
        self,
        context: Any,
        filename: str,
    ) -> dict[str, Any]:
        """Regex-count exports, classes, interfaces, and functions in a ``.ts`` file."""
        code = content_parser.get_file_content(context, filename)

        exports = len(re.findall(r"^\s*export\s+", code, re.MULTILINE))
        classes = len(re.findall(r"\bexport\s+class\s+\w+", code))
        interfaces = len(re.findall(r"\bexport\s+interface\s+\w+", code))
        functions = len(re.findall(r"\bexport\s+(?:async\s+)?function\s+\w+", code))
        default_exports = len(re.findall(r"\bexport\s+default\s+", code))
        const_exports = len(re.findall(r"\bexport\s+const\s+\w+", code))

        return {
            "exports": exports,
            "classes": classes,
            "interfaces": interfaces,
            "functions": functions,
            "default_exports": default_exports,
            "const_exports": const_exports,
        }

    def analyze_javascript_api(
        self,
        context: Any,
        filename: str,
    ) -> dict[str, Any]:
        """Regex-count exports, classes, and functions in a ``.js`` file."""
        code = content_parser.get_file_content(context, filename)

        exports = len(re.findall(r"^\s*export\s+", code, re.MULTILINE))
        classes = len(re.findall(r"\bexport\s+class\s+\w+", code))
        functions = len(re.findall(r"\bexport\s+function\s+\w+", code))
        default_exports = len(re.findall(r"\bexport\s+default\s+", code))
        const_exports = len(re.findall(r"\bexport\s+const\s+\w+", code))

        return {
            "exports": exports,
            "classes": classes,
            "functions": functions,
            "default_exports": default_exports,
            "const_exports": const_exports,
        }

    def analyze_python_api(
        self,
        context: Any,
        filename: str,
    ) -> dict[str, Any]:
        """Regex-count public classes, functions, and ``__all__`` entries in ``.py``."""
        code = content_parser.get_file_content(context, filename)

        all_match = re.search(r"__all__\s*=\s*\[(.*?)\]", code, re.DOTALL)
        exports = 0
        if all_match:
            exports = len(re.findall(r'[\'"](\w+)[\'"]', all_match.group(1)))

        class_pattern = r"^\s*(?:@\w+\s*\n\s*)?class\s+\w+"
        classes = len(re.findall(class_pattern, code, re.MULTILINE))
        functions = len(re.findall(r"^\s*def\s+\w+\s*\(", code, re.MULTILINE))

        return {
            "exports": exports,
            "classes": classes,
            "functions": functions,
        }

    def analyze_rust_api(
        self,
        context: Any,
        filename: str,
    ) -> dict[str, Any]:
        """Regex-count ``pub`` items (structs, enums, traits, fns) in a ``.rs`` file."""
        code = content_parser.get_file_content(context, filename)

        structs = len(re.findall(r"pub\s+struct\s+\w+", code))
        all_pub_fns = len(re.findall(r"pub\s+(?:async\s+)?fn\s+\w+", code))

        impl_blocks = re.findall(r"impl\s+\w+\s*\{(.*?)\n\}", code, re.DOTALL)
        public_methods_in_impl = 0
        constructors = 0
        for block in impl_blocks:
            all_methods = re.findall(r"pub\s+fn\s+(\w+)", block)
            for method_name in all_methods:
                if method_name == "new":
                    constructors += 1
                public_methods_in_impl += 1

        standalone_fns = all_pub_fns - public_methods_in_impl
        functions = public_methods_in_impl - constructors + standalone_fns
        public_methods = all_pub_fns

        return {
            "structs": structs,
            "functions": functions,
            "public_methods": public_methods,
        }
