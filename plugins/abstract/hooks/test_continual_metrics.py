#!/usr/bin/env python3
"""Integration test for continual metrics in dual-hook system."""

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


def run_pre_hook(skill_ref: str) -> dict | None:
    """Run PreToolUse hook and return output."""
    pre_env = {
        "CLAUDE_TOOL_NAME": "Skill",
        "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
        "CLAUDE_SESSION_ID": "test-session",
    }
    result = subprocess.run(
        [sys.executable, "plugins/abstract/hooks/pre_skill_execution.py"],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, **pre_env},
    )
    if result.returncode != 0:
        print(f"✗ PreToolUse failed: {result.stderr}")
        return None
    return json.loads(result.stdout)


def run_post_hook(skill_ref: str, iteration: int) -> dict | None:
    """Run PostToolUse hook and return output."""
    # Alternate success/failure based on iteration
    tool_output = "Error: validation failed" if iteration % 2 == 0 else "Success"
    post_env = {
        "CLAUDE_TOOL_NAME": "Skill",
        "CLAUDE_TOOL_INPUT": json.dumps({"skill": skill_ref}),
        "CLAUDE_TOOL_OUTPUT": tool_output,
        "CLAUDE_SESSION_ID": "test-session",
    }
    result = subprocess.run(
        [sys.executable, "plugins/abstract/hooks/skill_execution_logger.py"],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, **post_env},
    )
    if result.returncode != 0:
        print(f"✗ PostToolUse failed: {result.stderr}")
        return None
    return json.loads(result.stdout)


def print_metrics(metrics: dict) -> None:
    """Print continual metrics summary."""
    print("  Continual Metrics:")
    print(f"    - Execution count: {metrics['execution_count']}")
    print(f"    - Average accuracy: {metrics['average_accuracy']:.2f}")
    print(f"    - Worst-case accuracy: {metrics['worst_case_accuracy']:.2f}")
    print(f"    - Stability gap: {metrics['stability_gap']:.2f}")


def verify_log_file(log_dir: Path) -> bool:
    """Verify log file exists and has valid entries."""
    log_date = datetime.now(UTC).strftime("%Y-%m-%d")
    log_file = log_dir / f"{log_date}.jsonl"

    if not log_file.exists():
        print(f"✗ Log file not found: {log_file}")
        return False

    print(f"✓ Log file exists: {log_file}")

    with open(log_file) as f:
        lines = f.readlines()

    print(f"✓ Log entries: {len(lines)}")

    last_entry = json.loads(lines[-1])
    if "continual_metrics" not in last_entry:
        print("✗ Last entry missing continual_metrics")
        return False

    metrics = last_entry["continual_metrics"]
    print("✓ Last entry has continual metrics:")
    print(f"    - Stability gap: {metrics['stability_gap']:.2f}")
    print(f"    - Worst-case: {metrics['worst_case_accuracy']:.2f}")
    print(f"    - Average: {metrics['average_accuracy']:.2f}")

    if metrics["stability_gap"] > 0:
        print(f"\n SUCCESS: Stability gap detected: {metrics['stability_gap']:.2f}")
        return True

    print("\n WARNING: Expected stability gap > 0")
    return False


def test_full_dual_hook_with_metrics() -> bool:
    """Test PreToolUse + PostToolUse with continual metrics calculation."""
    print("Testing Dual-Hook Continual Metrics System")
    print("=" * 70)

    skill_ref = "abstract:skill-auditor"
    log_dir = Path.home() / ".claude" / "skills" / "logs" / "abstract" / "skill-auditor"

    # Run 5 iterations to build up history
    for i in range(5):
        print(f"\n--- Iteration {i + 1}/5 ---")

        pre_output = run_pre_hook(skill_ref)
        if not pre_output:
            return False

        invocation_id = pre_output["hookSpecificOutput"]["invocation_id"]
        print(f"PreToolUse: {invocation_id}")

        time.sleep(0.05)  # 50ms simulated execution

        post_output = run_post_hook(skill_ref, i)
        if not post_output:
            return False

        duration = post_output["hookSpecificOutput"]["duration_ms"]
        outcome = post_output["hookSpecificOutput"]["outcome"]
        print(f"PostToolUse: {outcome}, {duration}ms")

        metrics = post_output["hookSpecificOutput"].get("continual_metrics")
        if metrics:
            print_metrics(metrics)
        else:
            print("  ✗ No continual metrics!")

    print("\n" + "=" * 70)
    print("Verification:")
    return verify_log_file(log_dir)


if __name__ == "__main__":
    success = test_full_dual_hook_with_metrics()
    sys.exit(0 if success else 1)
