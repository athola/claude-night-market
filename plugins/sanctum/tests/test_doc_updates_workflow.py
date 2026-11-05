"""Contract tests for the doc-updates workflow documents.

Issue #50: tests for doc-updates workflow phases.

The workflow is executed by the model from `skills/doc-updates/SKILL.md`,
its `modules/`, and `commands/update-docs.md`. These tests read those
files: the per-directory limits, the filler-phrase list (executed as the
shipped regexes), the consolidation scan targets, and the skip flag.
Editing a limit or pattern out of one document turns a test red.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = PLUGIN_ROOT / "skills" / "doc-updates"


def _read(*parts: str) -> str:
    return PLUGIN_ROOT.joinpath(*parts).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def style_text() -> str:
    return _read("skills", "doc-updates", "modules", "directory-style-rules.md")


@pytest.fixture(scope="module")
def skill_text() -> str:
    return _read("skills", "doc-updates", "SKILL.md")


@pytest.fixture(scope="module")
def command_text() -> str:
    return _read("commands", "update-docs.md")


def _limits_for(style_text: str, heading: str) -> dict[str, int]:
    """Return {rule: number} from the limits table under a `### ` heading."""
    section = style_text.split(f"### {heading}", 1)[1].split("\n### ", 1)[0]
    rows = re.findall(r"^\| (Max [^|]+?) \| (\d+)", section, re.M)
    return {rule: int(number) for rule, number in rows}


@pytest.fixture(scope="module")
def filler_patterns(style_text: str) -> list[re.Pattern[str]]:
    """The FILLER_PHRASES list exactly as the module ships it."""
    block = re.search(r"FILLER_PHRASES = (\[.*?\n\])", style_text, re.DOTALL)
    assert block, "directory-style-rules.md no longer ships FILLER_PHRASES"
    patterns = ast.literal_eval(block.group(1))
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


def _filler_hits(patterns: list[re.Pattern[str]], content: str) -> int:
    return sum(len(pattern.findall(content)) for pattern in patterns)


@pytest.mark.unit
class TestDirectoryStyleRules:
    def test_docs_directory_is_strict(self, style_text: str) -> None:
        limits = _limits_for(style_text, "docs/ ")
        assert limits["Max file length"] == 500
        assert limits["Max section length"] == 100
        assert limits["Max paragraph sentences"] == 4
        assert limits["Max list items"] == 10
        assert limits["Max table rows"] == 15

    def test_book_directory_is_lenient(self, style_text: str) -> None:
        limits = _limits_for(style_text, "book/ ")
        assert limits["Max file length"] == 1000
        assert limits["Max section length"] == 300
        assert limits["Max paragraph sentences"] == 8
        assert limits["Max list items"] == 15
        assert limits["Max table rows"] == 25

    def test_book_limits_exceed_docs_limits_on_every_rule(
        self, style_text: str
    ) -> None:
        docs = _limits_for(style_text, "docs/ ")
        book = _limits_for(style_text, "book/ ")
        assert all(book[rule] > docs[rule] for rule in docs)

    def test_command_table_agrees_with_the_module_on_line_limits(
        self, style_text: str, command_text: str
    ) -> None:
        assert "| `docs/` | Strict reference | 500 lines | 4 sentences |" in (
            command_text
        )
        assert "| `book/` | Technical book | 1000 lines | 8 sentences |" in (
            command_text
        )
        assert _limits_for(style_text, "docs/ ")["Max file length"] == 500
        assert _limits_for(style_text, "book/ ")["Max file length"] == 1000

    def test_unlisted_directories_default_to_strict(self, command_text: str) -> None:
        assert "| Other | Default strict | 500 lines | 4 sentences |" in command_text

    def test_skill_repeats_the_bloat_thresholds(self, skill_text: str) -> None:
        assert "files exceeding 500 lines in docs/, 1000 in book/" in skill_text


@pytest.mark.unit
class TestFillerPhraseDetection:
    def test_detects_in_order_to(self, filler_patterns: list[re.Pattern[str]]) -> None:
        text = "We use a cache in order to speed up reads."
        assert _filler_hits(filler_patterns, text) == 1

    def test_detects_it_should_be_noted(
        self, filler_patterns: list[re.Pattern[str]]
    ) -> None:
        text = "It should be noted that the cache is cold at startup."
        assert _filler_hits(filler_patterns, text) == 1

    def test_detects_this_document_describes(
        self, filler_patterns: list[re.Pattern[str]]
    ) -> None:
        text = "This document describes the configuration options."
        assert _filler_hits(filler_patterns, text) == 1

    def test_detects_as_mentioned_variants(
        self, filler_patterns: list[re.Pattern[str]]
    ) -> None:
        text = "As mentioned above, the cache is cold. As mentioned later is fine."
        assert _filler_hits(filler_patterns, text) == 1

    def test_clean_content_has_no_fillers(
        self, filler_patterns: list[re.Pattern[str]]
    ) -> None:
        text = "The cache is cold at startup. Warm it with `make warm`."
        assert _filler_hits(filler_patterns, text) == 0

    def test_skill_names_the_filler_phrase_check(self, skill_text: str) -> None:
        assert '"in order' in skill_text


@pytest.mark.unit
class TestWallOfTextDetection:
    def test_module_flags_paragraphs_above_the_sentence_limit(
        self, style_text: str
    ) -> None:
        assert "if sentence_count > max_sentences:" in style_text
        assert '"type": "wall_of_text"' in style_text

    def test_wall_of_text_is_reported_as_a_warning_with_a_fix(
        self, style_text: str
    ) -> None:
        assert (
            "| warning | wall_of_text | Paragraph 3 has 7 sentences (limit: 4) "
            "| Break into smaller paragraphs |" in style_text
        )

    def test_skill_warns_on_paragraph_and_file_limits(self, skill_text: str) -> None:
        assert (
            "paragraphs that exceed length limits or files that surpass" in skill_text
        )


@pytest.mark.unit
class TestConsolidationDetection:
    def test_skill_scans_for_untracked_report_files(self, skill_text: str) -> None:
        assert "Untracked reports (ALL_CAPS *_REPORT.md, *_ANALYSIS.md files)" in (
            skill_text
        )

    def test_command_scans_for_untracked_report_files(self, command_text: str) -> None:
        assert "Untracked reports (ALL_CAPS *_REPORT.md files)" in command_text

    def test_skill_scans_for_bloated_committed_docs(self, skill_text: str) -> None:
        assert "Bloated committed docs" in skill_text

    def test_merging_or_deleting_requires_user_approval(self, skill_text: str) -> None:
        approval = skill_text.split("**User approval required before:**")[1].split(
            "**Skip options:**", maxsplit=1
        )[0]
        assert "Merging content from one file to another" in approval
        assert "Deleting stale or redundant files" in approval

    def test_consolidation_module_lists_untracked_reports_as_merge_or_delete(
        self,
    ) -> None:
        module = _read(
            "skills", "doc-updates", "modules", "consolidation-integration.md"
        )
        assert "### Untracked Reports (merge or delete)" in module


@pytest.mark.unit
class TestSkipConsolidationFlag:
    def test_command_usage_line_accepts_the_flag(self, command_text: str) -> None:
        assert "[--skip-consolidation]" in command_text

    def test_flag_skips_the_consolidation_phase(
        self, command_text: str, skill_text: str
    ) -> None:
        assert "`--skip-consolidation` - Skip redundancy detection phase" in (
            command_text
        )
        assert "| `--skip-consolidation` | Skip Phase 2.5 consolidation check |" in (
            skill_text
        )

    def test_consolidation_runs_by_default(self, skill_text: str) -> None:
        assert "Use `--skip-consolidation` flag to bypass this phase" in skill_text


@pytest.mark.unit
class TestAccuracyScanning:
    def test_version_claims_are_compared_with_plugin_json(self) -> None:
        module = _read("skills", "doc-updates", "modules", "accuracy-scanning.md")
        assert "Compares version references in documentation against `plugin.json`" in (
            module
        )

    def test_count_claims_are_verified_against_directories(self) -> None:
        module = _read("skills", "doc-updates", "modules", "accuracy-scanning.md")
        assert "Verifies claims like" in module
        assert "against actual directory count" in module

    def test_module_reports_a_version_mismatch_with_claimed_and_actual(self) -> None:
        module = _read("skills", "doc-updates", "modules", "accuracy-scanning.md")
        assert '"type": "version_mismatch"' in module
        assert '"claimed": claimed_version' in module
