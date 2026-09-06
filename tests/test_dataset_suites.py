"""
Unit Tests for Benchmark Suite Loader and Task Schema Integrity:
- Validates all 6 formal benchmark suites and arm perturbation suite
- Verifies exact 60-task defensible matrix aggregation
- Asserts unique task IDs and schema completeness across all tasks
"""

import pytest
from core.schemas import UniversalTask
from datasets.loader import filter_tasks, get_all_tasks, get_benchmark_suite, get_task_by_id


class TestDatasetSuites:
    """Tests evaluating dataset loader completeness and task definitions."""

    def test_get_all_tasks_exact_sixty(self):
        tasks = get_all_tasks()
        assert len(tasks) == 60, f"Expected exactly 60 tasks across the 6 formal suites, got {len(tasks)}"

        # Verify task IDs are strictly unique
        task_ids = [t.task_id for t in tasks]
        assert len(task_ids) == len(set(task_ids)), "Duplicate task ID found in 60-task matrix!"

    def test_suite_names_and_counts(self):
        # 1. Enterprise: 18 tasks
        ent = get_benchmark_suite("enterprise")
        assert len(ent) == 18

        # 2. InjecAgent: 12 tasks
        sec = get_benchmark_suite("injecagent")
        assert len(sec) == 12

        # 3. GAIA: 10 tasks
        gaia = get_benchmark_suite("gaia")
        assert len(gaia) == 10

        # 4. ToolBench: 10 tasks
        tool = get_benchmark_suite("toolbench")
        assert len(tool) == 10

        # 5. HotpotQA: 5 tasks
        hotpot = get_benchmark_suite("hotpotqa")
        assert len(hotpot) == 5

        # 6. SWE-bench: 5 tasks
        swe = get_benchmark_suite("swebench")
        assert len(swe) == 5

        # Arm Perturbation: 5 tasks
        arm = get_benchmark_suite("arm_perturbation")
        assert len(arm) == 5

        # 'all' suite
        all_tasks = get_benchmark_suite("all")
        assert len(all_tasks) == 60

    def test_invalid_suite_name_raises_error(self):
        with pytest.raises(ValueError, match="Unknown benchmark suite"):
            get_benchmark_suite("nonexistent_suite_xyz")

    def test_all_tasks_conform_to_schema(self):
        all_tasks = get_all_tasks() + get_benchmark_suite("arm_perturbation")
        for task in all_tasks:
            assert isinstance(task, UniversalTask)
            assert bool(task.task_id.strip())
            assert bool(task.name.strip())
            assert bool(task.objective.strip())
            assert task.expected_schema is not None
            assert task.frozen_rubric is not None
            assert isinstance(task.allowed_tools, list)
            assert task.complexity is not None
            assert task.family is not None
            assert task.dataset_source is not None

    def test_get_task_by_id_lookup(self):
        # Case insensitive lookup
        t1 = get_task_by_id("t01")
        assert t1 is not None and t1.task_id == "T01"

        sec1 = get_task_by_id("sec01")
        assert sec1 is not None and sec1.task_id == "SEC01"

        tool1 = get_task_by_id("tool01")
        assert tool1 is not None and tool1.task_id == "TOOL01"

        swe1 = get_task_by_id("swe01")
        assert swe1 is not None and swe1.task_id == "SWE01"

        arm1 = get_task_by_id("arm01")
        assert arm1 is not None and arm1.task_id == "ARM01"

        assert get_task_by_id("UNKNOWN_999") is None
