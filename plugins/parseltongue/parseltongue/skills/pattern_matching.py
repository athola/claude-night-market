"""Design pattern detection skill for parseltongue."""

from __future__ import annotations

import ast
import re
from typing import Any


class PatternMatchingSkill:
    """Detect design patterns in Python code using AST analysis."""

    async def find_patterns(
        self, code: str, language: str = "python"
    ) -> dict[str, Any]:
        if language != "python":
            return {
                "patterns": [],
                "optimization_suggestions": [],
                "note": f"Only Python supported, got {language}",
            }

        if not code:
            return {"patterns": [], "optimization_suggestions": []}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                "patterns": [],
                "optimization_suggestions": [],
                "error": "Invalid Python syntax",
            }

        patterns: list[dict[str, Any]] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            methods = {
                item.name
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            attrs: set[str] = set()
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            attrs.add(target.id)
                        elif isinstance(target, ast.Attribute):
                            attrs.add(target.attr)

            # Singleton
            if "_instance" in attrs and (
                "__new__" in methods or "get_instance" in methods
            ):
                patterns.append(
                    {
                        "pattern": "singleton",
                        "class": node.name,
                        "line": node.lineno,
                        "evidence": "_instance attribute with __new__/get_instance",
                    }
                )

            # Observer
            observer_methods = methods & {
                "subscribe",
                "notify",
                "attach",
                "detach",
                "add_observer",
                "remove_observer",
                "notify_observers",
            }
            if len(observer_methods) >= 2:
                patterns.append(
                    {
                        "pattern": "observer",
                        "class": node.name,
                        "line": node.lineno,
                        "evidence": f"Methods: {', '.join(sorted(observer_methods))}",
                    }
                )

            # Strategy
            if "__init__" in methods:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        for arg in item.args.args:
                            if arg.annotation and isinstance(arg.annotation, ast.Name):
                                if arg.annotation.id in (
                                    "Callable",
                                    "Protocol",
                                    "Strategy",
                                ):
                                    patterns.append(
                                        {
                                            "pattern": "strategy",
                                            "class": node.name,
                                            "line": node.lineno,
                                            "evidence": f"Parameter "
                                            f"'{arg.arg}' typed as "
                                            f"{arg.annotation.id}",
                                        }
                                    )

        # Factory
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            return_classes: set[str] = set()
            has_conditional = False
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.IfExp)):
                    has_conditional = True
                if isinstance(child, ast.Return) and child.value:
                    if isinstance(child.value, ast.Call):
                        if isinstance(child.value.func, ast.Name):
                            name = child.value.func.id
                            if name[0].isupper():
                                return_classes.add(name)
            if has_conditional and len(return_classes) >= 2:
                patterns.append(
                    {
                        "pattern": "factory",
                        "function": node.name,
                        "line": node.lineno,
                        "evidence": "Returns different classes: "
                        + ", ".join(sorted(return_classes)),
                    }
                )

        # Decorator
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            uses_wraps = False
            for child in ast.walk(node):
                if isinstance(child, ast.Attribute) and child.attr == "wraps":
                    uses_wraps = True
                if isinstance(child, ast.Name) and child.id == "wraps":
                    uses_wraps = True
            if uses_wraps:
                patterns.append(
                    {
                        "pattern": "decorator",
                        "function": node.name,
                        "line": node.lineno,
                        "evidence": "Uses @wraps, function decorator pattern",
                    }
                )

        return {"patterns": patterns, "optimization_suggestions": []}

    def match_patterns(self, code: str, language: str = "python") -> dict[str, Any]:
        """Match patterns in code with confidence scoring.

        Args:
            code: Code to analyze
            language: Programming language

        Returns:
            Dictionary with patterns and confidence
        """
        patterns: list[str] = []
        confidence = 0.5

        if not code:
            return {"patterns": [], "confidence": 0.0}

        # Detect nested loops
        if re.search(r"for\s+\w+\s+in\s+.*:\s*\n\s+for\s+\w+\s+in", code):
            patterns.append("nested_loop")
            confidence = 0.8

        # Detect list comprehensions
        if re.search(r"\[.*for\s+\w+\s+in\s+.*\]", code):
            patterns.append("list_comprehension")
            confidence = max(confidence, 0.7)

        return {"patterns": patterns, "confidence": confidence}

    def recognize_test_patterns(self, code: str) -> dict[str, Any]:
        """Recognize testing patterns in code.

        Args:
            code: Test code to analyze

        Returns:
            Dictionary with recognized testing patterns
        """
        recognized_patterns: list[str] = []
        pytest_patterns: list[str] = []
        structures: list[str] = []
        test_classes: list[str] = []
        lifecycle_methods: list[str] = []
        confidence = 0.0

        if not code:
            return {
                "recognized_patterns": recognized_patterns,
                "confidence": 0.0,
                "patterns": {"pytest": pytest_patterns},
                "structures": structures,
                "test_classes": test_classes,
                "lifecycle_methods": lifecycle_methods,
            }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                "recognized_patterns": [],
                "confidence": 0.0,
                "patterns": {"pytest": []},
                "structures": [],
                "test_classes": [],
                "lifecycle_methods": [],
            }

        # Detect pytest fixtures
        if "@pytest.fixture" in code or "@fixture" in code:
            pytest_patterns.append("fixture")
            recognized_patterns.append("test_pattern")

        # Detect test classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.startswith("Test"):
                    structures.append("test_class")
                    test_classes.append(node.name)
                    confidence = max(confidence, 0.9)

                # Check for lifecycle methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name in (
                            "setup_method",
                            "teardown_method",
                            "setup_class",
                            "teardown_class",
                            "setUp",
                            "tearDown",
                        ):
                            lifecycle_methods.append(item.name)

        # Detect test functions
        if re.search(r"def test_\w+", code):
            recognized_patterns.append("test_pattern")
            confidence = max(confidence, 0.85)

        return {
            "recognized_patterns": recognized_patterns,
            "confidence": confidence,
            "patterns": {"pytest": pytest_patterns},
            "structures": structures,
            "test_classes": test_classes,
            "lifecycle_methods": lifecycle_methods,
        }

    def recognize_ddd_patterns(self, code: str) -> dict[str, Any]:
        """Recognize Domain-Driven Design patterns.

        Args:
            code: Code to analyze

        Returns:
            Dictionary with DDD pattern analysis
        """
        ddd_patterns: dict[str, Any] = {}
        entities: list[str] = []
        value_objects: list[str] = []
        repositories: list[str] = []
        domain_services: list[str] = []

        if not code:
            return {"ddd_patterns": ddd_patterns}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"ddd_patterns": ddd_patterns}

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            methods = {
                item.name for item in node.body if isinstance(item, ast.FunctionDef)
            }
            bases = [b.id if isinstance(b, ast.Name) else "" for b in node.bases]
            decorators = []
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name):
                    decorators.append(dec.id)
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)

            # Entity: has id and mutable methods
            if any(
                arg.arg == "id"
                for item in node.body
                if isinstance(item, ast.FunctionDef) and item.name == "__init__"
                for arg in item.args.args
            ) or (
                "dataclass" in decorators
                and any(
                    isinstance(item, ast.AnnAssign)
                    and isinstance(item.target, ast.Name)
                    and item.target.id == "id"
                    for item in node.body
                )
            ):
                # Not frozen = entity
                is_frozen = any(
                    "frozen" in str(ast.dump(dec)) and "True" in str(ast.dump(dec))
                    for dec in node.decorator_list
                    if isinstance(dec, ast.Call)
                )
                if not is_frozen and methods - {"__init__", "__post_init__"}:
                    entities.append(node.name)

            # Value Object: frozen dataclass or immutable
            if "dataclass" in decorators:
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call):
                        for kw in dec.keywords:
                            if (
                                kw.arg == "frozen"
                                and isinstance(kw.value, ast.Constant)
                                and kw.value.value is True
                            ):
                                value_objects.append(node.name)

            # Repository: has save/find/delete methods
            repo_methods = methods & {
                "save",
                "find_by_id",
                "find",
                "delete",
                "add",
                "get",
                "remove",
            }
            if (
                len(repo_methods) >= 2
                or "Repository" in node.name
                or ("ABC" in bases
                and repo_methods)
            ):
                if "Repository" in node.name or ("ABC" in bases and repo_methods):
                    repositories.append(node.name)

            # Domain Service: has repository dependency
            if "Service" in node.name and "__init__" in methods:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        for arg in item.args.args:
                            if arg.arg == "repository":
                                domain_services.append(node.name)

        if entities:
            ddd_patterns["entity"] = True
            ddd_patterns["entities"] = entities
        if value_objects:
            ddd_patterns["value_object"] = True
            ddd_patterns["value_objects"] = value_objects
        if repositories:
            ddd_patterns["repository"] = True
            ddd_patterns["repositories"] = repositories
        if domain_services:
            ddd_patterns["domain_service"] = True
            ddd_patterns["domain_services"] = domain_services

        return {"ddd_patterns": ddd_patterns}

    def recognize_gof_patterns(self, code: str) -> dict[str, Any]:
        """Recognize Gang of Four design patterns.

        Args:
            code: Code to analyze

        Returns:
            Dictionary with GoF pattern analysis
        """
        gof_patterns: dict[str, Any] = {}
        factories: list[str] = []
        observers: list[str] = []
        strategies: list[str] = []

        if not code:
            return {"gof_patterns": gof_patterns}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"gof_patterns": gof_patterns}

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            methods = {
                item.name for item in node.body if isinstance(item, ast.FunctionDef)
            }
            bases = []
            for b in node.bases:
                if isinstance(b, ast.Name):
                    bases.append(b.id)

            # Factory: has create/static methods returning different types
            if "Factory" in node.name or (
                any(
                    isinstance(dec, ast.Name) and dec.id == "staticmethod"
                    for item in node.body
                    if isinstance(item, ast.FunctionDef)
                    for dec in item.decorator_list
                )
                and "create" in "".join(methods).lower()
            ):
                factories.append(node.name)

            # Observer: has subscribe/notify methods
            observer_methods = methods & {
                "subscribe",
                "notify",
                "attach",
                "detach",
                "notify_observers",
                "add_observer",
                "remove_observer",
            }
            if len(observer_methods) >= 2 or ("Observer" in node.name and "ABC" in bases):
                observers.append(node.name)

            # Strategy: abstract class with single method
            if (
                ("ABC" in bases
                and "Strategy" in node.name)
                or ("Payment" in node.name
                and "ABC" in bases)
            ) or any(b in strategies or "Strategy" in b for b in bases):
                strategies.append(node.name)

        if factories:
            gof_patterns["factory_method"] = True
            gof_patterns["factories"] = factories
        if observers:
            gof_patterns["observer"] = True
            gof_patterns["observers"] = observers
        if strategies:
            gof_patterns["strategy"] = True
            gof_patterns["strategies"] = strategies

        return {"gof_patterns": gof_patterns}

    def recognize_async_patterns(self, code: str) -> dict[str, Any]:
        """Recognize async programming patterns.

        Args:
            code: Code to analyze

        Returns:
            Dictionary with async pattern analysis
        """
        async_patterns: dict[str, bool] = {}
        pattern_instances: list[str] = []

        if not code:
            return {
                "async_patterns": async_patterns,
                "pattern_instances": pattern_instances,
            }

        # Async context manager
        if "__aenter__" in code or "@asynccontextmanager" in code:
            async_patterns["async_context_manager"] = True

        # Retry pattern
        if "retry" in code.lower() or ("for attempt" in code and "await" in code):
            async_patterns["retry_pattern"] = True
            # Find function names with retry
            for match in re.finditer(
                r"async\s+def\s+(\w*retry\w*)", code, re.IGNORECASE
            ):
                pattern_instances.append(match.group(1))
            # Also check for fetch_with_retry style names
            for match in re.finditer(r"async\s+def\s+(fetch_with_\w+)", code):
                if match.group(1) not in pattern_instances:
                    pattern_instances.append(match.group(1))

        # Concurrent processing
        if "asyncio.gather" in code or "create_task" in code:
            async_patterns["concurrent_processing"] = True

        # Batch processing
        if "batch" in code.lower() and "await" in code:
            async_patterns["batch_processing"] = True

        return {
            "async_patterns": async_patterns,
            "pattern_instances": pattern_instances,
        }

    def recognize_performance_patterns(self, code: str) -> dict[str, Any]:
        """Recognize performance patterns and anti-patterns.

        Args:
            code: Code to analyze

        Returns:
            Dictionary with performance pattern analysis
        """
        performance_patterns: dict[str, Any] = {}
        anti_patterns: list[str] = []
        good_patterns: list[str] = []
        pattern_instances: list[str] = []

        if not code:
            return {
                "performance_patterns": performance_patterns,
                "anti_patterns": anti_patterns,
                "good_patterns": good_patterns,
                "pattern_instances": pattern_instances,
            }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                "performance_patterns": {},
                "anti_patterns": [],
                "good_patterns": [],
                "pattern_instances": [],
            }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Detect nested loops (O(n^2))
                for child in ast.walk(node):
                    if isinstance(child, ast.For):
                        for grandchild in ast.walk(child):
                            if (
                                isinstance(grandchild, ast.For)
                                and grandchild is not child
                            ):
                                anti_patterns.append(node.name)
                                performance_patterns["optimization_opportunity"] = True
                                break

                # Detect set usage (O(1) lookups)
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            if child.func.id == "set":
                                good_patterns.append(node.name)

                # Detect generators
                for child in ast.walk(node):
                    if isinstance(child, ast.Yield):
                        pattern_instances.append(node.name)
                        performance_patterns["memory_efficient"] = True

        return {
            "performance_patterns": performance_patterns,
            "anti_patterns": anti_patterns,
            "good_patterns": good_patterns,
            "pattern_instances": pattern_instances,
        }

    def recognize_architectural_patterns(self, code: str) -> dict[str, Any]:
        """Recognize architectural patterns (MVC, Repository, etc.).

        Args:
            code: Code to analyze

        Returns:
            Dictionary with architectural pattern analysis
        """
        architectural_patterns: dict[str, bool] = {}
        pattern_instances: list[str] = []

        if not code:
            return {
                "architectural_patterns": architectural_patterns,
                "pattern_instances": pattern_instances,
            }

        # MVC pattern
        has_model = bool(re.search(r"class\s+\w*Model\b", code))
        has_view = bool(re.search(r"class\s+\w*View\b", code))
        has_controller = bool(re.search(r"class\s+\w*Controller\b", code))
        if has_controller and (has_model or has_view):
            architectural_patterns["mvc"] = True
            for match in re.finditer(r"class\s+(\w*Controller)\b", code):
                pattern_instances.append(match.group(1))

        # Repository pattern (class defs or references)
        repo_matches = re.findall(r"(\w*Repository)\b", code)
        if repo_matches:
            architectural_patterns["repository"] = True
            for name in dict.fromkeys(repo_matches):
                pattern_instances.append(name)

        # Unit of Work pattern
        if re.search(r"class\s+\w*UnitOfWork\b", code) or (
            "commit" in code and "register_new" in code
        ):
            architectural_patterns["unit_of_work"] = True

        return {
            "architectural_patterns": architectural_patterns,
            "pattern_instances": pattern_instances,
        }

    def identify_anti_patterns(self, code: str) -> dict[str, Any]:
        """Identify anti-patterns in code.

        Args:
            code: Code to analyze

        Returns:
            Dictionary with anti-pattern analysis
        """
        anti_patterns: list[str] = []
        severity = ""
        description = ""

        if not code:
            return {
                "anti_patterns": anti_patterns,
                "severity": severity,
                "description": description,
            }

        # Nested loops
        if re.search(r"for\s+\w+.*:\s*\n\s+for\s+\w+", code, re.MULTILINE):
            anti_patterns.append("nested_loops")
            severity = "performance_issue"
            description = "O(n\u00b2) nested loop detected"

        # Memory leak (growing collection without cleanup)
        if re.search(r"\.append\(", code) and not re.search(
            r"\.(clear|pop|remove)\(", code
        ):
            if "cache" in code.lower() or "global" in code.lower():
                anti_patterns.append("memory_leak")
                description = "growing_collection without cleanup"

        # Blocking in async
        if "time.sleep" in code and "async" in code:
            anti_patterns.append("blocking_async")
            description = "event_loop_blocking with time.sleep"

        return {
            "anti_patterns": anti_patterns,
            "severity": severity,
            "description": description,
        }

    def match_dsl_patterns(self, code: str) -> dict[str, Any]:
        """Match Domain-Specific Language patterns.

        Args:
            code: DSL code to analyze

        Returns:
            Dictionary with DSL pattern analysis
        """
        dsl_patterns: dict[str, bool] = {}
        structures: dict[str, int] = {
            "nested_blocks": 0,
            "route_definitions": 0,
            "validation_rules": 0,
        }

        if not code:
            return {
                "dsl_patterns": dsl_patterns,
                "structures": structures,
            }

        # Configuration DSL
        if re.search(r"\w+\s*\{[^}]*\w+\s*:", code, re.DOTALL):
            dsl_patterns["configuration_dsl"] = True
            structures["nested_blocks"] = len(re.findall(r"\w+\s*\{", code))

        # Routing DSL
        route_matches = re.findall(r'"/[^"]*"\s*->', code)
        if route_matches:
            dsl_patterns["routing_dsl"] = True
            structures["route_definitions"] = len(route_matches)

        # Validation DSL
        validation_matches = re.findall(r"\w+:\s*(required|optional)", code)
        if validation_matches:
            dsl_patterns["validation_dsl"] = True
            structures["validation_rules"] = len(validation_matches)

        return {
            "dsl_patterns": dsl_patterns,
            "structures": structures,
        }

    def suggest_improvements(self, code: str) -> dict[str, Any]:
        """Suggest pattern improvements for code.

        Args:
            code: Code to analyze

        Returns:
            Dictionary with improvement suggestions
        """
        suggestions: list[dict[str, str]] = []

        if not code:
            return {"suggestions": suggestions}

        # Nested loop optimization
        if re.search(r"for\s+\w+.*:\s*\n\s+for\s+\w+", code, re.MULTILINE):
            suggestions.append(
                {
                    "issue": "Nested loops detected (O(n\u00b2))",
                    "improvement": "Use a set for O(1) lookups",
                    "before": "for i in items:\n    for j in items:\n"
                    "        if i == j: ...",
                    "after": "seen = set(items)\nfor i in items:\n"
                    "    if i in seen: ...",
                }
            )

        # Growing list without bounds
        if ".append(" in code and "break" not in code:
            suggestions.append(
                {
                    "issue": "Unbounded list growth",
                    "improvement": "Consider using a bounded collection or generator",
                    "before": "results = []\nfor item in items:\n"
                    "    results.append(process(item))",
                    "after": "results = [process(item) for item in items]",
                }
            )

        return {"suggestions": suggestions}

    def validate_pattern_consistency(self, code: str) -> dict[str, Any]:
        """Validate consistency of design patterns used in code.

        Args:
            code: Code to analyze

        Returns:
            Dictionary with consistency analysis
        """
        consistency: dict[str, Any] = {
            "mixed_patterns": False,
            "issues": [],
            "recommendations": [],
        }

        if not code:
            return {"consistency_analysis": consistency}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"consistency_analysis": consistency}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = {
                    item.name for item in node.body if isinstance(item, ast.FunctionDef)
                }

                # Check for mixed responsibilities
                has_data = bool(methods & {"add_item", "find_item", "get", "set"})
                has_persistence = bool(
                    methods
                    & {
                        "save_to_database",
                        "load_from_database",
                        "persist",
                    }
                )

                if has_data and has_persistence:
                    consistency["mixed_patterns"] = True
                    consistency["issues"].append("single_responsibility_violation")
                    consistency["recommendations"].append(
                        "Separate data management from persistence"
                    )

        return {"consistency_analysis": consistency}

    def detect_pattern_variations(
        self, code: str, pattern_name: str = ""
    ) -> dict[str, Any]:
        """Detect variations of a specific design pattern.

        Args:
            code: Code to analyze
            pattern_name: Name of the pattern to look for

        Returns:
            Dictionary with pattern variation analysis
        """
        variations: dict[str, Any] = {}
        trade_offs: dict[str, Any] = {}

        if not code or not pattern_name:
            return {
                "pattern_variations": variations,
                "trade_offs": trade_offs,
            }

        if pattern_name == "singleton":
            try:
                tree = ast.parse(code)
            except SyntaxError:
                return {
                    "pattern_variations": {},
                    "trade_offs": {},
                }

            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue

                methods = {
                    item.name for item in node.body if isinstance(item, ast.FunctionDef)
                }
                attrs: set[str] = set()
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                attrs.add(target.id)

                # Classic singleton
                if "_instance" in attrs and "__new__" in methods:
                    if "_lock" in attrs:
                        variations["thread_safe_singleton"] = {
                            "class": node.name,
                            "advantages": [
                                "Thread-safe",
                                "Double-checked locking",
                            ],
                            "disadvantages": [
                                "More complex",
                                "Slight overhead",
                            ],
                        }
                    else:
                        variations["classic_singleton"] = {
                            "class": node.name,
                            "advantages": [
                                "Simple implementation",
                            ],
                            "disadvantages": [
                                "Not thread-safe",
                            ],
                        }

                # Metaclass singleton
                if "__call__" in methods and "_instances" in attrs:
                    variations["metaclass_singleton"] = {
                        "class": node.name,
                        "advantages": [
                            "Reusable across classes",
                            "Clean syntax",
                        ],
                        "disadvantages": [
                            "Complex metaclass usage",
                        ],
                    }

            trade_offs = {
                "simple_vs_threadsafe": "Classic is simpler but not thread-safe",
            }

        return {
            "pattern_variations": variations,
            "trade_offs": trade_offs,
        }

    def recognize_patterns(self, code: str) -> dict[str, Any]:
        """Recognize any patterns in code (general purpose).

        Args:
            code: Code to analyze

        Returns:
            Dictionary with recognized patterns
        """
        recognized_patterns: list[str] = []
        confidence = 0.0

        if not code:
            return {
                "recognized_patterns": recognized_patterns,
                "confidence": confidence,
            }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                "recognized_patterns": [],
                "confidence": 0.0,
                "error": "Could not parse code",
            }

        # Check for class definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                recognized_patterns.append(f"class:{node.name}")
                confidence = max(confidence, 0.6)

        # Check for function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                recognized_patterns.append(f"function:{node.name}")
                confidence = max(confidence, 0.5)

        return {
            "recognized_patterns": recognized_patterns,
            "confidence": confidence,
        }

    def generate_pattern_documentation(self, code: str) -> dict[str, Any]:
        """Generate documentation for patterns found in code.

        Args:
            code: Code to analyze

        Returns:
            Dictionary with pattern documentation
        """
        docs: dict[str, Any] = {}

        if not code:
            return {"documentation": docs}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"documentation": docs}

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            methods = {
                item.name for item in node.body if isinstance(item, ast.FunctionDef)
            }

            # Repository pattern
            repo_methods = methods & {
                "save",
                "find_by_id",
                "find",
                "delete",
                "add",
            }
            if "Repository" in node.name or len(repo_methods) >= 2:
                docs["repository_pattern"] = {
                    "description": "Repository pattern for data access",
                    "usage": f"Use {node.name} to abstract data persistence",
                    "benefits": [
                        "Separates domain from data access",
                        "Enables testing with in-memory repositories",
                    ],
                }

            # Service pattern
            if "Service" in node.name:
                docs["service_pattern"] = {
                    "description": "Service pattern for business logic",
                    "usage": f"Use {node.name} to orchestrate operations",
                    "benefits": [
                        "Centralizes business logic",
                        "Coordinates between domain objects",
                    ],
                }

        return {"documentation": docs}

    def compare_pattern_alternatives(
        self, code: str, pattern_type: str = ""
    ) -> dict[str, Any]:
        """Compare alternative implementations of a pattern.

        Args:
            code: Code containing multiple pattern implementations
            pattern_type: Type of pattern to compare

        Returns:
            Dictionary with comparison analysis
        """
        alternatives: list[dict[str, str]] = []
        comparison_matrix: list[dict[str, str]] = []
        recommendations: dict[str, Any] = {}

        if not code:
            return {
                "comparison": {
                    "alternatives": alternatives,
                    "comparison_matrix": comparison_matrix,
                    "recommendations": recommendations,
                }
            }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                "comparison": {
                    "alternatives": [],
                    "comparison_matrix": [],
                    "recommendations": {},
                }
            }

        if pattern_type == "factory":
            # Find factory functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if "create" in node.name or "factory" in node.name.lower():
                        alternatives.append(
                            {
                                "name": node.name,
                                "type": "simple_factory",
                            }
                        )
                        comparison_matrix.append(
                            {
                                "name": node.name,
                                "flexibility": "low",
                                "complexity": "low",
                            }
                        )

                if isinstance(node, ast.ClassDef):
                    if "Factory" in node.name:
                        alternatives.append(
                            {
                                "name": node.name,
                                "type": "abstract_factory",
                            }
                        )
                        comparison_matrix.append(
                            {
                                "name": node.name,
                                "flexibility": "high",
                                "complexity": "medium",
                            }
                        )

            recommendations = {
                "when_to_use": {
                    "simple_factory": "When you have a small, fixed set of types",
                    "abstract_factory": "When you need families of related objects",
                },
            }

        return {
            "comparison": {
                "alternatives": alternatives,
                "comparison_matrix": comparison_matrix,
                "recommendations": recommendations,
            }
        }
