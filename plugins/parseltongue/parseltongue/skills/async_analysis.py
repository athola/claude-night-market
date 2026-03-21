"""Async code analysis skill for parseltongue.

Provides detailed analysis of async Python code including:
- Async function detection and analysis
- Context manager pattern recognition
- Concurrency pattern detection
- Blocking call detection
- Missing await detection
- Error handling analysis
- Timeout pattern analysis
- Resource management analysis
- Performance analysis
- Race condition detection
- Event loop usage analysis
- Best practices validation
- Testing pattern analysis
- Complex scenario analysis
- Improvement suggestions
"""

from __future__ import annotations

import ast
import asyncio
from typing import Any


class AsyncAnalysisSkill:
    """Skill for analyzing async Python code patterns."""

    def __init__(self) -> None:
        """Initialize the async analysis skill."""
        pass

    def _parse_code(self, code: str) -> tuple[ast.Module | None, dict | None]:
        """Parse code into an AST, returning an error dict on failure."""
        try:
            return ast.parse(code), None
        except SyntaxError:
            return None, {"error": "Invalid Python syntax"}

    async def analyze_async_functions(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze async functions in the provided code.

        Args:
            code: Python code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing async function analysis

        """
        if not code:
            return {"async_functions": []}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"async_functions": [], **(err or {})}

        async_functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                # Count await calls in the function
                await_count = sum(
                    1 for child in ast.walk(node) if isinstance(child, ast.Await)
                )

                # Extract parameters
                params = [arg.arg for arg in node.args.args]

                async_functions.append(
                    {
                        "name": node.name,
                        "line_number": node.lineno,
                        "parameters": params,
                        "await_calls": await_count,
                    }
                )

        return {"async_functions": async_functions}

    async def analyze_context_managers(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze async context managers in the code.

        Args:
            code: Python code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing context manager analysis

        """
        if not code:
            return {"context_managers": {}}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"context_managers": {}, **(err or {})}

        context_managers = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [
                    item.name
                    for item in node.body
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]

                has_aenter = "__aenter__" in methods
                has_aexit = "__aexit__" in methods

                if has_aenter or has_aexit:
                    context_managers[node.name] = {
                        "has_async_context_manager": has_aenter and has_aexit,
                        "methods": [
                            m for m in methods if m in ("__aenter__", "__aexit__")
                        ],
                    }

        return {"context_managers": context_managers}

    async def analyze_concurrency_patterns(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Detect concurrency patterns in async code.

        Args:
            code: Python code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing concurrency pattern analysis

        """
        if not code:
            return {"concurrency_patterns": {}}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"concurrency_patterns": {}, **(err or {})}

        patterns: dict[str, Any] = {}
        gather_functions: list[str] = []
        create_task_functions: list[str] = []
        task_group_functions: list[str] = []

        gather_error_handling = "none"

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name
                concurrent_calls, err_handling = self._analyze_gather_pattern(
                    node, gather_functions
                )
                if err_handling != "none":
                    gather_error_handling = err_handling
                self._check_create_task_pattern(node, create_task_functions)
                self._check_task_group_pattern(node, task_group_functions)

                if concurrent_calls:
                    patterns[function_name] = {
                        "concurrent_operations": concurrent_calls[0]
                        if len(concurrent_calls) == 1
                        else concurrent_calls,
                    }

        if gather_functions:
            patterns["gather_usage"] = {
                "functions": list(set(gather_functions)),
                "error_handling": gather_error_handling,
            }

        if create_task_functions:
            patterns["create_task_usage"] = {
                "functions": list(set(create_task_functions))
            }

        if task_group_functions:
            patterns["task_group_usage"] = {
                "functions": list(set(task_group_functions))
            }

        return {"concurrency_patterns": patterns}

    def _analyze_gather_pattern(
        self, node: ast.AsyncFunctionDef, gather_functions: list[str]
    ) -> tuple[list[str], str]:
        """Analyze asyncio.gather() usage pattern.

        Args:
            node: Async function node to analyze
            gather_functions: List to accumulate functions using gather

        Returns:
            Tuple of (concurrent calls list, error handling strategy)

        """
        concurrent_calls: list[str] = []
        error_handling = "none"
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and (
                self._is_call_to(child, "asyncio.gather")
                or self._is_call_to(child, "gather")
            ):
                gather_functions.append(node.name)
                for kw in child.keywords:
                    if kw.arg == "return_exceptions":
                        error_handling = "return_exceptions"
                concurrent_calls.extend(self._extract_gather_args(child, node))
        return concurrent_calls, error_handling

    def _extract_gather_args(
        self, call_node: ast.Call, func_node: ast.AsyncFunctionDef
    ) -> list[str]:
        """Extract function names from gather() arguments.

        Args:
            call_node: The gather() call node
            func_node: The parent async function

        Returns:
            List of function names called in gather

        """
        calls: list[str] = []
        for arg in call_node.args:
            if isinstance(arg, ast.Starred):
                calls.extend(self._extract_starred_arg(arg, func_node))
            elif isinstance(arg, ast.Call):
                calls.extend(self._extract_call_name(arg))
        return calls

    def _extract_starred_arg(
        self, arg: ast.Starred, func_node: ast.AsyncFunctionDef
    ) -> list[str]:
        """Extract call names from starred arguments.

        Args:
            arg: The starred argument node
            func_node: The parent function to search for list comprehensions

        Returns:
            List of function names found

        """
        calls: list[str] = []
        list_comp = None

        if isinstance(arg.value, ast.ListComp):
            list_comp = arg.value
        elif isinstance(arg.value, ast.Name):
            # Trace variable to its list comprehension assignment
            var_name = arg.value.id
            for stmt in ast.walk(func_node):
                if isinstance(stmt, ast.Assign) and isinstance(
                    stmt.value, ast.ListComp
                ):
                    for t in stmt.targets:
                        if isinstance(t, ast.Name) and t.id == var_name:
                            list_comp = stmt.value

        if list_comp and isinstance(list_comp.elt, ast.Call):
            calls.extend(self._extract_call_name(list_comp.elt))

        return calls

    def _extract_call_name(self, call_node: ast.Call) -> list[str]:
        """Extract function name from a call node.

        Args:
            call_node: The call node to analyze

        Returns:
            List containing the function name if found

        """
        if isinstance(call_node.func, ast.Name):
            return [call_node.func.id]
        if isinstance(call_node.func, ast.Attribute):
            return [call_node.func.attr]
        return []

    def _check_create_task_pattern(
        self, node: ast.AsyncFunctionDef, create_task_functions: list[str]
    ) -> None:
        """Check for asyncio.create_task() usage.

        Args:
            node: Async function node to analyze
            create_task_functions: List to accumulate functions using create_task

        """
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and (
                self._is_call_to(child, "asyncio.create_task")
                or self._is_call_to(child, "create_task")
            ):
                create_task_functions.append(node.name)

    def _check_task_group_pattern(
        self, node: ast.AsyncFunctionDef, task_group_functions: list[str]
    ) -> None:
        """Check for TaskGroup usage.

        Args:
            node: Async function node to analyze
            task_group_functions: List to accumulate functions using TaskGroup

        """
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and self._is_call_to(child, "TaskGroup"):
                task_group_functions.append(node.name)

    async def detect_blocking_calls(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Detect blocking calls in async code.

        Args:
            code: Python code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing blocking call analysis

        """
        if not code:
            return {"blocking_patterns": {}}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"blocking_patterns": {}, **(err or {})}

        blocking_patterns: dict[str, Any] = {}
        recommendations: list[str] = []

        # Collect sync function names and their blocking calls
        sync_func_names: set[str] = set()
        sync_func_blocking: dict[str, list[str]] = {}
        self._collect_sync_function_info(tree, sync_func_names, sync_func_blocking)

        # Check for blocking calls in async functions
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        self._check_time_sleep(
                            child, blocking_patterns, recommendations
                        )
                        self._check_requests(child, blocking_patterns, recommendations)
                        self._check_file_io(child, blocking_patterns, recommendations)
                        self._check_sync_function_call(
                            child,
                            sync_func_names,
                            sync_func_blocking,
                            blocking_patterns,
                            recommendations,
                        )

        blocking_patterns["recommendations"] = list(set(recommendations))
        return {"blocking_patterns": blocking_patterns}

    def _collect_sync_function_info(
        self,
        tree: ast.Module,
        sync_func_names: set[str],
        sync_func_blocking: dict[str, list[str]],
    ) -> None:
        """Collect information about sync functions and their blocking calls.

        Args:
            tree: AST module to analyze
            sync_func_names: Set to accumulate sync function names
            sync_func_blocking: Dict to track blocking calls per function

        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not isinstance(
                node, ast.AsyncFunctionDef
            ):
                sync_func_names.add(node.name)
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and (
                        self._is_call_to(child, "time.sleep")
                        or self._is_call_to(child, "sleep")
                    ):
                        sync_func_blocking.setdefault(node.name, []).append(
                            "time_sleep"
                        )

    def _check_time_sleep(
        self,
        call: ast.Call,
        blocking_patterns: dict[str, Any],
        recommendations: list[str],
    ) -> None:
        """Check for time.sleep() calls.

        Args:
            call: Call node to check
            blocking_patterns: Dict to accumulate patterns found
            recommendations: List to accumulate recommendations

        """
        if self._is_call_to(call, "time.sleep") or self._is_call_to(call, "sleep"):
            blocking_patterns["time_sleep"] = {"blocks_event_loop": True}
            recommendations.append("Replace time.sleep() with asyncio.sleep()")

    def _check_requests(
        self,
        call: ast.Call,
        blocking_patterns: dict[str, Any],
        recommendations: list[str],
    ) -> None:
        """Check for requests library calls.

        Args:
            call: Call node to check
            blocking_patterns: Dict to accumulate patterns found
            recommendations: List to accumulate recommendations

        """
        if self._is_call_to(call, "requests.get") or self._is_call_to(
            call, "requests.post"
        ):
            blocking_patterns["requests"] = {"blocks_event_loop": True}
            recommendations.append("Replace requests with aiohttp")

    def _check_file_io(
        self,
        call: ast.Call,
        blocking_patterns: dict[str, Any],
        recommendations: list[str],
    ) -> None:
        """Check for file I/O blocking calls.

        Args:
            call: Call node to check
            blocking_patterns: Dict to accumulate patterns found
            recommendations: List to accumulate recommendations

        """
        if isinstance(call.func, ast.Name) and call.func.id == "open":
            blocking_patterns["file_io"] = {"blocks_event_loop": True}
            recommendations.append("Consider using aiofiles for async file I/O")

    def _check_sync_function_call(
        self,
        call: ast.Call,
        sync_func_names: set[str],
        sync_func_blocking: dict[str, list[str]],
        blocking_patterns: dict[str, Any],
        recommendations: list[str],
    ) -> None:
        """Check for calls to sync functions from async context.

        Args:
            call: Call node to check
            sync_func_names: Set of sync function names
            sync_func_blocking: Dict of blocking calls per sync function
            blocking_patterns: Dict to accumulate patterns found
            recommendations: List to accumulate recommendations

        """
        call_name = None
        if isinstance(call.func, ast.Name):
            call_name = call.func.id
        elif isinstance(call.func, ast.Attribute):
            call_name = call.func.attr

        if call_name and call_name in sync_func_names:
            blocking_patterns["sync_function_call"] = {
                "function_name": call_name,
                "blocks_event_loop": True,
            }
            recommendations.append(f"Consider making '{call_name}' async")
            # Propagate blocking calls from the sync function
            for blocking in sync_func_blocking.get(call_name, []):
                if blocking == "time_sleep":
                    blocking_patterns["time_sleep"] = {"blocks_event_loop": True}
                    recommendations.append("Replace time.sleep() with asyncio.sleep()")

    async def detect_missing_await(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Detect missing await keywords in async code.

        Args:
            code: Python code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing missing await analysis

        """
        if not code:
            return {"missing_awaits": {}}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"missing_awaits": {}, **(err or {})}

        missing_awaits: dict[str, Any] = {}

        # Track function calls that might need await
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name

                # Look for direct assignment from a call (potential missing await)
                for child in node.body:
                    # Check if right side is a call (not wrapped in await)
                    if isinstance(child, ast.Assign) and isinstance(
                        child.value, ast.Call
                    ):
                        # This is a call without await
                        call_name = None
                        if isinstance(child.value.func, ast.Name):
                            call_name = child.value.func.id
                        elif isinstance(child.value.func, ast.Attribute):
                            call_name = child.value.func.attr

                        # Common async function patterns
                        if call_name and any(
                            keyword in call_name.lower()
                            for keyword in [
                                "fetch",
                                "get",
                                "post",
                                "api",
                                "async",
                                "call",
                            ]
                        ):
                            missing_awaits[function_name] = {
                                "line_number": child.lineno,
                                "suggestion": "Add await before the coroutine call",
                            }

        return {"missing_awaits": missing_awaits}

    async def analyze_error_handling(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze async error handling patterns.

        Args:
            code: Python code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing error handling analysis

        """
        if not code:
            return {"error_handling": {"try_catch_blocks": [], "functions": {}}}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"error_handling": {}, **(err or {})}

        try_catch_blocks: list[dict[str, Any]] = []
        functions: dict[str, Any] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name
                has_error_handling = False
                exception_types: list[str] = []
                graceful_degradation = False

                # Check for try/except blocks
                for child in ast.walk(node):
                    if isinstance(child, ast.Try):
                        has_error_handling = True
                        try_catch_blocks.append(
                            {
                                "line_number": child.lineno,
                                "function": function_name,
                            }
                        )

                        # Extract exception types
                        for handler in child.handlers:
                            if handler.type:
                                if isinstance(handler.type, ast.Name):
                                    exception_types.append(handler.type.id)
                                elif isinstance(handler.type, ast.Attribute):
                                    exception_types.append(
                                        f"{handler.type.value.id}.{handler.type.attr}"
                                        if isinstance(handler.type.value, ast.Name)
                                        else handler.type.attr
                                    )

                            # Check for graceful degradation
                            # (returning a fallback value in except block)
                            for stmt in handler.body:
                                if isinstance(stmt, ast.Return):
                                    graceful_degradation = True

                functions[function_name] = {
                    "has_error_handling": has_error_handling,
                    "exception_types": list(set(exception_types)),
                    "graceful_degradation": graceful_degradation,
                }

        return {
            "error_handling": {
                "try_catch_blocks": try_catch_blocks,
                "functions": functions,
            }
        }

    async def analyze_timeouts(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze timeout patterns in async code.

        Args:
            code: Python code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing timeout analysis

        """
        if not code:
            return {"timeout_analysis": {"wait_for_usage": {}, "functions": {}}}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"timeout_analysis": {}, **(err or {})}

        wait_for_functions: list[str] = []
        functions: dict[str, Any] = {}
        # Timeout position in wait_for() call arguments
        timeout_arg_index = 2

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name
                timeout_value = self._extract_timeout_parameter(node)
                has_timeout, timeout_value = self._check_wait_for_calls(
                    node, wait_for_functions, timeout_value, timeout_arg_index
                )
                handles_timeout_error = self._check_timeout_error_handling(node)

                if has_timeout:
                    functions[function_name] = {
                        "has_timeout": True,
                        "timeout_value": timeout_value,
                        "handles_timeout_error": handles_timeout_error,
                    }

        return {
            "timeout_analysis": {
                "wait_for_usage": {
                    "functions": list(set(wait_for_functions)),
                },
                "functions": functions,
            }
        }

    def _extract_timeout_parameter(self, node: ast.AsyncFunctionDef) -> Any:
        """Extract timeout parameter from function defaults.

        Args:
            node: Async function node to analyze

        Returns:
            Timeout value if found, None otherwise

        """
        for i, arg in enumerate(node.args.args):
            if arg.arg == "timeout" and node.args.defaults:
                defaults_offset = len(node.args.args) - len(node.args.defaults)
                default_index = i - defaults_offset
                if 0 <= default_index < len(node.args.defaults):
                    default = node.args.defaults[default_index]
                    if isinstance(default, ast.Constant):
                        return default.value
        return None

    def _check_wait_for_calls(
        self,
        node: ast.AsyncFunctionDef,
        wait_for_functions: list[str],
        timeout_value: Any,
        timeout_arg_index: int,
    ) -> tuple[bool, Any]:
        """Check for asyncio.wait_for() calls and extract timeout values.

        Args:
            node: Async function node to analyze
            wait_for_functions: List to accumulate functions using wait_for
            timeout_value: Current timeout value
            timeout_arg_index: Index of timeout argument in wait_for

        Returns:
            Tuple of (has_timeout, timeout_value)

        """
        has_timeout = False
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and (
                self._is_call_to(child, "asyncio.wait_for")
                or self._is_call_to(child, "wait_for")
            ):
                has_timeout = True
                wait_for_functions.append(node.name)
                # Try to extract timeout from keyword arguments
                for keyword in child.keywords:
                    if keyword.arg == "timeout" and isinstance(
                        keyword.value, ast.Constant
                    ):
                        timeout_value = keyword.value.value
                # Try to extract timeout from positional arguments
                pos_arg = (
                    child.args[timeout_arg_index - 1]
                    if len(child.args) >= timeout_arg_index
                    else None
                )
                if pos_arg is not None and isinstance(pos_arg, ast.Constant):
                    timeout_value = pos_arg.value
        return has_timeout, timeout_value

    def _check_timeout_error_handling(self, node: ast.AsyncFunctionDef) -> bool:
        """Check if function handles TimeoutError.

        Args:
            node: Async function node to analyze

        Returns:
            True if TimeoutError is handled

        """
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                for handler in child.handlers:
                    if handler.type:
                        type_name = ""
                        if isinstance(handler.type, ast.Name):
                            type_name = handler.type.id
                        elif isinstance(handler.type, ast.Attribute):
                            type_name = handler.type.attr
                        if "TimeoutError" in type_name:
                            return True
        return False

    async def analyze_resource_management(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze async resource management patterns.

        Args:
            code: Python code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing resource management analysis

        """
        if not code:
            return {"resource_management": {"services": {}}}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"resource_management": {}, **(err or {})}

        services: dict[str, Any] = {}
        has_session_management = False

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                uses_context_manager, cleanup_in_finally = (
                    self._check_context_manager_methods(node)
                )
                creates_session = self._check_session_creation(node)
                closes_session = self._check_session_closure(node)

                if creates_session or closes_session:
                    has_session_management = True
                    services[class_name] = {
                        "creates_session": creates_session,
                        "closes_session": closes_session,
                        "uses_context_manager": uses_context_manager,
                        "cleanup_in_finally": cleanup_in_finally,
                    }

        result: dict[str, Any] = {"services": services}
        if has_session_management:
            result["session_management"] = True

        return {"resource_management": result}

    def _check_context_manager_methods(
        self, class_node: ast.ClassDef
    ) -> tuple[bool, bool]:
        """Check if class has context manager methods.

        Args:
            class_node: Class node to analyze

        Returns:
            Tuple of (uses_context_manager, cleanup_in_finally)

        """
        uses_context_manager = False
        cleanup_in_finally = False

        for item in class_node.body:
            if isinstance(item, ast.AsyncFunctionDef):
                if item.name == "__aexit__":
                    uses_context_manager = True
                    # Check if __aexit__ calls close()
                    for child in ast.walk(item):
                        if (
                            isinstance(child, ast.Call)
                            and isinstance(child.func, ast.Attribute)
                            and child.func.attr == "close"
                        ):
                            cleanup_in_finally = True
                elif item.name == "__aenter__":
                    uses_context_manager = True

        return uses_context_manager, cleanup_in_finally

    def _check_session_creation(self, class_node: ast.ClassDef) -> bool:
        """Check if class creates a session.

        Args:
            class_node: Class node to analyze

        Returns:
            True if session creation is found

        """
        for item in ast.walk(class_node):
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and "session" in target.attr.lower()
                    ):
                        return True
        return False

    def _check_session_closure(self, class_node: ast.ClassDef) -> bool:
        """Check if class closes a session.

        Args:
            class_node: Class node to analyze

        Returns:
            True if session closure is found

        """
        for item in ast.walk(class_node):
            if (
                isinstance(item, ast.Call)
                and isinstance(item.func, ast.Attribute)
                and item.func.attr == "close"
            ):
                return True
        return False

    async def analyze_performance(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze async performance patterns.

        Args:
            code: Python code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing performance analysis

        """
        if not code:
            return {"performance_analysis": {"issues": {}}}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"performance_analysis": {}, **(err or {})}

        issues: dict[str, Any] = {}
        concurrent_alternative: dict[str, Any] = {}
        improvement_potential: dict[str, Any] = {}

        # Track all async functions for concurrent alternative detection
        async_func_names: list[str] = []
        sequential_funcs: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name
                async_func_names.append(function_name)

                # Look for for loops with await inside
                for child in ast.walk(node):
                    if isinstance(child, ast.For):
                        has_await = any(
                            isinstance(item, ast.Await) for item in ast.walk(child)
                        )

                        if has_await:
                            sequential_funcs.append(function_name)
                            if "sequential_processing" not in issues:
                                issues["sequential_processing"] = {}
                            issues["sequential_processing"][function_name] = {
                                "issue": "Sequential await in loop",
                                "problem": "sequential_async_calls",
                                "suggestion": "Consider using asyncio.gather()",
                            }

                # Detect gather usage for concurrent alternative
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and (
                        self._is_call_to(child, "asyncio.gather")
                        or self._is_call_to(child, "gather")
                    ):
                        concurrent_alternative[function_name] = {
                            "pattern": "asyncio.gather",
                        }

        # Calculate improvement potential
        if sequential_funcs:
            improvement_potential = {
                "speedup": float(max(2.0, len(sequential_funcs) * 2.0)),
            }

        return {
            "performance_analysis": {
                "issues": issues,
                "concurrent_alternative": concurrent_alternative,
                "improvement_potential": improvement_potential,
            }
        }

    async def detect_race_conditions(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Detect potential race conditions in async code.

        Args:
            code: Python code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing race condition analysis

        """
        if not code:
            return {
                "race_conditions": {
                    "unsynchronized_shared_state": {},
                    "safe_patterns": {},
                    "recommendations": [],
                }
            }

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"race_conditions": {}, **(err or {})}

        unsynchronized: dict[str, Any] = {}
        safe_patterns: dict[str, Any] = {}
        recommendations: list[str] = []

        self._check_async_function_locks(tree, safe_patterns)
        module_shared_state = self._collect_module_shared_state(tree)
        self._check_shared_state_access(
            tree, module_shared_state, safe_patterns, unsynchronized, recommendations
        )
        self._check_class_shared_state(
            tree, safe_patterns, unsynchronized, recommendations
        )

        return {
            "race_conditions": {
                "unsynchronized_shared_state": unsynchronized,
                "safe_patterns": safe_patterns,
                "recommendations": recommendations,
            }
        }

    def _check_async_function_locks(
        self, tree: ast.Module, safe_patterns: dict[str, Any]
    ) -> None:
        """Check async functions for lock usage patterns.

        Args:
            tree: AST module to analyze
            safe_patterns: Dictionary to accumulate safe patterns found

        """
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name
                uses_lock = self._detect_lock_usage(node)
                if uses_lock:
                    safe_patterns[function_name] = {"uses_lock": True}

    def _detect_lock_usage(self, func_node: ast.AsyncFunctionDef) -> bool:
        """Detect if function uses a lock pattern.

        Args:
            func_node: Async function node to analyze

        Returns:
            True if lock usage is detected

        """
        for child in ast.walk(func_node):
            if isinstance(child, ast.AsyncWith):
                for with_item in child.items:
                    ctx = with_item.context_expr
                    # counter["lock"] pattern
                    if (
                        isinstance(ctx, ast.Subscript)
                        and isinstance(ctx.slice, ast.Constant)
                        and ctx.slice.value == "lock"
                    ):
                        return True
                    # self.lock pattern
                    if isinstance(ctx, ast.Attribute) and "lock" in ctx.attr.lower():
                        return True
                    # lock variable pattern
                    if isinstance(ctx, ast.Name) and "lock" in ctx.id.lower():
                        return True
        return False

    def _collect_module_shared_state(self, tree: ast.Module) -> dict[str, int]:
        """Collect module-level shared state variables.

        Args:
            tree: AST module to analyze

        Returns:
            Dictionary mapping state variable names to access counts

        """
        module_shared_state: dict[str, int] = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        module_shared_state[target.id] = 0
        return module_shared_state

    def _check_shared_state_access(
        self,
        tree: ast.Module,
        module_shared_state: dict[str, int],
        safe_patterns: dict[str, Any],
        unsynchronized: dict[str, Any],
        recommendations: list[str],
    ) -> None:
        """Check for unsynchronized access to shared state.

        Args:
            tree: AST module to analyze
            module_shared_state: Map of module-level variables
            safe_patterns: Dictionary of safe patterns found
            unsynchronized: Dictionary to accumulate unsynchronized accesses
            recommendations: List to accumulate recommendations

        """
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name
                accesses = 0

                for child in ast.walk(node):
                    if (
                        isinstance(child, ast.Subscript)
                        and isinstance(child.value, ast.Name)
                        and child.value.id in module_shared_state
                    ):
                        accesses += 1

                if accesses > 0 and function_name not in safe_patterns:
                    unsynchronized[function_name] = {"accesses": accesses}
                    recommendations.append(
                        f"Add asyncio.Lock to protect shared state in '{function_name}'"
                    )

    def _check_class_shared_state(
        self,
        tree: ast.Module,
        safe_patterns: dict[str, Any],
        unsynchronized: dict[str, Any],
        recommendations: list[str],
    ) -> None:
        """Check classes for unsynchronized shared state.

        Args:
            tree: AST module to analyze
            safe_patterns: Dictionary of safe patterns found
            unsynchronized: Dictionary to accumulate unsynchronized classes
            recommendations: List to accumulate recommendations

        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_shared_state = any(
                    isinstance(item, ast.Assign) for item in node.body
                )
                class_uses_lock = self._check_class_lock_usage(node)

                if has_shared_state and not class_uses_lock:
                    unsynchronized[node.name] = {
                        "warning": "Shared state without synchronization",
                    }
                    recommendations.append(f"Add asyncio.Lock to class '{node.name}'")
                elif has_shared_state and class_uses_lock:
                    safe_patterns[node.name] = {"uses_lock": True}

    def _check_class_lock_usage(self, class_node: ast.ClassDef) -> bool:
        """Check if class uses lock in its async methods.

        Args:
            class_node: Class node to analyze

        Returns:
            True if lock usage is detected in any async method

        """
        for body_item in class_node.body:
            if isinstance(body_item, ast.AsyncFunctionDef):
                for child in ast.walk(body_item):
                    if isinstance(child, ast.Call) and (
                        self._is_call_to(child, "asyncio.Lock")
                        or self._is_call_to(child, "Lock")
                    ):
                        return True
        return False

    async def analyze_testing_patterns(
        self, code: str, _tree: ast.Module | None = None
    ) -> dict[str, Any]:
        """Analyze async testing patterns.

        Args:
            code: Python code to analyze
            _tree: Pre-parsed AST (internal optimisation)

        Returns:
            Dictionary containing testing pattern analysis

        """
        if not code:
            return {"testing_analysis": {}}

        tree = _tree
        if tree is None:
            tree, err = self._parse_code(code)
            if tree is None:
                return {"testing_analysis": {}, **(err or {})}

        uses_pytest_asyncio = False
        async_test_count = 0
        uses_asyncmock = False
        timeout_testing = False
        concurrency_testing = False

        for node in ast.walk(tree):
            # Check for pytest.mark.asyncio
            if isinstance(node, ast.AsyncFunctionDef):
                if node.name.startswith("test_"):
                    async_test_count += 1

                for decorator in node.decorator_list:
                    if (
                        isinstance(decorator, ast.Attribute)
                        and decorator.attr == "asyncio"
                    ):
                        uses_pytest_asyncio = True

            # Check for AsyncMock
            if isinstance(node, ast.Call) and self._is_call_to(node, "AsyncMock"):
                uses_asyncmock = True

        # Check for timeout testing patterns
        if "TimeoutError" in code or "wait_for" in code:
            timeout_testing = True

        # Check for concurrency testing patterns
        if "asyncio.gather" in code or "create_task" in code:
            concurrency_testing = True

        return {
            "testing_analysis": {
                "uses_pytest_asyncio": uses_pytest_asyncio,
                "async_test_count": async_test_count,
                "mocking_patterns": {
                    "uses_asyncmock": uses_asyncmock,
                },
                "timeout_testing": timeout_testing,
                "concurrency_testing": concurrency_testing,
            }
        }

    async def analyze_event_loop_usage(self, code: str) -> dict[str, Any]:
        """Analyze event loop usage patterns in async code.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing event loop analysis

        """
        if not code:
            return {"event_loop_analysis": {}}

        loop_management: dict[str, int] = {
            "get_event_loop_usage": 0,
            "new_event_loop_usage": 0,
            "get_running_loop_usage": 0,
        }
        callback_usage: list[str] = []
        proper_loop_close = False

        # Count event loop API calls
        if "get_event_loop" in code:
            loop_management["get_event_loop_usage"] = code.count("get_event_loop")
        if "new_event_loop" in code:
            loop_management["new_event_loop_usage"] = code.count("new_event_loop")
        if "get_running_loop" in code:
            loop_management["get_running_loop_usage"] = code.count("get_running_loop")

        # Check for callback patterns
        for pattern in ["call_soon", "call_later", "call_at"]:
            if pattern in code:
                callback_usage.append(pattern)

        # Check for proper loop cleanup
        if "loop.close()" in code or ".close()" in code:
            proper_loop_close = True

        return {
            "event_loop_analysis": {
                "loop_management": loop_management,
                "callback_usage": callback_usage,
                "cleanup_patterns": {
                    "proper_loop_close": proper_loop_close,
                },
            }
        }

    async def validate_best_practices(self, code: str) -> dict[str, Any]:
        """Validate async code against best practices.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing validation results

        """
        if not code:
            return {"validation": {"good_practices": {}, "compliance_score": 0.0}}

        tree, err = self._parse_code(code)
        if tree is None:
            return {
                "validation": {
                    "good_practices": {},
                    "compliance_score": 0.0,
                    **(err or {}),
                }
            }

        good_practices: dict[str, bool] = {}
        recommendations: list[str] = []
        score = 0.0
        total_checks = 4

        # Check for context manager usage
        if "__aenter__" in code or "async with" in code:
            good_practices["context_manager_usage"] = True
            score += 1
        else:
            recommendations.append("Use async context managers for resources")

        # Check for error handling and resource cleanup concurrently
        error_result, resource_result = await asyncio.gather(
            self.analyze_error_handling(code, _tree=tree),
            self.analyze_resource_management(code, _tree=tree),
        )

        if error_result["error_handling"].get("try_catch_blocks"):
            good_practices["error_handling"] = True
            score += 1
        else:
            recommendations.append("Add try/except blocks for error handling")

        # Check for resource cleanup
        services = resource_result["resource_management"].get("services", {})
        if (
            any(s.get("closes_session", False) for s in services.values())
            or "__aexit__" in code
        ):
            good_practices["resource_cleanup"] = True
            score += 1
        else:
            recommendations.append("Ensure resources are properly cleaned up")

        # Check for concurrent processing
        if "asyncio.gather" in code or "create_task" in code:
            good_practices["concurrent_processing"] = True
            score += 1
        else:
            recommendations.append("Consider concurrent processing with asyncio.gather")

        compliance_score = score / total_checks if total_checks > 0 else 0.0

        return {
            "validation": {
                "good_practices": good_practices,
                "compliance_score": compliance_score,
                "recommendations": recommendations,
            }
        }

    async def analyze_complex_scenarios(self, code: str) -> dict[str, Any]:
        """Analyze complex async code scenarios.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing complex analysis results

        """
        if not code:
            return {"complex_analysis": {}}

        complex_analysis: dict[str, Any] = {}
        self._analyze_cache_patterns(code, complex_analysis)
        self._analyze_rate_limiting(code, complex_analysis)
        self._analyze_custom_context_managers(code, complex_analysis)
        self._analyze_resource_cleanup(code, complex_analysis)

        return {"complex_analysis": complex_analysis}

    def _analyze_cache_patterns(
        self, code: str, complex_analysis: dict[str, Any]
    ) -> None:
        """Analyze cache stampede prevention patterns.

        Args:
            code: Python code to analyze
            complex_analysis: Dictionary to accumulate analysis results

        """
        if "cache" in code.lower():
            prevents_stampede = "create_task" in code or "future" in code.lower()
            uses_futures = "create_task" in code or "future" in code.lower()
            complex_analysis["cache_anti_pattern"] = {
                "prevents_cache_stampede": prevents_stampede,
                "uses_futures": uses_futures,
            }

    def _analyze_rate_limiting(
        self, code: str, complex_analysis: dict[str, Any]
    ) -> None:
        """Analyze rate limiting patterns.

        Args:
            code: Python code to analyze
            complex_analysis: Dictionary to accumulate analysis results

        """
        if "rate_limit" in code.lower() or "rate_limiter" in code.lower():
            complex_analysis["rate_limiting"] = True

    def _analyze_custom_context_managers(
        self, code: str, complex_analysis: dict[str, Any]
    ) -> None:
        """Analyze custom async context manager patterns.

        Args:
            code: Python code to analyze
            complex_analysis: Dictionary to accumulate analysis results

        """
        if "@asynccontextmanager" in code or "__aenter__" in code:
            complex_analysis["custom_context_manager"] = True

    def _analyze_resource_cleanup(
        self,
        code: str,
        complex_analysis: dict[str, Any],
        _tree: ast.Module | None = None,
    ) -> None:
        """Analyze resource cleanup in try/except blocks.

        Args:
            code: Python code to analyze
            complex_analysis: Dictionary to accumulate analysis results
            _tree: Pre-parsed AST (internal optimisation)

        """
        tree = _tree
        if tree is None:
            tree, _ = self._parse_code(code)
            if tree is None:
                complex_analysis["resource_cleanup"] = {
                    "error_cleanup": False,
                    "finally_blocks": 0,
                }
                return

        finally_blocks = 0
        error_cleanup = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                if node.finalbody:
                    finally_blocks += 1
                # Check for cleanup in except handlers
                for handler in node.handlers:
                    for stmt in ast.walk(handler):
                        if (
                            isinstance(stmt, ast.Call)
                            and isinstance(stmt.func, ast.Attribute)
                            and stmt.func.attr in ("pop", "remove", "close")
                        ):
                            error_cleanup = True

        complex_analysis["resource_cleanup"] = {
            "error_cleanup": error_cleanup,
            "finally_blocks": finally_blocks,
        }

    async def suggest_improvements(self, code: str) -> dict[str, Any]:
        """Suggest improvements for async code.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing improvement suggestions

        """
        if not code:
            return {"improvements": []}

        tree, err = self._parse_code(code)
        if tree is None:
            return {"improvements": [], **(err or {})}

        improvements: list[dict[str, str]] = []

        # Run various analyses with shared parse tree
        blocking = await self.detect_blocking_calls(code, _tree=tree)
        performance = await self.analyze_performance(code, _tree=tree)
        race_conditions = await self.detect_race_conditions(code, _tree=tree)
        missing_await = await self.detect_missing_await(code, _tree=tree)

        # Add suggestions based on findings
        if blocking.get("blocking_patterns"):
            bp = blocking["blocking_patterns"]
            if "time_sleep" in bp:
                improvements.append(
                    {
                        "category": "blocking_call",
                        "issue": "Blocking time.sleep() in async context",
                        "recommendation": "Use asyncio.sleep() instead",
                        "code_before": "time.sleep(1)",
                        "code_after": "await asyncio.sleep(1)",
                        "explanation": "Use asyncio.sleep() instead of "
                        "time.sleep() to avoid blocking the event loop",
                    }
                )
            if "sync_function_call" in bp:
                func_name = bp["sync_function_call"].get("function_name", "sync_func")
                improvements.append(
                    {
                        "category": "blocking_call",
                        "issue": f"Sync function '{func_name}' called in async",
                        "recommendation": f"Make '{func_name}' async",
                        "code_before": f"result = {func_name}()",
                        "code_after": f"result = await {func_name}()",
                        "explanation": f"Convert '{func_name}' to an async "
                        f"function to avoid blocking",
                    }
                )

        if missing_await.get("missing_awaits"):
            for func_name in missing_await["missing_awaits"]:
                improvements.append(
                    {
                        "category": "missing_await",
                        "issue": f"Missing await in '{func_name}'",
                        "recommendation": "Add await keyword",
                        "code_before": "data = api_call()",
                        "code_after": "data = await api_call()",
                        "explanation": "Add await keyword before async "
                        "function calls to properly wait for the result",
                    }
                )

        if performance.get("performance_analysis", {}).get("issues"):
            improvements.append(
                {
                    "category": "performance",
                    "issue": "Sequential async processing in loop",
                    "recommendation": "Use asyncio.gather()",
                    "code_before": "for item in items:\n"
                    "    result = await process_item(item)",
                    "code_after": "results = await asyncio.gather("
                    "*[process_item(item) for item in items])",
                    "explanation": "Use asyncio.gather() to process items "
                    "concurrently instead of sequentially",
                }
            )

        if race_conditions.get("race_conditions", {}).get(
            "unsynchronized_shared_state"
        ):
            improvements.append(
                {
                    "category": "race_condition",
                    "issue": "Shared state without synchronization",
                    "recommendation": "Use asyncio.Lock",
                    "code_before": "self.counter += 1",
                    "code_after": "async with self.lock:\n    self.counter += 1",
                    "explanation": "Protect shared state with asyncio.Lock "
                    "to prevent race conditions",
                }
            )

        return {"improvements": improvements}

    def _is_call_to(self, node: ast.Call, target: str) -> bool:
        """Check if a call node is calling a specific function.

        Args:
            node: AST Call node
            target: Target function name (e.g., "asyncio.gather")

        Returns:
            True if the call matches the target

        """
        if isinstance(node.func, ast.Name):
            return node.func.id == target or node.func.id == target.split(".")[-1]

        if isinstance(node.func, ast.Attribute):
            if "." in target:
                module, func = target.rsplit(".", 1)
                if isinstance(node.func.value, ast.Name):
                    return node.func.value.id == module and node.func.attr == func
            return node.func.attr == target.split(".")[-1]

        return False
