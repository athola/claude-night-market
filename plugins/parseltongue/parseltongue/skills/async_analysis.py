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
from typing import Any


class AsyncAnalysisSkill:
    """Skill for analyzing async Python code patterns."""

    def __init__(self) -> None:
        """Initialize the async analysis skill."""
        pass

    async def analyze_async_functions(self, code: str) -> dict[str, Any]:
        """Analyze async functions in the provided code.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing async function analysis
        """
        if not code:
            return {"async_functions": []}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"async_functions": [], "error": "Invalid Python syntax"}

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

    async def analyze_context_managers(self, code: str) -> dict[str, Any]:
        """Analyze async context managers in the code.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing context manager analysis
        """
        if not code:
            return {"context_managers": {}}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"context_managers": {}, "error": "Invalid Python syntax"}

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

    async def analyze_concurrency_patterns(self, code: str) -> dict[str, Any]:
        """Detect concurrency patterns in async code.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing concurrency pattern analysis
        """
        if not code:
            return {"concurrency_patterns": {}}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"concurrency_patterns": {}, "error": "Invalid Python syntax"}

        patterns: dict[str, Any] = {}

        # Track asyncio.gather usage
        gather_functions: list[str] = []
        create_task_functions: list[str] = []
        task_group_functions: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name
                concurrent_calls: list[str] = []

                # Check for asyncio.gather
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if self._is_call_to(
                            child, "asyncio.gather"
                        ) or self._is_call_to(child, "gather"):
                            gather_functions.append(function_name)

                            # Check for return_exceptions keyword
                            error_handling = "none"
                            for kw in child.keywords:
                                if kw.arg == "return_exceptions":
                                    error_handling = "return_exceptions"

                            # Track what functions are called inside gather
                            for arg in child.args:
                                if isinstance(arg, ast.Starred):
                                    # *tasks or similar
                                    list_comp = None
                                    if isinstance(arg.value, ast.ListComp):
                                        list_comp = arg.value
                                    elif isinstance(arg.value, ast.Name):
                                        # Trace variable to its assignment
                                        var_name = arg.value.id
                                        for stmt in ast.walk(node):
                                            if isinstance(stmt, ast.Assign):
                                                for t in stmt.targets:
                                                    if (
                                                        isinstance(t, ast.Name)
                                                        and t.id == var_name
                                                        and isinstance(
                                                            stmt.value,
                                                            ast.ListComp,
                                                        )
                                                    ):
                                                        list_comp = stmt.value
                                    if list_comp is not None:
                                        elt = list_comp.elt
                                        if isinstance(elt, ast.Call):
                                            if isinstance(elt.func, ast.Name):
                                                concurrent_calls.append(elt.func.id)
                                            elif isinstance(elt.func, ast.Attribute):
                                                concurrent_calls.append(elt.func.attr)
                                elif isinstance(arg, ast.Call):
                                    if isinstance(arg.func, ast.Name):
                                        concurrent_calls.append(arg.func.id)
                                    elif isinstance(arg.func, ast.Attribute):
                                        concurrent_calls.append(arg.func.attr)

                            patterns["gather_usage"] = {
                                "functions": list(set(gather_functions)),
                                "error_handling": error_handling,
                            }

                        if self._is_call_to(
                            child, "asyncio.create_task"
                        ) or self._is_call_to(child, "create_task"):
                            create_task_functions.append(function_name)

                        if self._is_call_to(child, "TaskGroup"):
                            task_group_functions.append(function_name)

                if concurrent_calls:
                    patterns[function_name] = {
                        "concurrent_operations": concurrent_calls[0]
                        if len(concurrent_calls) == 1
                        else concurrent_calls,
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

    async def detect_blocking_calls(self, code: str) -> dict[str, Any]:
        """Detect blocking calls in async code.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing blocking call analysis
        """
        if not code:
            return {"blocking_patterns": {}}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"blocking_patterns": {}, "error": "Invalid Python syntax"}

        blocking_patterns: dict[str, Any] = {}
        recommendations: list[str] = []

        # Collect sync function names and their blocking calls
        sync_func_names: set[str] = set()
        sync_func_blocking: dict[str, list[str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not isinstance(
                node, ast.AsyncFunctionDef
            ):
                sync_func_names.add(node.name)
                # Check if sync function contains blocking calls
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if self._is_call_to(child, "time.sleep") or self._is_call_to(
                            child, "sleep"
                        ):
                            sync_func_blocking.setdefault(node.name, []).append(
                                "time_sleep"
                            )

        # Check for blocking calls in async functions
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        # time.sleep
                        if self._is_call_to(child, "time.sleep") or self._is_call_to(
                            child, "sleep"
                        ):
                            blocking_patterns["time_sleep"] = {
                                "blocks_event_loop": True,
                            }
                            recommendations.append(
                                "Replace time.sleep() with asyncio.sleep()"
                            )

                        # requests library
                        if self._is_call_to(child, "requests.get") or self._is_call_to(
                            child, "requests.post"
                        ):
                            blocking_patterns["requests"] = {
                                "blocks_event_loop": True,
                            }
                            recommendations.append("Replace requests with aiohttp")

                        # open() for file I/O
                        if isinstance(child.func, ast.Name) and child.func.id == "open":
                            blocking_patterns["file_io"] = {
                                "blocks_event_loop": True,
                            }
                            recommendations.append(
                                "Consider using aiofiles for async file I/O"
                            )

                        # Detect calls to sync functions from async context
                        call_name = None
                        if isinstance(child.func, ast.Name):
                            call_name = child.func.id
                        elif isinstance(child.func, ast.Attribute):
                            call_name = child.func.attr

                        if call_name and call_name in sync_func_names:
                            blocking_patterns["sync_function_call"] = {
                                "function_name": call_name,
                                "blocks_event_loop": True,
                            }
                            recommendations.append(
                                f"Consider making '{call_name}' async"
                            )
                            # Propagate blocking calls from the
                            # sync function
                            for blocking in sync_func_blocking.get(call_name, []):
                                if blocking == "time_sleep":
                                    blocking_patterns["time_sleep"] = {
                                        "blocks_event_loop": True,
                                    }
                                    recommendations.append(
                                        "Replace time.sleep() with asyncio.sleep()"
                                    )

        blocking_patterns["recommendations"] = list(set(recommendations))

        return {"blocking_patterns": blocking_patterns}

    async def detect_missing_await(self, code: str) -> dict[str, Any]:
        """Detect missing await keywords in async code.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing missing await analysis
        """
        if not code:
            return {"missing_awaits": {}}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"missing_awaits": {}, "error": "Invalid Python syntax"}

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

    async def analyze_error_handling(self, code: str) -> dict[str, Any]:
        """Analyze async error handling patterns.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing error handling analysis
        """
        if not code:
            return {"error_handling": {"try_catch_blocks": [], "functions": {}}}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"error_handling": {}, "error": "Invalid Python syntax"}

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

    async def analyze_timeouts(self, code: str) -> dict[str, Any]:
        """Analyze timeout patterns in async code.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing timeout analysis
        """
        if not code:
            return {"timeout_analysis": {"wait_for_usage": {}, "functions": {}}}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"timeout_analysis": {}, "error": "Invalid Python syntax"}

        wait_for_functions: list[str] = []
        functions: dict[str, Any] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name
                has_timeout = False
                timeout_value = None
                handles_timeout_error = False

                # Check function defaults for timeout parameter
                for i, arg in enumerate(node.args.args):
                    if arg.arg == "timeout" and node.args.defaults:
                        # Find the matching default value
                        defaults_offset = len(node.args.args) - len(node.args.defaults)
                        default_index = i - defaults_offset
                        if 0 <= default_index < len(node.args.defaults):
                            default = node.args.defaults[default_index]
                            if isinstance(default, ast.Constant):
                                timeout_value = default.value

                # Check for asyncio.wait_for
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and (
                        self._is_call_to(child, "asyncio.wait_for")
                        or self._is_call_to(child, "wait_for")
                    ):
                        has_timeout = True
                        wait_for_functions.append(function_name)

                        # Try to extract timeout value from call
                        for keyword in child.keywords:
                            if keyword.arg == "timeout" and isinstance(
                                keyword.value, ast.Constant
                            ):
                                timeout_value = keyword.value.value
                        # Also check positional args (second arg is timeout)
                        if len(child.args) >= 2 and isinstance(
                            child.args[1], ast.Constant
                        ):
                            timeout_value = child.args[1].value

                # Check for TimeoutError handling
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
                                    handles_timeout_error = True

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

    async def analyze_resource_management(self, code: str) -> dict[str, Any]:
        """Analyze async resource management patterns.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing resource management analysis
        """
        if not code:
            return {"resource_management": {"services": {}}}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"resource_management": {}, "error": "Invalid Python syntax"}

        services: dict[str, Any] = {}
        has_session_management = False

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                creates_session = False
                closes_session = False
                cleanup_in_finally = False
                uses_context_manager = False

                # Check for __aexit__ method (context manager cleanup)
                has_aexit = False
                for item in node.body:
                    if isinstance(item, ast.AsyncFunctionDef):
                        if item.name == "__aexit__":
                            has_aexit = True
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

                # Check for session creation/cleanup in methods
                for walk_item in ast.walk(node):
                    # Check for session creation
                    if isinstance(walk_item, ast.Assign):
                        for target in walk_item.targets:
                            if (
                                isinstance(target, ast.Attribute)
                                and "session" in target.attr.lower()
                            ):
                                creates_session = True
                                has_session_management = True

                    # Check for session closure
                    if isinstance(walk_item, ast.Call) and (
                        isinstance(walk_item.func, ast.Attribute)
                        and walk_item.func.attr == "close"
                    ):
                        closes_session = True

                if creates_session or closes_session:
                    services[class_name] = {
                        "creates_session": creates_session,
                        "closes_session": closes_session,
                        "uses_context_manager": uses_context_manager,
                        "cleanup_in_finally": cleanup_in_finally or has_aexit,
                    }

        result: dict[str, Any] = {"services": services}
        if has_session_management:
            result["session_management"] = True

        return {"resource_management": result}

    async def analyze_performance(self, code: str) -> dict[str, Any]:
        """Analyze async performance patterns.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing performance analysis
        """
        if not code:
            return {"performance_analysis": {"issues": {}}}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"performance_analysis": {}, "error": "Invalid Python syntax"}

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

    async def detect_race_conditions(self, code: str) -> dict[str, Any]:
        """Detect potential race conditions in async code.

        Args:
            code: Python code to analyze

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

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"race_conditions": {}, "error": "Invalid Python syntax"}

        unsynchronized: dict[str, Any] = {}
        safe_patterns: dict[str, Any] = {}
        recommendations: list[str] = []

        # Check async functions for lock usage
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name
                uses_lock = False

                # Check for async with lock pattern
                for child in ast.walk(node):
                    if isinstance(child, ast.AsyncWith):
                        # Check if it's using a lock
                        for with_item in child.items:
                            ctx = with_item.context_expr
                            # counter["lock"] pattern
                            if isinstance(ctx, ast.Subscript) and isinstance(
                                ctx.slice, ast.Constant
                            ):
                                if ctx.slice.value == "lock":
                                    uses_lock = True
                            # self.lock pattern
                            if isinstance(ctx, ast.Attribute):
                                if "lock" in ctx.attr.lower():
                                    uses_lock = True
                            # lock variable pattern
                            if isinstance(ctx, ast.Name):
                                if "lock" in ctx.id.lower():
                                    uses_lock = True

                if uses_lock:
                    safe_patterns[function_name] = {"uses_lock": True}

        # Check module-level shared state
        module_shared_state: dict[str, int] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Check if this is at module level (not inside a function/class)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Track shared state accesses
                        module_shared_state[target.id] = 0

        # Count accesses to shared state in async functions
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name
                accesses = 0

                for child in ast.walk(node):
                    if isinstance(child, ast.Subscript):
                        if isinstance(child.value, ast.Name):
                            if child.value.id in module_shared_state:
                                accesses += 1

                if accesses > 0 and function_name not in safe_patterns:
                    unsynchronized[function_name] = {"accesses": accesses}
                    recommendations.append(
                        f"Add asyncio.Lock to protect shared state in '{function_name}'"
                    )

        # Check for classes with shared state
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_shared_state = False
                class_uses_lock = False

                for body_item in node.body:
                    if isinstance(body_item, ast.Assign):
                        has_shared_state = True

                    if isinstance(body_item, ast.AsyncFunctionDef):
                        for child in ast.walk(body_item):
                            if isinstance(child, ast.Call) and (
                                self._is_call_to(child, "asyncio.Lock")
                                or self._is_call_to(child, "Lock")
                            ):
                                class_uses_lock = True

                if has_shared_state and not class_uses_lock:
                    unsynchronized[node.name] = {
                        "warning": "Shared state without synchronization",
                    }
                    recommendations.append(f"Add asyncio.Lock to class '{node.name}'")
                elif has_shared_state and class_uses_lock:
                    safe_patterns[node.name] = {"uses_lock": True}

        return {
            "race_conditions": {
                "unsynchronized_shared_state": unsynchronized,
                "safe_patterns": safe_patterns,
                "recommendations": recommendations,
            }
        }

    async def analyze_testing_patterns(self, code: str) -> dict[str, Any]:
        """Analyze async testing patterns.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing testing pattern analysis
        """
        if not code:
            return {"testing_analysis": {}}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"testing_analysis": {}, "error": "Invalid Python syntax"}

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

        # Check for error handling
        error_result = await self.analyze_error_handling(code)
        if error_result["error_handling"].get("try_catch_blocks"):
            good_practices["error_handling"] = True
            score += 1
        else:
            recommendations.append("Add try/except blocks for error handling")

        # Check for resource cleanup
        resource_result = await self.analyze_resource_management(code)
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

        # Check for cache patterns
        if "cache" in code.lower():
            prevents_stampede = "create_task" in code or "future" in code.lower()
            uses_futures = "create_task" in code or "future" in code.lower()
            complex_analysis["cache_anti_pattern"] = {
                "prevents_cache_stampede": prevents_stampede,
                "uses_futures": uses_futures,
            }

        # Check for rate limiting
        if "rate_limit" in code.lower() or "rate_limiter" in code.lower():
            complex_analysis["rate_limiting"] = True

        # Check for custom context managers
        if "@asynccontextmanager" in code or "__aenter__" in code:
            complex_analysis["custom_context_manager"] = True

        # Analyze resource cleanup
        try:
            tree = ast.parse(code)
        except SyntaxError:
            tree = None

        finally_blocks = 0
        error_cleanup = False
        if tree:
            for node in ast.walk(tree):
                if isinstance(node, ast.Try):
                    if node.finalbody:
                        finally_blocks += 1
                    # Check for cleanup in except handlers
                    for handler in node.handlers:
                        for stmt in ast.walk(handler):
                            if isinstance(stmt, ast.Call):
                                if isinstance(stmt.func, ast.Attribute):
                                    if stmt.func.attr in ("pop", "remove", "close"):
                                        error_cleanup = True

        complex_analysis["resource_cleanup"] = {
            "error_cleanup": error_cleanup,
            "finally_blocks": finally_blocks,
        }

        return {"complex_analysis": complex_analysis}

    async def suggest_improvements(self, code: str) -> dict[str, Any]:
        """Suggest improvements for async code.

        Args:
            code: Python code to analyze

        Returns:
            Dictionary containing improvement suggestions
        """
        if not code:
            return {"improvements": []}

        improvements: list[dict[str, str]] = []

        # Run various analyses
        blocking = await self.detect_blocking_calls(code)
        performance = await self.analyze_performance(code)
        race_conditions = await self.detect_race_conditions(code)
        missing_await = await self.detect_missing_await(code)

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
