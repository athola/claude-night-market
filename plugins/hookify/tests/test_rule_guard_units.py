"""Direct unit tests for rule_guard's two pure decision functions.

``test_rule_guard_hook.py`` drives the hook through a subprocess, which
is the right shape for the end-to-end contract and reports 0% line
coverage for the module. These tests import the module's pure decision
functions and exercise the branches the subprocess suite never reaches:
the MultiEdit context mapping, a transcript path that does not exist, a
``tool_input`` that is not a dict, stdin that is not a JSON object, and
each of decide's output shapes.

Nothing is mocked. ``classify`` and ``decide`` take a payload and a
result list, so the real functions run against real inputs. The two
boundaries are stubbed where they are unavoidable: the transcript tail
reads a tmp_path file, and ``_read_payload`` reads a StringIO stdin.

``main()`` is deliberately left to the subprocess suite, which is where
the ConfigLoader and stdout wiring is worth exercising whole.
"""

from __future__ import annotations

import importlib
import io
import sys
from pathlib import Path

import pytest

from hookify.core.config_loader import RuleConfig
from hookify.core.rule_engine import RuleEngine, RuleResult

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "hooks"))

# Imported through importlib because the hooks directory only joins
# sys.path on the line above; a plain import statement here is an E402.
rule_guard = importlib.import_module("rule_guard")


def _result(action: str, message: str, name: str = "r") -> RuleResult:
    """Build a matched RuleResult carrying the given action."""
    rule = RuleConfig(name=name, enabled=True, event="bash", pattern="x", action=action)
    return RuleResult(matched=True, rule=rule, action=action, message=message)


