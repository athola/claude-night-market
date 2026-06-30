"""Tests for phantom.loop - the agent loop and tool orchestration.

Feature: Agent Loop
    As an automation developer
    I want an agent loop that cycles between Claude and the display
    So that Claude can complete multi-step desktop tasks autonomously
"""

from __future__ import annotations

from unittest.mock import MagicMock

from phantom.display import ActionResult, DisplayConfig, DisplayToolkit
from phantom.loop import (
    ClientSetup,
    IterationContext,
    LoopConfig,
    LoopHooks,
    LoopResult,
    _execute_tool,
    _format_tool_result,
    _handle_text_editor,
    _process_iteration,
    _run_tool_block,
    build_tools,
    get_beta_flag,
    resolve_tool_version,
)


class TestResolveToolVersion:
    """Feature: Model-to-tool-version resolution."""

    def test_opus_46_uses_latest(self):
        """
        Scenario: Opus 4.6 model
        Given model "claude-opus-4-6"
        When resolving tool version
        Then it returns 20251124
        And that version maps to the latest tool generation
        """
        assert resolve_tool_version("claude-opus-4-6") == "20251124"

    def test_sonnet_46_uses_latest(self):
        assert resolve_tool_version("claude-sonnet-4-6") == "20251124"

    def test_sonnet_45_uses_older(self):
        assert resolve_tool_version("claude-sonnet-4-5-20250514") == "20250124"

    def test_unknown_model_falls_back_to_latest(self):
        """
        Scenario: Unknown model
        Given an unrecognized model string
        When resolving tool version
        Then it falls back to the latest version
        And the fallback is the string "20251124"
        """
        assert resolve_tool_version("claude-future-9000") == "20251124"


class TestGetBetaFlag:
    """Feature: Beta flag selection."""

    def test_latest_version_flag(self):
        assert get_beta_flag("20251124") == "computer-use-2025-11-24"

    def test_older_version_flag(self):
        assert get_beta_flag("20250124") == "computer-use-2025-01-24"

    def test_unknown_version_defaults(self):
        assert get_beta_flag("unknown") == "computer-use-2025-11-24"


class TestBuildTools:
    """Feature: Tool list construction for API requests."""

    def test_default_config_includes_all_tools(self):
        """
        Scenario: Default tool config
        Given default LoopConfig
        When building tools
        Then computer, text_editor, and bash tools are included
        """
        config = LoopConfig()
        display = DisplayConfig(width=1024, height=768)
        tools = build_tools(config, display)

        assert len(tools) == 3
        names = [t["name"] for t in tools]
        assert "computer" in names
        assert "str_replace_based_edit_tool" in names
        assert "bash" in names

    def test_computer_tool_has_display_dimensions(self):
        """
        Scenario: Computer tool dimensions
        Given a 1024x768 display config
        When building tools
        Then the computer tool has matching dimensions
        And both width and height match the display config values
        """
        config = LoopConfig()
        display = DisplayConfig(width=1024, height=768)
        tools = build_tools(config, display)

        computer = tools[0]
        assert computer["display_width_px"] == 1024
        assert computer["display_height_px"] == 768

    def test_disable_bash(self):
        """
        Scenario: Bash disabled
        Given LoopConfig with include_bash=False
        When building tools
        Then bash tool is not in the list
        And the computer tool is still present
        """
        config = LoopConfig(include_bash=False)
        display = DisplayConfig()
        tools = build_tools(config, display)

        names = [t["name"] for t in tools]
        assert "bash" not in names
        assert "computer" in names

    def test_disable_text_editor(self):
        config = LoopConfig(include_text_editor=False)
        display = DisplayConfig()
        tools = build_tools(config, display)

        names = [t["name"] for t in tools]
        assert "str_replace_based_edit_tool" not in names

    def test_zoom_enabled_for_latest_version(self):
        """
        Scenario: Zoom feature enabled
        Given LoopConfig with enable_zoom=True and Opus 4.6
        When building tools
        Then the computer tool has enable_zoom=True
        """
        config = LoopConfig(model="claude-opus-4-6", enable_zoom=True)
        display = DisplayConfig()
        tools = build_tools(config, display)

        computer = tools[0]
        assert computer.get("enable_zoom") is True


class TestLoopConfig:
    """Feature: Loop configuration defaults."""

    def test_defaults(self):
        config = LoopConfig()
        assert config.model == "claude-sonnet-4-6"
        assert config.max_iterations == 15
        assert config.max_tokens == 4096
        assert config.thinking_budget is None

    def test_custom_values(self):
        config = LoopConfig(
            model="claude-opus-4-6",
            max_iterations=5,
            thinking_budget=2048,
        )
        assert config.model == "claude-opus-4-6"
        assert config.max_iterations == 5
        assert config.thinking_budget == 2048


