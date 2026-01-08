#!/usr/bin/env python3
"""
Comprehensive integration test suite for Pensieve continual learning.

Tests ACTUAL hook execution with real plugin skills, not mocks.
Verifies:
1. PreToolUse hook fires and stores state
2. PostToolUse hook fires and calculates metrics
3. Duration tracking works accurately
4. Continual metrics are calculated correctly
5. Stability gap detection works
6. Logs are written to correct locations
"""

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


class PensieveIntegrationTest:
    """Integration tests for Pensieve continual learning system."""

    def __init__(self):
        self.claude_home = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))
        self.logs_dir = self.claude_home / "skills" / "logs"
        self.observability_dir = self.claude_home / "skills" / "observability"
        self.test_results = []
        self.passed = 0
        self.failed = 0

    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.test_results.append({"name": name, "passed": passed, "details": details})
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        print(f"{status}: {name}")
        if details:
            print(f"  {details}")

    def test_01_hook_files_exist(self) -> bool:
        """Test that hook files exist and are executable."""
        print("\n[Test 1] Verifying Hook Files")
        print("=" * 70)

        pensieve_hooks = Path("plugins/pensieve/hooks")
        required_files = [
            pensieve_hooks / "pre_skill_tracker.py",
            pensieve_hooks / "post_skill_tracker.py",
            pensieve_hooks / "hooks.json",
        ]

        all_exist = True
        for file_path in required_files:
            exists = file_path.exists()
            executable = file_path.stat().st_mode & 0o111 if exists else False
            passed = exists and executable
            self.log_test(
                f"Hook file: {file_path.name}",
                passed,
                f"Executable: {executable}" if exists else "Not found",
            )
            if not passed:
                all_exist = False

        return all_exist

    def test_02_pre_tool_use_hook(self) -> bool:
        """Test PreToolUse hook fires and stores state."""
        print("\n[Test 2] PreToolUse Hook Execution")
        print("=" * 70)

        skill_ref = "abstract:skill-auditor"
        invocation_id = f"{skill_ref}:{time.time()}"

        # Set up environment
        env = {
            **os.environ,
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_SESSION_ID": "test-session-123",
        }

        # Run PreToolUse hook
        result = subprocess.run(
            [sys.executable, "plugins/pensieve/hooks/pre_skill_tracker.py"],
            capture_output=True,
            text=True,
            env=env,
            timeout=5,
        )

        if result.returncode != 0:
            self.log_test(
                "PreToolUse hook execution",
                False,
                f"Exit code: {result.returncode}, stderr: {result.stderr}",
            )
            return False

        # Verify output
        try:
            output = json.loads(result.stdout)
            hook_data = output.get("hookSpecificOutput", {})

            inv_id = hook_data.get("invocation_id")
            event_name = hook_data.get("hookEventName")
            skill = hook_data.get("skill")

            self.log_test("PreToolUse returns JSON", True)
            self.log_test("Invocation ID generated", True, f"ID: {inv_id[:50]}...")
            self.log_test("Hook event name correct", event_name == "PreToolUse")
            self.log_test("Skill reference correct", skill == skill_ref)

        except (json.JSONDecodeError, KeyError) as e:
            self.log_test("PreToolUse output parsing", False, str(e))
            return False

        # Verify state file was created
        state_files = list(self.observability_dir.glob(f"{skill_ref}:*.json"))
        if state_files:
            state_file = state_files[-1]  # Get most recent
            with open(state_file) as f:
                state = json.load(f)

            self.log_test("State file created", True)
            self.log_test("State has timestamp", "timestamp" in state)
            self.log_test("State has invocation_id", "invocation_id" in state)
            self.log_test("State has skill", state.get("skill") == skill_ref)

            return True
        else:
            self.log_test("State file created", False, "No state files found")
            return False

    def test_03_post_tool_use_hook(self) -> bool:
        """Test PostToolUse hook calculates metrics and logs correctly."""
        print("\n[Test 3] PostToolUse Hook Execution")
        print("=" * 70)

        skill_ref = "abstract:skill-auditor"

        # Set up environment
        env = {
            **os.environ,
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_TOOL_OUTPUT": "Skill validation completed successfully",
            "CLAUDE_SESSION_ID": "test-session-123",
        }

        # Run PostToolUse hook
        result = subprocess.run(
            [sys.executable, "plugins/pensieve/hooks/post_skill_tracker.py"],
            capture_output=True,
            text=True,
            env=env,
            timeout=5,
        )

        if result.returncode != 0:
            self.log_test(
                "PostToolUse hook execution",
                False,
                f"Exit code: {result.returncode}, stderr: {result.stderr}",
            )
            return False

        # Verify output
        try:
            output = json.loads(result.stdout)
            hook_data = output.get("hookSpecificOutput", {})

            event_name = hook_data.get("hookEventName")
            skill = hook_data.get("skill")
            outcome = hook_data.get("outcome")
            duration = hook_data.get("duration_ms")
            metrics = hook_data.get("continual_metrics")

            self.log_test("PostToolUse returns JSON", True)
            self.log_test("Hook event name correct", event_name == "PostToolUse")
            self.log_test("Skill reference correct", skill == skill_ref)
            self.log_test("Outcome detected", outcome == "success")
            self.log_test("Duration measured", duration is not None and duration > 0)

            if metrics:
                self.log_test("Continual metrics calculated", True)
                self.log_test("Has execution count", "execution_count" in metrics)
                self.log_test("Has average accuracy", "average_accuracy" in metrics)
                self.log_test(
                    "Has worst-case accuracy", "worst_case_accuracy" in metrics
                )
                self.log_test("Has stability gap", "stability_gap" in metrics)
            else:
                self.log_test("Continual metrics calculated", False, "No metrics")
                return False

        except (json.JSONDecodeError, KeyError) as e:
            self.log_test("PostToolUse output parsing", False, str(e))
            return False

        # Verify log file was created
        log_dir = self.logs_dir / "abstract" / "skill-auditor"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"

        if log_file.exists():
            with open(log_file) as f:
                lines = f.readlines()

            self.log_test("Log file created", True, f"Entries: {len(lines)}")

            # Verify log entry structure
            if lines:
                try:
                    entry = json.loads(lines[-1])
                    self.log_test("Log entry has timestamp", "timestamp" in entry)
                    self.log_test(
                        "Log entry has skill", entry.get("skill") == skill_ref
                    )
                    self.log_test("Log entry has outcome", "outcome" in entry)
                    self.log_test("Log entry has duration", "duration_ms" in entry)
                    self.log_test("Log entry has metrics", "continual_metrics" in entry)

                    return True
                except json.JSONDecodeError:
                    self.log_test("Log entry parsing", False, "Invalid JSON")
                    return False
        else:
            self.log_test("Log file created", False, f"Not found: {log_file}")
            return False

    def test_04_duration_tracking(self) -> bool:
        """Test accurate duration tracking across PreToolUse and PostToolUse."""
        print("\n[Test 4] Duration Tracking Accuracy")
        print("=" * 70)

        skill_ref = "sanctum:pr-review"

        # PreToolUse
        env = {
            **os.environ,
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
        }

        start = time.perf_counter()
        result = subprocess.run(
            [sys.executable, "plugins/pensieve/hooks/pre_skill_tracker.py"],
            capture_output=True,
            env=env,
            timeout=5,
        )
        pre_duration = (time.perf_counter() - start) * 1000

        if result.returncode != 0:
            self.log_test("PreToolUse for duration test", False)
            return False

        # Simulate skill execution delay
        skill_delay = 0.1  # 100ms
        time.sleep(skill_delay)

        # PostToolUse
        env = {
            **os.environ,
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            "CLAUDE_TOOL_OUTPUT": "PR review completed",
        }

        result = subprocess.run(
            [sys.executable, "plugins/pensieve/hooks/post_skill_tracker.py"],
            capture_output=True,
            text=True,
            env=env,
            timeout=5,
        )

        if result.returncode != 0:
            self.log_test("PostToolUse for duration test", False)
            return False

        # Parse output
        try:
            output = json.loads(result.stdout)
            tracked_duration = output["hookSpecificOutput"].get("duration_ms")

            if tracked_duration:
                # Should be approximately skill_delay (100ms) + hook overhead
                # Allow ±50ms tolerance
                expected = skill_delay * 1000
                tolerance = 50

                in_range = abs(tracked_duration - expected) <= tolerance

                self.log_test(
                    "Duration tracked",
                    True,
                    f"{tracked_duration}ms (expected ~{expected}ms)",
                )
                self.log_test(
                    "Duration accurate",
                    in_range,
                    f"Difference: {abs(tracked_duration - expected):.1f}ms",
                )

                return in_range
            else:
                self.log_test("Duration tracked", False, "No duration in output")
                return False

        except (json.JSONDecodeError, KeyError) as e:
            self.log_test("Duration output parsing", False, str(e))
            return False

    def test_05_stability_gap_detection(self) -> bool:
        """Test stability gap calculation with mixed success/failure."""
        print("\n[Test 5] Stability Gap Detection")
        print("=" * 70)

        skill_ref = "test:stability-skill"
        failures = [
            0,
            0,
            1,
            0,
            1,
            0,
        ]  # Pattern: success, success, fail, success, fail, success

        print(f"Running {len(failures)} iterations to build history...")

        for i, should_fail in enumerate(failures):
            # PreToolUse
            env = {
                **os.environ,
                "CLAUDE_TOOL_NAME": "Skill",
                "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            }

            subprocess.run(
                [sys.executable, "plugins/pensieve/hooks/pre_skill_tracker.py"],
                capture_output=True,
                env=env,
                timeout=5,
            )

            time.sleep(0.01)  # Small delay

            # PostToolUse
            tool_output = "Error: validation failed" if should_fail else "Success"
            env = {
                **os.environ,
                "CLAUDE_TOOL_NAME": "Skill",
                "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
                "CLAUDE_TOOL_OUTPUT": tool_output,
            }

            result = subprocess.run(
                [sys.executable, "plugins/pensieve/hooks/post_skill_tracker.py"],
                capture_output=True,
                text=True,
                env=env,
                timeout=5,
            )

            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)
                    metrics = output["hookSpecificOutput"].get("continual_metrics", {})
                    gap = metrics.get("stability_gap", 0)
                    worst = metrics.get("worst_case_accuracy", 0)
                    avg = metrics.get("average_accuracy", 0)

                    print(
                        f"  Iteration {i+1}: {'FAIL' if should_fail else 'OK'} → "
                        f"gap={gap:.2f}, worst={worst:.2f}, avg={avg:.2f}"
                    )
                except (json.JSONDecodeError, KeyError):
                    pass

        # Check final metrics
        log_dir = self.logs_dir / "test" / "stability-skill"
        log_date = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = log_dir / f"{log_date}.jsonl"

        if not log_file.exists():
            self.log_test("Stability gap log file created", False)
            return False

        with open(log_file) as f:
            last_entry = json.loads(f.readlines()[-1])
            metrics = last_entry.get("continual_metrics", {})

            final_gap = metrics.get("stability_gap", 0)
            final_worst = metrics.get("worst_case_accuracy", 0)
            final_avg = metrics.get("average_accuracy", 0)

            # Expected: 4/6 success = 0.67 avg, 0.0 worst, gap = 0.67
            expected_gap = 0.67
            tolerance = 0.1

            gap_correct = abs(final_gap - expected_gap) <= tolerance
            worst_correct = final_worst == 0.0
            avg_correct = abs(final_avg - 0.67) <= tolerance

            self.log_test(
                "Final stability gap calculated",
                gap_correct,
                f"{final_gap:.2f} (expected ~{expected_gap:.2f})",
            )
            self.log_test(
                "Worst-case accuracy correct", worst_correct, f"{final_worst:.2f}"
            )
            self.log_test(
                "Average accuracy correct",
                avg_correct,
                f"{final_avg:.2f} (expected ~0.67)",
            )

            # Expected gap > 0 (should detect instability)
            gap_detected = final_gap > 0.3
            self.log_test(
                "Stability gap detected (> 0.3)", gap_detected, f"Gap: {final_gap:.2f}"
            )

            return gap_correct and worst_correct and avg_correct and gap_detected

    def test_06_cross_plugin_tracking(self) -> bool:
        """Test that hooks work with skills from different plugins."""
        print("\n[Test 6] Cross-Plugin Skill Tracking")
        print("=" * 70)

        test_skills = [
            "abstract:skill-auditor",
            "sanctum:pr-review",
            "imbue:proof-of-work",
        ]

        for skill_ref in test_skills:
            # PreToolUse
            env = {
                **os.environ,
                "CLAUDE_TOOL_NAME": "Skill",
                "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
            }

            result = subprocess.run(
                [sys.executable, "plugins/pensieve/hooks/pre_skill_tracker.py"],
                capture_output=True,
                env=env,
                timeout=5,
            )

            time.sleep(0.01)

            # PostToolUse
            env = {
                **os.environ,
                "CLAUDE_TOOL_NAME": "Skill",
                "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
                "CLAUDE_TOOL_OUTPUT": "Success",
            }

            result = subprocess.run(
                [sys.executable, "plugins/pensieve/hooks/post_skill_tracker.py"],
                capture_output=True,
                env=env,
                timeout=5,
            )

            tracked = result.returncode == 0
            plugin = skill_ref.split(":")[0]
            self.log_test(f"Tracked skill from {plugin}", tracked)

        # Verify logs for all plugins
        all_logged = True
        for skill_ref in test_skills:
            plugin = skill_ref.split(":")[0]
            skill = skill_ref.split(":")[1]
            log_dir = self.logs_dir / plugin / skill
            log_date = datetime.now(UTC).strftime("%Y-%m-%d")
            log_file = log_dir / f"{log_date}.jsonl"

            exists = log_file.exists()
            self.log_test(f"Log file exists for {plugin}", exists)

            if not exists:
                all_logged = False

        return all_logged

    def test_07_error_handling(self) -> bool:
        """Test that hooks handle errors gracefully."""
        print("\n[Test 7] Error Handling")
        print("=" * 70)

        # Test with malformed input
        env = {
            **os.environ,
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": "invalid json{{{",
        }

        result = subprocess.run(
            [sys.executable, "plugins/pensieve/hooks/pre_skill_tracker.py"],
            capture_output=True,
            env=env,
            timeout=5,
        )

        # Should exit gracefully (code 0) even with malformed input
        graceful = result.returncode == 0
        self.log_test("Handles malformed input gracefully", graceful, "Exit code: 0")

        # Test with error output
        env = {
            **os.environ,
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": "test:skill"}),
            "CLAUDE_TOOL_OUTPUT": "Error: something went wrong",
        }

        result = subprocess.run(
            [sys.executable, "plugins/pensieve/hooks/post_skill_tracker.py"],
            capture_output=True,
            text=True,
            env=env,
            timeout=5,
        )

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                outcome = output["hookSpecificOutput"].get("outcome")
                error_detected = outcome == "failure"
                self.log_test("Detects failure in output", error_detected)
            except (json.JSONDecodeError, KeyError):
                self.log_test("Detects failure in output", False)
        else:
            self.log_test("Handles error output gracefully", False)

        return graceful

    def run_all_tests(self) -> bool:
        """Run all integration tests."""
        print("\n" + "=" * 70)
        print("PENSIEVE INTEGRATION TEST SUITE")
        print("=" * 70)
        print(f"Logs directory: {self.logs_dir}")
        print(f"Observability directory: {self.observability_dir}")
        print("=" * 70)

        # Create directories
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.observability_dir.mkdir(parents=True, exist_ok=True)

        # Run tests
        tests = [
            self.test_01_hook_files_exist,
            self.test_02_pre_tool_use_hook,
            self.test_03_post_tool_use_hook,
            self.test_04_duration_tracking,
            self.test_05_stability_gap_detection,
            self.test_06_cross_plugin_tracking,
            self.test_07_error_handling,
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {e}")

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success rate: {self.passed / (self.passed + self.failed) * 100:.1f}%")
        print("=" * 70)

        if self.failed > 0:
            print("\nFailed tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  ✗ {result['name']}: {result['details']}")

        return self.failed == 0


if __name__ == "__main__":
    tester = PensieveIntegrationTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