class TestClassifyMapsPayloadsOntoHookifyEvents:
    """
    Feature: hook payload to hookify event mapping

    As the hookify runtime
    I want every registered Claude Code event mapped onto one hookify
    event and its documented context fields
    So that a rule written against those fields sees them populated.
    """

    def test_multiedit_joins_every_edit_into_one_text_pair(self) -> None:
        """
        GIVEN a MultiEdit payload carrying three edits
        WHEN classify maps it onto the file event
        THEN new_text and old_text are the newline-joined halves

        The Write and Edit branches read a single field each, so a
        MultiEdit branch that read only ``edits[0]`` would pass every
        existing test while letting a rule miss the second and third
        edit of a batch.
        """
        payload = {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": "/repo/a.py",
                "edits": [
                    {"old_string": "one", "new_string": "ONE"},
                    {"old_string": "two", "new_string": "TWO"},
                    {"old_string": "three", "new_string": "THREE"},
                ],
            },
        }

        event, context = rule_guard.classify(payload)

        assert event == "file"
        assert context["new_text"] == "ONE\nTWO\nTHREE"
        assert context["old_text"] == "one\ntwo\nthree"
        assert context["content"] == context["new_text"]
        assert context["file_path"] == "/repo/a.py"

    def test_write_maps_content_onto_new_text_with_no_old_text(self) -> None:
        """
        GIVEN a Write payload
        WHEN classify maps it onto the file event
        THEN new_text and content hold the body and old_text is empty

        A Write has no prior text, so a rule matching on old_text must
        see the empty string rather than the body it is replacing.
        """
        _, context = rule_guard.classify(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": "/repo/new.md", "content": "body"},
            }
        )

        assert context["new_text"] == "body"
        assert context["content"] == "body"
        assert context["old_text"] == ""

    def test_edit_keeps_both_halves_of_the_replacement(self) -> None:
        """
        GIVEN an Edit payload
        WHEN classify maps it onto the file event
        THEN old_string and new_string land in old_text and new_text

        Rules that fire on removal (a deleted safety check) read
        old_text, and rules that fire on insertion read new_text, so
        swapping the two inverts every such rule.
        """
        _, context = rule_guard.classify(
            {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": "/repo/a.py",
                    "old_string": "before",
                    "new_string": "after",
                },
            }
        )

        assert context["old_text"] == "before"
        assert context["new_text"] == "after"

    def test_multiedit_with_no_edits_yields_empty_text(self) -> None:
        """
        GIVEN a MultiEdit payload whose edits list is absent
        WHEN classify maps it onto the file event
        THEN both text fields are empty strings rather than None

        Every rule condition calls a string operator on these fields,
        so None here is an AttributeError inside the engine.
        """
        event, context = rule_guard.classify(
            {"tool_name": "MultiEdit", "tool_input": {"file_path": "/repo/a.py"}}
        )

        assert event == "file"
        assert context["new_text"] == ""
        assert context["old_text"] == ""

    @pytest.mark.parametrize(
        "tool_input",
        ["a string", ["a", "list"], None, 7],
        ids=["str", "list", "none", "int"],
    )
    def test_non_dict_tool_input_still_yields_empty_context(
        self, tool_input: object
    ) -> None:
        """
        GIVEN a Bash payload whose tool_input is not a dict
        WHEN classify runs
        THEN the command is the empty string and nothing raises

        A malformed payload must pass the event through, not crash the
        hook: the module docstring makes a crashed guard the one
        outcome that is never acceptable.
        """
        event, context = rule_guard.classify(
            {"tool_name": "Bash", "tool_input": tool_input}
        )

        assert event == "bash"
        assert context == {"command": ""}

    def test_unregistered_tool_passes_through(self) -> None:
        """
        GIVEN a tool outside the registered set
        WHEN classify runs
        THEN it returns None so main prints an empty decision
        """
        assert rule_guard.classify({"tool_name": "Read", "tool_input": {}}) is None

    def test_prompt_event_carries_the_user_prompt(self) -> None:
        """
        GIVEN a UserPromptSubmit payload
        WHEN classify runs
        THEN the prompt event carries the prompt text
        """
        assert rule_guard.classify(
            {"hook_event_name": "UserPromptSubmit", "prompt": "do the thing"}
        ) == ("prompt", {"user_prompt": "do the thing"})

    def test_second_stop_in_a_row_passes_through(self) -> None:
        """
        GIVEN a Stop payload flagged stop_hook_active
        WHEN classify runs
        THEN it returns None

        The session already continued once on this hook's say-so, and a
        second block is an infinite loop.
        """
        assert (
            rule_guard.classify(
                {
                    "hook_event_name": "Stop",
                    "stop_hook_active": True,
                    "transcript_path": "/does/not/matter",
                }
            )
            is None
        )

    def test_missing_transcript_yields_empty_context_and_a_stderr_line(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """
        GIVEN a Stop payload whose transcript_path does not exist
        WHEN classify runs
        THEN the transcript is empty and the reason reaches stderr

        stderr is the only channel that separates "no rule matched"
        from "the hook could not read its input", and the module
        docstring commits to writing on it.
        """
        event, context = rule_guard.classify(
            {"hook_event_name": "Stop", "transcript_path": "/no/such/transcript.jsonl"}
        )

        assert event == "stop"
        assert context == {"transcript": ""}
        assert "cannot read transcript" in capsys.readouterr().err

    def test_stop_reads_only_the_transcript_tail(self, tmp_path: Path) -> None:
        """
        GIVEN a transcript larger than the tail budget
        WHEN classify runs
        THEN only the last _TRANSCRIPT_TAIL_BYTES reach the context

        The whole file runs to megabytes, and a stop rule that scanned
        all of it would spend the session's time on history no rule
        asks about.
        """
        transcript = tmp_path / "transcript.jsonl"
        head = "A" * (rule_guard._TRANSCRIPT_TAIL_BYTES * 2)
        transcript.write_text(head + "TAILMARKER", encoding="utf-8")

        _, context = rule_guard.classify(
            {"hook_event_name": "Stop", "transcript_path": str(transcript)}
        )

        assert context["transcript"].endswith("TAILMARKER")
        assert len(context["transcript"]) == rule_guard._TRANSCRIPT_TAIL_BYTES


class TestReadPayloadRefusesWhatItCannotUse:
    """
    Feature: stdin to payload

    As the hookify runtime
    I want unusable stdin turned into a pass rather than a crash
    So that a malformed event never ends the session.
    """

    @pytest.mark.parametrize(
        "raw",
        ["", "   \n  ", "{not json", '"a bare string"', "[1, 2, 3]", "null"],
        ids=["empty", "whitespace", "malformed", "string", "list", "null"],
    )
    def test_unusable_stdin_yields_none(
        self, raw: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        GIVEN stdin carrying no payload, broken JSON, or valid JSON
              that is not an object
        WHEN _read_payload runs
        THEN it returns None so the event passes untouched

        Returning the parsed non-dict instead would push a string or a
        list into classify, where every ``.get`` is an AttributeError
        and the hook dies mid-event.
        """
        monkeypatch.setattr(rule_guard.sys, "stdin", io.StringIO(raw))

        assert rule_guard._read_payload() is None

    def test_malformed_json_reports_the_parse_error_on_stderr(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        """
        GIVEN stdin carrying broken JSON
        WHEN _read_payload runs
        THEN the decoder's complaint reaches stderr

        Silence here is indistinguishable from a clean pass, which is
        how a payload-shape regression survives a release.
        """
        monkeypatch.setattr(rule_guard.sys, "stdin", io.StringIO("{not json"))

        rule_guard._read_payload()

        assert "malformed stdin JSON" in capsys.readouterr().err

    def test_a_json_object_is_returned_as_the_payload(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        GIVEN stdin carrying a JSON object
        WHEN _read_payload runs
        THEN that object is returned unchanged
        """
        monkeypatch.setattr(
            rule_guard.sys, "stdin", io.StringIO('{"tool_name": "Bash"}')
        )

        assert rule_guard._read_payload() == {"tool_name": "Bash"}


class TestDecideShapesTheDecisionPerEvent:
    """
    Feature: matched rules to Claude Code decision JSON

    As the hookify runtime
    I want each event's decision written in the shape that event
    accepts
    So that a block rule actually denies the call it matched.
    """

    def test_no_matches_produces_an_empty_decision(self) -> None:
        """
        GIVEN no rule matched
        WHEN decide runs
        THEN the decision is empty and the event proceeds
        """
        engine = RuleEngine([])

        assert rule_guard.decide("bash", [], engine) == {}

    @pytest.mark.parametrize("event", ["prompt", "stop"])
    def test_blocking_rule_on_a_session_event_uses_the_decision_key(
        self, event: str
    ) -> None:
        """
        GIVEN a matched block rule on the prompt or stop event
        WHEN decide runs
        THEN the output uses decision/reason, not permissionDecision

        These two events do not accept hookSpecificOutput, so emitting
        the tool shape here blocks nothing at all.
        """
        engine = RuleEngine([])

        decision = rule_guard.decide(event, [_result("block", "stop that")], engine)

        assert decision["decision"] == "block"
        assert "stop that" in decision["reason"]
        assert "hookSpecificOutput" not in decision

    def test_blocking_rule_on_a_tool_event_denies_the_call(self) -> None:
        """
        GIVEN a matched block rule on a tool event
        WHEN decide runs
        THEN the PreToolUse deny shape carries the formatted message
        """
        engine = RuleEngine([])

        decision = rule_guard.decide(
            "bash", [_result("block", "no frobnicate")], engine
        )

        specific = decision["hookSpecificOutput"]
        assert specific["hookEventName"] == "PreToolUse"
        assert specific["permissionDecision"] == "deny"
        assert "no frobnicate" in specific["permissionDecisionReason"]

    @pytest.mark.parametrize("event", ["bash", "file", "prompt", "stop"])
    def test_warn_only_matches_attach_a_system_message_on_every_event(
        self, event: str
    ) -> None:
        """
        GIVEN matched rules that all warn
        WHEN decide runs
        THEN the decision is a systemMessage and nothing is denied

        A warn rule that reached the deny branch would turn advice into
        a hard stop, which is the failure a user notices first.
        """
        engine = RuleEngine([])

        decision = rule_guard.decide(event, [_result("warn", "heads up")], engine)

        assert "heads up" in decision["systemMessage"]
        assert "decision" not in decision
        assert "hookSpecificOutput" not in decision

    def test_one_blocking_rule_among_warnings_still_blocks(self) -> None:
        """
        GIVEN a warn rule and a block rule both matched
        WHEN decide runs
        THEN the call is denied and both messages are reported

        Order must not decide this: a block that lost to an earlier
        warn would silently downgrade the strictest rule in the
        catalog.
        """
        engine = RuleEngine([])

        decision = rule_guard.decide(
            "file",
            [_result("warn", "soft note", "w"), _result("block", "hard stop", "b")],
            engine,
        )

        reason = decision["hookSpecificOutput"]["permissionDecisionReason"]
        assert decision["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "hard stop" in reason
        assert "soft note" in reason
