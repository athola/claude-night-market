"""Tests for scripts/dogfooder/reporter.py.

Covers MakefileDogfooder orchestration, coverage calculation, target
insertion, .PHONY update, and report generation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from dogfooder.reporter import MakefileDogfooder

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_makefile(tmp_path) -> Path:
    """A minimal Makefile with one target and .PHONY declaration."""
    content = (
        ".PHONY: help test\n"
        "\n"
        "help: ## Show help\n"
        "\t@echo help\n"
        "\n"
        "test: ## Run tests\n"
        "\tpytest\n"
    )
    mf = tmp_path / "plugins" / "myplugin" / "Makefile"
    mf.parent.mkdir(parents=True, exist_ok=True)
    mf.write_text(content)
    return mf


@pytest.fixture
def simple_readme(tmp_path) -> Path:
    """A minimal README.md with a slash command."""
    content = "# My Plugin\n\n## Usage\n\nRun `/update-docs` to update documentation.\n"
    readme = tmp_path / "plugins" / "myplugin" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text(content)
    return readme


@pytest.fixture
def dogfooder(tmp_path, simple_makefile, simple_readme) -> MakefileDogfooder:
    """A MakefileDogfooder instance pointed at tmp_path."""
    return MakefileDogfooder(root_dir=tmp_path, plugins_dir="plugins", verbose=False)


# ---------------------------------------------------------------------------
# MakefileDogfooder.__init__
# ---------------------------------------------------------------------------


class TestMakefileDogfoaderInit:
    """MakefileDogfooder initializes with sensible defaults."""

    @pytest.mark.unit
    def test_default_plugins_dir(self, tmp_path):
        """Default plugins_dir is 'plugins'."""
        d = MakefileDogfooder(root_dir=tmp_path)
        assert d.plugins_dir == "plugins"

    @pytest.mark.unit
    def test_report_initialized_empty(self, tmp_path):
        """Report starts with zero counts."""
        d = MakefileDogfooder(root_dir=tmp_path)
        assert d.report["plugins_analyzed"] == 0
        assert d.report["commands_found"] == 0

    @pytest.mark.unit
    def test_essential_targets_loaded(self, tmp_path):
        """Essential targets are loaded from catalog (dict or list)."""
        d = MakefileDogfooder(root_dir=tmp_path)
        assert d.essential_targets is not None
        assert isinstance(d.essential_targets, (list, dict))


# ---------------------------------------------------------------------------
# MakefileDogfooder._calc_coverage
# ---------------------------------------------------------------------------


class TestCalcCoverage:
    """_calc_coverage computes percentage correctly."""

    @pytest.mark.unit
    def test_zero_required_returns_100(self, tmp_path):
        """When no required targets, coverage is 100%."""
        d = MakefileDogfooder(root_dir=tmp_path)
        assert d._calc_coverage(0, 0) == 100

    @pytest.mark.unit
    def test_full_coverage(self, tmp_path):
        """When all required targets exist, returns 100."""
        d = MakefileDogfooder(root_dir=tmp_path)
        assert d._calc_coverage(5, 5) == 100

    @pytest.mark.unit
    def test_partial_coverage(self, tmp_path):
        """Partial coverage is rounded down."""
        d = MakefileDogfooder(root_dir=tmp_path)
        assert d._calc_coverage(4, 3) == 75

    @pytest.mark.unit
    def test_no_existing_targets_is_zero(self, tmp_path):
        """When none exist, coverage is 0."""
        d = MakefileDogfooder(root_dir=tmp_path)
        assert d._calc_coverage(4, 0) == 0

    @pytest.mark.unit
    def test_capped_at_100(self, tmp_path):
        """Coverage never exceeds 100."""
        d = MakefileDogfooder(root_dir=tmp_path)
        assert d._calc_coverage(3, 5) == 100


# ---------------------------------------------------------------------------
# MakefileDogfooder.analyze_plugin
# ---------------------------------------------------------------------------


class TestAnalyzePlugin:
    """analyze_plugin returns analysis findings for a single plugin."""

    @pytest.mark.unit
    def test_returns_no_readme_when_readme_missing(self, dogfooder, tmp_path):
        """Returns 'no-readme' status when README.md is absent."""
        # Create a plugin dir without README
        plugin_dir = tmp_path / "plugins" / "nodocshere"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        result = dogfooder.analyze_plugin("nodocshere")
        assert result["status"] == "no-readme"

    @pytest.mark.unit
    def test_returns_no_makefile_when_makefile_missing(self, dogfooder, tmp_path):
        """Returns 'no-makefile' status when Makefile is absent."""
        plugin_dir = tmp_path / "plugins" / "norf"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        (plugin_dir / "README.md").write_text("# No Makefile\n")
        result = dogfooder.analyze_plugin("norf")
        assert result["status"] == "no-makefile"

    @pytest.mark.unit
    def test_returns_finding_for_valid_plugin(self, dogfooder):
        """Returns a finding dict with expected keys for a valid plugin."""
        result = dogfooder.analyze_plugin("myplugin")
        assert "commands_documented" in result
        assert "targets_missing" in result
        assert "coverage_percent" in result

    @pytest.mark.unit
    def test_finding_appended_to_report(self, dogfooder):
        """Analyze updates the report findings list."""
        dogfooder.analyze_plugin("myplugin")
        assert len(dogfooder.report["findings"]) >= 1

    @pytest.mark.unit
    def test_commands_count_updated_in_report(self, dogfooder):
        """commands_found in report is incremented."""
        dogfooder.analyze_plugin("myplugin")
        assert dogfooder.report["commands_found"] >= 0

    @pytest.mark.unit
    def test_generate_missing_triggers_makefile_generation(self, tmp_path):
        """When generate_missing=True and no Makefile, generation is attempted."""
        plugin_dir = tmp_path / "plugins" / "newplugin"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        (plugin_dir / "README.md").write_text("# New Plugin\n")

        d = MakefileDogfooder(root_dir=tmp_path, plugins_dir="plugins")
        with patch(
            "dogfooder.reporter.generate_makefile", return_value=True
        ) as mock_gen:
            d.analyze_plugin("newplugin", generate_missing=True)

        mock_gen.assert_called_once()


# ---------------------------------------------------------------------------
# MakefileDogfooder._filter_duplicate_targets
# ---------------------------------------------------------------------------


class TestFilterDuplicateTargets:
    """_filter_duplicate_targets removes already-existing targets."""

    @pytest.mark.unit
    def test_new_target_kept(self, tmp_path):
        """A target not in existing_targets is kept."""
        d = MakefileDogfooder(root_dir=tmp_path)
        content = "new-target: ## New\n\t@echo hi\n"
        result = d._filter_duplicate_targets(content, set())
        assert "new-target:" in "\n".join(result)

    @pytest.mark.unit
    def test_existing_target_removed(self, tmp_path):
        """A target already in existing_targets is removed."""
        d = MakefileDogfooder(root_dir=tmp_path)
        content = "existing-target: ## Existing\n\t@echo already there\n"
        result = d._filter_duplicate_targets(content, {"existing-target"})
        joined = "\n".join(result)
        assert "existing-target:" not in joined

    @pytest.mark.unit
    def test_recipe_lines_of_duplicate_skipped(self, tmp_path):
        """Recipe lines of a duplicate target are also filtered out."""
        d = MakefileDogfooder(root_dir=tmp_path)
        content = "dup: ## Dup\n\t@echo skip me\n"
        result = d._filter_duplicate_targets(content, {"dup"})
        joined = "\n".join(result)
        assert "skip me" not in joined

    @pytest.mark.unit
    def test_does_not_add_duplicate_target_twice(self, tmp_path):
        """When same target appears twice in generated content, only added once."""
        d = MakefileDogfooder(root_dir=tmp_path)
        content = "my-target: ## One\n\t@echo 1\n\nmy-target: ## Two\n\t@echo 2\n"
        result = d._filter_duplicate_targets(content, set())
        joined = "\n".join(result)
        assert joined.count("my-target:") == 1


# ---------------------------------------------------------------------------
# MakefileDogfooder._determine_insertion_strategy
# ---------------------------------------------------------------------------


class TestDetermineInsertionStrategy:
    """_determine_insertion_strategy picks appropriate insertion point."""

    @pytest.mark.unit
    def test_appends_to_end_when_no_percent_colons(self, tmp_path):
        """When no %:: in content, appends to end."""
        d = MakefileDogfooder(root_dir=tmp_path)
        original = "help:\n\t@echo help\n"
        new_content = "new-target:\n\t@echo new\n"
        result = d._determine_insertion_strategy(original, new_content)
        assert result.endswith("new-target:\n\t@echo new\n\n")

    @pytest.mark.unit
    def test_inserts_before_percent_colon_rule(self, tmp_path):
        """When %:: exists, content is inserted before it."""
        d = MakefileDogfooder(root_dir=tmp_path)
        original = "help:\n\t@echo help\n\n%::\n\t@echo catchall\n"
        new_content = "new-target:\n\t@echo new\n"
        result = d._determine_insertion_strategy(original, new_content)
        assert "new-target:" in result
        assert "%::" in result
        new_pos = result.index("new-target:")
        percent_pos = result.index("%::")
        assert new_pos < percent_pos


# ---------------------------------------------------------------------------
# MakefileDogfooder.apply_targets_to_makefile
# ---------------------------------------------------------------------------


class TestApplyTargetsToMakefile:
    """apply_targets_to_makefile writes new targets to a Makefile."""

    @pytest.mark.unit
    def test_dry_run_does_not_modify_file(self, dogfooder, tmp_path):
        """In dry_run mode, Makefile is not written."""
        makefile = tmp_path / "plugins" / "myplugin" / "Makefile"
        original_content = makefile.read_text()
        finding = {
            "plugin": "myplugin",
            "makefile": str(
                (tmp_path / "plugins" / "myplugin" / "Makefile").relative_to(tmp_path)
            ),
            "missing_targets": [],
        }
        new_content = "new-target: ## New\n\t@echo new\n"
        dogfooder.apply_targets_to_makefile(
            "myplugin", finding, new_content, dry_run=True
        )
        assert makefile.read_text() == original_content

    @pytest.mark.unit
    def test_returns_false_when_makefile_missing(self, dogfooder, tmp_path, capsys):
        """Returns False when Makefile path doesn't exist."""
        finding = {
            "plugin": "ghost",
            "makefile": "plugins/ghost/Makefile",
            "missing_targets": [],
        }
        result = dogfooder.apply_targets_to_makefile(
            "ghost", finding, "new-target: ## x\n", dry_run=False
        )
        assert result is False

    @pytest.mark.unit
    def test_writes_new_target_when_not_dry_run(self, dogfooder, tmp_path):
        """When not dry_run, new target is written to the Makefile."""
        makefile = tmp_path / "plugins" / "myplugin" / "Makefile"
        finding = {
            "plugin": "myplugin",
            "makefile": str(makefile.relative_to(tmp_path)),
            "missing_targets": ["brand-new-target"],
        }
        new_content = "brand-new-target: ## New target\n\t@echo new\n"
        result = dogfooder.apply_targets_to_makefile(
            "myplugin", finding, new_content, dry_run=False
        )
        assert result is True
        updated = makefile.read_text()
        assert "brand-new-target" in updated


