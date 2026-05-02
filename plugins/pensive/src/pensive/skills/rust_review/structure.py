"""Structural analysis for Rust review: macros, traits, const generics."""

from __future__ import annotations

from typing import Any

from ..rust_review_data import (
    CONST_GENERIC_STRUCT_RE,
    CONST_MAX_RE,
    DERIVE_MACRO_RE,
    DOC_COMMENT_RE,
    GENERIC_METHOD_RE,
    IMPL_FOR_RE,
    MACRO_RULES_RE,
    STATIC_METHOD_RE,
    TRAIT_DEF_RE,
    TRAIT_METHOD_RE,
)

__all__ = ["StructureMixin"]


class StructureMixin:
    """Mixin providing macro, trait, and const generic analysis."""

    def analyze_macros(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze macro usage patterns.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with macro analysis
        """
        content = context.get_file_content(file_path)
        custom_macros = []
        derive_macros = []
        problematic_patterns = []

        lines = self._get_lines(content)
        for i, line in enumerate(lines):
            if DERIVE_MACRO_RE.search(line):
                derive_macros.append({"line": i + 1, "macros": line})

            macro_match = MACRO_RULES_RE.search(line)
            if macro_match:
                macro_name = macro_match.group(1)
                custom_macros.append({"line": i + 1, "name": macro_name})

                has_docs = any(
                    DOC_COMMENT_RE.search(lines[j]) for j in range(max(0, i - 5), i)
                )

                if "unsafe" in macro_name.lower() and not has_docs:
                    problematic_patterns.append(
                        {
                            "line": i + 1,
                            "type": "undocumented_unsafe_macro",
                            "name": macro_name,
                            "description": ("Unsafe macro without documentation"),
                        }
                    )

            if "macro_rules!" in line:
                for j in range(i, min(len(lines), i + 20)):
                    if "return" in lines[j] and not lines[j].strip().startswith("//"):
                        problematic_patterns.append(
                            {
                                "line": j + 1,
                                "type": "hidden_control_flow",
                                "description": (
                                    "Macro contains hidden return statement"
                                ),
                            }
                        )
                        break

        return {
            "custom_macros": custom_macros,
            "derive_macros": derive_macros,
            "problematic_patterns": problematic_patterns,
        }

    def analyze_traits(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze trait implementations.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with trait analysis
        """
        content = context.get_file_content(file_path)
        trait_definitions: list[dict[str, Any]] = []
        implementations: list[dict[str, Any]] = []
        object_safety_issues: list[dict[str, Any]] = []
        missing_methods: list[str] = []

        lines = self._get_lines(content)
        current_trait = None
        trait_methods: list[str] = []

        for i, line in enumerate(lines):
            trait_match = TRAIT_DEF_RE.search(line) if "impl" not in line else None
            if trait_match:
                current_trait = trait_match.group(1)
                trait_methods = []
                trait_definitions.append({"line": i + 1, "name": current_trait})

            if current_trait:
                method_match = TRAIT_METHOD_RE.search(line)
                if method_match:
                    trait_methods.append(method_match.group(1))

                    if GENERIC_METHOD_RE.search(line):
                        object_safety_issues.append(
                            {
                                "line": i + 1,
                                "trait": current_trait,
                                "issue": "Generic method - not object-safe",
                            }
                        )

                    if (
                        STATIC_METHOD_RE.search(line)
                        and "->" in line
                        and "self" not in line
                    ):
                        object_safety_issues.append(
                            {
                                "line": i + 1,
                                "trait": current_trait,
                                "issue": "Static method - not object-safe",
                            }
                        )

            if current_trait and line.strip() == "}":
                current_trait = None

            impl_match = IMPL_FOR_RE.search(line)
            if impl_match:
                trait_name, type_name = impl_match.groups()
                implementations.append(
                    {
                        "line": i + 1,
                        "trait": trait_name,
                        "type": type_name,
                    }
                )

        return {
            "trait_definitions": trait_definitions,
            "implementations": implementations,
            "object_safety_issues": object_safety_issues,
            "missing_methods": missing_methods,
        }

    def analyze_const_generics(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze const generic usage.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with const generic analysis
        """
        content = context.get_file_content(file_path)
        const_generic_structs = []
        bounded_generics = []
        unconstrained_usage = []

        lines = self._get_lines(content)
        current_struct = None

        for i, line in enumerate(lines):
            struct_match = CONST_GENERIC_STRUCT_RE.search(line)
            if struct_match:
                struct_name = struct_match.group(1)
                const_param = struct_match.group(2)
                current_struct = struct_name
                const_generic_structs.append(
                    {
                        "line": i + 1,
                        "name": struct_name,
                        "const_param": const_param,
                    }
                )

                is_used = any(
                    const_param in lines[j] and j != i
                    for j in range(i, min(len(lines), i + 10))
                )
                if not is_used:
                    unconstrained_usage.append(
                        {
                            "line": i + 1,
                            "struct": struct_name,
                            "issue": (f"Const generic {const_param} unconstrained"),
                        }
                    )

            if CONST_MAX_RE.search(line):
                bounded_generics.append(
                    {
                        "line": i + 1,
                        "description": "Const generic with bounds",
                    }
                )

            if "PhantomData" in line and current_struct:
                unconstrained_usage.append(
                    {
                        "line": i + 1,
                        "struct": current_struct,
                        "issue": (
                            "PhantomData usage - may indicate unconstrained type"
                        ),
                    }
                )

        return {
            "const_generic_structs": const_generic_structs,
            "bounded_generics": bounded_generics,
            "unconstrained_usage": unconstrained_usage,
        }
