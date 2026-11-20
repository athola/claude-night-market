"""Tests for scripts/session_cost.py, the session spend ledger.

Feature: show where a Claude Code session's spend went

    As a user deciding whether to compress tool output
    I want the spend split into cache writes, cache reads and output,
    and the re-read cost of each tool result
    So that I compress what costs money, not what merely has many tokens

Billed-run studies found token and cost reduction weakly correlated
(arXiv 2607.12161, r = 0.15) because cache creation and reads dominate.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "session_cost.py"


@pytest.fixture(scope="module")
def ledger():
    spec = importlib.util.spec_from_file_location("session_cost", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assistant(
    msg_id: str,
    *,
    model: str = "claude-sonnet-4-6",
    tool_uses: tuple[tuple[str, str], ...] = (),
    **counts: int,
) -> str:
    inp, read, out = counts.get("inp", 0), counts.get("read", 0), counts.get("out", 0)
    write_5m, write_1h = counts.get("write_5m", 0), counts.get("write_1h", 0)
    usage = {
        "input_tokens": inp,
        "cache_creation_input_tokens": write_5m + write_1h,
        "cache_read_input_tokens": read,
        "output_tokens": out,
        "cache_creation": {
            "ephemeral_5m_input_tokens": write_5m,
            "ephemeral_1h_input_tokens": write_1h,
        },
    }
    content = [{"type": "tool_use", "id": tid, "name": name} for tid, name in tool_uses]
    return json.dumps(
        {
            "type": "assistant",
            "message": {
                "id": msg_id,
                "model": model,
                "usage": usage,
                "content": content,
            },
        }
    )


def _tool_result(tool_use_id: str, text: str) -> str:
    return json.dumps(
        {
            "type": "user",
            "message": {
                "content": [
                    {"type": "tool_result", "tool_use_id": tool_use_id, "content": text}
                ]
            },
        }
    )


COMPACT = json.dumps({"type": "system", "subtype": "compact_boundary"})


class TestUsageTotals:
    """Usage is summed once per request and weighted by category."""

    def test_a_message_logged_once_per_content_block_is_counted_once(
        self, ledger
    ) -> None:
        """A repeated message counts once.

        GIVEN one assistant message written three times, as Claude Code does
        WHEN the ledger sums usage
        THEN it counts that message's usage once.
        """
        line = _assistant("m1", inp=10, read=1_000, out=50)
        report = ledger.summarize([line, line, line])

        assert report["requests"] == 1
        assert report["tokens"]["cache_read"] == 1_000
        assert report["tokens"]["output"] == 50

    def test_categories_are_weighted_in_base_input_units(self, ledger) -> None:
        """Each category is weighted by its price multiple.

        GIVEN a Sonnet 4.6 request with every category
        WHEN weighted
        THEN 5m writes cost 1.25x, 1h writes 2x, reads 0.1x, output 5x.
        """
        line = _assistant(
            "m1", inp=100, write_5m=400, write_1h=100, read=10_000, out=20
        )
        units = ledger.summarize([line])["units"]

        assert units == {
            "input": 100,
            "cache_write_5m": 500,
            "cache_write_1h": 200,
            "cache_read": 1_000,
            "output": 100,
        }

    def test_shares_sum_to_one(self, ledger) -> None:
        """Shares are fractions of the weighted total, not of raw tokens."""
        line = _assistant("m1", inp=100, write_1h=100, read=10_000, out=20)
        shares = ledger.summarize([line])["shares"]

        assert sum(shares.values()) == pytest.approx(1.0)
        assert shares["cache_read"] == pytest.approx(1_000 / 1_400)

    @pytest.mark.parametrize(
        ("model", "rate"),
        [
            ("claude-fable-5-2", 0.025),
            ("claude-mythos-5-1", 0.025),
            ("claude-opus-5-5", 0.05),
            ("claude-sonnet-5-5", 0.05),
            ("claude-opus-5", 0.1),
            ("claude-haiku-4-5", 0.1),
            ("some-future-model", 0.1),
        ],
    )
    def test_cache_reads_use_the_model_rate(self, ledger, model, rate) -> None:
        """Cache reads are 0.1x on most models and lower on a few."""
        line = _assistant("m1", model=model, read=1_000)
        assert ledger.summarize([line])["units"]["cache_read"] == pytest.approx(
            1_000 * rate
        )

    def test_writes_without_a_split_count_as_5m(self, ledger) -> None:
        """Older usage records carry no 5m/1h split. The cheaper rate is assumed."""
        raw = json.loads(_assistant("m1", write_5m=0, write_1h=0))
        raw["message"]["usage"] = {"cache_creation_input_tokens": 80}
        report = ledger.summarize([json.dumps(raw)])

        assert report["tokens"]["cache_write_5m"] == 80

    def test_malformed_and_foreign_lines_are_skipped_and_counted(self, ledger) -> None:
        """A torn or non-object line is reported, not fatal. A blank line is ignored."""
        lines = ["not json", "[1, 2]", "", _assistant("m1", out=5)]
        report = ledger.summarize(lines)

        assert report["requests"] == 1
        assert report["skipped_lines"] == 2

    def test_an_empty_transcript_reports_zeros(self, ledger) -> None:
        """No requests means no shares to divide, rather than a ZeroDivisionError."""
        report = ledger.summarize([])

        assert report["requests"] == 0
        assert report["shares"] == {}
        assert report["top_tool_results"] == []


class TestToolResultRereads:
    """A tool result costs a cache read on every request that resends it."""

    def test_reread_cost_counts_only_requests_after_the_first_send(
        self, ledger
    ) -> None:
        """Re-reads start after the request that first sends a result.

        GIVEN a 4,000-char Read result followed by three requests
        WHEN costed
        THEN the first request writes it and the next two re-read it:
        1,000 tokens x 2 reads x 0.1.
        """
        lines = [
            _assistant("m0", tool_uses=(("t1", "Read"),)),
            _tool_result("t1", "x" * 4_000),
            _assistant("m1"),
            _assistant("m2"),
            _assistant("m3"),
        ]
        top = ledger.summarize(lines)["top_tool_results"]

        assert top == [
            {
                "tool": "Read",
                "tokens": 1_000,
                "rereads": 2,
                "reread_units": pytest.approx(200.0),
            }
        ]

    def test_a_compaction_ends_the_rereads(self, ledger) -> None:
        """After compact_boundary the old results are no longer in the prompt."""
        lines = [
            _assistant("m0", tool_uses=(("t1", "Bash"),)),
            _tool_result("t1", "y" * 400),
            _assistant("m1"),
            _assistant("m2"),
            COMPACT,
            _assistant("m3"),
            _assistant("m4"),
        ]
        top = ledger.summarize(lines)["top_tool_results"]

        assert top[0]["rereads"] == 1

    def test_results_are_ranked_by_reread_cost_and_capped(self, ledger) -> None:
        """Ranking is by re-read cost; totals still cover every result."""
        lines = [
            _assistant("m0", tool_uses=(("a", "Grep"), ("b", "Bash"), ("c", "Read"))),
            _tool_result("a", "a" * 400),
            _tool_result("b", "b" * 40_000),
            _tool_result("c", "c" * 4_000),
            _assistant("m1"),
            _assistant("m2"),
        ]
        report = ledger.summarize(lines, top=2)

        assert [row["tool"] for row in report["top_tool_results"]] == ["Bash", "Read"]
        assert report["tool_results"]["count"] == 3
        assert report["tool_results"]["tokens"] == 11_100

    def test_text_blocks_in_a_list_result_are_counted(self, ledger) -> None:
        """Only text blocks count toward size; image data is not prompt text."""
        raw = json.loads(_tool_result("t1", ""))
        raw["message"]["content"][0]["content"] = [
            {"type": "text", "text": "z" * 800},
            {"type": "image", "source": {"data": "ignored"}},
        ]
        lines = [_assistant("m0", tool_uses=(("t1", "Read"),)), json.dumps(raw)]

        assert ledger.summarize(lines)["tool_results"]["tokens"] == 200


class TestCommandLine:
    """The script prints a table or JSON and fails cleanly."""

    def test_json_flag_prints_the_report(self, ledger, tmp_path, capsys) -> None:
        """--json prints the same report summarize() returns."""
        transcript = tmp_path / "s.jsonl"
        transcript.write_text(_assistant("m1", read=1_000, out=10) + "\n")

        assert ledger.main([str(transcript), "--json"]) == 0
        assert json.loads(capsys.readouterr().out)["requests"] == 1

    def test_table_names_each_category_and_the_reread_share(
        self, ledger, tmp_path, capsys
    ) -> None:
        """The default table labels every category and the re-read share."""
        transcript = tmp_path / "s.jsonl"
        transcript.write_text(
            "\n".join(
                [
                    _assistant("m0", read=500, tool_uses=(("t1", "Read"),)),
                    _tool_result("t1", "x" * 4_000),
                    _assistant("m1", read=1_500),
                    _assistant("m2", read=2_500),
                ]
            )
        )

        assert ledger.main([str(transcript)]) == 0
        out = capsys.readouterr().out
        for label in ("cache read", "cache write", "output", "Read"):
            assert label in out
        assert "re-reading tool results" in out

    def test_a_missing_file_exits_2(self, ledger, tmp_path, capsys) -> None:
        """An unreadable transcript is a usage error on stderr, exit 2."""
        assert ledger.main([str(tmp_path / "absent.jsonl")]) == 2
        assert "absent.jsonl" in capsys.readouterr().err


# Probe-shaped Cursor transcript (cursor-agent 2026.11.19): role and message
# only, with no usage and no tool results.
_CURSOR_TRANSCRIPT = [
    json.dumps(
        {"role": "user", "message": {"content": [{"type": "text", "text": "q"}]}}
    ),
    json.dumps(
        {
            "role": "assistant",
            "message": {
                "content": [{"type": "tool_use", "name": "Shell", "input": {}}]
            },
        }
    ),
    json.dumps({"type": "turn_ended", "status": "success"}),
]


class TestCursorTranscripts:
    """Cursor transcripts carry no usage, which must be said, not shown as zero."""

    def test_a_cursor_transcript_is_named(self, ledger) -> None:
        """A zero-request report from a Cursor file would read as a free session."""
        report = ledger.summarize(_CURSOR_TRANSCRIPT)

        assert report["format"] == "cursor"
        assert report["requests"] == 0

    def test_a_claude_transcript_is_named(self, ledger) -> None:
        """Format is reported for every transcript, so --json readers can branch."""
        assert ledger.summarize([_assistant("m1", out=1)])["format"] == "claude"

    def test_the_table_points_a_cursor_user_at_the_dashboard(
        self, ledger, tmp_path, capsys
    ) -> None:
        """The table says why there is nothing to count and where usage lives."""
        transcript = tmp_path / "cursor.jsonl"
        transcript.write_text("\n".join(_CURSOR_TRANSCRIPT))

        assert ledger.main([str(transcript)]) == 0
        out = capsys.readouterr().out
        assert "Cursor" in out
        assert "usage" in out.lower()
        assert "cache read" not in out
