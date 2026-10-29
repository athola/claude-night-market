"""Queue frontmatter stays parseable whatever value a field carries.

Two hooks built their frontmatter with f-strings and each kept its own
``_yaml_scalar``. Only the fields someone remembered to wrap were safe:
``session_id`` went out bare, so a colon or a newline in it produced an
entry no parser reads, which is how 2544 staging captures went dark
(83f1b05e). Every field now goes through one renderer, and these tests
read the result back with the parser the corpus itself uses.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
import research_queue
import web_research_handler

from memory_palace.corpus._frontmatter import parse_entry_frontmatter
from shared.frontmatter import render_frontmatter

HOSTILE_VALUES = [
    '"quoted" and \\ backslash',
    "---",
    "line one\nline two\n---\nkey: injected",
    "key: value",
    "# looks like a comment",
    "trailing colon:",
    "- list item",
    "{flow: mapping}",
    "",
    "yes",
    "null",
    "123",
]

#: Every string field the two writers emit, across all three entry kinds.
STRING_FIELDS = [
    "queue_entry_id",
    "session_type",
    "source_type",
    "topic",
    "status",
    "priority",
    "url",
    "query",
    "content_hash",
    "session_id",
]


def _parse(block: str) -> dict:
    parsed = parse_entry_frontmatter(block + "\n# body\n")
    assert parsed is not None, block
    return parsed


class TestRenderFrontmatter:
    """Feature: one renderer every queue writer uses."""

    @pytest.mark.parametrize("value", HOSTILE_VALUES)
    @pytest.mark.parametrize("field", STRING_FIELDS)
    def test_hostile_string_round_trips(self, field: str, value: str) -> None:
        """A string comes back as the same string, never a new key."""
        assert _parse(render_frontmatter({field: value})) == {field: value}

    def test_scalars_keep_their_parsed_types(self) -> None:
        """Counts stay ints, flags stay bools, timestamps stay datetimes."""
        created = datetime(2026, 9, 28, 10, 0, tzinfo=timezone.utc)
        fields = {
            "created_at": created,
            "content_length": 42,
            "result_count": 0,
            "web_searches": 5,
            "auto_generated": True,
        }

        assert _parse(render_frontmatter(fields)) == fields

    def test_keys_keep_their_order(self) -> None:
        """Reviewers read these by eye, so field order is part of the format."""
        block = render_frontmatter({"b": "1", "a": "2"})

        assert block.splitlines() == ["---", 'b: "1"', 'a: "2"', "---"]

    def test_an_unsupported_type_is_refused(self) -> None:
        """A list would need YAML block syntax this renderer does not write."""
        with pytest.raises(TypeError, match="tags"):
            render_frontmatter({"tags": ["a"]})


class TestWritersUseTheRenderer:
    """Feature: every field each hook writes survives a hostile value."""

    @pytest.fixture(autouse=True)
    def _isolated_queue(self, tmp_path, monkeypatch):
        monkeypatch.setattr(web_research_handler, "QUEUE_DIR", tmp_path)
        monkeypatch.setattr(web_research_handler, "DATA_ROOT", tmp_path)
        monkeypatch.setattr(web_research_handler, "update_index", lambda **_: None)

    @pytest.mark.parametrize("value", HOSTILE_VALUES)
    def test_research_queue_session_and_topic(self, value: str) -> None:
        """``session_id`` went out bare, so a colon in it broke the entry."""
        now = datetime(2026, 9, 28, tzinfo=timezone.utc)

        parsed = _parse_entry(research_queue._render(value, "prompt", 4, value, now))

        assert parsed["topic"] == value
        assert parsed["session_id"] == (value or "unknown")
        assert parsed["web_searches"] == 4
        assert parsed["created_at"] == now

    @pytest.mark.parametrize("value", HOSTILE_VALUES)
    def test_webfetch_url(self, value: str) -> None:
        """A URL path can carry any of the hostile values."""
        url = f"https://example.test/{value}"

        stored = web_research_handler.store_webfetch_content(
            content="# Plain Title\n\nBody text.\n", url=url, prompt="p"
        )

        parsed = _parse_entry(Path(stored).read_text(encoding="utf-8"))
        assert parsed["url"] == url
        assert parsed["source_type"] == "webfetch"

    @pytest.mark.parametrize("value", [v for v in HOSTILE_VALUES if v.strip()])
    def test_websearch_query(self, value: str) -> None:
        """The query is written twice, as ``topic`` and as ``query``."""
        stored = web_research_handler.store_websearch_results(
            query=value,
            results=[{"title": "t", "url": "https://example.test/a", "snippet": "s"}],
        )

        parsed = _parse_entry(Path(stored).read_text(encoding="utf-8"))
        assert parsed["query"] == value
        assert parsed["topic"] == value
        assert parsed["result_count"] == 1

    @pytest.mark.parametrize(
        "hook", [research_queue, web_research_handler], ids=lambda m: m.__name__
    )
    def test_no_hook_keeps_its_own_scalar_quoting(self, hook) -> None:
        """A private quoting helper is how the twin copies started."""
        source = Path(hook.__file__).read_text(encoding="utf-8")

        assert "def _yaml_scalar" not in source


def _parse_entry(text: str) -> dict:
    parsed = parse_entry_frontmatter(text)
    assert parsed is not None, text[:400]
    return parsed


def test_an_astral_character_round_trips_as_utf8() -> None:
    """The default JSON dump escapes an emoji as a pair YAML reads apart."""
    import yaml

    from shared.frontmatter import render_frontmatter

    block = render_frontmatter({"topic": "Launch \U0001f680 notes"})
    topic = yaml.safe_load(block.strip("-\n"))["topic"]

    assert topic == "Launch \U0001f680 notes"
    topic.encode("utf-8")


@pytest.mark.parametrize(
    "text",
    [
        "launch \U0001f680 now",
        "it\x92s",
        "NEL\x85here",
        "del\x7fchar",
        "sep line para",
        "nonchar￾￿",
        "lone\ud800surrogate",
    ],
    ids=[
        "emoji",
        "c1_cp1252",
        "nel",
        "del",
        "line_separators",
        "nonchars",
        "surrogate",
    ],
)
def test_text_yaml_cannot_hold_raw_round_trips_through_safe_load(text: str) -> None:
    """Characters PyYAML rejects or folds are escaped, emoji stay literal."""
    import yaml

    block = render_frontmatter({"topic": text})
    assert yaml.safe_load(block.split("---")[1])["topic"] == text
    if "\U0001f680" in text:
        assert "\U0001f680" in block
