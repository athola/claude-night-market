"""Agent loop for computer use interactions.

Manages the conversation cycle between Claude and the display
toolkit: send screenshots, receive actions, execute them, repeat.
"""

from __future__ import annotations

import logging
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anthropic

from phantom.cost import CostTracker, estimate_screenshot_tokens
from phantom.display import ActionResult, DisplayConfig, DisplayToolkit
from phantom.safety import ActionFilter, ConfirmationGate, no_confirm
from phantom.stuck import ScreenshotTracker, StuckPolicy

logger = logging.getLogger(__name__)


def _extract_screenshot_b64(tool_result: dict) -> str | None:
    """Extract base64 screenshot data from a tool result."""
    for item in tool_result.get("content", []):
        if isinstance(item, dict) and item.get("type") == "image":
            return item.get("source", {}).get("data") or None
    return None


# Model-to-tool-version mapping
TOOL_VERSIONS = {
    "claude-opus-4-6": "20251124",
    "claude-sonnet-4-6": "20251124",
    "claude-opus-4-5-20250620": "20251124",
    "claude-sonnet-4-5-20250514": "20250124",
    "claude-haiku-4-5-20251001": "20250124",
}

BETA_FLAGS = {
    "20251124": "computer-use-2025-11-24",
    "20250124": "computer-use-2025-01-24",
}

# Latest tool versions for each component
LATEST_TOOL_VERSIONS = {
    "20251124": {
        "computer": "computer_20251124",
        "text_editor": "text_editor_20250728",
        "bash": "bash_20250124",
    },
    "20250124": {
        "computer": "computer_20250124",
        "text_editor": "text_editor_20250124",
        "bash": "bash_20250124",
    },
}


def resolve_tool_version(model: str) -> str:
    """Get the correct tool version for a model.

    Falls back to the latest version if the model is unknown.
    """
    for prefix, version in TOOL_VERSIONS.items():
        if model.startswith(prefix):
            return version
    return "20251124"


def get_beta_flag(tool_version: str) -> str:
    """Get the beta flag for a tool version."""
    return BETA_FLAGS.get(tool_version, "computer-use-2025-11-24")


@dataclass
class LoopConfig:
    """Configuration for the agent loop."""

    model: str = "claude-sonnet-4-6"
    max_tokens: int = 4096
    max_iterations: int = 15
    thinking_budget: int | None = None
    system_prompt: str | None = None
    include_bash: bool = True
    include_text_editor: bool = True
    enable_zoom: bool = False
    # Safety: blocked screen regions [(x1,y1,x2,y2), ...]
    blocked_regions: list[tuple[int, int, int, int]] = field(
        default_factory=list,
    )
    # Stuck detection: abort after N identical screenshots
    max_stuck: int = 3
    # Budget: max USD to spend (None = unlimited)
    budget_usd: float | None = None


@dataclass
class LoopResult:
    """Result of a complete agent loop run."""

    messages: list[dict[str, Any]] = field(default_factory=list)
    iterations: int = 0
    final_text: str = ""
    actions_taken: int = 0
    actions_blocked: int = 0
    stopped_reason: str = ""
    cost_summary: str = ""


def build_tools(
    config: LoopConfig,
    display: DisplayConfig,
) -> list[dict[str, Any]]:
    """Build the tools list for the API request."""
    tool_version = resolve_tool_version(config.model)
    versions = LATEST_TOOL_VERSIONS.get(tool_version, LATEST_TOOL_VERSIONS["20251124"])

    computer_tool: dict[str, Any] = {
        "type": versions["computer"],
        "name": "computer",
        "display_width_px": display.width,
        "display_height_px": display.height,
        "display_number": display.display_number,
    }
    if config.enable_zoom and tool_version == "20251124":
        computer_tool["enable_zoom"] = True

    tools: list[dict[str, Any]] = [computer_tool]

    if config.include_text_editor:
        tools.append(
            {
                "type": versions["text_editor"],
                "name": "str_replace_based_edit_tool",
            }
        )

    if config.include_bash:
        tools.append(
            {
                "type": versions["bash"],
                "name": "bash",
            }
        )

    return tools


