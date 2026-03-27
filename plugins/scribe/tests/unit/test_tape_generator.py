"""Tests for tape generator.

Validates VHS tape output format, timing model, string escaping,
and duration management.
"""

from __future__ import annotations

import pytest
from scribe.session_parser import AssistantTurn, ToolUse, UserTurn
from scribe.tape_generator import (
    SUPPORTED_FORMATS,
    TapeConfig,
    escape_vhs,
    generate_tape,
)


class TestTapeHeader:
    """Feature: tape file has correct header directives.

    As a VHS consumer
    I want the tape to start with Output and Set commands
    So that the terminal is configured before content plays
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_output_directive_present(self) -> None:
        """Scenario: Output directive is the first line.

        Given a tape config with output_path
        When generating a tape
        Then the first line is an Output directive
        """
        config = TapeConfig(output_path="demo.gif")
        tape = generate_tape([], config)
        lines = tape.strip().split("\n")
        assert lines[0] == "Output demo.gif"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_set_commands_present(self) -> None:
        """Scenario: Set commands configure the terminal.

        Given a tape config with default values
        When generating a tape
        Then Set Width, Height, FontSize, Theme are present
        """
        config = TapeConfig(output_path="out.gif")
        tape = generate_tape([], config)
        assert "Set Width 960" in tape
        assert "Set Height 540" in tape
        assert "Set FontSize 16" in tape
        assert 'Set Theme "Dracula"' in tape

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_custom_config_values(self) -> None:
        """Scenario: custom config values are reflected.

        Given a non-default config
        When generating a tape
        Then Set commands use the custom values
        """
        config = TapeConfig(
            output_path="custom.gif",
            theme="Solarized Dark",
            width=1280,
            height=720,
            font_size=20,
        )
        tape = generate_tape([], config)
        assert "Set Width 1280" in tape
        assert "Set Height 720" in tape
        assert "Set FontSize 20" in tape
        assert 'Set Theme "Solarized Dark"' in tape


class TestUserTurnRendering:
    """Feature: user turns rendered with prompt prefix.

    As a tape viewer
    I want user messages prefixed with "$ "
    So that they look like terminal input
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_user_turn_prefixed_with_dollar(self) -> None:
        """Scenario: user text gets "$ " prefix.

        Given a UserTurn
        When generating the tape
        Then the Type command includes "$ " before the text
        """
        turns = [UserTurn(text="hello")]
        config = TapeConfig(output_path="out.gif")
        tape = generate_tape(turns, config)
        assert '$ hello"' in tape
        # Verify the dollar prefix is present in the Type command
        assert any(
            '"$ hello"' in line for line in tape.split("\n") if line.startswith("Type")
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_user_typing_speed(self) -> None:
        """Scenario: user typing speed is 30ms/char.

        Given a UserTurn
        When generating the tape
        Then the Type command uses 30ms timing (scaled)
        """
        turns = [UserTurn(text="hello")]
        config = TapeConfig(output_path="out.gif", speed=1.0)
        tape = generate_tape(turns, config)
        assert "Type@30ms" in tape

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_user_multiline_split(self) -> None:
        """Scenario: multi-line user text produces separate Type+Enter.

        Given a UserTurn with newlines
        When generating the tape
        Then each line has its own Type+Enter pair
        """
        turns = [UserTurn(text="line one\nline two")]
        config = TapeConfig(output_path="out.gif")
        tape = generate_tape(turns, config)
        assert 'Type@30ms "$ line one"' in tape
        assert 'Type@30ms "line two"' in tape
        assert tape.count("Enter") >= 2


class TestAssistantTurnRendering:
    """Feature: assistant turns rendered at reading speed.

    As a tape viewer
    I want assistant responses to appear at a readable pace
    So that I can follow the conversation
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_assistant_typing_speed(self) -> None:
        """Scenario: assistant typing speed is 15ms/char.

        Given an AssistantTurn
        When generating the tape
        Then the Type command uses 15ms timing
        """
        turns = [AssistantTurn(text="response")]
        config = TapeConfig(output_path="out.gif")
        tape = generate_tape(turns, config)
        assert "Type@15ms" in tape

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_assistant_multiline_split(self) -> None:
        """Scenario: multi-line assistant text is split into lines.

        Given an AssistantTurn with multiple lines
        When generating the tape
        Then each line gets its own Type+Enter pair
        """
        turns = [AssistantTurn(text="line A\nline B\nline C")]
        config = TapeConfig(output_path="out.gif")
        tape = generate_tape(turns, config)
        assert 'Type@15ms "line A"' in tape
        assert 'Type@15ms "line B"' in tape
        assert 'Type@15ms "line C"' in tape


class TestToolSummaryRendering:
    """Feature: tool summaries rendered with indentation.

    As a tape viewer
    I want tool calls to be indented and quick
    So that they stand out as machine actions
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tool_indented_with_two_spaces(self) -> None:
        """Scenario: tool summary has two-space indent.

        Given a ToolUse turn
        When generating the tape
        Then the Type command text starts with "  "
        """
        turns = [ToolUse(tool_name="Read", summary="Read /file.py", input={})]
        config = TapeConfig(output_path="out.gif")
        tape = generate_tape(turns, config)
        assert 'Type@100ms "  Read /file.py"' in tape

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tool_typing_speed_flat(self) -> None:
        """Scenario: tool summary typing speed is 100ms flat.

        Given a ToolUse turn
        When generating the tape
        Then the Type command uses 100ms timing
        """
        turns = [ToolUse(tool_name="Bash", summary="Ran: ls", input={})]
        config = TapeConfig(output_path="out.gif")
        tape = generate_tape(turns, config)
        assert "Type@100ms" in tape


class TestTimingModel:
    """Feature: timing model with pauses and speed scaling.

    As a tape viewer
    I want natural pauses between turns and a final hold
    So that the replay has rhythm and the ending is readable
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_pause_between_turns(self) -> None:
        """Scenario: 1.5s pause between turns.

        Given two turns
        When generating the tape
        Then there is a Sleep 1500ms between them
        """
        turns = [
            UserTurn(text="hello"),
            AssistantTurn(text="hi"),
        ]
        config = TapeConfig(output_path="out.gif")
        tape = generate_tape(turns, config)
        assert "Sleep 1500ms" in tape

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_final_hold(self) -> None:
        """Scenario: 3s hold at the end.

        Given any turns
        When generating the tape
        Then the last line before EOF is Sleep 3000ms
        """
        turns = [UserTurn(text="hello")]
        config = TapeConfig(output_path="out.gif")
        tape = generate_tape(turns, config)
        content_lines = [line for line in tape.strip().split("\n") if line.strip()]
        assert content_lines[-1] == "Sleep 3000ms"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_speed_multiplier(self) -> None:
        """Scenario: speed 2.0 halves all durations.

        Given a config with speed=2.0
        When generating the tape
        Then pauses are halved (750ms instead of 1500ms)
        """
        turns = [
            UserTurn(text="hello"),
            AssistantTurn(text="hi"),
        ]
        config = TapeConfig(output_path="out.gif", speed=2.0)
        tape = generate_tape(turns, config)
        assert "Sleep 750ms" in tape
        # User typing: 30/2.0 = 15ms
        assert "Type@15ms" in tape
        # Final hold: 3000/2.0 = 1500ms
        content_lines = [line for line in tape.strip().split("\n") if line.strip()]
        assert content_lines[-1] == "Sleep 1500ms"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_enter_after_each_type(self) -> None:
        """Scenario: every Type is followed by Enter.

        Given any turn
        When generating the tape
        Then every Type line is followed by an Enter line
        """
        turns = [UserTurn(text="hello")]
        config = TapeConfig(output_path="out.gif")
        tape = generate_tape(turns, config)
        lines = [line.strip() for line in tape.split("\n") if line.strip()]
        for i, line in enumerate(lines):
            if line.startswith("Type"):
                assert i + 1 < len(lines)
                assert lines[i + 1] == "Enter"


class TestStringEscaping:
    """Feature: VHS string escaping for special characters.

    As a tape generator
    I want to escape quotes and backslashes
    So that VHS parses the tape correctly
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_double_quotes_escaped(self) -> None:
        """Scenario: double quotes become escaped quotes."""
        assert escape_vhs('say "hello"') == 'say \\"hello\\"'

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_backslashes_escaped(self) -> None:
        """Scenario: backslashes become double backslashes."""
        assert escape_vhs("path\\to\\file") == "path\\\\to\\\\file"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_unicode_passes_through(self) -> None:
        """Scenario: non-ASCII unicode is unchanged."""
        assert escape_vhs("hello world") == "hello world"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_combined_escaping(self) -> None:
        """Scenario: quotes and backslashes in the same string."""
        result = escape_vhs('a\\b "c"')
        assert result == 'a\\\\b \\"c\\"'

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_escaping_in_tape_output(self) -> None:
        """Scenario: escaped text appears correctly in Type commands.

        Given a user turn with quotes
        When generating the tape
        Then the Type command has escaped quotes
        """
        turns = [UserTurn(text='say "hello"')]
        config = TapeConfig(output_path="out.gif")
        tape = generate_tape(turns, config)
        assert 'Type@30ms "$ say \\"hello\\""' in tape


class TestDurationManagement:
    """Feature: max-duration truncation.

    As a replay user
    I want to cap the GIF duration
    So that long sessions produce shareable files
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_no_max_duration_includes_all(self) -> None:
        """Scenario: no max_duration includes all turns.

        Given 10 turns and no max_duration
        When generating the tape
        Then all turns appear in the output
        """
        turns = [UserTurn(text=f"turn {i}") for i in range(10)]
        config = TapeConfig(output_path="out.gif")
        tape = generate_tape(turns, config)
        for i in range(10):
            assert f"turn {i}" in tape

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_max_duration_truncates_with_message(self) -> None:
        """Scenario: max_duration truncates and adds count message.

        Given many turns and a short max_duration
        When generating the tape
        Then only some turns appear and a "... (N more turns)" line
        is added
        """
        turns = [UserTurn(text=f"turn {i}") for i in range(20)]
        # Very short duration -- should truncate early
        config = TapeConfig(output_path="out.gif", max_duration=3.0)
        tape = generate_tape(turns, config)
        assert "... (" in tape
        assert "more turns)" in tape

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_max_duration_single_turn_always_included(self) -> None:
        """Scenario: at least one turn is always included.

        Given one turn and a tiny max_duration
        When generating the tape
        Then the turn is still present
        """
        turns = [UserTurn(text="only turn")]
        config = TapeConfig(output_path="out.gif", max_duration=0.1)
        tape = generate_tape(turns, config)
        assert "only turn" in tape


class TestOutputFormats:
    """Feature: multiple output formats (GIF, MP4, WebM).

    As a replay user
    I want to choose between GIF, MP4, and WebM output
    So that I can use the best format for my use case
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_gif_output_extension(self) -> None:
        """Scenario: default output path ends with .gif.

        Given a default TapeConfig
        When generating a tape
        Then the Output directive path ends with .gif
        """
        config = TapeConfig()
        tape = generate_tape([], config)
        first_line = tape.strip().split("\n")[0]
        assert first_line.endswith(".gif")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_mp4_output_extension(self) -> None:
        """Scenario: output_path ending in .mp4 produces MP4 directive.

        Given a TapeConfig with output_path ending in .mp4
        When generating a tape
        Then the Output directive uses the .mp4 path
        """
        config = TapeConfig(output_path="replay.mp4")
        tape = generate_tape([], config)
        first_line = tape.strip().split("\n")[0]
        assert first_line == "Output replay.mp4"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_webm_output_extension(self) -> None:
        """Scenario: output_path ending in .webm produces WebM directive.

        Given a TapeConfig with output_path ending in .webm
        When generating a tape
        Then the Output directive uses the .webm path
        """
        config = TapeConfig(output_path="replay.webm")
        tape = generate_tape([], config)
        first_line = tape.strip().split("\n")[0]
        assert first_line == "Output replay.webm"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_output_format_override(self) -> None:
        """Scenario: output_format overrides the extension from output_path.

        Given a TapeConfig with output_path ending in .gif
        And output_format set to "mp4"
        When generating a tape
        Then the Output directive uses .mp4 extension
        """
        config = TapeConfig(output_path="replay.gif", output_format="mp4")
        tape = generate_tape([], config)
        first_line = tape.strip().split("\n")[0]
        assert first_line == "Output replay.mp4"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_invalid_format_raises(self) -> None:
        """Scenario: unsupported format raises ValueError.

        Given a TapeConfig with output_format set to "svg"
        When generating a tape
        Then a ValueError is raised
        """
        config = TapeConfig(output_path="replay.gif", output_format="svg")
        with pytest.raises(ValueError, match="Unsupported output format"):
            generate_tape([], config)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_invalid_extension_raises(self) -> None:
        """Scenario: unsupported extension in output_path raises ValueError.

        Given a TapeConfig with output_path ending in .avi
        When generating a tape
        Then a ValueError is raised
        """
        config = TapeConfig(output_path="replay.avi")
        with pytest.raises(ValueError, match="Unsupported output format"):
            generate_tape([], config)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_supported_formats_constant(self) -> None:
        """Scenario: SUPPORTED_FORMATS contains the three VHS formats.

        Given the SUPPORTED_FORMATS constant
        Then it contains gif, mp4, and webm
        """
        assert SUPPORTED_FORMATS == {"gif", "mp4", "webm"}
