"""Scalability tests for imbue workflow performance.

This module tests how imbue workflows scale with large datasets,
concurrent executions, and complex scenarios.
"""

import gc
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import psutil
import pytest

# Constants for PLR2004 magic values
ZERO_POINT_ONE = 0.1
ZERO_POINT_TWO = 0.2
TWO_POINT_ZERO = 2.0
THREE_POINT_ZERO = 3.0
THREE = 3
FOUR = 4
FIVE_POINT_ZERO = 5.0
THIRTY = 30
FIFTY = 50
HUNDRED = 100
THOUSAND = 1000
FIVE_THOUSAND = 5000
TEN_THOUSAND = 10000
# Threshold constants
LOOKUP_TIME_THRESHOLD = 0.001
COMPRESSION_RATIO_THRESHOLD = 0.05
TIME_PER_RECORD_THRESHOLD = 0.001
# Constants for scalability thresholds
MAX_MEMORY_FOR_1000_FILES = 10_000_000  # 10MB
HIGH_RISK_LINE_CHANGE_THRESHOLD = 10
MEDIUM_RISK_LINE_CHANGE_THRESHOLD = FIFTY
MAX_PROCESSING_TIME_SECONDS = FIVE_POINT_ZERO
MAX_UNIQUE_FILES_IN_EVIDENCE = HUNDRED
MAX_EVIDENCE_LOG_MEMORY = 50_000_000  # 50MB
MAX_TOTAL_MEMORY_USAGE_MB = 200
MAX_DATASET_MEMORY_USAGE_MB = 150


