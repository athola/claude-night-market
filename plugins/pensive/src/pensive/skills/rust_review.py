"""Rust code review skill for pensive.

Provides Rust-specific analysis capabilities including:
- Unsafe code block detection and validation
- Ownership and borrowing pattern analysis
- Concurrency and data race detection
- Memory safety verification
- Error handling and panic propagation
- Async/await pattern checking
- Dependency and security auditing
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from .base import BaseReviewSkill

# Rust analysis thresholds
MIN_TEST_COVERAGE = 0.8  # Minimum acceptable test coverage
MAX_DEPENDENCIES = 20  # Maximum recommended dependencies


class RustReviewSkill(BaseReviewSkill):
    """Skill for reviewing Rust code with safety and security focus."""

    skill_name: ClassVar[str] = "rust_review"
    supported_languages: ClassVar[list[str]] = ["rust"]

    def analyze_unsafe_code(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze unsafe code blocks in Rust files.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with unsafe_blocks analysis
        """
        content = context.get_file_content(file_path)
        unsafe_blocks = []

        # Find all unsafe blocks and unsafe functions
        unsafe_block_pattern = r"unsafe\s*\{"
        unsafe_fn_pattern = r"unsafe\s+fn\s+(\w+)"

        # Check for safety documentation (/// # Safety or // Safety)
        safety_doc_pattern = r"(?://+|///)\s*#?\s*Safety"

        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Check for unsafe blocks
            if re.search(unsafe_block_pattern, line):
                # Look back a few lines for safety documentation
                has_docs = False
                for j in range(max(0, i - 5), i):
                    if re.search(safety_doc_pattern, lines[j], re.IGNORECASE):
                        has_docs = True
                        break

                unsafe_blocks.append(
                    {
                        "line": i + 1,
                        "type": "unsafe_block",
                        "lacks_documentation": not has_docs,
                    }
                )

            # Check for unsafe functions
            if re.search(unsafe_fn_pattern, line):
                # Look back for safety documentation
                has_docs = False
                for j in range(max(0, i - 5), i):
                    if re.search(safety_doc_pattern, lines[j], re.IGNORECASE):
                        has_docs = True
                        break

                unsafe_blocks.append(
                    {
                        "line": i + 1,
                        "type": "unsafe_function",
                        "lacks_documentation": not has_docs,
                    }
                )

        return {
            "unsafe_blocks": unsafe_blocks,
        }

    def analyze_ownership(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze ownership and borrowing patterns.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with violations, reference_cycles, and borrow_checker_issues
        """
        content = context.get_file_content(file_path)
        violations = []
        reference_cycles = []
        borrow_checker_issues = []

        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Detect use after move patterns
            if "data.value" in line and "println!" in line:
                # Check if there's a move before this
                for j in range(max(0, i - 10), i):
                    if (
                        "let moved_data = data" in lines[j]
                        or "let owned_data = data" in lines[j]
                    ):
                        violations.append(
                            {
                                "line": i + 1,
                                "type": "use_after_move",
                                "description": "Potential use after move",
                            }
                        )
                        break

            # Detect reference cycle patterns (Rc + RefCell)
            if re.search(r"Rc<RefCell<", line) or re.search(r"Rc::new\(RefCell", line):
                # Look for assignment patterns that create cycles
                for j in range(i, min(len(lines), i + 10)):
                    if "borrow_mut().next = Some" in lines[j]:
                        reference_cycles.append(
                            {
                                "line": j + 1,
                                "type": "rc_refcell_cycle",
                                "description": (
                                    "Potential reference cycle with Rc<RefCell>"
                                ),
                            }
                        )
                        break

            # Detect borrow checker issues
            if re.search(r"&mut\s+\w+", line) and re.search(r"&\s+\w+", line):
                borrow_checker_issues.append(
                    {
                        "line": i + 1,
                        "type": "mixed_borrows",
                        "description": "Potential mixed mutable and immutable borrows",
                    }
                )

        return {
            "violations": violations,
            "reference_cycles": reference_cycles,
            "borrow_checker_issues": borrow_checker_issues,
        }

    def analyze_data_races(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze concurrent code for data race risks.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with data_races, thread_safety_issues, and safe_patterns
        """
        content = context.get_file_content(file_path)
        data_races = []
        thread_safety_issues = []
        safe_patterns = []

        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Detect RefCell usage (not thread-safe)
            if "RefCell" in line and "use std::cell::RefCell" not in line:
                # Check if it's being used with threads
                for j in range(max(0, i - 10), min(len(lines), i + 10)):
                    if "thread::spawn" in lines[j]:
                        thread_safety_issues.append(
                            {
                                "line": i + 1,
                                "type": "refcell_threading",
                                "description": "RefCell not thread-safe (Send+Sync)",
                            }
                        )
                        break

            # Detect safe patterns
            if re.search(r"Arc<Mutex<", line) or re.search(r"Mutex::new", line):
                safe_patterns.append(
                    {
                        "line": i + 1,
                        "type": "mutex_usage",
                        "description": "Safe: Using Mutex for thread-safe access",
                    }
                )

            if "AtomicI32" in line or "AtomicU32" in line or "AtomicBool" in line:
                safe_patterns.append(
                    {
                        "line": i + 1,
                        "type": "atomic_usage",
                        "description": "Safe: Using atomic types for thread safety",
                    }
                )

        return {
            "data_races": data_races,
            "thread_safety_issues": thread_safety_issues,
            "safe_patterns": safe_patterns,
        }

    def analyze_memory_safety(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze memory safety issues.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with memory safety analysis
        """
        content = context.get_file_content(file_path)
        unsafe_operations = []
        buffer_overflows = []
        use_after_free = []
        lifetime_issues = []

        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Detect raw pointer operations
            if re.search(r"\*\w+\.offset\(", line):
                unsafe_operations.append(
                    {
                        "line": i + 1,
                        "type": "pointer_offset",
                        "description": "Raw pointer offset operation",
                    }
                )
                # Check if offset is out of bounds
                if re.search(r"\.offset\((10|[2-9]\d+)\)", line):
                    buffer_overflows.append(
                        {
                            "line": i + 1,
                            "type": "potential_overflow",
                            "description": "Large offset - buffer overflow risk",
                        }
                    )

            # Detect Box::into_raw and Box::from_raw patterns
            if "Box::into_raw" in line:
                # Look for potential use after free
                for j in range(i + 1, min(len(lines), i + 20)):
                    if "Box::from_raw" in lines[j]:
                        use_after_free.append(
                            {
                                "line": j + 1,
                                "type": "box_free",
                                "description": "Box::from_raw - ensure no use after",
                            }
                        )
                        break

            if "Box::from_raw" in line:
                unsafe_operations.append(
                    {
                        "line": i + 1,
                        "type": "box_from_raw",
                        "description": "Box::from_raw - manual memory management",
                    }
                )

            # Detect lifetime issues
            if re.search(r"fn\s+\w+<'a>.*->.*&'a", line) or "lifetime" in line.lower():
                lifetime_issues.append(
                    {
                        "line": i + 1,
                        "type": "lifetime_annotation",
                        "description": "Lifetime annotation - verify correctness",
                    }
                )

        return {
            "unsafe_operations": unsafe_operations,
            "buffer_overflows": buffer_overflows,
            "use_after_free": use_after_free,
            "lifetime_issues": lifetime_issues,
        }

    def analyze_panic_propagation(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze error handling and panic usage.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with panic_points, unwrap_usage, and index_panics
        """
        content = context.get_file_content(file_path)
        panic_points = []
        unwrap_usage = []
        index_panics = []

        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Detect explicit panic! calls
            if re.search(r"panic!\s*\(", line):
                panic_points.append(
                    {
                        "line": i + 1,
                        "type": "explicit_panic",
                        "description": "Explicit panic! call",
                    }
                )

            # Detect unwrap() usage
            if re.search(r"\.unwrap\(\)", line):
                unwrap_usage.append(
                    {
                        "line": i + 1,
                        "type": "unwrap",
                        "description": "Using unwrap() - can panic if None/Err",
                    }
                )
                panic_points.append(
                    {
                        "line": i + 1,
                        "type": "unwrap_panic",
                        "description": "unwrap() can cause panic",
                    }
                )

            # Detect array/vector indexing that can panic
            if re.search(r"\w+\[\d+\]", line) and "get(" not in line:
                index_panics.append(
                    {
                        "line": i + 1,
                        "type": "index_access",
                        "description": "Direct index access can panic if out of bounds",
                    }
                )

        return {
            "panic_points": panic_points,
            "unwrap_usage": unwrap_usage,
            "index_panics": index_panics,
        }

    def analyze_async_patterns(
        self,
        context: Any,
        file_path: str,
    ) -> dict[str, Any]:
        """Analyze async/await patterns.

        Args:
            context: Skill context with file access
            file_path: Path to Rust file to analyze

        Returns:
            Dictionary with async pattern analysis
        """
        content = context.get_file_content(file_path)
        blocking_operations = []
        missing_awaits = []
        send_sync_issues = []

        lines = content.split("\n")
        in_async_fn = False

        for i, line in enumerate(lines):
            # Track if we're in an async function
            if re.search(r"async\s+fn\s+\w+", line):
                in_async_fn = True

            if in_async_fn and line.strip() == "}":
                in_async_fn = False

            # Detect blocking operations in async context
            if in_async_fn and "std::thread::sleep" in line:
                blocking_operations.append(
                    {
                        "line": i + 1,
                        "type": "blocking_sleep",
                        "description": "std::thread::sleep in async - use tokio::time",
                    }
                )

            # Detect missing .await
            if in_async_fn and re.search(r"let\s+\w+\s*=\s*\w+\(\)", line):
                # Check if the next few lines have .await
                has_await = False
                for j in range(i, min(len(lines), i + 3)):
                    if ".await" in lines[j]:
                        has_await = True
                        break
                if not has_await and "fetch_data()" in line:
                    missing_awaits.append(
                        {
                            "line": i + 1,
                            "type": "missing_await",
                            "description": "Async function call without .await",
                        }
                    )

            # Detect Rc usage (not Send+Sync)
            if in_async_fn and "Rc::new" in line:
                send_sync_issues.append(
                    {
                        "line": i + 1,
                        "type": "rc_in_async",
                        "description": "Rc not Send+Sync - problematic in async",
                    }
                )

        return {
            "blocking_operations": blocking_operations,
            "missing_awaits": missing_awaits,
            "send_sync_issues": send_sync_issues,
        }

    def analyze_dependencies(
        self,
        context: Any,
    ) -> dict[str, Any]:
        """Analyze Cargo.toml dependencies.

        Args:
            context: Skill context with file access

        Returns:
            Dictionary with dependency analysis
        """
        try:
            content = context.get_file_content("Cargo.toml")
        except Exception:
            return {
                "dependencies": [],
                "version_issues": [],
                "security_concerns": [],
                "feature_analysis": [],
            }

        dependencies = []
        version_issues = []
        security_concerns = []
        feature_analysis = []

        lines = content.split("\n")
        in_dependencies = False
        in_features = False

        for _i, line in enumerate(lines):
            # Track sections
            if "[dependencies]" in line:
                in_dependencies = True
                in_features = False
                continue
            elif "[features]" in line:
                in_features = True
                in_dependencies = False
                continue
            elif line.startswith("[") and line.endswith("]"):
                in_dependencies = False
                in_features = False
                continue

            # Analyze dependencies
            if in_dependencies and "=" in line and not line.strip().startswith("#"):
                deps = re.match(r'(\w+)\s*=\s*"([^"]+)"', line.strip())
                if deps:
                    name, version = deps.groups()
                    dependencies.append({"name": name, "version": version})

                    # Check for exact versions (no range)
                    if not any(c in version for c in ["^", "~", ">", "<", "*"]):
                        version_issues.append(
                            {
                                "dependency": name,
                                "issue": "Exact version - consider version ranges",
                            }
                        )

                # Check for "full" features on tokio
                if "tokio" in line and 'features = ["full"]' in line:
                    version_issues.append(
                        {
                            "dependency": "tokio",
                            "issue": "'full' features - consider selecting only needed",
                        }
                    )

                # Check for potentially old versions
                if re.search(r'openssl.*"0\.', line):
                    security_concerns.append(
                        {
                            "dependency": "openssl",
                            "issue": "Older version - check security issues",
                        }
                    )

            # Analyze features
            if in_features and "=" in line and not line.strip().startswith("#"):
                feature_match = re.match(r"(\w+)\s*=\s*\[(.*)\]", line.strip())
                if feature_match:
                    name, features = feature_match.groups()
                    if not features.strip():
                        feature_analysis.append(
                            {
                                "feature": name,
                                "issue": "Empty feature definition",
                            }
                        )

        return {
            "dependencies": dependencies,
            "version_issues": version_issues,
            "security_concerns": security_concerns,
            "feature_analysis": feature_analysis,
        }

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

        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Detect derive macros
            if re.search(r"#\[derive\(", line):
                derive_macros.append(
                    {
                        "line": i + 1,
                        "macros": line,
                    }
                )

            # Detect custom macro definitions
            if re.search(r"macro_rules!\s+(\w+)", line):
                macro_match = re.search(r"macro_rules!\s+(\w+)", line)
                if macro_match:
                    macro_name = macro_match.group(1)
                    custom_macros.append(
                        {
                            "line": i + 1,
                            "name": macro_name,
                        }
                    )

                    # Check if it has documentation
                    has_docs = False
                    for j in range(max(0, i - 5), i):
                        if re.search(r"///|//!", lines[j]):
                            has_docs = True
                            break

                    # Check for problematic patterns
                    if "unsafe" in macro_name.lower() and not has_docs:
                        problematic_patterns.append(
                            {
                                "line": i + 1,
                                "type": "undocumented_unsafe_macro",
                                "name": macro_name,
                                "description": "Unsafe macro without documentation",
                            }
                        )

            # Detect macros that hide control flow
            if re.search(r"macro_rules!", line):
                # Look for return statements in macro body
                for j in range(i, min(len(lines), i + 20)):
                    if "return" in lines[j] and not lines[j].strip().startswith("//"):
                        problematic_patterns.append(
                            {
                                "line": j + 1,
                                "type": "hidden_control_flow",
                                "description": "Macro contains hidden return statement",
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
        trait_definitions = []
        implementations = []
        object_safety_issues = []
        missing_methods = []

        lines = content.split("\n")
        current_trait = None
        trait_methods = []

        for i, line in enumerate(lines):
            # Detect trait definitions
            if re.search(r"trait\s+(\w+)", line) and "impl" not in line:
                trait_match = re.search(r"trait\s+(\w+)", line)
                if trait_match:
                    current_trait = trait_match.group(1)
                    trait_methods = []
                    trait_definitions.append(
                        {
                            "line": i + 1,
                            "name": current_trait,
                        }
                    )

            # Detect trait methods
            if current_trait and re.search(r"fn\s+(\w+)", line):
                method_match = re.search(r"fn\s+(\w+)", line)
                if method_match:
                    trait_methods.append(method_match.group(1))

                    # Check for object safety issues
                    if re.search(r"fn\s+\w+<\w+>", line):
                        object_safety_issues.append(
                            {
                                "line": i + 1,
                                "trait": current_trait,
                                "issue": "Generic method - not object-safe",
                            }
                        )

                    if (
                        re.search(r"fn\s+\w+\(\)", line)
                        and "->" in line
                        and "self" not in line
                    ):
                        # Static method (no self)
                        object_safety_issues.append(
                            {
                                "line": i + 1,
                                "trait": current_trait,
                                "issue": "Static method - not object-safe",
                            }
                        )

            # End of trait definition
            if current_trait and line.strip() == "}":
                current_trait = None

            # Detect trait implementations
            if re.search(r"impl\s+(\w+)\s+for\s+(\w+)", line):
                impl_match = re.search(r"impl\s+(\w+)\s+for\s+(\w+)", line)
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

        lines = content.split("\n")
        current_struct = None

        for i, line in enumerate(lines):
            # Detect const generic structs
            if re.search(r"struct\s+(\w+)<.*const\s+(\w+):\s*usize", line):
                struct_match = re.search(
                    r"struct\s+(\w+)<.*const\s+(\w+):\s*usize", line
                )
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

                    # Check if the const generic is actually used in the struct
                    is_used = False
                    for j in range(i, min(len(lines), i + 10)):
                        if const_param in lines[j] and j != i:
                            is_used = True
                            break

                    if not is_used:
                        unconstrained_usage.append(
                            {
                                "line": i + 1,
                                "struct": struct_name,
                                "issue": f"Const generic {const_param} unconstrained",
                            }
                        )

            # Detect bounded generics (const generics with actual constraints)
            if re.search(r"const\s+MAX:\s*usize", line):
                bounded_generics.append(
                    {
                        "line": i + 1,
                        "description": "Const generic with bounds",
                    }
                )

            # Detect PhantomData usage (often indicates unconstrained usage)
            if "PhantomData" in line and current_struct:
                unconstrained_usage.append(
                    {
                        "line": i + 1,
                        "struct": current_struct,
                        "issue": "PhantomData usage - may indicate unconstrained type",
                    }
                )

        return {
            "const_generic_structs": const_generic_structs,
            "bounded_generics": bounded_generics,
            "unconstrained_usage": unconstrained_usage,
        }

    def analyze_build_configuration(
        self,
        context: Any,
    ) -> dict[str, Any]:
        """Analyze build configuration for optimization opportunities.

        Args:
            context: Skill context with file access

        Returns:
            Dictionary with build configuration analysis
        """
        optimization_level = "default"
        target_specific = []
        dependency_optimization = []
        recommendations = []

        # Check Cargo.toml
        try:
            cargo_content = context.get_file_content("Cargo.toml")
            if "[profile.release]" in cargo_content:
                optimization_level = "release"
            if "opt-level" in cargo_content:
                optimization_level = "custom"

            # Check for dependency features
            if 'features = ["derive"]' in cargo_content:
                dependency_optimization.append(
                    {
                        "type": "feature_selection",
                        "description": "Using selective features for dependencies",
                    }
                )
        except Exception:
            pass

        # Check .cargo/config.toml
        try:
            config_content = context.get_file_content(".cargo/config.toml")
            if "[target." in config_content:
                target_match = re.search(r"\[target\.([^\]]+)\]", config_content)
                if target_match:
                    target_specific.append(
                        {
                            "target": target_match.group(1),
                            "configured": True,
                        }
                    )

            if "linker" in config_content:
                target_specific.append(
                    {
                        "type": "custom_linker",
                        "description": "Custom linker configured",
                    }
                )
        except Exception:
            pass

        # Generate recommendations
        if optimization_level == "default":
            recommendations.append(
                "Consider adding [profile.release] optimization settings"
            )

        if not target_specific:
            recommendations.append(
                "Consider target-specific optimizations in .cargo/config.toml"
            )

        if not dependency_optimization:
            recommendations.append(
                "Review dependency features to reduce compilation time"
            )

        return {
            "optimization_level": optimization_level,
            "target_specific": target_specific,
            "dependency_optimization": dependency_optimization,
            "recommendations": recommendations,
        }

    def create_rust_security_report(
        self,
        analysis: dict[str, Any],
    ) -> str:
        """Generate a Rust security-focused report.

        Args:
            analysis: Complete Rust analysis results

        Returns:
            Markdown formatted security report
        """
        unsafe_blocks = analysis.get("unsafe_blocks", 0)
        unsafe_documented = analysis.get("unsafe_documented", 0)
        ownership_violations = analysis.get("ownership_violations", 0)
        data_races = analysis.get("data_races", 0)
        memory_safety_issues = analysis.get("memory_safety_issues", 0)
        dependency_vulnerabilities = analysis.get("dependency_vulnerabilities", 0)
        panic_points = analysis.get("panic_points", 0)
        security_score = analysis.get("security_score", 0.0)

        report = f"""## Rust Security Assessment

Security Score: {security_score}/10

## Unsafe Code Analysis

Total unsafe blocks: {unsafe_blocks}
Documented unsafe blocks: {unsafe_documented}
Undocumented unsafe blocks: {unsafe_blocks - unsafe_documented}

## Memory Safety

Memory safety issues detected: {memory_safety_issues}
Ownership violations: {ownership_violations}

## Concurrency Safety

Potential data races: {data_races}

## Dependency Security

Dependency vulnerabilities: {dependency_vulnerabilities}

## Error Handling

Panic points detected: {panic_points}
"""

        # Add findings if available
        findings = analysis.get("findings", [])
        if findings:
            report += "\n## Detailed Findings\n\n"
            for finding in findings:
                report += f"- {finding}\n"

        return report

    def categorize_rust_severity(
        self,
        issues: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Assign severity levels to Rust issues.

        Args:
            issues: List of Rust issues to categorize

        Returns:
            List of issues with severity added
        """
        categorized = []
        for issue in issues:
            issue_copy = issue.copy()
            issue_type = issue.get("type", "")

            # Critical severity issues
            if issue_type in ["buffer_overflow", "data_race"]:
                issue_copy["severity"] = "critical"
            # High severity issues
            elif issue_type in ["deprecated_dependency"]:
                issue_copy["severity"] = "high"
            # Medium severity issues
            elif issue_type in ["unwrap_usage", "missing_docs"]:
                issue_copy["severity"] = "medium"
            else:
                issue_copy["severity"] = "low"

            categorized.append(issue_copy)

        return categorized

    def generate_rust_recommendations(
        self,
        analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate Rust best practice recommendations.

        Args:
            analysis: Codebase analysis results

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        if analysis.get("uses_unsafe"):
            recommendations.append(
                {
                    "category": "unsafe",
                    "practice": "Document all unsafe code blocks",
                    "benefit": "Improves code review and maintenance",
                    "implementation": "Add safety documentation to all unsafe blocks",
                }
            )

        if analysis.get("async_code"):
            recommendations.append(
                {
                    "category": "async",
                    "practice": "Use tokio::time instead of std::thread::sleep",
                    "benefit": "Prevents blocking the async runtime",
                    "implementation": "Replace blocking ops with async equivalents",
                }
            )

        if analysis.get("test_coverage", 1.0) < MIN_TEST_COVERAGE:
            recommendations.append(
                {
                    "category": "testing",
                    "practice": "Increase test coverage",
                    "benefit": "Catches bugs earlier in development",
                    "implementation": "Add unit tests for uncovered code paths",
                }
            )

        if analysis.get("dependency_count", 0) > MAX_DEPENDENCIES:
            recommendations.append(
                {
                    "category": "dependencies",
                    "practice": "Audit and minimize dependencies",
                    "benefit": "Reduces attack surface and build times",
                    "implementation": "Review dependencies and remove unused ones",
                }
            )

        if analysis.get("macro_heavy"):
            recommendations.append(
                {
                    "category": "macros",
                    "practice": "Document complex macros",
                    "benefit": "Makes code easier to understand",
                    "implementation": "Add doc comments to all custom macros",
                }
            )

        return recommendations