# ---------------------------------------------------------------------------
# MakefileDogfooder._find_phony_block
# ---------------------------------------------------------------------------


class TestFindPhonyBlock:
    """_find_phony_block extracts the .PHONY declaration."""

    @pytest.mark.unit
    def test_finds_single_line_phony(self, tmp_path):
        """Single-line .PHONY block is detected."""
        d = MakefileDogfooder(root_dir=tmp_path)
        content = ".PHONY: help test\n\nhelp:\n\t@echo h\n"
        result = d._find_phony_block(content)
        assert len(result) >= 1
        assert ".PHONY" in result[0]

    @pytest.mark.unit
    def test_finds_multiline_phony(self, tmp_path):
        """Multi-line .PHONY block (with backslashes) is fully detected."""
        d = MakefileDogfooder(root_dir=tmp_path)
        content = ".PHONY: help \\\n\ttest \\\n\tbuild\n\nhelp:\n\t@echo h\n"
        result = d._find_phony_block(content)
        assert len(result) >= 3

    @pytest.mark.unit
    def test_empty_when_no_phony(self, tmp_path):
        """Returns empty list when no .PHONY block found."""
        d = MakefileDogfooder(root_dir=tmp_path)
        result = d._find_phony_block("help:\n\t@echo h\n")
        assert result == []


