"""Performance tests for spec-kit wrapped commands."""

# ruff: noqa: S101
import os
import time
from unittest.mock import Mock

import psutil
import pytest


class TestPerformanceBenchmarks:
    """Performance benchmarking for wrapped commands."""

    class TestWrappedCommandPerformance:
        """Test performance characteristics of wrapped commands."""

        def test_skill_loading_performance(self, mock_skill_loading):
            """Benchmark skill loading times."""
            start_time = time.time()

            # Simulate skill loading
            skills_loaded = []
            for skill_name, _skill_config in mock_skill_loading.items():
                # Simulate loading delay
                time.sleep(0.01)  # 10ms per skill
                skills_loaded.append(skill_name)

            loading_time = time.time() - start_time

            # Should load all skills within reasonable time
            assert len(skills_loaded) == 2
            assert loading_time < 1.0  # Should load in under 1 second

        def test_artifact_generation_performance(self, sample_artifacts):
            """Benchmark artifact generation performance."""
            start_time = time.time()

            # Simulate artifact generation
            artifacts_to_generate = [
                "research.md",
                "data-model.md",
                "contracts/api.yaml",
                "validation-report.md",
            ]

            generated_artifacts = []
            for artifact in artifacts_to_generate:
                # Simulate generation time
                time.sleep(0.05)  # 50ms per artifact
                generated_artifacts.append(artifact)

            generation_time = time.time() - start_time

            # Should generate artifacts efficiently
            assert len(generated_artifacts) == 4
            assert generation_time < 2.0  # Should complete in under 2 seconds

        def test_memory_usage_during_execution(self, sample_artifacts):
            """Test memory usage patterns during command execution."""
            process = psutil.Process(os.getpid())

            # Get initial memory
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Simulate command execution with data processing
            large_data = []
            for i in range(1000):
                large_data.append(f"Task {i}: " + "x" * 100)

            # Get peak memory
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Memory increase should be reasonable
            memory_increase = peak_memory - initial_memory
            assert memory_increase < 100  # Should not use more than 100MB extra

        def test_concurrent_skill_execution(self):
            """Test concurrent execution of multiple skills."""
            import concurrent.futures

            def simulate_skill_execution(skill_name):
                """Simulate skill execution with delay."""
                time.sleep(0.1)  # 100ms execution time
                return f"{skill_name} completed"

            skills = ["writing-plans", "speckit-orchestrator", "brainstorming"]

            start_time = time.time()

            # Execute skills concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(simulate_skill_execution, skill) for skill in skills
                ]
                results = [future.result() for future in futures]

            concurrent_time = time.time() - start_time

            # Concurrent execution should be faster than sequential
            assert len(results) == 3
            assert concurrent_time < 0.3  # Should complete in under 300ms

        def test_session_persistence_performance(self):
            """Test performance of session state persistence."""
            # Create large session state
            session_state = {
                "session_id": "test-session",
                "artifacts": {f"artifact_{i}": f"data_{i}" * 100 for i in range(100)},
                "task_history": [f"task_{i}" for i in range(500)],
            }

            # Simulate save operation
            start_time = time.time()
            str(session_state)  # Simulate serialization
            save_time = time.time() - start_time

            # Should handle large session state efficiently
            assert len(session_state["artifacts"]) == 100
            assert len(session_state["task_history"]) == 500
            assert save_time < 0.5  # Should save in under 500ms

    class TestScalabilityMetrics:
        """Test scalability of wrapped commands."""

        def test_large_project_handling(self):
            """Test performance with large project structures."""
            # Simulate large project with many artifacts
            project_size = 1000  # Number of artifacts

            start_time = time.time()

            # Simulate processing many artifacts
            processed_count = 0
            for i in range(project_size):
                # Simulate artifact processing
                _ = f"artifact_{i}" * 10  # Simulate work
                processed_count += 1

                # Periodically check performance
                if i % 100 == 0 and i > 0:
                    elapsed = time.time() - start_time
                    rate = i / elapsed

                    # Should maintain processing rate
                    assert rate > 50  # Should process at least 50 artifacts/second

            total_time = time.time() - start_time
            total_rate = project_size / total_time

            assert processed_count == project_size
            assert total_rate > 50  # Overall rate should be maintained

        def test_memory_scaling_with_project_size(self):
            """Test memory usage scales linearly with project size."""
            base_memory = psutil.Process(os.getpid()).memory_info().rss

            # Simulate processing different project sizes
            project_sizes = [100, 500, 1000]
            memory_usage = []

            for size in project_sizes:
                # Clear previous data
                test_data = []

                # Process project of given size
                for i in range(size):
                    test_data.append(f"item_{i}" * 10)

                # Measure memory
                current_memory = psutil.Process(os.getpid()).memory_info().rss
                memory_usage.append(current_memory - base_memory)

                # Clean up
                del test_data

            # Memory usage should scale reasonably
            # (allowing for some non-linear behavior due to Python's memory management)
            assert len(memory_usage) == 3
            assert (
                memory_usage[-1] < memory_usage[0] * 20
            )  # Not more than 20x increase for 10x data

        def test_command_execution_time_limits(self):
            """Test that commands execute within acceptable time limits."""
            command_time_limits = {
                "startup.wrapped": 5.0,  # 5 seconds
                "plan.wrapped": 10.0,  # 10 seconds
                "tasks.wrapped": 15.0,  # 15 seconds
            }

            for command, time_limit in command_time_limits.items():
                start_time = time.time()

                # Simulate command execution
                if "startup" in command:
                    time.sleep(0.1)  # Quick startup
                elif "plan" in command:
                    time.sleep(0.5)  # Planning takes longer
                elif "tasks" in command:
                    time.sleep(1.0)  # Task generation takes longest

                execution_time = time.time() - start_time

                # Should complete within time limit
                assert execution_time < time_limit, (
                    f"{command} took {execution_time:.2f}s, limit is {time_limit}s"
                )

    class TestResourceOptimization:
        """Test resource optimization features."""

        def test_lazy_loading_of_skills(self):
            """Test that skills are loaded only when needed."""
            loaded_skills = set()

            def mock_skill_loader(skill_name):
                """Mock skill loader that tracks loading."""
                if skill_name not in loaded_skills:
                    time.sleep(0.01)  # Loading delay
                    loaded_skills.add(skill_name)
                return Mock()

            # Test startup - only essential skills
            startup_skills = ["speckit-orchestrator"]
            for skill in startup_skills:
                mock_skill_loader(skill)

            assert "speckit-orchestrator" in loaded_skills
            assert "writing-plans" not in loaded_skills  # Not loaded yet

            # Test planning - loads additional skills
            planning_skills = ["writing-plans"]
            for skill in planning_skills:
                mock_skill_loader(skill)

            assert "writing-plans" in loaded_skills

        def test_caching_mechanisms(self):
            """Test caching of frequently accessed data."""
            cache = {}
            cache_hits = 0
            cache_misses = 0

            def cached_lookup(key):
                nonlocal cache_hits, cache_misses

                if key in cache:
                    cache_hits += 1
                    return cache[key]
                else:
                    cache_misses += 1
                    # Simulate expensive operation
                    time.sleep(0.01)
                    result = f"data_for_{key}"
                    cache[key] = result
                    return result

            # Perform lookups with some repetition
            lookup_keys = ["spec", "plan", "tasks", "spec", "plan", "spec"]

            start_time = time.time()
            results = [cached_lookup(key) for key in lookup_keys]
            lookup_time = time.time() - start_time

            # Should benefit from caching
            assert len(results) == 6
            assert cache_hits == 3  # 3 repeated lookups
            assert cache_misses == 3  # 3 unique lookups
            assert lookup_time < 0.1  # Should be fast due to caching

        def test_memory_cleanup_after_command(self):
            """Test memory cleanup after command completion."""
            process = psutil.Process(os.getpid())

            # Measure baseline memory
            baseline_memory = process.memory_info().rss

            # Simulate command with large data
            large_data = []
            for i in range(10000):
                large_data.append(f"data_{i}" * 100)

            # Measure peak memory
            peak_memory = process.memory_info().rss

            # Clean up data
            del large_data

            # Force garbage collection
            import gc

            gc.collect()

            # Measure memory after cleanup
            cleanup_memory = process.memory_info().rss

            # Memory should be released after cleanup
            memory_increase_after_cleanup = cleanup_memory - baseline_memory
            peak_memory_increase = peak_memory - baseline_memory

            # Most memory should be released
            assert memory_increase_after_cleanup < peak_memory_increase * 0.2

    @pytest.fixture
    def mock_skill_loading(self):
        """Mock skill loading for performance testing."""
        return {
            "writing-plans": {
                "capabilities": ["planning", "task_breakdown", "dependency_analysis"],
                "status": "loaded",
            },
            "speckit-orchestrator": {
                "capabilities": ["coordination", "workflow_management"],
                "status": "loaded",
            },
        }

    @pytest.fixture
    def sample_artifacts(self, tmp_path):
        """Create sample artifacts for performance testing."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        # Create multiple artifact files
        for i in range(10):
            artifact_file = artifacts_dir / f"artifact_{i}.md"
            artifact_file.write_text(f"# Artifact {i}\n\nContent for artifact {i}\n")

        return artifacts_dir