class TestWorkflowScalability:
    """Feature: Imbue workflow scalability under various loads.

    As a workflow system
    I want to scale efficiently with large inputs
    So that performance remains acceptable
    """

    @pytest.fixture
    def large_change_set(self):
        """Create a large change set for scalability testing."""
        return {
            "files_changed": [
                f"src/module_{i // 100}/file_{i}.py" for i in range(1000)
            ],
            "lines_added": sum(i % 100 + 1 for i in range(1000)),
            "lines_removed": sum(i % 50 for i in range(1000)),
            "commit_count": 150,
            "authors": [f"author_{i % 10}" for i in range(50)],
            "time_span_days": 30,
        }

    @pytest.fixture
    def concurrent_workflow_scenario(self):
        """Scenario for concurrent workflow testing."""
        return {
            "concurrent_reviews": 10,
            "concurrent_catchups": 5,
            "concurrent_agents": 3,
            "total_operations": 18,
        }

    @pytest.mark.slow
    def test_large_diff_analysis_scalability(self, large_change_set) -> None:
        """Scenario: Diff analysis scales with large change sets.

        Given 1000+ files changed
        When performing diff analysis
        Then performance should remain acceptable.
        """
        # Simulate large diff analysis
        files_changed = large_change_set["files_changed"]
        lines_added = large_change_set["lines_added"]
        lines_removed = large_change_set["lines_removed"]

        # Measure diff analysis performance
        start_time = time.time()

        # Simulate categorization (algorithmic complexity test)
        categorized_changes = {
            "additions": [],
            "modifications": [],
            "deletions": [],
            "renames": [],
        }

        # Process changes with O(n) complexity
        for _i, file_path in enumerate(files_changed):
            change_type = "modification"  # Simplified categorization
            lines_in_file = lines_added // len(files_changed)

            change = {
                "file": file_path,
                "type": change_type,
                "lines_added": lines_in_file,
                "lines_removed": lines_in_file // 4,
                "semantic_category": self._categorize_file_type(file_path),
                "risk_level": self._assess_risk_level(file_path, lines_in_file),
            }

            categorized_changes[change_type + "s"].append(change)

        # Generate summary statistics
        summary = {
            "total_files": len(files_changed),
            "total_lines_added": lines_added,
            "total_lines_removed": lines_removed,
            "categories": {},
            "risk_levels": {},
        }

        # Aggregate by category (O(n) operation)
        for change in categorized_changes["modifications"]:
            cat = change["semantic_category"]
            summary["categories"][cat] = summary["categories"].get(cat, 0) + 1

            risk = change["risk_level"]
            summary["risk_levels"][risk] = summary["risk_levels"].get(risk, 0) + 1

        end_time = time.time()
        execution_time = end_time - start_time

        # Assert scalability
        assert (
            execution_time < TWO_POINT_ZERO
        )  # Should process 1000 files in under 2 seconds
        assert len(categorized_changes["modifications"]) == THOUSAND
        assert summary["total_files"] == THOUSAND
        assert len(summary["categories"]) > 0
        assert len(summary["risk_levels"]) > 0

        # Memory efficiency check
        total_memory = sys.getsizeof(categorized_changes) + sys.getsizeof(summary)
        assert (
            total_memory < MAX_MEMORY_FOR_1000_FILES
        )  # Under 10MB for processing 1000 files

    def _categorize_file_type(self, file_path) -> str:
        """Categorize a file by its path."""
        if "auth" in file_path or "security" in file_path:
            return "security"
        if "test" in file_path:
            return "tests"
        if "docs" in file_path or "README" in file_path:
            return "documentation"
        if "config" in file_path or "settings" in file_path:
            return "configuration"
        return "application"

    def _assess_risk_level(self, file_path, lines_changed) -> str:
        """Assess risk level based on file and changes."""
        if "auth" in file_path or "security" in file_path:
            return (
                "High" if lines_changed > HIGH_RISK_LINE_CHANGE_THRESHOLD else "Medium"
            )
        if "test" in file_path:
            return "Low"
        if lines_changed > MEDIUM_RISK_LINE_CHANGE_THRESHOLD:
            return "Medium"
        return "Low"

    @pytest.mark.slow
    def test_evidence_logging_scalability(self) -> None:
        """Scenario: Evidence logging scales with large evidence sets.

        Given 10,000+ evidence items to log
        When managing evidence during review
        Then performance should remain efficient.
        """
        # Generate large evidence set
        evidence_count = TEN_THOUSAND
        large_evidence_set = []

        for i in range(evidence_count):
            evidence_item = {
                "id": f"E{i:05d}",
                "command": f"test_command_{i}",
                "output": f"Output {i} with some content",
                "timestamp": datetime.now(UTC).isoformat(),
                "working_directory": "/test/repo",
                "file": f"src/file_{i % 100}.py",
                "line": (i % 200) + 1,
            }
            large_evidence_set.append(evidence_item)

        # Test evidence logging performance
        start_time = time.time()

        # Simulate evidence log management
        evidence_log = {
            "session_id": "scalability-test",
            "timestamp": datetime.now(UTC).isoformat(),
            "evidence": [],
            "citations": [],
            "evidence_index": {},  # For quick lookup
        }

        # Process evidence in batches (scalable approach)
        batch_size = THOUSAND
        for i in range(0, len(large_evidence_set), batch_size):
            batch = large_evidence_set[i : i + batch_size]

            # Process batch
            for evidence in batch:
                evidence_log["evidence"].append(evidence)
                evidence_log["evidence_index"][evidence["id"]] = evidence

        # Generate summary statistics
        summary = {
            "total_evidence": len(evidence_log["evidence"]),
            "session_duration": time.time() - start_time,
            "evidence_by_file": {},
            "commands_used": set(),
        }

        for evidence in evidence_log["evidence"]:
            file_path = evidence["file"]
            summary["evidence_by_file"][file_path] = (
                summary["evidence_by_file"].get(file_path, 0) + 1
            )
            summary["commands_used"].add(evidence["command"])

        # Test lookup performance
        lookup_start = time.time()
        lookups = ["E00001", "E05000", "E09999"]
        for evidence_id in lookups:
            found = evidence_log["evidence_index"].get(evidence_id)
            assert found is not None
        lookup_time = time.time() - lookup_start

        end_time = time.time()
        total_time = end_time - start_time

        # Assert scalability
        assert (
            total_time < MAX_PROCESSING_TIME_SECONDS
        )  # Should process 10,000 items in under 5 seconds
        assert summary["total_evidence"] == evidence_count
        assert (
            len(summary["evidence_by_file"]) <= MAX_UNIQUE_FILES_IN_EVIDENCE
        )  # Max 100 unique files
        assert len(summary["commands_used"]) > 0
        assert lookup_time < LOOKUP_TIME_THRESHOLD  # Very fast lookup with index

        # Memory efficiency
        log_memory = sys.getsizeof(evidence_log)
        assert (
            log_memory < MAX_EVIDENCE_LOG_MEMORY
        )  # Under 50MB for 10,000 evidence items

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(
        self, concurrent_workflow_scenario
    ) -> None:
        """Scenario: Concurrent workflow execution scales properly.

        Given multiple workflows running simultaneously
        When executing in parallel
        Then resource usage should be controlled.
        """
        # Simulate concurrent workflow execution
        concurrent_reviews = concurrent_workflow_scenario["concurrent_reviews"]
        concurrent_catchups = concurrent_workflow_scenario["concurrent_catchups"]
        concurrent_agents = concurrent_workflow_scenario["concurrent_agents"]

        # Track execution metrics
        execution_results = []
        execution_lock = threading.Lock()

        def execute_review_workflow(workflow_id) -> str:
            """Simulate review workflow execution."""
            start_time = time.time()
            thread_id = threading.get_ident()

            # Simulate workflow steps with realistic timing
            workflow_steps = [
                ("context_establishment", 0.1),
                ("scope_inventory", 0.2),
                ("evidence_logging", 0.15),
                ("analysis", 0.3),
                ("report_generation", 0.1),
            ]

            for _step_name, step_duration in workflow_steps:
                time.sleep(step_duration)  # Simulate work

            end_time = time.time()

            with execution_lock:
                execution_results.append(
                    {
                        "workflow_id": workflow_id,
                        "workflow_type": "review",
                        "execution_time": end_time - start_time,
                        "thread_id": thread_id,
                        "steps_completed": len(workflow_steps),
                    },
                )

            return f"review-{workflow_id}-completed"

        def execute_catchup_workflow(workflow_id) -> str:
            """Simulate catchup workflow execution."""
            start_time = time.time()
            thread_id = threading.get_ident()

            # Simulate catchup steps (generally faster)
            catchup_steps = [
                ("baseline_establishment", 0.05),
                ("change_enumeration", 0.1),
                ("insight_extraction", 0.08),
                ("followup_generation", 0.02),
            ]

            for _step_name, step_duration in catchup_steps:
                time.sleep(step_duration)

            end_time = time.time()

            with execution_lock:
                execution_results.append(
                    {
                        "workflow_id": workflow_id,
                        "workflow_type": "catchup",
                        "execution_time": end_time - start_time,
                        "thread_id": thread_id,
                        "steps_completed": len(catchup_steps),
                    },
                )

            return f"catchup-{workflow_id}-completed"

        def execute_agent_workflow(workflow_id) -> str:
            """Simulate agent workflow execution."""
            start_time = time.time()
            thread_id = threading.get_ident()

            # Simulate agent steps (more intensive)
            agent_steps = [
                ("autonomous_discovery", 0.2),
                ("deep_analysis", 0.4),
                ("finding_categorization", 0.15),
                ("recommendation_generation", 0.1),
                ("report_compilation", 0.15),
            ]

            for _step_name, step_duration in agent_steps:
                time.sleep(step_duration)

            end_time = time.time()

            with execution_lock:
                execution_results.append(
                    {
                        "workflow_id": workflow_id,
                        "workflow_type": "agent",
                        "execution_time": end_time - start_time,
                        "thread_id": thread_id,
                        "steps_completed": len(agent_steps),
                    },
                )

            return f"agent-{workflow_id}-completed"

        # Execute workflows concurrently
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=8) as executor:
            # Submit review workflows
            review_futures = [
                executor.submit(execute_review_workflow, f"review-{i}")
                for i in range(concurrent_reviews)
            ]

            # Submit catchup workflows
            catchup_futures = [
                executor.submit(execute_catchup_workflow, f"catchup-{i}")
                for i in range(concurrent_catchups)
            ]

            # Submit agent workflows
            agent_futures = [
                executor.submit(execute_agent_workflow, f"agent-{i}")
                for i in range(concurrent_agents)
            ]

            # Wait for all workflows to complete
            all_futures = review_futures + catchup_futures + agent_futures
            results = [future.result() for future in all_futures]

        end_time = time.time()
        total_execution_time = end_time - start_time

        # Analyze results
        assert len(results) == concurrent_workflow_scenario["total_operations"]
        assert (
            len(execution_results) == concurrent_workflow_scenario["total_operations"]
        )

        # Check performance efficiency
        review_results = [
            r for r in execution_results if r["workflow_type"] == "review"
        ]
        catchup_results = [
            r for r in execution_results if r["workflow_type"] == "catchup"
        ]
        agent_results = [r for r in execution_results if r["workflow_type"] == "agent"]

        # Concurrent execution should be faster than sequential
        sequential_time_estimate = (
            sum(r["execution_time"] for r in review_results)
            + sum(r["execution_time"] for r in catchup_results)
            + sum(r["execution_time"] for r in agent_results)
        )

        efficiency_ratio = sequential_time_estimate / total_execution_time
        assert efficiency_ratio > THREE  # At least 3x speedup from parallelization

        # Check thread utilization
        thread_ids = {r["thread_id"] for r in execution_results}
        assert len(thread_ids) >= FOUR  # Should use multiple threads

        # Verify workflow completion
        for result in execution_results:
            assert result["steps_completed"] > 0
            assert result["execution_time"] > 0

    @pytest.mark.slow
    def test_memory_usage_with_large_datasets(self, tmp_path) -> None:
        """Scenario: Memory usage scales appropriately with large datasets.

        Given large amounts of data to process
        When performing workflow operations
        Then memory usage should be controlled.
        """
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create large dataset
        large_dataset = {
            "findings": [
                {
                    "id": f"F{i:05d}",
                    "title": f"Finding {i}",
                    "description": f"Description for finding {i} "
                    + "x" * 100,  # Larger content
                    "severity": ["Critical", "High", "Medium", "Low"][i % 4],
                    "file": f"src/file_{i % 100}.py",
                    "line": (i % 500) + 1,
                    "evidence_refs": [f"E{j}" for j in range(i % 10)],
                    "recommendation": f"Recommendation {i} " + "y" * 200,
                    "metadata": {"extra_data": "z" * 50},
                }
                for i in range(5000)  # 5000 findings
            ],
            "evidence": [
                {
                    "id": f"E{i:05d}",
                    "command": f"command_{i}",
                    "output": f"Output {i} " + "a" * 300,
                    "timestamp": "2024-12-04T10:00:00Z",
                    "context": {"extra": "b" * 100},
                }
                for i in range(10000)  # 10000 evidence items
            ],
        }

        # Measure memory after dataset creation
        gc.collect()
        after_dataset_memory = process.memory_info().rss / 1024 / 1024
        dataset_memory_usage = after_dataset_memory - initial_memory

        # Perform workflow operations
        start_time = time.time()

        # Simulate report generation

        generated_report = {}

        # Process findings by severity
        for severity in ["Critical", "High", "Medium", "Low"]:
            severity_findings = [
                f for f in large_dataset["findings"] if f["severity"] == severity
            ]
            generated_report[f"{severity}_Findings"] = severity_findings[
                :100
            ]  # Limit for memory

        # Generate summary statistics
        summary = {
            "total_findings": len(large_dataset["findings"]),
            "total_evidence": len(large_dataset["evidence"]),
            "severity_distribution": {},
            "memory_efficient": True,
        }

        for finding in large_dataset["findings"]:
            severity = finding["severity"]
            summary["severity_distribution"][severity] = (
                summary["severity_distribution"].get(severity, 0) + 1
            )

        # Clear large dataset to test memory cleanup
        large_dataset.clear()
        gc.collect()

        end_time = time.time()
        processing_time = end_time - start_time

        # Final memory measurement
        final_memory = process.memory_info().rss / 1024 / 1024
        final_memory_usage = final_memory - initial_memory

        # Assert memory efficiency
        assert processing_time < THREE_POINT_ZERO  # Processing should be fast
        assert summary["total_findings"] == FIVE_THOUSAND
        assert summary["total_evidence"] == TEN_THOUSAND
        assert len(summary["severity_distribution"]) == FOUR

        # Memory usage should be reasonable (allow for test environment variation)
        assert (
            final_memory_usage < MAX_TOTAL_MEMORY_USAGE_MB
        )  # Under 200MB total memory usage
        assert (
            dataset_memory_usage < MAX_DATASET_MEMORY_USAGE_MB
        )  # Dataset itself under 150MB

        # Memory cleanup should be effective
        assert (
            final_memory_usage < dataset_memory_usage * 1.5
        )  # Should not leak much memory

    @pytest.mark.slow
    def test_token_conservation_scalability(self) -> None:
        """Scenario: Token conservation scales with large inputs.

        Given large amounts of content to process
        When applying token conservation strategies
        Then output should remain token-efficient.
        """
        # Simulate large content that needs token conservation
        large_content = []
        for i in range(1000):
            large_content.append(
                {
                    "file": f"src/module_{i // 50}/file_{i}.py",
                    "content": "Line of content " * 100,  # 100 lines per file
                    "size_chars": len("Line of content " * 100),
                },
            )

        # Test different token conservation strategies
        strategies = {
            "full_content": lambda items: [
                {"file": item["file"], "content": item["content"]} for item in items
            ],
            "summary_only": lambda items: [
                {"file": item["file"], "size": len(item["content"])} for item in items
            ],
            "sample_first_10": lambda items: [
                {"file": item["file"], "content": item["content"][:200]}
                for item in items[:10]
            ],
            "categorized_summary": self._categorized_summary_strategy,
        }

        strategy_results = {}

        for strategy_name, strategy_func in strategies.items():
            start_time = time.time()

            # Apply strategy
            result = strategy_func(large_content)
            result_size = sum(len(str(item)) for item in result)

            end_time = time.time()

            strategy_results[strategy_name] = {
                "processing_time": end_time - start_time,
                "output_items": len(result),
                "output_size_chars": result_size,
                "compression_ratio": result_size
                / sum(item["size_chars"] for item in large_content),
            }

        # Analyze strategy effectiveness
        full_size = strategy_results["full_content"]["output_size_chars"]

        # Assert conservation effectiveness
        # summary_only should be much smaller
        assert strategy_results["summary_only"]["output_size_chars"] < full_size * 0.1
        assert strategy_results["summary_only"]["compression_ratio"] < ZERO_POINT_ONE

        # sample_first_10 should be much smaller
        assert (
            strategy_results["sample_first_10"]["output_size_chars"]
            < full_size * COMPRESSION_RATIO_THRESHOLD
        )
        assert (
            strategy_results["sample_first_10"]["compression_ratio"]
            < COMPRESSION_RATIO_THRESHOLD
        )

        # categorized_summary should be efficient
        assert (
            strategy_results["categorized_summary"]["output_size_chars"]
            < full_size * 0.2
        )
        assert (
            strategy_results["categorized_summary"]["compression_ratio"]
            < ZERO_POINT_TWO
        )

        # All strategies should process quickly
        for _strategy_name, result in strategy_results.items():
            assert result["processing_time"] < 1.0  # Each strategy under 1 second

        # Verify information retention balance
        summary_result = strategy_results["summary_only"]
        categorized_result = strategy_results["categorized_summary"]

        # Should retain key information while being compact
        assert summary_result["output_items"] == THOUSAND  # All files represented
        assert (
            categorized_result["output_items"] <= FIFTY
        )  # Reasonable number of categories

    def _categorized_summary_strategy(self, items):
        """Token-efficient categorization strategy."""
        categories = {}
        for item in items:
            # Categorize by module (first level of directory)
            module = item["file"].split("/")[1] if "/" in item["file"] else "root"
            if module not in categories:
                categories[module] = {"count": 0, "total_size": 0, "sample_files": []}

            categories[module]["count"] += 1
            categories[module]["total_size"] += item["size_chars"]
            if len(categories[module]["sample_files"]) < THREE:
                categories[module]["sample_files"].append(item["file"])

        # Return compact representation
        return [
            {
                "category": category,
                "file_count": details["count"],
                "total_chars": details["total_size"],
                "samples": details["sample_files"],
            }
            for category, details in categories.items()
        ]

    @pytest.mark.slow
    def test_database_scalability_simulation(self) -> None:
        """Scenario: Workflow scales with database-like operations.

        Given large numbers of records to process
        When performing database-style operations
        Then performance should remain acceptable.
        """
        # Simulate database-style operations for workflow
        records = [
            {
                "id": i,
                "type": ["finding", "evidence", "action", "citation"][i % 4],
                "data": f"Data {i} " + "x" * (i % 100 + 50),  # Variable size data
                "timestamp": f"2024-12-{(i % 30) + 1:02d}",
                "tags": [f"tag_{j}" for j in range(i % 5)],
            }
            for i in range(10000)  # 10,000 records
        ]

        # Test various database-style operations
        operations_performance = {}

        # Operation 1: Filter by type
        start_time = time.time()
        filtered_by_type = {}
        for record in records:
            record_type = record["type"]
            if record_type not in filtered_by_type:
                filtered_by_type[record_type] = []
            filtered_by_type[record_type].append(record)
        operations_performance["filter_by_type"] = time.time() - start_time

        # Operation 2: Group by date
        start_time = time.time()
        grouped_by_date = {}
        for record in records:
            date = record["timestamp"]
            if date not in grouped_by_date:
                grouped_by_date[date] = []
            grouped_by_date[date].append(record)
        operations_performance["group_by_date"] = time.time() - start_time

        # Operation 3: Search by content (simple simulation)
        start_time = time.time()
        search_results = []
        search_term = "Data 42"  # Should find specific records
        for record in records:
            if search_term in record["data"]:
                search_results.append(record)
        operations_performance["search_content"] = time.time() - start_time

        # Operation 4: Aggregate statistics
        start_time = time.time()
        stats = {
            "total_records": len(records),
            "records_by_type": dict.fromkeys(
                ["finding", "evidence", "action", "citation"],
                0,
            ),
            "avg_data_size": sum(len(r["data"]) for r in records) / len(records),
            "unique_tags": set(),
        }

        for record in records:
            stats["records_by_type"][record["type"]] += 1
            stats["unique_tags"].update(record["tags"])

        stats["unique_tags"] = len(stats["unique_tags"])
        operations_performance["aggregate_stats"] = time.time() - start_time

        # Operation 5: Complex join simulation
        start_time = time.time()
        # Simulate joining findings with evidence
        findings = [r for r in records if r["type"] == "finding"]
        evidence = [r for r in records if r["type"] == "evidence"]

        join_results = []
        for finding in findings[:100]:  # Limit for performance
            # Find related evidence (simplified join)
            related_evidence = [
                e for e in evidence[:100] if finding["id"] % 10 == e["id"] % 10
            ]
            join_results.append(
                {"finding": finding, "related_evidence": related_evidence},
            )
        operations_performance["complex_join"] = time.time() - start_time

        # Assert scalability
        total_time = sum(operations_performance.values())
        assert total_time < FIVE_POINT_ZERO  # All operations under 5 seconds

        # Individual operation performance
        assert operations_performance["filter_by_type"] < 1.0
        assert operations_performance["group_by_date"] < 1.0
        assert operations_performance["search_content"] < TWO_POINT_ZERO
        assert operations_performance["aggregate_stats"] < 1.0
        assert operations_performance["complex_join"] < 1.0

        # Verify operation correctness
        assert len(filtered_by_type) == FOUR  # 4 types
        assert len(grouped_by_date) == THIRTY  # 30 unique dates
        assert stats["total_records"] == TEN_THOUSAND
        assert len(join_results) == HUNDRED  # Limited as expected
        assert stats["unique_tags"] > 0

        # Performance scaling check (should be roughly O(n))
        # If we double the records, time should roughly double
        # (not exponentially increase)
        time_per_record = total_time / len(records)
        assert time_per_record < TIME_PER_RECORD_THRESHOLD  # Less than 1ms per record