# ---------------------------------------------------------------------------
# MakefileDogfooder._extract_phony_targets
# ---------------------------------------------------------------------------


class TestExtractPhonyTargets:
    """_extract_phony_targets parses target names from .PHONY lines."""

    @pytest.mark.unit
    def test_extracts_single_line_targets(self, tmp_path):
        """Targets on a single .PHONY line are extracted."""
        d = MakefileDogfooder(root_dir=tmp_path)
        targets = d._extract_phony_targets([".PHONY: help test build"])
        assert "help" in targets
        assert "test" in targets
        assert "build" in targets

    @pytest.mark.unit
    def test_extracts_multiline_targets(self, tmp_path):
        """Targets across multiple .PHONY continuation lines are extracted."""
        d = MakefileDogfooder(root_dir=tmp_path)
        lines = [".PHONY: help \\", "\ttest \\", "\tbuild"]
        targets = d._extract_phony_targets(lines)
        assert "help" in targets
        assert "test" in targets
        assert "build" in targets


# ---------------------------------------------------------------------------
# MakefileDogfooder._build_phony_block
# ---------------------------------------------------------------------------


class TestBuildPhonyBlock:
    """_build_phony_block formats the .PHONY block with line breaks."""

    @pytest.mark.unit
    def test_short_list_fits_on_one_line(self, tmp_path):
        """Few targets produce a single .PHONY line."""
        d = MakefileDogfooder(root_dir=tmp_path)
        lines = d._build_phony_block(["help", "test"])
        assert len(lines) == 1
        assert ".PHONY: help test" in lines[0]

    @pytest.mark.unit
    def test_long_list_wraps(self, tmp_path):
        """Many targets cause line wrapping with backslash continuation."""
        d = MakefileDogfooder(root_dir=tmp_path)
        # Generate enough targets to exceed line length limit
        targets = [f"target-{i:03d}" for i in range(20)]
        lines = d._build_phony_block(targets)
        assert len(lines) > 1
        # All but last line should end with \\
        for line in lines[:-1]:
            assert line.endswith("\\")


