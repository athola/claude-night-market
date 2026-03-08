"""Tests for convention harvester — extracts review patterns from PR comments."""

from __future__ import annotations

from pathlib import Path

from harvester import (
    ConventionSuggestion,
    extract_patterns,
    load_suggestions,
    merge_suggestion,
    save_suggestions,
)


class TestExtractPatterns:
    """Extract potential convention patterns from PR review comments."""

    def test_extracts_import_pattern(self) -> None:
        """Detect import-discipline comments."""
        comments = [
            {
                "path": "src/utils.py",
                "line": 10,
                "body": "do not import outside of top level; fix all instances",
            }
        ]
        suggestions = extract_patterns(comments)
        assert len(suggestions) >= 1
        matched = [s for s in suggestions if s.pattern_id == "import-discipline"]
        assert len(matched) == 1
        assert "import" in matched[0].evidence.lower()

    def test_extracts_destructive_git_pattern(self) -> None:
        """Detect destructive git operations."""
        comments = [
            {
                "path": "skills/recovery.md",
                "line": 42,
                "body": "NEVER do this; instead fix from git log history diff. "
                "See above about never doing git checkout.",
            }
        ]
        suggestions = extract_patterns(comments)
        matched = [s for s in suggestions if s.pattern_id == "destructive-git"]
        assert len(matched) == 1

    def test_extracts_suppression_pattern(self) -> None:
        """Detect lint suppression comments."""
        comments = [
            {
                "path": "tests/test_foo.py",
                "line": 5,
                "body": "Do not import outside of top level; fix all instances "
                "of this noqa across the codebase instead of ignoring with noqa",
            }
        ]
        suggestions = extract_patterns(comments)
        matched = [s for s in suggestions if s.pattern_id == "no-suppression"]
        assert len(matched) == 1

    def test_extracts_consolidation_pattern(self) -> None:
        """Detect doc consolidation comments."""
        comments = [
            {
                "path": "docs/new-guide.md",
                "line": None,
                "body": "remove, consolidate into existing docs. "
                "make sure this happens on all future PRs",
            }
        ]
        suggestions = extract_patterns(comments)
        matched = [s for s in suggestions if s.pattern_id == "consolidate-docs"]
        assert len(matched) == 1

    def test_extracts_artifact_pattern(self) -> None:
        """Detect committed artifact comments."""
        comments = [
            {
                "path": ".attune/mission-state.json",
                "line": None,
                "body": "this is an artifact, make sure it gets .gitignored",
            }
        ]
        suggestions = extract_patterns(comments)
        matched = [s for s in suggestions if s.pattern_id == "no-artifacts"]
        assert len(matched) == 1

    def test_ignores_agent_responses(self) -> None:
        """Filter out automated agent response comments."""
        comments = [
            {
                "path": "src/foo.py",
                "line": 10,
                "body": "Fixed in 4794946d. Moved all deferred imports "
                "to top-level across 5 test files.",
            }
        ]
        suggestions = extract_patterns(comments)
        assert len(suggestions) == 0

    def test_ignores_unrelated_comments(self) -> None:
        """Ordinary comments produce no suggestions."""
        comments = [
            {
                "path": "src/main.py",
                "line": 1,
                "body": "Looks good, nice work on the refactor.",
            }
        ]
        suggestions = extract_patterns(comments)
        assert len(suggestions) == 0

    def test_handles_empty_comments(self) -> None:
        """Empty comment list produces no suggestions."""
        suggestions = extract_patterns([])
        assert suggestions == []

    def test_deduplicates_same_pattern(self) -> None:
        """Multiple comments matching same pattern merge into one."""
        comments = [
            {
                "path": "a.py",
                "line": 1,
                "body": "fix import outside of top level",
            },
            {
                "path": "b.py",
                "line": 5,
                "body": "Do not import outside of top level",
            },
        ]
        suggestions = extract_patterns(comments)
        import_matches = [
            s for s in suggestions if s.pattern_id == "import-discipline"
        ]
        assert len(import_matches) == 1
        assert import_matches[0].occurrence_count == 2


class TestSuggestionPersistence:
    """Save and load suggestions to/from YAML."""

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """Suggestions survive save/load cycle."""
        suggestions = [
            ConventionSuggestion(
                pattern_id="import-discipline",
                description="Imports must be at top level",
                evidence="do not import outside of top level",
                source_prs=[272, 254],
                occurrence_count=3,
                proposed_codex_id=None,
                promoted=False,
            )
        ]
        path = tmp_path / "suggestions.json"
        save_suggestions(suggestions, path)
        loaded = load_suggestions(path)
        assert len(loaded) == 1
        assert loaded[0].pattern_id == "import-discipline"
        assert loaded[0].source_prs == [272, 254]
        assert loaded[0].occurrence_count == 3

    def test_load_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """Missing file returns empty list."""
        loaded = load_suggestions(tmp_path / "nope.json")
        assert loaded == []

    def test_merge_new_suggestion(self, tmp_path: Path) -> None:
        """New suggestion is appended to existing file."""
        path = tmp_path / "suggestions.json"
        existing = ConventionSuggestion(
            pattern_id="old-pattern",
            description="Old",
            evidence="old evidence",
            source_prs=[100],
            occurrence_count=1,
        )
        save_suggestions([existing], path)

        new = ConventionSuggestion(
            pattern_id="new-pattern",
            description="New",
            evidence="new evidence",
            source_prs=[200],
            occurrence_count=1,
        )
        merge_suggestion(new, path)
        loaded = load_suggestions(path)
        assert len(loaded) == 2
        ids = {s.pattern_id for s in loaded}
        assert ids == {"old-pattern", "new-pattern"}

    def test_merge_existing_increments_count(self, tmp_path: Path) -> None:
        """Merging duplicate pattern increments count and adds PRs."""
        path = tmp_path / "suggestions.json"
        existing = ConventionSuggestion(
            pattern_id="import-discipline",
            description="Imports at top",
            evidence="evidence1",
            source_prs=[100],
            occurrence_count=2,
        )
        save_suggestions([existing], path)

        new = ConventionSuggestion(
            pattern_id="import-discipline",
            description="Imports at top",
            evidence="evidence2",
            source_prs=[200],
            occurrence_count=1,
        )
        merge_suggestion(new, path)
        loaded = load_suggestions(path)
        assert len(loaded) == 1
        assert loaded[0].occurrence_count == 3
        assert set(loaded[0].source_prs) == {100, 200}


class TestMapToCodex:
    """Map suggestions to existing codex conventions."""

    def test_suggestion_maps_to_existing_convention(self) -> None:
        """Known patterns map to existing codex IDs."""
        from harvester import map_to_codex_id

        assert map_to_codex_id("import-discipline") == "C1"
        assert map_to_codex_id("no-artifacts") == "C2"
        assert map_to_codex_id("destructive-git") == "C3"
        assert map_to_codex_id("no-suppression") == "C4"
        assert map_to_codex_id("consolidate-docs") == "C5"

    def test_unknown_pattern_returns_none(self) -> None:
        """Unknown patterns return None (potential new convention)."""
        from harvester import map_to_codex_id

        assert map_to_codex_id("unknown-pattern") is None