class TestLoopResult:
    """Feature: Loop result structure."""

    def test_default_result(self):
        result = LoopResult()
        assert result.iterations == 0
        assert result.actions_taken == 0
        assert result.final_text == ""
        assert result.messages == []


class TestExecuteTool:
    """Feature: Tool execution dispatch."""

    def test_computer_tool_delegates_to_display(self):
        """
        Scenario: Computer tool execution
        Given a computer tool_use with a click action
        When _execute_tool is called
        Then it delegates to the DisplayToolkit
        And the result contains the expected tool_use_id
        """
        mock_display = MagicMock(spec=DisplayToolkit)
        mock_display.execute.return_value = ActionResult(success=True)
        mock_display.take_screenshot.return_value = ActionResult(
            success=True, screenshot_b64="fakepng"
        )

        result = _execute_tool(
            "computer",
            {"action": "left_click", "coordinate": [100, 200]},
            "tool-id-1",
            mock_display,
        )

        mock_display.execute.assert_called_once()
        assert result["type"] == "tool_result"
        assert result["tool_use_id"] == "tool-id-1"

    def test_computer_screenshot_action_no_double_capture(self):
        """
        Scenario: Screenshot action
        Given a screenshot tool_use
        When _execute_tool is called
        Then it does not take a second screenshot
        And the result still carries the screenshot from execute()
        """
        mock_display = MagicMock(spec=DisplayToolkit)
        mock_display.execute.return_value = ActionResult(
            success=True, screenshot_b64="screen1"
        )

        result = _execute_tool(
            "computer",
            {"action": "screenshot"},
            "tool-id-2",
            mock_display,
        )

        # take_screenshot should NOT be called for screenshot actions
        mock_display.take_screenshot.assert_not_called()
        assert result["tool_use_id"] == "tool-id-2"

    def test_unknown_tool_returns_error(self):
        mock_display = MagicMock(spec=DisplayToolkit)
        result = _execute_tool("unknown_tool", {}, "tool-id-3", mock_display)
        assert result.get("is_error") is True
        assert "Unknown tool" in result["content"]

    def test_action_callback_invoked(self):
        """
        Scenario: Action callback
        Given an on_action callback
        When a computer action executes
        Then the callback receives the action type and dict
        And the result is a valid tool_result dict
        """
        mock_display = MagicMock(spec=DisplayToolkit)
        mock_display.execute.return_value = ActionResult(success=True)
        mock_display.take_screenshot.return_value = ActionResult(success=True)

        callback = MagicMock()
        result = _execute_tool(
            "computer",
            {"action": "left_click", "coordinate": [1, 2]},
            "id",
            mock_display,
            hooks=LoopHooks(on_action=callback),
        )
        callback.assert_called_once_with(
            "left_click",
            {"action": "left_click", "coordinate": [1, 2]},
        )
        assert result["type"] == "tool_result"


class TestFormatToolResult:
    """Feature: Tool result formatting for Claude API."""

    def test_success_with_screenshot(self):
        """
        Scenario: Successful action with screenshot
        Given a successful ActionResult with screenshot data
        When formatting as tool_result
        Then it includes an image content block
        And is_error is absent from the result
        """
        result = ActionResult(success=True, screenshot_b64="abc123")
        formatted = _format_tool_result("id-1", result)

        assert formatted["tool_use_id"] == "id-1"
        assert not formatted.get("is_error")
        content = formatted["content"]
        assert any(c["type"] == "image" for c in content)

    def test_failure_includes_error(self):
        """
        Scenario: Failed action
        Given a failed ActionResult
        When formatting as tool_result
        Then it includes is_error=True and the error message
        """
        result = ActionResult(success=False, error="Display not found")
        formatted = _format_tool_result("id-2", result)

        assert formatted["is_error"] is True
        assert "Display not found" in formatted["content"]

    def test_success_without_screenshot(self):
        result = ActionResult(success=True)
        formatted = _format_tool_result("id-3", result)

        content = formatted["content"]
        assert any(c.get("text") == "Action completed" for c in content)