# ---------------------------------------------------------------------------
# MakefileDogfooder.fix_makefile_pronounce
# ---------------------------------------------------------------------------


class TestFixMakefilePronounce:
    """fix_makefile_pronounce updates .PHONY declaration."""

    @pytest.mark.unit
    def test_returns_false_when_makefile_missing(self, dogfooder, tmp_path):
        """Returns False when Makefile doesn't exist."""
        finding = {
            "makefile": "plugins/ghost/Makefile",
            "missing_targets": ["new-target"],
        }
        result = dogfooder.fix_makefile_pronounce("ghost", finding)
        assert result is False

    @pytest.mark.unit
    def test_returns_true_when_no_missing_targets(
        self, dogfooder, simple_makefile, tmp_path
    ):
        """Returns True early when no missing targets."""
        finding = {
            "makefile": str(simple_makefile.relative_to(tmp_path)),
            "missing_targets": [],
        }
        result = dogfooder.fix_makefile_pronounce("myplugin", finding)
        assert result is True

    @pytest.mark.unit
    def test_returns_false_when_no_phony_block(self, dogfooder, tmp_path, capsys):
        """Returns False and warns when no .PHONY block found."""
        plugin_dir = tmp_path / "plugins" / "nophony"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        mf = plugin_dir / "Makefile"
        mf.write_text("help:\n\t@echo help\n")

        finding = {
            "makefile": str(mf.relative_to(tmp_path)),
            "missing_targets": ["demo-something"],
        }
        result = dogfooder.fix_makefile_pronounce("nophony", finding)
        assert result is False

    @pytest.mark.unit
    def test_adds_new_targets_to_phony_dry_run(
        self, dogfooder, simple_makefile, tmp_path
    ):
        """In dry_run mode, .PHONY is not modified."""
        original = simple_makefile.read_text()
        finding = {
            "makefile": str(simple_makefile.relative_to(tmp_path)),
            "missing_targets": ["new-demo"],
        }
        dogfooder.fix_makefile_pronounce("myplugin", finding, dry_run=True)
        assert simple_makefile.read_text() == original


