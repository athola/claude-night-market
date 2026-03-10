"""Scalability tests for imbue workflow performance.

This module tests how imbue workflows scale with large datasets,
concurrent executions, and complex scenarios.
"""

from __future__ import annotations

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

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_large_diff_analysis_scalability(
        self,
        large_change_set,
    ) -> None:
        """Scenario: Diff analysis scales with large change sets.

        Given 1000+ files changed
        When performing diff analysis
        Then performance should remain acceptable.
        """
        files_changed = large_change_set["files_changed"]
        lines_added = large_change_set["lines_added"]

        start_time = time.time()

        categorized_changes = {
            "additions": [],
            "modifications": [],
            "deletions": [],
            "renames": [],
        }

        for file_path in files_changed:
            lines_in_file = lines_added // len(files_changed)
            change = {
                "file": file_path,
                "type": "modification",
                "lines_added": lines_in_file,
                "lines_removed": lines_in_file // 4,
                "semantic_category": self._categorize_file_type(
                    file_path,
                ),
                "risk_level": self._assess_risk_level(
                    file_path,
                    lines_in_file,
                ),
            }
            categorized_changes["modifications"].append(change)

        summary = {
            "total_files": len(files_changed),
            "categories": {},
            "risk_levels": {},
        }
        for change in categorized_changes["modifications"]:
            cat = change["semantic_category"]
            summary["categories"][cat] = summary["categories"].get(cat, 0) + 1
            risk = change["risk_level"]
            summary["risk_levels"][risk] = summary["risk_levels"].get(risk, 0) + 1

        execution_time = time.time() - start_time

        assert execution_time < TWO_POINT_ZERO
        assert len(categorized_changes["modifications"]) == THOUSAND
        assert summary["total_files"] == THOUSAND
        assert len(summary["categories"]) >= 1
        assert len(summary["risk_levels"]) >= 1

        total_memory = sys.getsizeof(categorized_changes) + sys.getsizeof(summary)
        assert total_memory < MAX_MEMORY_FOR_1000_FILES


class TestEvidenceLoggingScalability:
    """Feature: Evidence logging scales with large evidence sets.

    As a review system
    I want evidence logging to perform efficiently
    So that large reviews do not slow down
    """

    @pytest.fixture
    def large_evidence_set(self):
        """Generate 10K evidence items for testing."""
        return [
            {
                "id": f"E{i:05d}",
                "command": f"test_command_{i}",
                "output": f"Output {i} with some content",
                "timestamp": datetime.now(UTC).isoformat(),
                "working_directory": "/test/repo",
                "file": f"src/file_{i % 100}.py",
                "line": (i % 200) + 1,
            }
            for i in range(TEN_THOUSAND)
        ]

    @pytest.fixture
    def evidence_log_result(self, large_evidence_set):
        """Process evidence set and return timing and summary."""
        start_time = time.time()

        evidence_log = {
            "session_id": "scalability-test",
            "timestamp": datetime.now(UTC).isoformat(),
            "evidence": [],
            "citations": [],
            "evidence_index": {},
        }

        batch_size = THOUSAND
        for i in range(0, len(large_evidence_set), batch_size):
            batch = large_evidence_set[i : i + batch_size]
            for evidence in batch:
                evidence_log["evidence"].append(evidence)
                evidence_log["evidence_index"][evidence["id"]] = evidence

        summary = {
            "total_evidence": len(evidence_log["evidence"]),
            "evidence_by_file": {},
            "commands_used": set(),
        }
        for evidence in evidence_log["evidence"]:
            fp = evidence["file"]
            summary["evidence_by_file"][fp] = summary["evidence_by_file"].get(fp, 0) + 1
            summary["commands_used"].add(evidence["command"])

        total_time = time.time() - start_time
        return evidence_log, summary, total_time

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_evidence_processing_time(
        self,
        evidence_log_result,
    ) -> None:
        """Scenario: Evidence processing completes in under 5 seconds.

        Given 10K evidence items
        When processing all items
        Then total time should be under 5 seconds.
        """
        _, _, total_time = evidence_log_result
        assert total_time < MAX_PROCESSING_TIME_SECONDS

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_evidence_count_accuracy(
        self,
        evidence_log_result,
    ) -> None:
        """Scenario: All evidence items are processed.

        Given 10K evidence items
        When processing completes
        Then total count should equal 10K.
        """
        _, summary, _ = evidence_log_result
        assert summary["total_evidence"] == TEN_THOUSAND

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_evidence_lookup_performance(
        self,
        evidence_log_result,
    ) -> None:
        """Scenario: Evidence lookup by ID is fast.

        Given an indexed evidence log
        When looking up specific evidence IDs
        Then lookup should complete in under 1ms.
        """
        evidence_log, _, _ = evidence_log_result

        lookup_start = time.time()
        for eid in ["E00001", "E05000", "E09999"]:
            found = evidence_log["evidence_index"].get(eid)
            assert isinstance(found, dict)
        lookup_time = time.time() - lookup_start

        assert lookup_time < LOOKUP_TIME_THRESHOLD

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_evidence_file_distribution(
        self,
        evidence_log_result,
    ) -> None:
        """Scenario: Evidence is distributed across files.

        Given 10K evidence items across 100 files
        When inspecting file distribution
        Then at most 100 unique files should appear.
        """
        _, summary, _ = evidence_log_result
        assert len(summary["evidence_by_file"]) <= MAX_UNIQUE_FILES_IN_EVIDENCE
        assert len(summary["commands_used"]) >= 1


