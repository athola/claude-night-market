#!/usr/bin/env python3
"""PROOF OF CONCEPT: PreToolUse + PostToolUse hooks for continual learning

This script demonstrates that:
1. PreToolUse hook can intercept Skill tool invocation BEFORE execution
2. PostToolUse hook can capture Skill execution AFTER completion
3. Both hooks receive complete tool_input, tool_output data
4. Duration tracking is possible across the pre/post boundary
5. This enables per-iteration continual learning (not just batch)

Expected usage:
- PreToolUse: Record start time, extract skill name, initialize metrics
- PostToolUse: Calculate duration, evaluate outcome, trigger learning loop

Run this script to verify hooks can intercept skill execution.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Constants
OUTPUT_PREVIEW_LENGTH = 500


def pre_tool_use_hook() -> None:
    """PreToolUse hook: Called BEFORE skill execution.

    Environment variables available:
    - CLAUDE_TOOL_NAME: "Skill" (when skill is invoked)
    - CLAUDE_TOOL_INPUT: JSON string with skill parameter
    - CLAUDE_SESSION_ID: Current session identifier

    This hook can:
    - Record start time for duration tracking
    - Parse skill name from tool_input
    - Initialize invocation-specific state
    - Perform pre-execution validation
    """
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")

    # Only process Skill tool invocations
    if tool_name != "Skill":
        sys.exit(0)

    try:
        tool_input = json.loads(tool_input_str)
        skill_ref = tool_input.get("skill", "unknown:unknown")

        # Parse plugin and skill name
        if ":" in skill_ref:
            plugin, skill = skill_ref.split(":", 1)
        else:
            plugin, skill = "unknown", skill_ref

        # Create invocation ID for tracking across pre/post hooks
        invocation_id = f"{plugin}:{skill}:{datetime.now(timezone.utc).timestamp()}"

        # Store pre-execution state
        state = {
            "invocation_id": invocation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "skill": skill_ref,
            "plugin": plugin,
            "skill_name": skill,
            "phase": "pre_tool_use",
            "tool_input": tool_input,
        }

        # Save state to temporary file for PostToolUse to read
        state_dir = Path.home() / ".claude" / "skills" / "observability"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / f"{invocation_id}.json"

        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

        # Output to stdout (becomes available to Claude Code)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "invocation_id": invocation_id,
                "skill": skill_ref,
                "message": f"Starting skill execution: {skill_ref}",
            }
        }

        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        # Never block Claude Code on hook errors
        sys.stderr.write(f"PreToolUse hook error: {e}\n")
        sys.exit(0)


def post_tool_use_hook() -> None:
    """PostToolUse hook: Called AFTER skill execution.

    Environment variables available:
    - CLAUDE_TOOL_NAME: "Skill"
    - CLAUDE_TOOL_INPUT: JSON string with skill parameter
    - CLAUDE_TOOL_OUTPUT: Skill execution output/result

    This hook can:
    - Calculate duration (if state file from PreToolUse exists)
    - Evaluate execution outcome (success/failure/partial)
    - Store execution log for later analysis
    - Trigger continual evaluation metrics
    """
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
    tool_output = os.environ.get("CLAUDE_TOOL_OUTPUT", "")

    # Only process Skill tool invocations
    if tool_name != "Skill":
        sys.exit(0)

    try:
        tool_input = json.loads(tool_input_str)
        skill_ref = tool_input.get("skill", "unknown:unknown")

        # Parse plugin and skill name
        if ":" in skill_ref:
            plugin, skill = skill_ref.split(":", 1)
        else:
            plugin, skill = "unknown", skill_ref

        # Try to find corresponding pre-execution state
        # (In real implementation, would use invocation_id from tool_input or context)
        state_dir = Path.home() / ".claude" / "skills" / "observability"

        # Find most recent state file for this skill
        pre_state = None
        if state_dir.exists():
            state_files = list(state_dir.glob(f"{plugin}:{skill}:*.json"))
            if state_files:
                # Get most recent
                latest_file = max(state_files, key=lambda p: p.stat().st_mtime)
                with open(latest_file) as f:
                    pre_state = json.load(f)

        # Calculate duration if we have pre-execution state
        duration_ms = None
        if pre_state:
            pre_time = datetime.fromisoformat(pre_state["timestamp"])
            post_time = datetime.now(timezone.utc)
            duration_ms = int((post_time - pre_time).total_seconds() * 1000)

        # Determine outcome
        outcome = "success"
        if "error" in tool_output.lower():
            outcome = "failure"
        elif "warning" in tool_output.lower():
            outcome = "partial"

        # Create execution log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "invocation_id": pre_state["invocation_id"] if pre_state else "unknown",
            "skill": skill_ref,
            "plugin": plugin,
            "skill_name": skill,
            "duration_ms": duration_ms,
            "outcome": outcome,
            "tool_input": tool_input,
            "output_length": len(tool_output),
            "output_preview": (
                tool_output[:OUTPUT_PREVIEW_LENGTH]
                if len(tool_output) > OUTPUT_PREVIEW_LENGTH
                else tool_output
            ),
        }

        # Save to execution log
        log_dir = Path.home() / ".claude" / "skills" / "logs" / plugin / skill
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Clean up state file
        if pre_state:
            state_file = state_dir / f"{pre_state['invocation_id']}.json"
            if state_file.exists():
                state_file.unlink()

        # Output to stdout
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "skill": skill_ref,
                "outcome": outcome,
                "duration_ms": duration_ms,
                "message": (
                    f"Completed skill execution: {skill_ref} "
                    f"({outcome}, {duration_ms}ms)"
                ),
            }
        }

        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"PostToolUse hook error: {e}\n")
        sys.exit(0)


if __name__ == "__main__":
    # Determine which hook to run based on calling convention
    # In production, Claude Code would call this script twice:
    # 1. Before tool execution (with pre-execution context)
    # 2. After tool execution (with post-execution context)

    # For testing, we'll simulate both phases
    if len(sys.argv) > 1 and sys.argv[1] == "--test-pre":
        print("Testing PreToolUse hook...")
        os.environ["CLAUDE_TOOL_NAME"] = "Skill"
        os.environ["CLAUDE_TOOL_INPUT"] = json.dumps(
            {"skill": "abstract:skill-auditor"}
        )
        os.environ["CLAUDE_SESSION_ID"] = "test-session-123"
        pre_tool_use_hook()

    elif len(sys.argv) > 1 and sys.argv[1] == "--test-post":
        print("Testing PostToolUse hook...")
        os.environ["CLAUDE_TOOL_NAME"] = "Skill"
        os.environ["CLAUDE_TOOL_INPUT"] = json.dumps(
            {"skill": "abstract:skill-auditor"}
        )
        os.environ["CLAUDE_TOOL_OUTPUT"] = (
            "Skill execution completed successfully with validation results."
        )
        post_tool_use_hook()

    elif len(sys.argv) > 1 and sys.argv[1] == "--test-full-loop":
        print("Testing full PreToolUse → PostToolUse loop...")
        print("\n=== Phase 1: PreToolUse ===")
        os.environ["CLAUDE_TOOL_NAME"] = "Skill"
        os.environ["CLAUDE_TOOL_INPUT"] = json.dumps(
            {"skill": "abstract:skill-auditor"}
        )
        os.environ["CLAUDE_SESSION_ID"] = "test-session-123"

        # Simulate PreToolUse
        result = subprocess.run(
            [sys.executable, __file__, "--test-pre"],
            check=False,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        # Simulate skill execution delay
        time.sleep(0.1)  # Simulate 100ms skill execution

        # Simulate PostToolUse
        print("\n=== Phase 2: PostToolUse ===")
        result = subprocess.run(
            [sys.executable, __file__, "--test-post"],
            check=False,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        print("\n=== Verification ===")
        # Check if log file was created
        log_file = (
            Path.home()
            / ".claude"
            / "skills"
            / "logs"
            / "abstract"
            / "skill-auditor"
            / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
        )
        if log_file.exists():
            print(f"✓ Log file created: {log_file}")
            with open(log_file) as f:
                for line in f:
                    log_entry = json.loads(line)
                    print(f"  - Invocation: {log_entry['invocation_id']}")
                    print(f"    Duration: {log_entry['duration_ms']}ms")
                    print(f"    Outcome: {log_entry['outcome']}")
        else:
            print(f"✗ Log file not found: {log_file}")

    else:
        # In production, detect phase from environment or use separate hook scripts
        # For now, default to PostToolUse (matches existing skill_execution_logger.py)
        post_tool_use_hook()