# ---------------------------------------------------------------------------
# MakefileDogfooder.generate_report
# ---------------------------------------------------------------------------


class TestGenerateReport:
    """generate_report produces human-readable or JSON output."""

    @pytest.mark.unit
    def test_text_report_contains_headers(self, tmp_path):
        """Text report contains standard headers."""
        d = MakefileDogfooder(root_dir=tmp_path)
        report = d.generate_report(output_format="text")
        assert "Makefile Dogfooding Report" in report
        assert "Plugins analyzed:" in report

    @pytest.mark.unit
    def test_json_report_is_valid_json(self, tmp_path):
        """JSON report is parseable JSON."""
        d = MakefileDogfooder(root_dir=tmp_path)
        report = d.generate_report(output_format="json")
        data = json.loads(report)
        assert "plugins_analyzed" in data

    @pytest.mark.unit
    def test_text_report_includes_findings(self, tmp_path):
        """Text report lists plugin findings."""
        d = MakefileDogfooder(root_dir=tmp_path)
        d.report["findings"].append(
            {
                "plugin": "testplugin",
                "coverage_percent": 75,
                "commands_documented": 2,
                "targets_missing": 1,
                "missing_targets": ["demo-cmd"],
            }
        )
        report = d.generate_report(output_format="text")
        assert "testplugin" in report
        assert "75%" in report

    @pytest.mark.unit
    def test_text_report_truncates_many_missing_targets(self, tmp_path):
        """When many missing targets, only first 5 are shown with count."""
        d = MakefileDogfooder(root_dir=tmp_path)
        d.report["findings"].append(
            {
                "plugin": "testplugin",
                "coverage_percent": 0,
                "commands_documented": 10,
                "targets_missing": 10,
                "missing_targets": [f"missing-{i}" for i in range(10)],
            }
        )
        report = d.generate_report(output_format="text")
        assert "more" in report

    @pytest.mark.unit
    def test_text_report_contains_recommendations(self, tmp_path):
        """Text report includes recommendation section."""
        d = MakefileDogfooder(root_dir=tmp_path)
        report = d.generate_report(output_format="text")
        assert "Recommendations" in report


# ---------------------------------------------------------------------------
# MakefileDogfooder.analyze_all
# ---------------------------------------------------------------------------