class TestConcurrentWorkflowExecution:
    """Feature: Concurrent workflow execution scales properly.

    As a workflow system
    I want parallel workflows to execute efficiently
    So that resource usage is controlled
    """

    @pytest.fixture
    def concurrent_workflow_scenario(self):
        """Scenario for concurrent workflow testing."""
        return {
            "concurrent_reviews": 10,
            "concurrent_catchups": 5,
            "concurrent_agents": 3,
            "total_operations": 18,
        }

    @pytest.fixture
    def concurrent_execution_results(
        self,
        concurrent_workflow_scenario,
    ):
        """Execute concurrent workflows and return results."""
        execution_results = []
        execution_lock = threading.Lock()

        def execute_workflow(wf_id, wf_type, steps):
            start = time.time()
            tid = threading.get_ident()
            for _, duration in steps:
                time.sleep(duration)
            with execution_lock:
                execution_results.append(
                    {
                        "workflow_id": wf_id,
                        "workflow_type": wf_type,
                        "execution_time": time.time() - start,
                        "thread_id": tid,
                        "steps_completed": len(steps),
                    }
                )
            return f"{wf_type}-{wf_id}-completed"

        review_steps = [
            ("context", 0.1),
            ("scope", 0.2),
            ("evidence", 0.15),
            ("analysis", 0.3),
            ("report", 0.1),
        ]
        catchup_steps = [
            ("baseline", 0.05),
            ("changes", 0.1),
            ("insights", 0.08),
            ("followups", 0.02),
        ]
        agent_steps = [
            ("discovery", 0.2),
            ("analysis", 0.4),
            ("categorize", 0.15),
            ("recommend", 0.1),
            ("compile", 0.15),
        ]

        scenario = concurrent_workflow_scenario
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for i in range(scenario["concurrent_reviews"]):
                futures.append(
                    executor.submit(
                        execute_workflow,
                        f"review-{i}",
                        "review",
                        review_steps,
                    )
                )
            for i in range(scenario["concurrent_catchups"]):
                futures.append(
                    executor.submit(
                        execute_workflow,
                        f"catchup-{i}",
                        "catchup",
                        catchup_steps,
                    )
                )
            for i in range(scenario["concurrent_agents"]):
                futures.append(
                    executor.submit(
                        execute_workflow,
                        f"agent-{i}",
                        "agent",
                        agent_steps,
                    )
                )
            results = [f.result() for f in futures]

        total_time = time.time() - start_time
        return results, execution_results, total_time

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_all_workflows_complete(
        self,
        concurrent_execution_results,
        concurrent_workflow_scenario,
    ) -> None:
        """Scenario: All concurrent workflows complete.

        Given 18 concurrent workflows
        When executing in parallel
        Then all 18 should complete.
        """
        results, exec_results, _ = concurrent_execution_results
        expected = concurrent_workflow_scenario["total_operations"]
        assert len(results) == expected
        assert len(exec_results) == expected

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_efficiency_ratio(
        self,
        concurrent_execution_results,
    ) -> None:
        """Scenario: Parallel execution is faster than sequential.

        Given concurrent workflow results
        When comparing parallel vs sequential time
        Then speedup should be at least 1.5x.
        """
        _, exec_results, total_time = concurrent_execution_results
        sequential_estimate = sum(r["execution_time"] for r in exec_results)
        efficiency_ratio = sequential_estimate / total_time
        assert efficiency_ratio > 1.5, (
            f"Expected 1.5x speedup, got {efficiency_ratio:.2f}x"
        )

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_thread_utilization(
        self,
        concurrent_execution_results,
    ) -> None:
        """Scenario: Multiple threads are used.

        Given concurrent workflow execution
        When inspecting thread IDs
        Then at least 2 threads should be used.
        """
        _, exec_results, _ = concurrent_execution_results
        thread_ids = {r["thread_id"] for r in exec_results}
        assert len(thread_ids) >= 2

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_all_steps_completed(
        self,
        concurrent_execution_results,
    ) -> None:
        """Scenario: Each workflow completes all its steps.

        Given concurrent workflows
        When inspecting results
        Then each workflow should have completed steps.
        """
        _, exec_results, _ = concurrent_execution_results
        for result in exec_results:
            assert result["steps_completed"] >= 1
            assert result["execution_time"] > 0