def run_loop(
    task: str,
    api_key: str,
    loop_config: LoopConfig | None = None,
    display_config: DisplayConfig | None = None,
    toolkit: DisplayToolkit | None = None,
    on_action: Callable[[str, dict[str, Any]], None] | None = None,
    on_screenshot: Callable[[str], None] | None = None,
    confirm_callback: Callable[[dict[str, Any]], bool] | None = None,
) -> LoopResult:
    """Run the computer use agent loop synchronously.

    Args:
        task: The user's task description.
        api_key: Anthropic API key.
        loop_config: Agent loop configuration.
        display_config: Display resolution config.
        toolkit: Pre-configured display toolkit (created if None).
        on_action: Callback(action_type, action_dict) for each action.
        on_screenshot: Callback(base64_png) for each screenshot.
        confirm_callback: Callback(action_dict) -> bool for approval.

    Returns:
        LoopResult with conversation history and stats.
    """
    config = loop_config or LoopConfig()
    d_config = display_config or DisplayConfig()
    display = toolkit or DisplayToolkit(config=d_config)

    # Initialize safety, stuck detection, and cost tracking
    action_filter = ActionFilter(blocked_regions=config.blocked_regions)
    gate = ConfirmationGate(
        callback=confirm_callback or no_confirm,
    )
    screenshot_tracker = ScreenshotTracker()
    stuck_policy = StuckPolicy(max_stuck=config.max_stuck)
    cost_tracker = CostTracker(
        model=config.model,
        budget_usd=config.budget_usd,
    )

    client = anthropic.Anthropic(api_key=api_key)
    tool_version = resolve_tool_version(config.model)
    beta_flag = get_beta_flag(tool_version)

    tools = build_tools(config, d_config)

    messages: list[dict[str, Any]] = [
        {"role": "user", "content": task},
    ]

    result = LoopResult(stopped_reason="max_iterations")

    for iteration in range(config.max_iterations):
        result.iterations = iteration + 1
        logger.info("Iteration %d/%d", iteration + 1, config.max_iterations)

        # Check budget before making API call
        if cost_tracker.budget_exceeded:
            result.stopped_reason = "budget_exceeded"
            logger.warning("Budget exceeded: %s", cost_tracker.summary())
            break

        # Build API kwargs
        kwargs: dict[str, Any] = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "messages": messages,
            "tools": tools,
            "betas": [beta_flag],
        }
        if config.system_prompt:
            kwargs["system"] = config.system_prompt
        if config.thinking_budget:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": config.thinking_budget,
            }

        response = client.beta.messages.create(**kwargs)

        # Track token costs
        usage = getattr(response, "usage", None)
        cost_tracker.record(
            input_tokens=getattr(usage, "input_tokens", 0) if usage else 0,
            output_tokens=getattr(usage, "output_tokens", 0) if usage else 0,
            screenshot_tokens_est=estimate_screenshot_tokens(
                d_config.width,
                d_config.height,
            ),
        )

        # Add assistant response to history
        response_content = response.content
        messages.append(
            {
                "role": "assistant",
                "content": [_block_to_dict(b) for b in response_content],
            }
        )

        # Process tool use blocks
        tool_results: list[dict[str, Any]] = []
        for block in response_content:
            if block.type == "tool_use":
                # Safety: check blocked regions
                if block.name == "computer" and not action_filter.is_allowed(
                    block.input
                ):
                    result.actions_blocked += 1
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": "Action blocked: restricted region",
                            "is_error": True,
                        }
                    )
                    continue

                # Safety: confirmation gate
                if block.name == "computer" and not gate.check(block.input):
                    result.actions_blocked += 1
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": "Action rejected by confirmation gate",
                            "is_error": True,
                        }
                    )
                    continue

                result.actions_taken += 1
                tool_result = _execute_tool(
                    block.name,
                    block.input,
                    block.id,
                    display,
                    on_action,
                    on_screenshot,
                )

                # Stuck detection: check if screenshot changed
                if block.name == "computer":
                    b64 = _extract_screenshot_b64(tool_result)
                    if b64:
                        is_stuck = screenshot_tracker.record(b64)
                        if is_stuck:
                            logger.warning(
                                "Stuck detected: %d consecutive identical screenshots",
                                screenshot_tracker.stuck_count,
                            )
                        if stuck_policy.should_abort(
                            screenshot_tracker.stuck_count,
                        ):
                            result.stopped_reason = "stuck"
                            result.cost_summary = cost_tracker.summary()
                            result.messages = messages
                            return result

                tool_results.append(tool_result)
            elif block.type == "text":
                result.final_text = block.text

        # If no tools were used, Claude is done
        if not tool_results:
            result.stopped_reason = "completed"
            break

        # Add tool results for next iteration
        messages.append({"role": "user", "content": tool_results})

    result.messages = messages
    result.cost_summary = cost_tracker.summary()
    return result