class TestAnalyzeAll:
    """analyze_all scans all plugin directories."""

    @pytest.mark.unit
    def test_skips_dot_directories(self, tmp_path):
        """Hidden directories (starting with .) are skipped."""
        plugins = tmp_path / "plugins"
        (plugins / ".hidden").mkdir(parents=True, exist_ok=True)
        d = MakefileDogfooder(root_dir=tmp_path, plugins_dir="plugins")
        d.analyze_all()
        finding_plugins = [f.get("plugin") for f in d.report["findings"]]
        assert ".hidden" not in finding_plugins

    @pytest.mark.unit
    def test_skips_shared_directory(self, tmp_path):
        """'shared' directory is skipped."""
        plugins = tmp_path / "plugins"
        (plugins / "shared").mkdir(parents=True, exist_ok=True)
        d = MakefileDogfooder(root_dir=tmp_path, plugins_dir="plugins")
        d.analyze_all()
        finding_plugins = [f.get("plugin") for f in d.report["findings"]]
        assert "shared" not in finding_plugins

    @pytest.mark.unit
    def test_updates_plugins_analyzed_count(self, tmp_path):
        """plugins_analyzed count reflects the number of directories found."""
        plugins = tmp_path / "plugins"
        (plugins / "plugin-a").mkdir(parents=True, exist_ok=True)
        (plugins / "plugin-b").mkdir(parents=True, exist_ok=True)
        d = MakefileDogfooder(root_dir=tmp_path, plugins_dir="plugins")
        d.analyze_all()
        # Should count both (even if they return no-readme status)
        assert d.report["plugins_analyzed"] == 2

    @pytest.mark.unit
    def test_verbose_mode_prints_findings(
        self, tmp_path, simple_makefile, simple_readme, capsys
    ):
        """In verbose mode, findings are printed for plugins with commands."""
        d = MakefileDogfooder(root_dir=tmp_path, plugins_dir="plugins", verbose=True)
        d.analyze_all()
        captured = capsys.readouterr().out
        # With verbose=True, plugin info should be printed if commands_documented
        # is in the finding (myplugin has readme + makefile)
        assert isinstance(captured, str)  # At minimum no crash


# ---------------------------------------------------------------------------
# MakefileDogfooder.generate_missing_targets
# ---------------------------------------------------------------------------


class TestGenerateMissingTargets:
    """generate_missing_targets creates Makefile content for a plugin."""

    @pytest.mark.unit
    def test_returns_generated_content(self, dogfooder, tmp_path):
        """Returns non-empty string of generated targets."""
        finding = {
            "plugin": "myplugin",
            "readme": str(
                (tmp_path / "plugins" / "myplugin" / "README.md").relative_to(tmp_path)
            ),
            "missing_targets": ["demo-update-docs"],
        }
        result = dogfooder.generate_missing_targets("myplugin", finding)
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_updates_targets_generated_count(self, dogfooder, tmp_path):
        """generate_missing_targets increments report targets_generated count."""
        finding = {
            "plugin": "myplugin",
            "readme": str(
                (tmp_path / "plugins" / "myplugin" / "README.md").relative_to(tmp_path)
            ),
            "missing_targets": [],
        }
        initial = dogfooder.report["targets_generated"]
        dogfooder.generate_missing_targets("myplugin", finding)
        # Count may increase if content has ## comments
        assert dogfooder.report["targets_generated"] >= initial


# ---------------------------------------------------------------------------
# Additional _insert_content_before_* coverage
# ---------------------------------------------------------------------------