class TestHandleTextEditor:
    """Feature: Text editor tool operations."""

    def test_view_reads_file(self, tmp_path):
        """
        Scenario: View a file
        Given a file with known content
        When the text editor view command is used
        Then it returns the file contents
        """
        f = tmp_path / "test.txt"
        f.write_text("hello world")

        result = _handle_text_editor(
            "id",
            {
                "command": "view",
                "path": str(f),
            },
        )
        assert "hello world" in result["content"]

    def test_create_writes_file(self, tmp_path):
        """
        Scenario: Create a file
        Given a path and content
        When the text editor create command is used
        Then the file is written to disk
        """
        f = tmp_path / "new.txt"
        result = _handle_text_editor(
            "id",
            {
                "command": "create",
                "path": str(f),
                "file_text": "new content",
            },
        )
        assert f.read_text() == "new content"
        assert not result.get("is_error")

    def test_str_replace_modifies_file(self, tmp_path):
        f = tmp_path / "edit.txt"
        f.write_text("foo bar baz")

        result = _handle_text_editor(
            "id",
            {
                "command": "str_replace",
                "path": str(f),
                "old_str": "bar",
                "new_str": "qux",
            },
        )
        assert f.read_text() == "foo qux baz"
        assert not result.get("is_error")

    def test_str_replace_missing_text_errors(self, tmp_path):
        f = tmp_path / "edit.txt"
        f.write_text("foo bar")

        result = _handle_text_editor(
            "id",
            {
                "command": "str_replace",
                "path": str(f),
                "old_str": "missing",
                "new_str": "x",
            },
        )
        assert result.get("is_error") is True

    def test_unknown_command_errors(self):
        result = _handle_text_editor("id", {"command": "delete_all"})
        assert result.get("is_error") is True


def _make_iteration_context(
    *,
    gate=None,
    stuck_policy=None,
    cost_tracker=None,
    screenshot_tracker=None,
    display=None,
) -> IterationContext:
    """Build an IterationContext with sensible mock defaults."""
    action_filter = MagicMock()
    action_filter.is_allowed.return_value = True
    if gate is None:
        gate = MagicMock()
        gate.check.return_value = True
    if cost_tracker is None:
        cost_tracker = MagicMock()
        cost_tracker.budget_exceeded = False
        cost_tracker.summary.return_value = ""
    if screenshot_tracker is None:
        screenshot_tracker = MagicMock()
        screenshot_tracker.record.return_value = False
        screenshot_tracker.stuck_count = 0
    if stuck_policy is None:
        stuck_policy = MagicMock()
        stuck_policy.should_abort.return_value = False
    if display is None:
        display = MagicMock(spec=DisplayToolkit)
        display.execute.return_value = ActionResult(success=True)
        display.take_screenshot.return_value = ActionResult(success=True)
    return IterationContext(
        config=LoopConfig(),
        d_config=DisplayConfig(),
        cost_tracker=cost_tracker,
        action_filter=action_filter,
        gate=gate,
        display=display,
        screenshot_tracker=screenshot_tracker,
        stuck_policy=stuck_policy,
        hooks=LoopHooks(),
    )


class TestRunToolBlockGateRejection:
    """Feature: Confirmation gate rejection path in _run_tool_block."""

    def test_gate_rejection_returns_error_result_and_increments_blocked(self):
        """
        Given a computer tool_use block whose action the filter permits
        And the confirmation gate rejects the action (returns False)
        When _run_tool_block is called
        Then the returned tool result carries is_error=True
        And the content indicates the action was rejected by the gate
        And actions_blocked is incremented by one
        And the abort flag is False (stuck policy is not triggered)
        """
        block = MagicMock()
        block.type = "tool_use"
        block.name = "computer"
        block.id = "gate-reject-tool-1"
        block.input = {"action": "left_click", "coordinate": [300, 400]}

        mock_gate = MagicMock()
        mock_gate.check.return_value = False

        ctx = _make_iteration_context(gate=mock_gate)
        result = LoopResult()

        tool_result, abort = _run_tool_block(block, ctx, result)

        assert abort is False, "gate rejection must not set the stuck-abort flag"
        assert result.actions_blocked == 1
        assert tool_result is not None
        assert tool_result.get("is_error") is True
        assert "rejected" in tool_result["content"].lower()

    def test_gate_rejection_does_not_execute_tool(self):
        """
        Given the gate rejects a computer action
        When _run_tool_block is called
        Then the display toolkit execute method is never called
        And actions_taken remains zero
        """
        block = MagicMock()
        block.type = "tool_use"
        block.name = "computer"
        block.id = "gate-reject-tool-2"
        block.input = {"action": "right_click", "coordinate": [10, 20]}

        mock_gate = MagicMock()
        mock_gate.check.return_value = False
        mock_display = MagicMock(spec=DisplayToolkit)

        ctx = _make_iteration_context(gate=mock_gate, display=mock_display)
        result = LoopResult()

        _run_tool_block(block, ctx, result)

        mock_display.execute.assert_not_called()
        assert result.actions_taken == 0


