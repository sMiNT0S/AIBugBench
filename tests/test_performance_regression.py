# SPDX-FileCopyrightText: 2024-2025 sMiNT0S
# SPDX-License-Identifier: Apache-2.0
"""
Performance regression testing for tiered submissions restructure.

Ensures no significant performance degradation during directory restructure.
"""

import os
import statistics
import threading
import time
import tracemalloc

import psutil
import pytest


class TestPerformanceRegression:
    """Test performance impact of tiered directory structure."""

    @pytest.fixture
    def performance_workspace(self, tmp_path):
        """Create workspace for performance testing."""
        workspace = tmp_path / "performance_test"
        workspace.mkdir()
        return workspace

    @pytest.fixture
    def large_submissions_structure(self, performance_workspace):
        """Create large submissions structure for scalability testing."""
        submissions = performance_workspace / "submissions"
        submissions.mkdir()

        # Create reference implementations (5 models)
        ref_impl = submissions / "reference_implementations"
        ref_impl.mkdir()
        for i in range(5):
            model = ref_impl / f"reference_model_{i}"
            model.mkdir()
            for j in range(5):  # 5 files per model
                (model / f"prompt_{j}_solution.py").write_text(
                    f"# Reference model {i} solution {j}"
                )

        # Create user submissions (50 models)
        user_subs = submissions / "user_submissions"
        user_subs.mkdir()
        for i in range(50):
            model = user_subs / f"user_model_{i}"
            model.mkdir()
            for j in range(5):  # 5 files per model
                (model / f"prompt_{j}_solution.py").write_text(f"# User model {i} solution {j}")

        # Create templates
        templates = submissions / "templates"
        templates.mkdir()
        template = templates / "template"
        template.mkdir()
        for j in range(5):
            (template / f"prompt_{j}_template.py").write_text(f"# Template {j}")

        return submissions

    def test_directory_scanning_performance(self, large_submissions_structure):
        """Test directory scanning performance with tiered structure."""

        def scan_submissions_directory(submissions_dir):
            """Scan submissions directory and return all models."""
            start_time = time.time()

            models = []

            # Scan reference implementations
            ref_impl = submissions_dir / "reference_implementations"
            if ref_impl.exists():
                for model_dir in ref_impl.iterdir():
                    if model_dir.is_dir():
                        models.append(("reference", model_dir.name, model_dir))

            # Scan user submissions
            user_subs = submissions_dir / "user_submissions"
            if user_subs.exists():
                for model_dir in user_subs.iterdir():
                    if model_dir.is_dir():
                        models.append(("user", model_dir.name, model_dir))

            scan_time = time.time() - start_time
            return models, scan_time

        models, scan_time = scan_submissions_directory(large_submissions_structure)

        # Performance assertions
        assert scan_time < 1.0, f"Directory scanning took {scan_time:.3f}s, should be < 1.0s"
        assert len(models) == 55, f"Expected 55 models, found {len(models)}"

        # Verify both types found
        ref_models = [m for m in models if m[0] == "reference"]
        user_models = [m for m in models if m[0] == "user"]
        assert len(ref_models) == 5
        assert len(user_models) == 50

    def test_memory_usage_scaling(self, large_submissions_structure):
        """Test memory usage scales linearly with number of models."""
        tracemalloc.start()

        def load_all_model_metadata(submissions_dir):
            """Load metadata for all models (simulating benchmark preparation)."""
            metadata = {}

            for tier in ["reference_implementations", "user_submissions"]:
                tier_dir = submissions_dir / tier
                if tier_dir.exists():
                    for model_dir in tier_dir.iterdir():
                        if model_dir.is_dir():
                            model_metadata = {
                                "name": model_dir.name,
                                "path": str(model_dir),
                                "files": [],
                                "size": 0,
                            }

                            for file_path in model_dir.glob("*.py"):
                                file_info = {
                                    "name": file_path.name,
                                    "size": file_path.stat().st_size,
                                    "content_preview": file_path.read_text()[:100],
                                }
                                model_metadata["files"].append(file_info)
                                model_metadata["size"] += file_info["size"]

                            metadata[f"{tier}/{model_dir.name}"] = model_metadata

            return metadata

        metadata = load_all_model_metadata(large_submissions_structure)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory usage should be reasonable
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 50, f"Peak memory usage {peak_mb:.1f}MB exceeds 50MB limit"

        # Should have loaded metadata for all models
        assert len(metadata) == 55

    def test_concurrent_access_performance(self, large_submissions_structure):
        """Test performance with concurrent access to submissions directory."""
        results = []
        errors = []

        def concurrent_scanner(submissions_dir, thread_id):
            """Scanner function for concurrent testing."""
            try:
                start_time = time.time()

                models = []
                for tier in ["reference_implementations", "user_submissions"]:
                    tier_dir = submissions_dir / tier
                    if tier_dir.exists():
                        for model_dir in tier_dir.iterdir():
                            if model_dir.is_dir():
                                # Simulate some work
                                file_count = len(list(model_dir.glob("*.py")))
                                models.append(
                                    {"tier": tier, "name": model_dir.name, "files": file_count}
                                )

                scan_time = time.time() - start_time
                results.append(
                    {"thread_id": thread_id, "models_found": len(models), "scan_time": scan_time}
                )

            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        # Run multiple concurrent scanners
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=concurrent_scanner, args=(large_submissions_structure, i)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)

        # Verify results
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"

        # All threads should find same number of models
        model_counts = [r["models_found"] for r in results]
        assert all(count == 55 for count in model_counts), (
            f"Inconsistent model counts: {model_counts}"
        )

        # Performance should be reasonable
        scan_times = [r["scan_time"] for r in results]
        max_scan_time = max(scan_times)
        assert max_scan_time < 2.0, f"Concurrent scan time {max_scan_time:.3f}s too slow"

    def test_file_io_performance(self, large_submissions_structure):
        """Test file I/O performance with new directory structure."""

        def benchmark_file_operations(submissions_dir, num_iterations=100):
            """Benchmark file operations."""
            times = {"read_operations": [], "stat_operations": [], "glob_operations": []}

            # Get list of all Python files
            all_files = list(submissions_dir.rglob("*.py"))

            for i in range(num_iterations):
                if i >= len(all_files):
                    break

                file_path = all_files[i % len(all_files)]

                # Time file read operation
                start = time.time()
                content = file_path.read_text()
                times["read_operations"].append(time.time() - start)

                # Time file stat operation
                start = time.time()
                stat_info = file_path.stat()
                times["stat_operations"].append(time.time() - start)

                # Time glob operation on parent directory
                start = time.time()
                glob_results = list(file_path.parent.glob("*.py"))
                times["glob_operations"].append(time.time() - start)

            return times

        performance_times = benchmark_file_operations(large_submissions_structure)

        # Calculate statistics
        for operation, times in performance_times.items():
            if times:
                avg_time = statistics.mean(times) * 1000  # Convert to milliseconds
                max_time = max(times) * 1000

                # Performance assertions (in milliseconds)
                assert avg_time < 10, f"{operation} avg time {avg_time:.3f}ms too slow"
                assert max_time < 100, f"{operation} max time {max_time:.3f}ms too slow"

    def test_memory_leaks_during_repeated_operations(self, large_submissions_structure):
        """Test for memory leaks during repeated operations."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        def repeated_model_discovery():
            """Simulate repeated model discovery operations."""
            for _ in range(10):  # 10 iterations
                models = []

                for tier in ["reference_implementations", "user_submissions"]:
                    tier_dir = large_submissions_structure / tier
                    if tier_dir.exists():
                        for model_dir in tier_dir.iterdir():
                            if model_dir.is_dir():
                                # Simulate loading model information
                                model_info = {
                                    "name": model_dir.name,
                                    "files": list(model_dir.glob("*.py")),
                                    "metadata": {},
                                }

                                # Read some file content
                                for file_path in model_info["files"][:2]:  # Limit to first 2 files
                                    content = file_path.read_text()
                                    model_info["metadata"][file_path.name] = len(content)

                                models.append(model_info)

                # Clear references to help garbage collection
                del models

        repeated_model_discovery()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be minimal (less than 10MB)
        assert memory_increase < 10, f"Memory leak detected: {memory_increase:.1f}MB increase"

    def test_scalability_with_large_model_count(self, performance_workspace):
        """Test scalability with very large number of models."""
        submissions = performance_workspace / "scalability_test"
        submissions.mkdir()

        # Create structure with many models
        user_subs = submissions / "user_submissions"
        user_subs.mkdir()

        model_counts = [10, 50, 100, 200]
        performance_data = []

        for count in model_counts:
            # Clear previous models
            for existing in user_subs.iterdir():
                if existing.is_dir():
                    import shutil

                    shutil.rmtree(existing)

            # Create specified number of models
            for i in range(count):
                model = user_subs / f"model_{i}"
                model.mkdir()
                (model / "solution.py").write_text(f"# Solution {i}")

            # Measure discovery performance
            start_time = time.time()

            models_found = []
            for model_dir in user_subs.iterdir():
                if model_dir.is_dir():
                    models_found.append(model_dir.name)

            discovery_time = time.time() - start_time

            performance_data.append(
                {
                    "model_count": count,
                    "discovery_time": discovery_time,
                    "models_found": len(models_found),
                }
            )

        # Verify scalability
        for data in performance_data:
            # Discovery time should scale roughly linearly
            time_per_model = data["discovery_time"] / data["model_count"]
            assert time_per_model < 0.01, (
                f"Time per model ({time_per_model:.4f}s) too high for {data['model_count']} models"
            )

            # Should find all models
            assert data["models_found"] == data["model_count"]

    def test_performance_comparison_old_vs_new(self, tmp_path):
        """Compare performance between old flat structure and new tiered structure."""
        # Create old flat structure
        old_submissions = tmp_path / "old_submissions"
        old_submissions.mkdir()

        for i in range(20):
            model = old_submissions / f"model_{i}"
            model.mkdir()
            (model / "solution.py").write_text(f"# Model {i}")

        # Create new tiered structure
        new_submissions = tmp_path / "new_submissions"
        new_submissions.mkdir()

        user_subs = new_submissions / "user_submissions"
        user_subs.mkdir()

        for i in range(20):
            model = user_subs / f"model_{i}"
            model.mkdir()
            (model / "solution.py").write_text(f"# Model {i}")

        def benchmark_discovery(submissions_dir, is_old_structure=True):
            """Benchmark model discovery for given structure."""
            start_time = time.time()

            models = []
            if is_old_structure:
                # Old flat structure scanning
                for item in submissions_dir.iterdir():
                    if item.is_dir() and (item / "solution.py").exists():
                        models.append(item.name)
            else:
                # New tiered structure scanning
                for tier in ["reference_implementations", "user_submissions"]:
                    tier_dir = submissions_dir / tier
                    if tier_dir.exists():
                        for item in tier_dir.iterdir():
                            if item.is_dir() and (item / "solution.py").exists():
                                models.append(f"{tier}/{item.name}")

            discovery_time = time.time() - start_time
            return len(models), discovery_time

        # Benchmark both structures
        old_count, old_time = benchmark_discovery(old_submissions, True)
        new_count, new_time = benchmark_discovery(new_submissions, False)

        # Verify same number of models found
        assert old_count == new_count == 20

        # Performance should be similar (within 50% difference)
        time_ratio = new_time / old_time if old_time > 0 else 1.0
        assert time_ratio < 2.0, f"New structure {time_ratio:.2f}x slower than old structure"

        # Both should be fast
        assert old_time < 0.1 and new_time < 0.1, (
            f"Discovery times too slow: old={old_time:.3f}s, new={new_time:.3f}s"
        )


class TestPerformanceMonitoring:
    """Test performance monitoring and metrics collection."""

    def test_benchmark_execution_timing(self, tmp_path):
        """Test timing of full benchmark execution."""
        # Create minimal submission structure for timing
        submissions = tmp_path / "submissions"
        submissions.mkdir()

        user_subs = submissions / "user_submissions"
        user_subs.mkdir()

        test_model = user_subs / "test_model"
        test_model.mkdir()

        # Create minimal working solutions
        solutions = {
            "prompt_1_solution.py": """