class TestMemoryUsageScalability:
    """Feature: Memory usage scales appropriately.

    As a workflow system
    I want memory to remain controlled with large data
    So that the system does not run out of memory
    """

    @pytest.fixture
    def memory_test_results(self, tmp_path):
        """Execute memory-intensive workflow and return metrics."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        large_dataset = {
            "findings": [
                {
                    "id": f"F{i:05d}",
                    "title": f"Finding {i}",
                    "description": f"Description {i} " + "x" * 100,
                    "severity": [
                        "Critical",
                        "High",
                        "Medium",
                        "Low",
                    ][i % 4],
                    "file": f"src/file_{i % 100}.py",
                    "line": (i % 500) + 1,
                    "evidence_refs": [f"E{j}" for j in range(i % 10)],
                    "recommendation": f"Rec {i} " + "y" * 200,
                    "metadata": {"extra_data": "z" * 50},
                }
                for i in range(5000)
            ],
            "evidence": [
                {
                    "id": f"E{i:05d}",
                    "command": f"command_{i}",
                    "output": f"Output {i} " + "a" * 300,
                    "timestamp": "2024-12-04T10:00:00Z",
                    "context": {"extra": "b" * 100},
                }
                for i in range(10000)
            ],
        }

        gc.collect()
        after_memory = process.memory_info().rss / 1024 / 1024
        dataset_memory = after_memory - initial_memory

        start_time = time.time()
        summary = {
            "total_findings": len(large_dataset["findings"]),
            "total_evidence": len(large_dataset["evidence"]),
            "severity_distribution": {},
        }
        for finding in large_dataset["findings"]:
            sev = finding["severity"]
            summary["severity_distribution"][sev] = (
                summary["severity_distribution"].get(sev, 0) + 1
            )

        large_dataset.clear()
        gc.collect()
        processing_time = time.time() - start_time

        final_memory = process.memory_info().rss / 1024 / 1024
        final_usage = final_memory - initial_memory

        return summary, processing_time, dataset_memory, final_usage

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_memory_processing_time(
        self,
        memory_test_results,
    ) -> None:
        """Scenario: Processing large datasets is fast.

        Given 5K findings and 10K evidence items
        When processing all data
        Then processing should complete in under 3 seconds.
        """
        _, processing_time, _, _ = memory_test_results
        assert processing_time < THREE_POINT_ZERO

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_memory_data_counts(
        self,
        memory_test_results,
    ) -> None:
        """Scenario: All data items are counted.

        Given 5K findings and 10K evidence items
        When generating summary
        Then counts should match inputs.
        """
        summary, _, _, _ = memory_test_results
        assert summary["total_findings"] == FIVE_THOUSAND
        assert summary["total_evidence"] == TEN_THOUSAND
        assert len(summary["severity_distribution"]) == FOUR

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_memory_usage_controlled(
        self,
        memory_test_results,
    ) -> None:
        """Scenario: Memory usage stays within bounds.

        Given large datasets processed
        When measuring memory
        Then usage should be under 200MB total.
        """
        _, _, dataset_memory, final_usage = memory_test_results
        assert final_usage < MAX_TOTAL_MEMORY_USAGE_MB
        assert dataset_memory < MAX_DATASET_MEMORY_USAGE_MB


class TestTokenConservationScalability:
    """Feature: Token conservation scales with large inputs.

    As a workflow system
    I want token-efficient output
    So that large reviews remain within context limits
    """

    def _categorized_summary_strategy(self, items):
        """Token-efficient categorization strategy."""
        categories = {}
        for item in items:
            module = item["file"].split("/")[1] if "/" in item["file"] else "root"
            if module not in categories:
                categories[module] = {
                    "count": 0,
                    "total_size": 0,
                    "sample_files": [],
                }
            categories[module]["count"] += 1
            categories[module]["total_size"] += item["size_chars"]
            if len(categories[module]["sample_files"]) < THREE:
                categories[module]["sample_files"].append(
                    item["file"],
                )

        return [
            {
                "category": cat,
                "file_count": details["count"],
                "total_chars": details["total_size"],
                "samples": details["sample_files"],
            }
            for cat, details in categories.items()
        ]

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_token_conservation_strategies(self) -> None:
        """Scenario: Token conservation strategies reduce output size.

        Given 1000 files with content
        When applying conservation strategies
        Then summary and sample strategies should compress 90%+.
        """
        large_content = [
            {
                "file": f"src/module_{i // 50}/file_{i}.py",
                "content": "Line of content " * 100,
                "size_chars": len("Line of content " * 100),
            }
            for i in range(1000)
        ]

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

        total_input_size = sum(item["size_chars"] for item in large_content)
        results = {}
        for name, func in strategies.items():
            start = time.time()
            result = func(large_content)
            result_size = sum(len(str(item)) for item in result)
            results[name] = {
                "processing_time": time.time() - start,
                "output_items": len(result),
                "output_size_chars": result_size,
                "compression_ratio": result_size / total_input_size,
            }

        full_size = results["full_content"]["output_size_chars"]

        assert results["summary_only"]["output_size_chars"] < (full_size * 0.1)
        assert results["summary_only"]["compression_ratio"] < (ZERO_POINT_ONE)
        assert results["sample_first_10"]["output_size_chars"] < (
            full_size * COMPRESSION_RATIO_THRESHOLD
        )
        assert results["categorized_summary"]["compression_ratio"] < (ZERO_POINT_TWO)

        for result in results.values():
            assert result["processing_time"] < 1.0

        assert results["summary_only"]["output_items"] == THOUSAND
        assert results["categorized_summary"]["output_items"] <= FIFTY


class TestDatabaseScalabilitySimulation:
    """Feature: Workflow scales with database-like operations.

    As a workflow system
    I want database-style operations to remain fast
    So that large review datasets are manageable
    """

    @pytest.fixture
    def db_records(self):
        """Generate 10K database-like records."""
        return [
            {
                "id": i,
                "type": [
                    "finding",
                    "evidence",
                    "action",
                    "citation",
                ][i % 4],
                "data": f"Data {i} " + "x" * (i % 100 + 50),
                "timestamp": f"2024-12-{(i % 30) + 1:02d}",
                "tags": [f"tag_{j}" for j in range(i % 5)],
            }
            for i in range(10000)
        ]

    @pytest.fixture
    def db_operation_results(self, db_records):
        """Run all DB-style operations and return timings."""
        timings = {}

        start = time.time()
        filtered_by_type = {}
        for record in db_records:
            rt = record["type"]
            filtered_by_type.setdefault(rt, []).append(record)
        timings["filter_by_type"] = time.time() - start

        start = time.time()
        grouped_by_date = {}
        for record in db_records:
            d = record["timestamp"]
            grouped_by_date.setdefault(d, []).append(record)
        timings["group_by_date"] = time.time() - start

        start = time.time()
        search_results = [r for r in db_records if "Data 42" in r["data"]]
        timings["search_content"] = time.time() - start

        start = time.time()
        stats = {
            "total_records": len(db_records),
            "records_by_type": dict.fromkeys(
                ["finding", "evidence", "action", "citation"],
                0,
            ),
            "avg_data_size": (
                sum(len(r["data"]) for r in db_records) / len(db_records)
            ),
            "unique_tags": set(),
        }
        for record in db_records:
            stats["records_by_type"][record["type"]] += 1
            stats["unique_tags"].update(record["tags"])
        stats["unique_tags"] = len(stats["unique_tags"])
        timings["aggregate_stats"] = time.time() - start

        start = time.time()
        findings = [r for r in db_records if r["type"] == "finding"]
        evidence = [r for r in db_records if r["type"] == "evidence"]
        join_results = []
        for finding in findings[:100]:
            related = [e for e in evidence[:100] if finding["id"] % 10 == e["id"] % 10]
            join_results.append(
                {
                    "finding": finding,
                    "related_evidence": related,
                }
            )
        timings["complex_join"] = time.time() - start

        return {
            "timings": timings,
            "filtered_by_type": filtered_by_type,
            "grouped_by_date": grouped_by_date,
            "search_results": search_results,
            "stats": stats,
            "join_results": join_results,
        }

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_db_total_operation_time(
        self,
        db_operation_results,
    ) -> None:
        """Scenario: All DB operations complete in under 5 seconds.

        Given 10K records
        When running filter, group, search, aggregate, join
        Then total time should be under 5 seconds.
        """
        total = sum(db_operation_results["timings"].values())
        assert total < FIVE_POINT_ZERO

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_db_operation_correctness(
        self,
        db_operation_results,
    ) -> None:
        """Scenario: DB operations produce correct results.

        Given 10K records with 4 types and 30 dates
        When running operations
        Then counts should match expected values.
        """
        r = db_operation_results
        assert len(r["filtered_by_type"]) == FOUR
        assert len(r["grouped_by_date"]) == THIRTY
        assert r["stats"]["total_records"] == TEN_THOUSAND
        assert len(r["join_results"]) == HUNDRED
        assert r["stats"]["unique_tags"] >= 1

    @pytest.mark.bdd
    @pytest.mark.slow
    def test_db_time_per_record(
        self,
        db_operation_results,
        db_records,
    ) -> None:
        """Scenario: Per-record processing is under 1ms.

        Given 10K records
        When measuring time per record
        Then it should be under 1ms (O(n) scaling).
        """
        total = sum(db_operation_results["timings"].values())
        time_per_record = total / len(db_records)
        assert time_per_record < TIME_PER_RECORD_THRESHOLD