class TestRunToolBlockStuckAbort:
    """Feature: Stuck-policy abort path in _run_tool_block."""

    def test_stuck_policy_abort_sets_abort_flag(self):
        """
        Given a computer tool_use block with a click action
        And the action filter and gate both allow the action
        And the display returns a screenshot in the tool result
        And the screenshot tracker records the frame as stuck
        And the stuck policy decides the loop must abort
        When _run_tool_block is called
        Then the returned abort flag is True
        And the tool result is still returned for message history continuity
        """
        block = MagicMock()
        block.type = "tool_use"
        block.name = "computer"
        block.id = "stuck-abort-tool-1"
        block.input = {"action": "left_click", "coordinate": [50, 50]}

        mock_screenshot_tracker = MagicMock()
        mock_screenshot_tracker.record.return_value = True
        mock_screenshot_tracker.stuck_count = 3

        mock_stuck_policy = MagicMock()
        mock_stuck_policy.should_abort.return_value = True

        mock_display = MagicMock(spec=DisplayToolkit)
        mock_display.execute.return_value = ActionResult(success=True)
        mock_display.take_screenshot.return_value = ActionResult(
            success=True, screenshot_b64="dGVzdA=="
        )

        ctx = _make_iteration_context(
            screenshot_tracker=mock_screenshot_tracker,
            stuck_policy=mock_stuck_policy,
            display=mock_display,
        )
        result = LoopResult()

        tool_result, abort = _run_tool_block(block, ctx, result)

        assert abort is True, "stuck policy abort must set abort_stuck=True"
        assert tool_result is not None, "tool result must still be returned"

    def test_stuck_policy_not_triggered_when_should_abort_false(self):
        """
        Given the screenshot tracker detects repeated frames
        And the stuck policy decides not to abort yet
        When _run_tool_block is called
        Then the abort flag is False
        """
        block = MagicMock()
        block.type = "tool_use"
        block.name = "computer"
        block.id = "stuck-no-abort-tool-1"
        block.input = {"action": "left_click", "coordinate": [5, 5]}

        mock_screenshot_tracker = MagicMock()
        mock_screenshot_tracker.record.return_value = True
        mock_screenshot_tracker.stuck_count = 1

        mock_stuck_policy = MagicMock()
        mock_stuck_policy.should_abort.return_value = False

        mock_display = MagicMock(spec=DisplayToolkit)
        mock_display.execute.return_value = ActionResult(success=True)
        mock_display.take_screenshot.return_value = ActionResult(
            success=True, screenshot_b64="dGVzdA=="
        )

        ctx = _make_iteration_context(
            screenshot_tracker=mock_screenshot_tracker,
            stuck_policy=mock_stuck_policy,
            display=mock_display,
        )
        result = LoopResult()

        _, abort = _run_tool_block(block, ctx, result)

        assert abort is False


class TestProcessIterationBudgetExceeded:
    """Feature: Budget-exceeded early return in _process_iteration."""

    def test_budget_exceeded_returns_stop_reason_without_api_call(self):
        """
        Given an IterationContext whose cost tracker reports budget_exceeded=True
        When _process_iteration is called
        Then it returns the string "budget_exceeded" immediately
        And the Anthropic API client is never called
        """
        mock_cost_tracker = MagicMock()
        mock_cost_tracker.budget_exceeded = True
        mock_cost_tracker.summary.return_value = "Cost: $1.00 / budget: $0.50"

        mock_client = MagicMock()

        ctx = _make_iteration_context(cost_tracker=mock_cost_tracker)
        client_setup = ClientSetup(
            client=mock_client,
            tools=[],
            beta_flag="computer-use-2025-11-24",
        )
        messages: list = [{"role": "user", "content": "do a thing"}]
        result = LoopResult()

        stop_reason = _process_iteration(ctx, client_setup, messages, result)

        assert stop_reason == "budget_exceeded"
        mock_client.beta.messages.create.assert_not_called()

    def test_budget_not_exceeded_proceeds_to_api(self):
        """
        Given cost_tracker.budget_exceeded is False
        And the client returns a response with no tool blocks
        When _process_iteration is called
        Then it does not short-circuit and calls the API
        """
        mock_cost_tracker = MagicMock()
        mock_cost_tracker.budget_exceeded = False
        mock_cost_tracker.summary.return_value = ""

        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = []
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.beta.messages.create.return_value = mock_response

        ctx = _make_iteration_context(cost_tracker=mock_cost_tracker)
        client_setup = ClientSetup(
            client=mock_client,
            tools=[],
            beta_flag="computer-use-2025-11-24",
        )
        messages: list = [{"role": "user", "content": "do a thing"}]
        result = LoopResult()

        stop_reason = _process_iteration(ctx, client_setup, messages, result)

        mock_client.beta.messages.create.assert_called_once()
        assert stop_reason == "completed"
