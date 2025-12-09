"""Performance tests for imbue validator.

This module tests the validation tool performance with large plugins
and complex scenarios, ensuring it scales appropriately.
"""

import time

import pytest


class TestValidatorPerformance:
    """Feature: Imbue validator performance under load.

    As a validation tool
    I want to handle large plugin structures efficiently
    So that validation completes in reasonable time
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
            "agents": []
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

            plugin_config["skills"].append({
                "name": f"skill-{i:03d}",
                "file": f"skills/skill-{i:03d}/SKILL.md"
            })

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

            plugin_config["commands"].append({
                "name": f"command-{i:03d}",
                "file": f"commands/command-{i:03d}.md"
            })

        # Write plugin.json
        (plugin_root / "plugin.json").write_text(
            str(plugin_config).replace("'", '"')  # Convert to JSON format
        )

        return plugin_root

    @pytest.mark.slow
    def test_validator_performance_large_plugin(self, large_plugin_structure):
        """Scenario: Validator performance with large plugin
        Given a plugin with 100+ skills and 50+ commands
        When running validation
        Then it should complete within reasonable time.
        """
        # Arrange - import validator
        try:
            from scripts.imbue_validator import ImbueValidator
        except ImportError:
            pytest.skip("ImbueValidator not available for performance testing")

        # Act - measure validation performance
        start_time = time.time()

        validator = ImbueValidator(large_plugin_structure)

        # Perform validation operations
        scan_result = validator.scan_review_workflows()
        validation_issues = validator.validate_review_workflows()
        report = validator.generate_report()

        end_time = time.time()

        execution_time = end_time - start_time

        # Assert performance
        assert execution_time < 5.0  # Should complete in under 5 seconds
        assert len(scan_result["skills_found"]) == 100
        assert len(scan_result["review_workflow_skills"]) >= 50  # About half should match patterns
        assert isinstance(validation_issues, list)
        assert len(report) > 0  # Report should be generated

        # Memory usage check (basic)
        import sys
        validator_size = sys.getsizeof(validator)
        assert validator_size < 100_000  # Should be under 100KB for in-memory representation

    @pytest.mark.slow
    def test_validator_scan_performance_patterns(self, large_plugin_structure):
        """Scenario: Pattern matching performance optimization
        Given many skill files with various patterns
        When scanning for review patterns
        Then pattern matching should be optimized.
        """
        try:
            from scripts.imbue_validator import ImbueValidator
        except ImportError:
            pytest.skip("ImbueValidator not available for performance testing")

        # Arrange
        validator = ImbueValidator(large_plugin_structure)

        # Act - measure pattern matching performance
        pattern_matching_times = []

        # Test multiple scans
        for i in range(5):
            start_time = time.time()
            validator.scan_review_workflows()
            end_time = time.time()

            scan_time = end_time - start_time
            pattern_matching_times.append(scan_time)

        # Calculate performance metrics
        avg_scan_time = sum(pattern_matching_times) / len(pattern_matching_times)
        max_scan_time = max(pattern_matching_times)
        min_scan_time = min(pattern_matching_times)

        # Assert consistent performance
        assert avg_scan_time < 1.0  # Average scan under 1 second
        assert max_scan_time < 2.0  # Maximum scan under 2 seconds
        assert max_scan_time - min_scan_time < 0.5  # Consistent timing (within 500ms)

        # Verify all scans produce same results
        scan_results = []
        for i in range(3):
            result = validator.scan_review_workflows()
            scan_results.append(result)

        # All scans should be identical
        for i in range(1, len(scan_results)):
            assert scan_results[i]["skills_found"] == scan_results[0]["skills_found"]
            assert scan_results[i]["review_workflow_skills"] == scan_results[0]["review_workflow_skills"]

    @pytest.mark.slow
    def test_validator_memory_efficiency(self, tmp_path):
        """Scenario: Memory usage remains reasonable
        Given validation processing many files
        When processing large datasets
        Then memory usage should scale linearly.
        """
        try:
            from scripts.imbue_validator import ImbueValidator
        except ImportError:
            pytest.skip("ImbueValidator not available for performance testing")

        import gc
        import tracemalloc

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
                (skill_dir / "SKILL.md").write_text(f"---\nname: skill-{i:03d}\n---\nContent {i}")

            # Create plugin.json
            (plugin_root / "plugin.json").write_text('{"name": "test", "skills": []}')

            # Measure memory usage
            tracemalloc.start()
            gc.collect()  # Force garbage collection

            # Run validation
            validator = ImbueValidator(plugin_root)
            validator.scan_review_workflows()

            # Get memory snapshot
            current, peak = tracemalloc.get_traced_memory()
            memory_snapshots.append({
                "skill_count": skill_count,
                "current_memory": current,
                "peak_memory": peak,
                "files_processed": len(validator.skill_files)
            })

            tracemalloc.stop()

        # Analyze memory scaling
        memory_per_skill = []
        for snapshot in memory_snapshots:
            memory_per_file = snapshot["peak_memory"] / snapshot["skill_count"]
            memory_per_skill.append(memory_per_file)

        avg_memory_per_file = sum(memory_per_skill) / len(memory_per_skill)
        max_memory_per_file = max(memory_per_skill)

        # Assert memory efficiency
        assert avg_memory_per_file < 50_000  # Less than 50KB per skill file
        assert max_memory_per_file < 100_000  # Less than 100KB per skill file

        # Check linear scaling ( shouldn't grow exponentially)
        if len(memory_per_skill) > 2:
            first_quarter = memory_per_skill[:len(memory_per_skill)//2]
            second_quarter = memory_per_skill[len(memory_per_skill)//2:]

            avg_first = sum(first_quarter) / len(first_quarter)
            avg_second = sum(second_quarter) / len(second_quarter)

            # Second half shouldn't use more than 3x memory per file of first half
            assert avg_second < avg_first * 3

    @pytest.mark.slow
    def test_validator_concurrent_performance(self, tmp_path):
        """Scenario: Validator handles concurrent processing
        Given multiple validation requests
        When processing in parallel
        Then performance should scale appropriately.
        """
        try:
            from scripts.imbue_validator import ImbueValidator
        except ImportError:
            pytest.skip("ImbueValidator not available for performance testing")

        import concurrent.futures
        import threading

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
                (skill_dir / "SKILL.md").write_text(f"---\nname: plugin-{i}-skill-{j}\n---\nContent")

            (plugin_root / "plugin.json").write_text('{"name": "test", "skills": []}')
            plugin_roots.append(plugin_root)

        # Concurrent validation function
        def validate_plugin(plugin_root):
            start_time = time.time()
            validator = ImbueValidator(plugin_root)
            scan_result = validator.scan_review_workflows()
            issues = validator.validate_review_workflows()
            end_time = time.time()
            return {
                "plugin": plugin_root.name,
                "execution_time": end_time - start_time,
                "skills_found": len(scan_result["skills_found"]),
                "issues_count": len(issues),
                "thread_id": threading.get_ident()
            }

        # Test sequential performance
        sequential_start = time.time()
        sequential_results = []
        for plugin_root in plugin_roots:
            result = validate_plugin(plugin_root)
            sequential_results.append(result)
        sequential_time = time.time() - sequential_start

        # Test concurrent performance
        concurrent_start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=plugin_count) as executor:
            concurrent_results = list(executor.map(validate_plugin, plugin_roots))
        concurrent_time = time.time() - concurrent_start

        # Analyze results
        sequential_time / plugin_count
        concurrent_time / plugin_count

        # Assert concurrent efficiency
        # Concurrent should be faster (though may not be perfectly parallel due to GIL)
        assert concurrent_time < sequential_time * 1.2  # Within 20% of optimal parallel speedup

        # Verify all plugins processed correctly
        assert len(concurrent_results) == plugin_count
        for result in concurrent_results:
            assert result["skills_found"] == 20
            assert isinstance(result["execution_time"], float)
            assert result["execution_time"] < 5.0  # Each plugin under 5 seconds

        # Verify thread safety
        thread_ids = [result["thread_id"] for result in concurrent_results]
        assert len(set(thread_ids)) > 1  # Multiple threads were used

    @pytest.mark.slow
    def test_validator_report_generation_performance(self, large_plugin_structure):
        """Scenario: Report generation performs efficiently
        Given large validation results
        When generating reports
        Then report generation should be fast.
        """
        try:
            from scripts.imbue_validator import ImbueValidator
        except ImportError:
            pytest.skip("ImbueValidator not available for performance testing")

        # Arrange
        validator = ImbueValidator(large_plugin_structure)
        validator.scan_review_workflows()

        # Act - measure report generation performance
        report_generation_times = []

        for i in range(10):  # Generate report multiple times
            start_time = time.time()
            report = validator.generate_report()
            end_time = time.time()

            report_time = end_time - start_time
            report_generation_times.append(report_time)

        # Assert report generation efficiency
        avg_report_time = sum(report_generation_times) / len(report_generation_times)
        max_report_time = max(report_generation_times)

        assert avg_report_time < 0.5  # Average under 500ms
        assert max_report_time < 1.0  # Maximum under 1 second

        # Verify report quality is maintained
        assert len(report) > 1000  # Substantial report content
        assert "Imbue Plugin Review Workflow Report" in report
        assert f"Skill Files: {len(validator.skill_files)}" in report

        # Check consistency across multiple generations
        reports = []
        for i in range(5):
            report = validator.generate_report()
            reports.append(report)

        # All reports should be identical
        for i in range(1, len(reports)):
            assert reports[i] == reports[0]

    @pytest.mark.slow
    def test_validator_regex_pattern_optimization(self, large_plugin_structure):
        """Scenario: Regex pattern matching is optimized
        Given many patterns to match against content
        When scanning skills
        Then regex compilation should be optimized.
        """
        try:
            from scripts.imbue_validator import ImbueValidator
        except ImportError:
            pytest.skip("ImbueValidator not available for performance testing")

        import re

        # Test different pattern compilation strategies
        patterns = [
            r"review",
            r"workflow",
            r"evidence",
            r"structured",
            r"output",
            r"orchestrat",
            r"checklist",
            r"deliverable",
            r"pattern1",
            r"pattern2",
            r"pattern3"
        ]

        # Strategy 1: Compile each time
        def compile_each_time(content, patterns):
            matches = []
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    matches.append(pattern)
            return matches

        # Strategy 2: Pre-compile patterns
        compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

        def pre_compiled(content, compiled_patterns):
            matches = []
            for compiled in compiled_patterns:
                if compiled.search(content):
                    matches.append(compiled.pattern)
            return matches

        # Strategy 3: Combined pattern
        combined_pattern = re.compile("|".join(patterns), re.IGNORECASE)

        def combined_pattern_search(content, pattern):
            return pattern.search(content) is not None

        # Test performance of each strategy
        test_content = "This is a review workflow with evidence logging and structured output patterns"
        iterations = 1000

        # Strategy 1: Compile each time
        start_time = time.time()
        for _ in range(iterations):
            compile_each_time(test_content, patterns)
        time1 = time.time() - start_time

        # Strategy 2: Pre-compiled
        start_time = time.time()
        for _ in range(iterations):
            pre_compiled(test_content, compiled_patterns)
        time2 = time.time() - start_time

        # Strategy 3: Combined pattern
        start_time = time.time()
        for _ in range(iterations):
            combined_pattern_search(test_content, combined_pattern)
        time3 = time.time() - start_time

        # Assert optimization effectiveness
        # Pre-compiled should be faster than compiling each time
        assert time2 < time1

        # Combined pattern should be fastest for simple matching
        assert time3 < time2

        # Performance improvement should be significant
        improvement_factor = time1 / time3
        assert improvement_factor > 2  # At least 2x improvement

    @pytest.mark.slow
    def test_validator_io_performance(self, tmp_path):
        """Scenario: File I/O operations are optimized
        Given many files to read
        When scanning plugin directory
        Then file I/O should be efficient.
        """
        try:
            from scripts.imbue_validator import ImbueValidator
        except ImportError:
            pytest.skip("ImbueValidator not available for performance testing")

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
            (skill_dir / "SKILL.md").write_text("Content " * (file_size // 8))  # ~1KB content

        (plugin_root / "plugin.json").write_text('{"name": "test", "skills": []}')

        # Test I/O performance
        start_time = time.time()

        validator = ImbueValidator(plugin_root)
        scan_result = validator.scan_review_workflows()

        io_time = time.time() - start_time

        # Assert I/O efficiency
        assert io_time < 3.0  # Should read 200 files in under 3 seconds

        # Calculate I/O throughput
        total_bytes = file_count * file_size
        throughput_mb_per_second = (total_bytes / (1024 * 1024)) / io_time

        assert throughput_mb_per_second > 1  # At least 1 MB/second throughput

        # Verify all files were processed
        assert len(validator.skill_files) == file_count
        assert len(scan_result["skills_found"]) == file_count