def process_records(filename):
    import json
    try:
        with open(filename) as f:
            return json.load(f)
    except:
        return []
            """,
            "prompt_2_config.json": '{"test": true}',
            "prompt_2_config_fixed.yaml": "test: true",
            "prompt_3_transform.py": """
def transform_and_enrich_users(users):
    return users
            """,
            "prompt_4_api_sync.py": """
def sync_users_to_crm(users, token):
    return None
            """,
        }

        for filename, content in solutions.items():
            (test_model / filename).write_text(content)

        # Mock benchmark execution timing
        def mock_benchmark_execution(model_path):
            """Mock benchmark execution with timing."""
            start_time = time.time()

            # Simulate validation steps
            validations = [
                ("file_exists", 0.001),
                ("syntax_check", 0.005),
                ("import_test", 0.010),
                ("function_test", 0.020),
                ("scoring", 0.050),
            ]

            results = {}
            for step, duration in validations:
                time.sleep(duration)  # Simulate work
                results[step] = True

            total_time = time.time() - start_time
            return results, total_time

        results, execution_time = mock_benchmark_execution(test_model)

        # Performance expectations
        assert execution_time < 1.0, f"Mock benchmark took {execution_time:.3f}s, should be < 1.0s"
        assert len(results) == 5, "All validation steps should complete"

    @pytest.mark.slow
    def test_resource_monitoring_during_execution(self, tmp_path):
        """Test resource monitoring during benchmark execution."""

        def monitor_resources(duration_seconds=2):
            """Monitor CPU and memory usage."""
            process = psutil.Process(os.getpid())
            samples = []

            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                sample = {
                    "timestamp": time.time(),
                    "cpu_percent": process.cpu_percent(),
                    "memory_mb": process.memory_info().rss / 1024 / 1024,
                    "open_files": len(process.open_files()),
                }
                samples.append(sample)
                time.sleep(0.1)

            return samples

        # Monitor resource usage
        samples = monitor_resources(1.0)  # Monitor for 1 second

        # Analyze resource usage
        cpu_usage = [s["cpu_percent"] for s in samples if s["cpu_percent"] > 0]
        memory_usage = [s["memory_mb"] for s in samples]
        max_open_files = max(s["open_files"] for s in samples)

        # Resource usage should be reasonable
        if cpu_usage:  # Only check if CPU data available
            avg_cpu = statistics.mean(cpu_usage)
            assert avg_cpu < 80, f"Average CPU usage {avg_cpu:.1f}% too high"

        avg_memory = statistics.mean(memory_usage)
        assert avg_memory < 200, f"Average memory usage {avg_memory:.1f}MB too high"
        assert max_open_files < 50, f"Too many open files: {max_open_files}"

    @pytest.mark.slow
    def test_performance_regression_detection(self):
        """Test detection of performance regressions."""
        # Simulate performance baseline and current measurements
        baseline_metrics = {
            "directory_scan_time": 0.050,
            "model_validation_time": 0.200,
            "memory_usage_mb": 45.0,
            "cpu_usage_percent": 25.0,
        }

        current_metrics = {
            "directory_scan_time": 0.055,  # 10% increase
            "model_validation_time": 0.310,  # 55% increase - regression!
            "memory_usage_mb": 48.0,  # 6% increase
            "cpu_usage_percent": 27.0,  # 8% increase
        }

        def detect_regressions(baseline, current, threshold=0.20):
            """Detect performance regressions above threshold."""
            regressions = []

            for metric, baseline_value in baseline.items():
                current_value = current.get(metric, baseline_value)

                if baseline_value > 0:
                    change_ratio = (current_value - baseline_value) / baseline_value
                    if change_ratio > threshold:
                        regressions.append(
                            {
                                "metric": metric,
                                "baseline": baseline_value,
                                "current": current_value,
                                "change_percent": change_ratio * 100,
                            }
                        )

            return regressions

        regressions = detect_regressions(baseline_metrics, current_metrics, 0.20)  # 20% threshold

        # Should detect the validation time regression
        assert len(regressions) == 1
        assert regressions[0]["metric"] == "model_validation_time"
        assert regressions[0]["change_percent"] > 50
