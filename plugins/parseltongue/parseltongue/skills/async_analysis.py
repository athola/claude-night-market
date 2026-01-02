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
- Testing pattern analysis
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

        patterns = {}

        # Track asyncio.gather usage
        gather_functions = []
        create_task_functions = []
        task_group_functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name

                # Check for asyncio.gather
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if self._is_call_to(
                            child, "asyncio.gather"
                        ) or self._is_call_to(child, "gather"):
                            gather_functions.append(function_name)

                        if self._is_call_to(
                            child, "asyncio.create_task"
                        ) or self._is_call_to(child, "create_task"):
                            create_task_functions.append(function_name)

                        if self._is_call_to(child, "TaskGroup"):
                            task_group_functions.append(function_name)

        if gather_functions:
            patterns["gather_usage"] = {"functions": list(set(gather_functions))}

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
            return {"blocking_patterns": {}, "recommendations": []}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"blocking_patterns": {}, "error": "Invalid Python syntax"}

        blocking_patterns = {}
        recommendations = []

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
                                "blocks_event_loop": True
                            }
                            recommendations.append(
                                "Replace time.sleep() with asyncio.sleep() in async functions"
                            )

                        # requests library
                        if self._is_call_to(child, "requests.get") or self._is_call_to(
                            child, "requests.post"
                        ):
                            blocking_patterns["requests"] = {"blocks_event_loop": True}
                            recommendations.append(
                                "Replace requests with aiohttp for async HTTP calls"
                            )

                        # open() for file I/O
                        if isinstance(child.func, ast.Name) and child.func.id == "open":
                            blocking_patterns["file_io"] = {"blocks_event_loop": True}
                            recommendations.append(
                                "Consider using aiofiles for async file I/O"
                            )

        return {
            "blocking_patterns": {
                **blocking_patterns,
                "recommendations": list(set(recommendations)),
            }
        }

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

        missing_awaits = {}

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
                                "suggestion": "Add await before the coroutine call"
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

        try_catch_blocks = []
        functions = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name
                has_error_handling = False
                exception_types = []

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

                functions[function_name] = {
                    "has_error_handling": has_error_handling,
                    "exception_types": list(set(exception_types)),
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
            return {"timeout_analysis": {"wait_for_usage": [], "functions": {}}}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"timeout_analysis": {}, "error": "Invalid Python syntax"}

        wait_for_usage = []
        functions = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name
                has_timeout = False
                timeout_value = None

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
                        wait_for_usage.append(
                            {
                                "function": function_name,
                                "line_number": child.lineno,
                            }
                        )

                        # Try to extract timeout value from call
                        for keyword in child.keywords:
                            if keyword.arg == "timeout" and isinstance(
                                keyword.value, ast.Constant
                            ):
                                timeout_value = keyword.value.value

                if has_timeout:
                    functions[function_name] = {
                        "has_timeout": True,
                        "timeout_value": timeout_value,
                    }

        return {
            "timeout_analysis": {
                "wait_for_usage": wait_for_usage,
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

        services = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                creates_session = False
                closes_session = False
                cleanup_in_finally = False

                # Check for __aexit__ method (context manager cleanup)
                has_aexit = False
                for item in node.body:
                    if (
                        isinstance(item, ast.AsyncFunctionDef)
                        and item.name == "__aexit__"
                    ):
                        has_aexit = True
                        # Check if __aexit__ calls close()
                        for child in ast.walk(item):
                            if (
                                isinstance(child, ast.Call)
                                and isinstance(child.func, ast.Attribute)
                                and child.func.attr == "close"
                            ):
                                cleanup_in_finally = True

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
                        "cleanup_in_finally": cleanup_in_finally or has_aexit,
                    }

        return {"resource_management": {"services": services}}

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

        issues = {}

        # Check for sequential processing in loops
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                function_name = node.name

                # Look for for loops with await inside
                for child in ast.walk(node):
                    if isinstance(child, ast.For):
                        has_await = any(
                            isinstance(item, ast.Await) for item in ast.walk(child)
                        )

                        if has_await:
                            issues["sequential_processing"] = {
                                function_name: {
                                    "issue": "Sequential await in loop",
                                    "suggestion": "Consider using asyncio.gather() for concurrent processing",
                                }
                            }

        concurrent_alternative = (
            "Use asyncio.gather() or asyncio.create_task() for concurrent execution"
            if issues
            else None
        )

        return {
            "performance_analysis": {
                "issues": issues,
                "concurrent_alternative": concurrent_alternative,
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
            return {"race_conditions": {"unsynchronized_shared_state": []}}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"race_conditions": {}, "error": "Invalid Python syntax"}

        unsynchronized_shared_state = []
        safe_patterns = {}

        # Track module-level shared state (for future use)
        # Kept for potential future enhancement to detect module-level race conditions

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
                            # counter["lock"] pattern
                            if (
                                isinstance(with_item.context_expr, ast.Subscript)
                                and isinstance(
                                    with_item.context_expr.slice, ast.Constant
                                )
                                and with_item.context_expr.slice.value == "lock"
                            ):
                                uses_lock = True

                if uses_lock:
                    safe_patterns[function_name] = {"uses_lock": True}

        # Check for classes with shared state
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check for shared state (class attributes)
                has_shared_state = False
                uses_lock = False

                for body_item in node.body:
                    # Check for class-level attributes
                    if isinstance(body_item, ast.Assign):
                        has_shared_state = True

                    # Check for asyncio.Lock usage
                    if isinstance(body_item, ast.AsyncFunctionDef):
                        for child in ast.walk(body_item):
                            if isinstance(child, ast.Call) and (
                                self._is_call_to(child, "asyncio.Lock")
                                or self._is_call_to(child, "Lock")
                            ):
                                uses_lock = True

                if has_shared_state and not uses_lock:
                    unsynchronized_shared_state.append(
                        {
                            "class": node.name,
                            "warning": "Shared state without synchronization",
                        }
                    )
                elif has_shared_state and uses_lock:
                    safe_patterns[node.name] = {"uses_lock": True}

        return {
            "race_conditions": {
                "unsynchronized_shared_state": unsynchronized_shared_state,
                "safe_patterns": safe_patterns,
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

        return {
            "testing_analysis": {
                "uses_pytest_asyncio": uses_pytest_asyncio,
                "async_test_count": async_test_count,
                "mocking_patterns": {
                    "uses_asyncmock": uses_asyncmock,
                },
            }
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

        improvements = []

        # Run various analyses
        blocking = await self.detect_blocking_calls(code)
        performance = await self.analyze_performance(code)
        race_conditions = await self.detect_race_conditions(code)
        missing_await = await self.detect_missing_await(code)

        # Add suggestions based on findings
        if blocking.get("blocking_patterns"):
            for pattern, _info in blocking["blocking_patterns"].items():
                if pattern == "time_sleep":
                    improvements.append(
                        {
                            "code_before": "time.sleep(1)",
                            "code_after": "await asyncio.sleep(1)",
                            "explanation": "Use asyncio.sleep() instead of time.sleep() to avoid blocking the event loop",
                        }
                    )

        if missing_await.get("missing_awaits"):
            improvements.append(
                {
                    "code_before": "data = api_call()",
                    "code_after": "data = await api_call()",
                    "explanation": "Add await keyword before async function calls to properly wait for the result",
                }
            )

        if performance.get("performance_analysis", {}).get("issues"):
            improvements.append(
                {
                    "code_before": """
for item in items:
    result = await process_item(item)
    results.append(result)
""".strip(),
                    "code_after": """
results = await asyncio.gather(*[process_item(item) for item in items])
""".strip(),
                    "explanation": "Use asyncio.gather() to process items concurrently instead of sequentially",
                }
            )

        if race_conditions.get("race_conditions", {}).get(
            "unsynchronized_shared_state"
        ):
            improvements.append(
                {
                    "code_before": "self.counter += 1",
                    "code_after": """
async with self.lock:
    self.counter += 1
""".strip(),
                    "explanation": "Protect shared state with asyncio.Lock to prevent race conditions",
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
