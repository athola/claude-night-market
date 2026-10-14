"""Scale tests for imbue validator.

The validator runs over large plugins, many files and parallel callers.
These tests check what holds at that scale: every file is found and read
once, results are deterministic, memory per file is bounded, and threads
share no state.
"""

from __future__ import annotations

import concurrent.futures
import gc
import sys
import threading
import tracemalloc
from pathlib import Path

import pytest
from scripts.imbue_validator import ImbueValidator

# Constants for PLR2004 magic values
TWO = 2
TWENTY = 20
HUNDRED = 100
THOUSAND = 1000
# Constants for performance thresholds
MIN_REVIEW_WORKFLOW_SKILLS = 50
MAX_VALIDATOR_SIZE_BYTES = 100_000  # 100KB
MAX_AVG_MEMORY_PER_SKILL_FILE = 50_000  # 50KB
MAX_MEMORY_PER_SKILL_FILE = 100_000  # 100KB
MIN_REPORT_LENGTH = THOUSAND
ITERATIONS_FOR_STRESS_TEST = THOUSAND

# No wall-clock thresholds: a time limit measures the host, not the
# validator. These tests assert counts, determinism across fresh
# instances, and bounded memory per file.


class TestValidatorPerformance:
    """Feature: Imbue validator behavior at scale.

    As a validation tool
    I want large plugin structures handled completely and deterministically
    So that a big plugin is validated as correctly as a small one
    """

    @pytest.fixture
    def large_plugin_structure(self, tmp_path):
        """Create a large mock plugin structure for performance testing."""
        plugin_root = tmp_path / "large-plugin"
        plugin_root.mkdir()

        # Create plugin.json
        plugin_config = {
            "name": "test-large-plugin",
            "version": "1.0.0",
            "description": "Large plugin for performance testing",
            "skills": [],
            "commands": [],
            "agents": [],
        }

        # Create many skills
        skills_dir = plugin_root / "skills"
        skills_dir.mkdir()

        for i in range(100):  # 100 skills
            skill_dir = skills_dir / f"skill-{i:03d}"
            skill_dir.mkdir()

            # Vary skill content
            skill_content = f"""---
name: skill-{i:03d}
description: Test skill number {i} for performance testing
category: {"review-patterns" if i % 2 == 0 else "utility-patterns"}
usage_patterns:
  - {"review-workflow" if i % 3 == 0 else "analysis-pattern"}
dependencies: []
tools: ["Read", "Grep", "Bash"]
tags: ["performance", "test", "skill-{i:03d}"]
---

# Skill {i:03d}

This is test skill number {i} for performance testing.

## Features
- Feature A for skill {i}
- Feature B for skill {i}
- Feature C for skill {i}

## TodoWrite Items
- `skill-{i:03d}:initialized`
- `skill-{i:03d}:completed`

## Usage
Use this skill for testing purposes.
"""
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(skill_content)

            plugin_config["skills"].append(
                {"name": f"skill-{i:03d}", "file": f"skills/skill-{i:03d}/SKILL.md"},
            )

        # Create many commands
        commands_dir = plugin_root / "commands"
        commands_dir.mkdir()

        for i in range(50):  # 50 commands
            command_file = commands_dir / f"command-{i:03d}.md"
            command_content = f"""---
name: command-{i:03d}
description: Test command {i}
usage: /command-{i:03d} [args]
---

# Command {i:03d}

Test command for performance testing.
"""
            command_file.write_text(command_content)

            plugin_config["commands"].append(
                {"name": f"command-{i:03d}", "file": f"commands/command-{i:03d}.md"},
            )

        # Write plugin.json
        (plugin_root / "plugin.json").write_text(
            str(plugin_config).replace("'", '"'),  # Convert to JSON format
        )

        return plugin_root

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_large_plugin_scan_finds_every_skill_and_reports(
        self, large_plugin_structure
    ) -> None:
        """Scenario: Validator over a large plugin.

        Given a plugin with 100 skills and 50 commands
        When running validation
        Then every skill is found, about half match the review patterns,
        and the report is produced.
        """
        # Arrange - import validator
        validator_cls = ImbueValidator

        validator = validator_cls(large_plugin_structure)

        scan_result = validator.scan_review_workflows()
        validation_issues = validator.validate_review_workflows()
        report = validator.generate_report()

        assert len(scan_result["skills_found"]) == HUNDRED
        assert (
            len(scan_result["review_workflow_skills"]) >= MIN_REVIEW_WORKFLOW_SKILLS
        )  # About half should match patterns
        assert isinstance(validation_issues, list)
        assert isinstance(report, str)
        assert "Imbue Plugin Review Workflow Report" in report

        # Memory usage check (basic)

        validator_size = sys.getsizeof(validator)
        assert (
            validator_size < MAX_VALIDATOR_SIZE_BYTES
        )  # Should be under 100KB for in-memory representation

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_fresh_validators_scan_a_large_plugin_identically(
        self, large_plugin_structure
    ) -> None:
        """Scenario: Pattern matching is deterministic.

        Given many skill files with various patterns
        When three fresh validators scan them
        Then all three find the same skills and the same review matches.
        """
        validator_cls = ImbueValidator

        # A fresh validator per scan. One instance caches its first scan,
        # and repeating scans on it would compare a result with itself.
        scan_results = [
            validator_cls(large_plugin_structure).scan_review_workflows()
            for _i in range(3)
        ]

        # All scans should be identical
        for i in range(1, len(scan_results)):
            assert scan_results[i]["skills_found"] == scan_results[0]["skills_found"]
            assert (
                scan_results[i]["review_workflow_skills"]
                == scan_results[0]["review_workflow_skills"]
            )

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_peak_memory_per_skill_file_stays_bounded(self, tmp_path) -> None:
        """Scenario: Memory per file does not grow with plugin size.

        Given plugins of 10, 25, 50 and 100 skills
        When each is scanned
        Then peak memory per skill file stays under a fixed bound.
        """
        validator_cls = ImbueValidator

        # Memory tracking
        memory_snapshots = []

        # Test with different plugin sizes
        skill_counts = [10, 25, 50, 100]

        for skill_count in skill_counts:
            # Create plugin of specific size
            plugin_root = tmp_path / f"test-plugin-{skill_count}"
            plugin_root.mkdir()

            # Create skills
            skills_dir = plugin_root / "skills"
            skills_dir.mkdir()

            for i in range(skill_count):
                skill_dir = skills_dir / f"skill-{i:03d}"
                skill_dir.mkdir()
                (skill_dir / "SKILL.md").write_text(
                    f"---\nname: skill-{i:03d}\n---\nContent {i}",
                )

            # Create plugin.json
            (plugin_root / "plugin.json").write_text('{"name": "test", "skills": []}')

            # Measure memory usage
            tracemalloc.start()
            gc.collect()  # Force garbage collection

            # Run validation
            validator_cls = ImbueValidator
            validator = validator_cls(plugin_root)
            validator.scan_review_workflows()

            # Get memory snapshot
            current, peak = tracemalloc.get_traced_memory()
            memory_snapshots.append(
                {
                    "skill_count": skill_count,
                    "current_memory": current,
                    "peak_memory": peak,
                    "files_processed": len(validator.skill_files),
                },
            )

            tracemalloc.stop()

        # Analyze memory scaling
        memory_per_skill = []
        for snapshot in memory_snapshots:
            memory_per_file = snapshot["peak_memory"] / snapshot["skill_count"]
            memory_per_skill.append(memory_per_file)

        avg_memory_per_file = sum(memory_per_skill) / len(memory_per_skill)
        max_memory_per_file = max(memory_per_skill)

        # Assert memory efficiency
        assert (
            avg_memory_per_file < MAX_AVG_MEMORY_PER_SKILL_FILE
        )  # Less than 50KB per skill file
        assert (
            max_memory_per_file < MAX_MEMORY_PER_SKILL_FILE
        )  # Less than 100KB per skill file

        # Check linear scaling ( shouldn't grow exponentially)
        if len(memory_per_skill) > TWO:
            first_quarter = memory_per_skill[: len(memory_per_skill) // 2]
            second_quarter = memory_per_skill[len(memory_per_skill) // 2 :]

            avg_first = sum(first_quarter) / len(first_quarter)
            avg_second = sum(second_quarter) / len(second_quarter)

            # Second half shouldn't use more than 3x memory per file of first half
            assert avg_second < avg_first * 3

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_concurrent_scans_match_sequential_results(self, tmp_path) -> None:
        """Scenario: Validators running in parallel threads share no state.

        Given five plugins
        When all five are validated at once on separate threads
        Then each result equals the one it gives alone.
        """
        # Create multiple plugins
        plugin_count = 5
        plugin_roots = []

        for i in range(plugin_count):
            plugin_root = tmp_path / f"concurrent-plugin-{i}"
            plugin_root.mkdir()

            # Create structure
            skills_dir = plugin_root / "skills"
            skills_dir.mkdir()

            for j in range(20):  # 20 skills per plugin
                skill_dir = skills_dir / f"skill-{j:03d}"
                skill_dir.mkdir()
                (skill_dir / "SKILL.md").write_text(
                    f"---\nname: plugin-{i}-skill-{j}\n---\nContent",
                )

            (plugin_root / "plugin.json").write_text('{"name": "test", "skills": []}')
            plugin_roots.append(plugin_root)

        # The barrier holds every concurrent call until all five are running,
        # so the comparison below is made with the threads truly overlapping.
        barrier = threading.Barrier(plugin_count, timeout=30)
        thread_ids = set()

        def validate_plugin(plugin_root, *, concurrent=False):
            if concurrent:
                thread_ids.add(threading.get_ident())
                barrier.wait()
            validator = ImbueValidator(plugin_root)
            scan_result = validator.scan_review_workflows()
            issues = validator.validate_review_workflows()
            return {
                "plugin": plugin_root.name,
                "skills_found": sorted(scan_result["skills_found"]),
                "issues": sorted(issues),
            }

        sequential_results = [validate_plugin(root) for root in plugin_roots]
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=plugin_count,
        ) as executor:
            concurrent_results = list(
                executor.map(
                    lambda root: validate_plugin(root, concurrent=True), plugin_roots
                )
            )

        # Threads share no state: each plugin scans to the same result it
        # gives alone, and no plugin sees another's skills.
        assert len(thread_ids) == plugin_count
        assert concurrent_results == sequential_results
        for result in concurrent_results:
            assert len(result["skills_found"]) == TWENTY

    @pytest.mark.slow
    def test_report_is_substantial_and_identical_across_generations(
        self, large_plugin_structure
    ) -> None:
        """Scenario: Report generation over a large plugin.

        Given scan results for a large plugin
        When the report is generated six times
        Then it names the skill count and every generation is identical.
        """
        validator_cls = ImbueValidator

        # Arrange
        validator = validator_cls(large_plugin_structure)
        validator.scan_review_workflows()

        report = validator.generate_report()

        assert len(report) > THOUSAND  # Substantial report content
        assert "Imbue Plugin Review Workflow Report" in report
        assert f"Skill Files: {len(validator.skill_files)}" in report

        # Check consistency across multiple generations
        reports = []
        for _i in range(5):
            report = validator.generate_report()
            reports.append(report)

        # All reports should be identical
        for i in range(1, len(reports)):
            assert reports[i] == reports[0]

    @pytest.mark.bdd
    def test_validator_evidence_patterns_match_regardless_of_case(
        self, tmp_path
    ) -> None:
        """Scenario: Evidence wording in capitals still counts.

        Given one skill that says EVIDENCE only in capitals and one that
            names no evidence practice at all
        When the plugin is validated
        Then only the second is reported as missing evidence logging

        The validator matches with re.IGNORECASE. Dropping the flag turns
        the first skill into a false positive.
        """
        plugin_root = tmp_path / "case-plugin"
        for name, body in (
            ("shouting", "Keep the EVIDENCE for every claim."),
            ("silent", "Nothing about practice here."),
        ):
            skill_dir = plugin_root / "skills" / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\n---\n{body}\n")
        (plugin_root / "plugin.json").write_text('{"name": "test", "skills": []}')

        issues = ImbueValidator(plugin_root).validate_review_workflows()

        assert "silent: Should have evidence logging patterns" in issues
        assert not any(issue.startswith("shouting:") for issue in issues)

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_scan_reads_each_of_200_skill_files_exactly_once(
        self, tmp_path, monkeypatch
    ) -> None:
        """Scenario: File reads are bounded by the file count.

        Given 200 skill files
        When the plugin directory is scanned
        Then every file is found and each is read exactly once.
        """
        validator_cls = ImbueValidator

        # Create plugin with many small files
        plugin_root = tmp_path / "io-performance-plugin"
        plugin_root.mkdir()

        skills_dir = plugin_root / "skills"
        skills_dir.mkdir()

        file_count = 200
        file_size = 1024  # 1KB per file

        for i in range(file_count):
            skill_dir = skills_dir / f"skill-{i:03d}"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "Content " * (file_size // 8),
            )  # ~1KB content

        (plugin_root / "plugin.json").write_text('{"name": "test", "skills": []}')

        reads: list[Path] = []
        real_read_text = Path.read_text

        def counting_read_text(path, *args, **kwargs):
            if path.name == "SKILL.md":
                reads.append(path)
            return real_read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", counting_read_text)

        validator = validator_cls(plugin_root)
        scan_result = validator.scan_review_workflows()

        assert len(validator.skill_files) == file_count
        assert len(scan_result["skills_found"]) == file_count
        assert len(reads) == file_count
        assert len(set(reads)) == file_count
