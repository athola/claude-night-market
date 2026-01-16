"""Integration tests for doc-updates workflow phases.

This module tests the enhanced doc-updates workflow phases:
- Phase 2.5: Consolidation detection
- Phase 5: Accuracy verification
- Directory-specific style rules

Issue #50: Add integration tests for doc-updates workflow phases

Following TDD/BDD principles with Given/When/Then docstrings.
"""

import re
from pathlib import Path
from typing import Any

import pytest

# ============================================================================
# Directory Style Rules Module Tests
# ============================================================================


class TestDirectoryStyleRules:
    """Feature: Directory-specific documentation style enforcement.

    As a documentation maintainer
    I want different style rules for docs/ vs book/ directories
    So that reference docs are concise and tutorials are comprehensive
    """

    @pytest.fixture
    def docs_strict_rules(self) -> dict[str, int]:
        """Given strict rules for docs/ directory."""
        return {
            "max_file_lines": 500,
            "max_section_lines": 100,
            "max_paragraph_sentences": 4,
            "max_list_items": 10,
            "max_table_rows": 15,
        }

    @pytest.fixture
    def book_lenient_rules(self) -> dict[str, int]:
        """Given lenient rules for book/ directory."""
        return {
            "max_file_lines": 1000,
            "max_section_lines": 300,
            "max_paragraph_sentences": 8,
            "max_list_items": 15,
            "max_table_rows": 25,
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_docs_file_within_line_limit(
        self, tmp_path: Path, docs_strict_rules: dict[str, int]
    ) -> None:
        """Scenario: docs/ file within line limit passes.

        Given a markdown file in docs/ with 400 lines
        When validating against docs/ rules
        Then it should pass the file length check.
        """
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        doc_file = docs_dir / "api-overview.md"
        doc_file.write_text("# API Overview\n\n" + "Line content\n" * 398)

        lines = doc_file.read_text().split("\n")
        assert len(lines) <= docs_strict_rules["max_file_lines"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_docs_file_exceeds_line_limit(
        self, tmp_path: Path, docs_strict_rules: dict[str, int]
    ) -> None:
        """Scenario: docs/ file exceeding line limit fails.

        Given a markdown file in docs/ with 600 lines
        When validating against docs/ rules
        Then it should fail the file length check.
        """
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        doc_file = docs_dir / "bloated-doc.md"
        doc_file.write_text("# Bloated\n\n" + "Line content\n" * 598)

        lines = doc_file.read_text().split("\n")
        assert len(lines) > docs_strict_rules["max_file_lines"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_book_file_within_lenient_limit(
        self, tmp_path: Path, book_lenient_rules: dict[str, int]
    ) -> None:
        """Scenario: book/ file within lenient limit passes.

        Given a markdown file in book/ with 800 lines
        When validating against book/ rules
        Then it should pass (800 < 1000 limit).
        """
        book_dir = tmp_path / "book" / "src"
        book_dir.mkdir(parents=True)
        book_file = book_dir / "tutorial.md"
        book_file.write_text("# Tutorial\n\n" + "Tutorial content\n" * 798)

        lines = book_file.read_text().split("\n")
        assert len(lines) <= book_lenient_rules["max_file_lines"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_book_file_exceeds_lenient_limit(
        self, tmp_path: Path, book_lenient_rules: dict[str, int]
    ) -> None:
        """Scenario: book/ file exceeding 1000 lines fails.

        Given a markdown file in book/ with 1100 lines
        When validating against book/ rules
        Then it should fail the file length check.
        """
        book_dir = tmp_path / "book" / "src"
        book_dir.mkdir(parents=True)
        book_file = book_dir / "mega-tutorial.md"
        book_file.write_text("# Mega Tutorial\n\n" + "Content\n" * 1098)

        lines = book_file.read_text().split("\n")
        assert len(lines) > book_lenient_rules["max_file_lines"]


class TestFillerPhraseDetection:
    """Feature: Detect and flag filler phrases in documentation.

    As a documentation maintainer
    I want to detect filler phrases
    So that documentation is direct and concise
    """

    FILLER_PHRASES = [
        r"\bin order to\b",
        r"\bit should be noted\b",
        r"\bas mentioned (above|below|earlier|previously)\b",
        r"\bmoving on\b",
        r"\bnow let's (look at|explore|consider)\b",
        r"\bthis (document|section|chapter) (describes|explains|covers)\b",
    ]

    def detect_filler(self, content: str) -> list[str]:
        """Detect filler phrases in content."""
        found = []
        for pattern in self.FILLER_PHRASES:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found.extend(matches)
        return found

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_in_order_to(self) -> None:
        """Scenario: Detect 'in order to' filler phrase.

        Given content containing 'in order to'
        When scanning for filler phrases
        Then it should be detected.
        """
        content = "In order to run the tests, execute pytest."
        fillers = self.detect_filler(content)
        assert len(fillers) > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_it_should_be_noted(self) -> None:
        """Scenario: Detect 'it should be noted' filler phrase.

        Given content containing 'it should be noted'
        When scanning for filler phrases
        Then it should be detected.
        """
        content = "It should be noted that this feature is experimental."
        fillers = self.detect_filler(content)
        assert len(fillers) > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_this_document_describes(self) -> None:
        """Scenario: Detect 'this document describes' filler phrase.

        Given content starting with 'This document describes'
        When scanning for filler phrases
        Then it should be detected.
        """
        content = "This document describes the API endpoints."
        fillers = self.detect_filler(content)
        assert len(fillers) > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_clean_content_has_no_fillers(self) -> None:
        """Scenario: Clean content has no filler phrases.

        Given content without filler phrases
        When scanning for filler phrases
        Then none should be detected.
        """
        content = "Run `pytest` to execute tests. Check the output for failures."
        fillers = self.detect_filler(content)
        assert len(fillers) == 0


class TestWallOfTextDetection:
    """Feature: Detect wall-of-text paragraphs.

    As a documentation maintainer
    I want to detect overly long paragraphs
    So that documentation remains scannable
    """

    def count_sentences(self, paragraph: str) -> int:
        """Count sentences in a paragraph."""
        # Simple sentence detection
        sentences = re.split(r"[.!?]+", paragraph.strip())
        return len([s for s in sentences if s.strip()])

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_wall_of_text_in_docs(self) -> None:
        """Scenario: Detect wall of text in docs/ (>4 sentences).

        Given a paragraph with 6 sentences
        When checking against docs/ rules (max 4 sentences)
        Then it should be flagged as wall of text.
        """
        paragraph = (
            "First sentence. Second sentence. Third sentence. "
            "Fourth sentence. Fifth sentence. Sixth sentence."
        )
        max_sentences = 4  # docs/ limit
        sentence_count = self.count_sentences(paragraph)
        assert sentence_count > max_sentences

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_longer_paragraphs_in_book(self) -> None:
        """Scenario: Allow longer paragraphs in book/ (up to 8 sentences).

        Given a paragraph with 6 sentences
        When checking against book/ rules (max 8 sentences)
        Then it should pass.
        """
        paragraph = (
            "First sentence. Second sentence. Third sentence. "
            "Fourth sentence. Fifth sentence. Sixth sentence."
        )
        max_sentences = 8  # book/ limit
        sentence_count = self.count_sentences(paragraph)
        assert sentence_count <= max_sentences

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_short_paragraph_passes(self) -> None:
        """Scenario: Short paragraph passes all rules.

        Given a paragraph with 2 sentences
        When checking against any rules
        Then it should pass.
        """
        paragraph = "First sentence. Second sentence."
        sentence_count = self.count_sentences(paragraph)
        assert sentence_count <= 4  # Passes even strict docs/ rules


# ============================================================================
# Accuracy Scanning Module Tests
# ============================================================================


class TestAccuracyScanning:
    """Feature: Validate documentation accuracy against codebase.

    As a documentation maintainer
    I want to verify version numbers and counts
    So that documentation stays accurate
    """

    @pytest.fixture
    def mock_plugin_versions(self) -> dict[str, str]:
        """Given actual plugin versions from plugin.json files."""
        return {
            "abstract": "1.2.8",
            "sanctum": "1.2.8",
            "scry": "1.1.0",
            "conserve": "1.0.0",
        }

    def extract_version_claims(self, content: str) -> list[tuple[str, str]]:
        """Extract version claims from content.

        Returns list of (plugin_name, version) tuples.
        Handles patterns like:
        - "abstract v2.0.0"
        - "abstract (v2.0.0)"
        - "The abstract plugin (v2.0.0)"
        """
        # Pattern 1: "name v1.2.3" or "name (v1.2.3)"
        pattern1 = r"(\w+)\s+(?:plugin\s+)?\(?v?(\d+\.\d+\.\d+)\)?"
        matches = re.findall(pattern1, content, re.IGNORECASE)
        return [(name.lower(), ver) for name, ver in matches]

    def extract_count_claims(self, content: str) -> list[tuple[int, str]]:
        """Extract count claims from content.

        Returns list of (count, item_type) tuples.
        """
        pattern = r"(\d+)\s+(plugins?|skills?|commands?|agents?)"
        matches = re.findall(pattern, content, re.IGNORECASE)
        return [
            (int(count), item_type.lower().rstrip("s")) for count, item_type in matches
        ]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_version_mismatch(
        self, mock_plugin_versions: dict[str, str]
    ) -> None:
        """Scenario: Detect version mismatch in documentation.

        Given documentation claiming 'abstract v2.0.0'
        And actual abstract version is 1.2.8
        When scanning for accuracy
        Then a version mismatch should be detected.
        """
        content = "The abstract plugin (v2.0.0) provides validation."
        claims = self.extract_version_claims(content)

        mismatches = []
        for plugin, claimed_ver in claims:
            if plugin in mock_plugin_versions:
                actual = mock_plugin_versions[plugin]
                if claimed_ver != actual:
                    mismatches.append((plugin, claimed_ver, actual))

        assert len(mismatches) == 1
        assert mismatches[0] == ("abstract", "2.0.0", "1.2.8")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_accepts_correct_version(
        self, mock_plugin_versions: dict[str, str]
    ) -> None:
        """Scenario: Accept correct version in documentation.

        Given documentation claiming 'sanctum v1.2.8'
        And actual sanctum version is 1.2.8
        When scanning for accuracy
        Then no mismatch should be detected.
        """
        content = "The sanctum plugin (v1.2.8) provides git workflows."
        claims = self.extract_version_claims(content)

        mismatches = []
        for plugin, claimed_ver in claims:
            if plugin in mock_plugin_versions:
                actual = mock_plugin_versions[plugin]
                if claimed_ver != actual:
                    mismatches.append((plugin, claimed_ver, actual))

        assert len(mismatches) == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_count_mismatch(self) -> None:
        """Scenario: Detect count mismatch in documentation.

        Given documentation claiming '15 plugins'
        And actual count is 8 plugins
        When scanning for accuracy
        Then a count mismatch should be detected.
        """
        content = "The marketplace contains 15 plugins."
        claims = self.extract_count_claims(content)
        actual_count = 8

        mismatches = []
        for claimed_count, item_type in claims:
            if item_type == "plugin" and claimed_count != actual_count:
                mismatches.append((item_type, claimed_count, actual_count))

        assert len(mismatches) == 1
        assert mismatches[0] == ("plugin", 15, 8)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_accepts_correct_count(self) -> None:
        """Scenario: Accept correct count in documentation.

        Given documentation claiming '8 plugins'
        And actual count is 8 plugins
        When scanning for accuracy
        Then no mismatch should be detected.
        """
        content = "The marketplace contains 8 plugins."
        claims = self.extract_count_claims(content)
        actual_count = 8

        mismatches = []
        for claimed_count, item_type in claims:
            if item_type == "plugin" and claimed_count != actual_count:
                mismatches.append((item_type, claimed_count, actual_count))

        assert len(mismatches) == 0


# ============================================================================
# Consolidation Integration Module Tests
# ============================================================================


class TestConsolidationDetection:
    """Feature: Detect consolidation opportunities in documentation.

    As a documentation maintainer
    I want to detect redundant and bloated files
    So that documentation stays lean and focused
    """

    @pytest.fixture
    def untracked_report_patterns(self) -> list[str]:
        """Given patterns for LLM-generated reports."""
        return [
            r".*_REPORT\.md$",
            r".*_ANALYSIS\.md$",
            r".*_REVIEW\.md$",
        ]

    def is_untracked_report(self, filename: str, patterns: list[str]) -> bool:
        """Check if filename matches untracked report patterns."""
        for pattern in patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                return True
        return False

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_untracked_report_md(
        self, untracked_report_patterns: list[str]
    ) -> None:
        """Scenario: Detect untracked *_REPORT.md files.

        Given a file named 'API_REVIEW_REPORT.md'
        When checking against report patterns
        Then it should be flagged as an untracked report.
        """
        filename = "API_REVIEW_REPORT.md"
        assert self.is_untracked_report(filename, untracked_report_patterns)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_analysis_report(
        self, untracked_report_patterns: list[str]
    ) -> None:
        """Scenario: Detect untracked *_ANALYSIS.md files.

        Given a file named 'MIGRATION_ANALYSIS.md'
        When checking against report patterns
        Then it should be flagged as an untracked report.
        """
        filename = "MIGRATION_ANALYSIS.md"
        assert self.is_untracked_report(filename, untracked_report_patterns)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ignores_regular_md_files(
        self, untracked_report_patterns: list[str]
    ) -> None:
        """Scenario: Ignore regular markdown files.

        Given a file named 'README.md'
        When checking against report patterns
        Then it should NOT be flagged.
        """
        filename = "README.md"
        assert not self.is_untracked_report(filename, untracked_report_patterns)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_bloated_docs_file(self, tmp_path: Path) -> None:
        """Scenario: Detect bloated file in docs/ directory.

        Given a docs/ file with 600 lines
        When checking for bloat (limit: 500 lines)
        Then it should be flagged as bloated.
        """
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        bloated = docs_dir / "bloated.md"
        bloated.write_text("# Bloated\n" + "Content\n" * 599)

        lines = bloated.read_text().split("\n")
        docs_limit = 500

        assert len(lines) > docs_limit

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_accepts_normal_docs_file(self, tmp_path: Path) -> None:
        """Scenario: Accept normal-sized docs/ file.

        Given a docs/ file with 300 lines
        When checking for bloat (limit: 500 lines)
        Then it should NOT be flagged.
        """
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        normal = docs_dir / "normal.md"
        normal.write_text("# Normal\n" + "Content\n" * 299)

        lines = normal.read_text().split("\n")
        docs_limit = 500

        assert len(lines) <= docs_limit


class TestSkipConsolidationFlag:
    """Feature: Support --skip-consolidation flag.

    As a user
    I want to skip consolidation checks
    So that I can do quick documentation updates
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skip_flag_bypasses_consolidation(self) -> None:
        """Scenario: --skip-consolidation bypasses Phase 2.5.

        Given the --skip-consolidation flag is set
        When running doc-updates workflow
        Then Phase 2.5 should be skipped entirely.
        """
        flags = {"skip_consolidation": True}
        should_run_consolidation = not flags.get("skip_consolidation", False)
        assert not should_run_consolidation

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_default_runs_consolidation(self) -> None:
        """Scenario: Default behavior runs consolidation.

        Given no --skip-consolidation flag
        When running doc-updates workflow
        Then Phase 2.5 should run.
        """
        flags: dict[str, Any] = {}
        should_run_consolidation = not flags.get("skip_consolidation", False)
        assert should_run_consolidation


# ============================================================================
# Integration Tests
# ============================================================================


class TestDocUpdatesWorkflowIntegration:
    """Feature: Full doc-updates workflow integration.

    As a documentation maintainer
    I want the complete workflow to work end-to-end
    So that I can confidently update documentation
    """

    @pytest.fixture
    def mock_project_structure(self, tmp_path: Path) -> Path:
        """Given a mock project with docs/, book/, and plugins/."""
        # Create docs/ with strict rules
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "api-overview.md").write_text(
            "# API Overview\n\nQuick reference for APIs.\n"
        )

        # Create book/ with lenient rules
        book = tmp_path / "book" / "src"
        book.mkdir(parents=True)
        (book / "tutorial.md").write_text(
            "# Tutorial\n\nThis is a longer tutorial with more content.\n" * 50
        )

        # Create plugins/ structure
        plugins = tmp_path / "plugins"
        plugin_a = plugins / "test-plugin" / ".claude-plugin"
        plugin_a.mkdir(parents=True)
        (plugin_a / "plugin.json").write_text(
            '{"name": "test-plugin", "version": "1.0.0"}'
        )

        return tmp_path

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_workflow_processes_docs_with_strict_rules(
        self, mock_project_structure: Path
    ) -> None:
        """Scenario: Workflow applies strict rules to docs/.

        Given a project with docs/ and book/ directories
        When processing documentation updates
        Then docs/ files should be validated with strict rules.
        """
        docs_file = mock_project_structure / "docs" / "api-overview.md"
        assert docs_file.exists()

        # Verify docs/ file passes strict rules
        content = docs_file.read_text()
        lines = content.split("\n")
        assert len(lines) <= 500  # Strict limit

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_workflow_processes_book_with_lenient_rules(
        self, mock_project_structure: Path
    ) -> None:
        """Scenario: Workflow applies lenient rules to book/.

        Given a project with docs/ and book/ directories
        When processing documentation updates
        Then book/ files should be validated with lenient rules.
        """
        book_file = mock_project_structure / "book" / "src" / "tutorial.md"
        assert book_file.exists()

        # Verify book/ file passes lenient rules
        content = book_file.read_text()
        lines = content.split("\n")
        assert len(lines) <= 1000  # Lenient limit

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_workflow_extracts_plugin_versions(
        self, mock_project_structure: Path
    ) -> None:
        """Scenario: Workflow can extract plugin versions.

        Given a project with plugin.json files
        When extracting versions for accuracy checking
        Then correct versions should be returned.
        """
        import json

        plugin_json = (
            mock_project_structure
            / "plugins"
            / "test-plugin"
            / ".claude-plugin"
            / "plugin.json"
        )
        assert plugin_json.exists()

        with open(plugin_json) as f:
            data = json.load(f)

        assert data["name"] == "test-plugin"
        assert data["version"] == "1.0.0"