def _execute_tool(
    name: str,
    tool_input: dict[str, Any],
    tool_use_id: str,
    display: DisplayToolkit,
    on_action: Callable | None = None,
    on_screenshot: Callable | None = None,
) -> dict[str, Any]:
    """Execute a single tool and format the result for Claude."""
    logger.debug("Executing tool: %s with input: %s", name, tool_input)

    if name == "computer":
        if on_action:
            on_action(tool_input.get("action", ""), tool_input)

        action_result = display.execute(tool_input)

        # Always take a screenshot after non-screenshot actions
        if tool_input.get("action") != "screenshot" and action_result.success:
            screenshot = display.take_screenshot()
            if screenshot.success and screenshot.screenshot_b64:
                action_result.screenshot_b64 = screenshot.screenshot_b64

        return _format_tool_result(tool_use_id, action_result, on_screenshot)

    elif name == "bash":
        # Execute bash command. shell=True is intentional here:
        # the Computer Use API design has Claude send arbitrary
        # shell commands. Security relies on sandboxing (Docker/VM),
        # not command sanitization. See Anthropic's reference impl.
        command = tool_input.get("command", "")
        try:
            proc = subprocess.run(
                ["bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = proc.stdout
            if proc.stderr:
                output += f"\nSTDERR:\n{proc.stderr}"
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": output or "(no output)",
            }
        except subprocess.TimeoutExpired:
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": "Command timed out after 30s",
                "is_error": True,
            }

    elif name == "str_replace_based_edit_tool":
        # Text editor - delegate to a simple file operation
        return _handle_text_editor(tool_use_id, tool_input)

    else:
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": f"Unknown tool: {name}",
            "is_error": True,
        }


def _format_tool_result(
    tool_use_id: str,
    result: ActionResult,
    on_screenshot: Callable | None = None,
) -> dict[str, Any]:
    """Format an ActionResult as a Claude tool_result."""
    if not result.success:
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": result.error or "Action failed",
            "is_error": True,
        }

    content: list[dict[str, Any]] = []

    if result.screenshot_b64:
        if on_screenshot:
            on_screenshot(result.screenshot_b64)
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": result.screenshot_b64,
                },
            }
        )

    if not content:
        content.append({"type": "text", "text": "Action completed"})

    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
    }


def _handle_text_editor(
    tool_use_id: str,
    tool_input: dict[str, Any],
) -> dict[str, Any]:
    """Handle text editor tool operations."""
    command = tool_input.get("command", "")
    path = tool_input.get("path", "")

    try:
        if command == "view":
            if not path:
                return {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": "path is required for view",
                    "is_error": True,
                }
            text = Path(path).read_text()
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": text,
            }

        elif command == "create":
            file_text = tool_input.get("file_text", "")
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(file_text)
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": f"Created {path}",
            }

        elif command == "str_replace":
            old_str = tool_input.get("old_str", "")
            new_str = tool_input.get("new_str", "")
            text = Path(path).read_text()
            if old_str not in text:
                return {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": "old_str not found in file",
                    "is_error": True,
                }
            text = text.replace(old_str, new_str, 1)
            Path(path).write_text(text)
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": f"Replaced in {path}",
            }

        else:
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": f"Unknown editor command: {command}",
                "is_error": True,
            }

    except Exception as e:
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": str(e),
            "is_error": True,
        }


def _block_to_dict(block: Any) -> dict[str, Any]:
    """Convert an API response block to a serializable dict."""
    if hasattr(block, "model_dump"):
        result: dict[str, Any] = block.model_dump()
        return result
    if hasattr(block, "to_dict"):
        result = block.to_dict()
        return result
    # Fallback for simple types
    return {"type": getattr(block, "type", "unknown")}