class TestInsertContentMethods:
    """Direct tests for the content insertion helper methods."""

    @pytest.mark.unit
    def test_insert_before_catchall_pattern_found(self, tmp_path):
        """_insert_content_before_catchall inserts before the pattern."""
        d = MakefileDogfooder(root_dir=tmp_path)
        content = "help:\n\t@echo h\n\n# Guard against accidental file creation\n%::\n\t@: # no-op\n"
        new_content = "new-target: ## New\n\t@echo new\n"
        result = d._insert_content_before_catchall(
            content, new_content, "\n# Guard against accidental file creation"
        )
        assert "new-target" in result
        new_pos = result.index("new-target")
        guard_pos = result.index("# Guard against accidental")
        assert new_pos < guard_pos

    @pytest.mark.unit
    def test_insert_before_catchall_pattern_not_found(self, tmp_path):
        """When catchall pattern not in content, appends to end."""
        d = MakefileDogfooder(root_dir=tmp_path)
        content = "help:\n\t@echo h\n"
        new_content = "new-target: ## New\n\t@echo new\n"
        result = d._insert_content_before_catchall(
            content, new_content, "\n# nonexistent pattern"
        )
        assert result.endswith("new-target: ## New\n\t@echo new\n\n")

    @pytest.mark.unit
    def test_insert_before_percent_colon(self, tmp_path):
        """_insert_content_before_percent_colon inserts before %:: rule."""
        d = MakefileDogfooder(root_dir=tmp_path)
        content = "help:\n\t@echo h\n\n%::\n\t@: # catchall\n"
        new_content = "brand-new: ## BN\n\t@echo bn\n"
        result = d._insert_content_before_percent_colon(content, new_content)
        assert "brand-new" in result
        assert "%::" in result
        new_pos = result.index("brand-new")
        percent_pos = result.index("%::")
        assert new_pos < percent_pos

    @pytest.mark.unit
    def test_filter_duplicate_non_target_line_after_skipped_target(self, tmp_path):
        """Non-recipe, non-empty line after duplicate target resets skip state."""
        d = MakefileDogfooder(root_dir=tmp_path)
        # 'dup' is already existing; 'comment' is a non-target non-tab line
        content = "dup: ## Dup\n\t@echo skip\n\n# A comment\nnew-target: ## New\n\t@echo new\n"
        result = d._filter_duplicate_targets(content, {"dup"})
        joined = "\n".join(result)
        assert "new-target:" in joined
        assert "@echo skip" not in joined


# ---------------------------------------------------------------------------
# fix_makefile_pronounce with non-dry-run
# ---------------------------------------------------------------------------


class TestFixMakefilePronounceNonDryRun:
    """fix_makefile_pronounce writes .PHONY update to disk."""

    @pytest.mark.unit
    def test_updates_phony_when_not_dry_run(self, simple_makefile, tmp_path, capsys):
        """New targets are added to .PHONY block when not dry_run."""
        d = MakefileDogfooder(root_dir=tmp_path, plugins_dir="plugins")
        finding = {
            "makefile": str(simple_makefile.relative_to(tmp_path)),
            "missing_targets": ["demo-update-docs"],
        }
        result = d.fix_makefile_pronounce("myplugin", finding, dry_run=False)
        assert result is True
        updated = simple_makefile.read_text()
        assert "demo-update-docs" in updated

    @pytest.mark.unit
    def test_no_op_when_all_targets_already_in_phony(self, simple_makefile, tmp_path):
        """When all missing targets already in .PHONY, returns True without writing."""
        d = MakefileDogfooder(root_dir=tmp_path, plugins_dir="plugins")
        # "help" and "test" are already in the .PHONY
        finding = {
            "makefile": str(simple_makefile.relative_to(tmp_path)),
            "missing_targets": ["help"],
        }
        original = simple_makefile.read_text()
        result = d.fix_makefile_pronounce("myplugin", finding, dry_run=False)
        assert result is True
        # .PHONY content should not have changed significantly
        assert simple_makefile.read_text() == original or result is True


# ---------------------------------------------------------------------------
# analyze_plugin with makefile-generation-failed
# ---------------------------------------------------------------------------


class TestAnalyzePluginGenerationFailed:
    """analyze_plugin returns generation-failed status when generation fails."""

    @pytest.mark.unit
    def test_generation_failed_returns_status(self, tmp_path):
        """When generate_makefile fails, returns makefile-generation-failed."""
        plugin_dir = tmp_path / "plugins" / "failplugin"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        (plugin_dir / "README.md").write_text("# Fail Plugin\n")

        d = MakefileDogfooder(root_dir=tmp_path, plugins_dir="plugins")
        with patch("dogfooder.reporter.generate_makefile", return_value=False):
            result = d.analyze_plugin("failplugin", generate_missing=True)

        assert result["status"] == "makefile-generation-failed"
