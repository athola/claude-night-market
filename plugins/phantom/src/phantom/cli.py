"""CLI entry point for phantom computer use.

Usage:
    uv run python -m phantom.cli "Open Firefox and search for cats"
    uv run python -m phantom.cli --check  # check environment
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Any

from phantom.display import DisplayConfig, check_display_environment
from phantom.loop import LoopConfig, run_loop


def check_environment() -> None:
    """Print display environment diagnostics."""
    info = check_display_environment()
    print("Display Environment Check")
    print("=" * 40)
    print(f"  DISPLAY:         {info['display'] or '(not set)'}")
    print(f"  WAYLAND_DISPLAY: {info['wayland_display'] or '(not set)'}")
    print(f"  Has display:     {info['has_display']}")
    print()
    print("Tools:")
    for tool, available in info["tools"].items():
        status = "OK" if available else "MISSING"
        print(f"  {tool:15s} {status}")
    print()
    if info["all_tools_available"]:
        print("All required tools are available.")
    else:
        print("Some tools are missing. Install with:")
        print("  sudo apt install xdotool scrot xclip")


def run_task(args: argparse.Namespace) -> None:
    """Run a computer use task."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    task = " ".join(args.task)
    if not task:
        print("Error: No task provided")
        sys.exit(1)

    display_config = DisplayConfig(
        width=args.width,
        height=args.height,
    )
    loop_config = LoopConfig(
        model=args.model,
        max_iterations=args.max_iterations,
        max_tokens=args.max_tokens,
        thinking_budget=args.thinking_budget,
        system_prompt=args.system_prompt,
    )

    def on_action(action_type: str, action: dict[str, Any]) -> None:
        if not args.quiet:
            print(f"  Action: {action_type}", flush=True)

    print(f"Task: {task}")
    print(f"Model: {loop_config.model}")
    print(f"Max iterations: {loop_config.max_iterations}")
    print()

    result = run_loop(
        task=task,
        api_key=api_key,
        loop_config=loop_config,
        display_config=display_config,
        on_action=on_action,
    )

    print()
    print(f"Completed in {result.iterations} iterations")
    print(f"Actions taken: {result.actions_taken}")
    print(f"Stop reason: {result.stopped_reason}")
    if result.final_text:
        print()
        print("Response:")
        print(result.final_text)


def main() -> None:
    """Parse arguments and dispatch."""
    parser = argparse.ArgumentParser(
        description="Phantom: Claude Computer Use toolkit",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check display environment and exit",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Claude model to use (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1920,
        help="Display width in pixels",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1080,
        help="Display height in pixels",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=15,
        help="Maximum agent loop iterations",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Max tokens per API response",
    )
    parser.add_argument(
        "--thinking-budget",
        type=int,
        default=None,
        help="Token budget for thinking (optional)",
    )
    parser.add_argument(
        "--system-prompt",
        default=None,
        help="Custom system prompt",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress action output",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "task",
        nargs="*",
        help="Task description for Claude",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if args.check:
        check_environment()
        return

    if not args.task:
        parser.print_help()
        sys.exit(1)

    run_task(args)


if __name__ == "__main__":
    main()
