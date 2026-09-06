"""
Unit Tests for Framework Adapters (GUIDE, CrewAI, LangGraph, AutoGen).
"""

import pytest
from adapters import get_adapter
from configs.settings import BenchSettings
from datasets.loader import get_task_by_id


class TestAdapters:
    """Tests evaluating all four framework adapters."""

    @pytest.fixture
    def mock_settings(self):
        return BenchSettings(mock_mode=True, model_name="gpt-4o", default_repetitions=1)

    def test_guide_adapter_execution(self, mock_settings):
        task = get_task_by_id("T01")
        assert task is not None

        adapter = get_adapter("guide", settings=mock_settings)
        result = adapter.run_task(task, repetition=1)

        assert result.framework_name == "guide"
        assert result.task_id == "T01"
        assert result.success is True
        assert result.intent_fidelity_score > 0.8
        assert result.trace_verified is True
        assert result.wall_clock_seconds >= 0.0
        assert result.total_tokens > 0

    def test_crewai_adapter_execution(self, mock_settings):
        task = get_task_by_id("T01")
        assert task is not None

        adapter = get_adapter("crewai", settings=mock_settings)
        result = adapter.run_task(task, repetition=1)

        assert result.framework_name == "crewai"
        assert result.task_id == "T01"
        assert result.wall_clock_seconds >= 0.0
        assert result.total_tokens > 0
        assert result.trace_verified is False

    def test_langgraph_adapter_execution(self, mock_settings):
        task = get_task_by_id("T07")
        assert task is not None

        adapter = get_adapter("langgraph", settings=mock_settings)
        result = adapter.run_task(task, repetition=1)

        assert result.framework_name == "langgraph"
        assert result.task_id == "T07"
        assert result.wall_clock_seconds >= 0.0
        assert result.total_tokens > 0

    def test_autogen_adapter_execution(self, mock_settings):
        task = get_task_by_id("T13")
        assert task is not None

        adapter = get_adapter("autogen", settings=mock_settings)
        result = adapter.run_task(task, repetition=1)

        assert result.framework_name == "autogen"
        assert result.task_id == "T13"
        assert result.wall_clock_seconds >= 0.0
        assert result.total_tokens > 0

    def test_adversarial_injection_defense_comparison(self, mock_settings):
        # SEC01 direct prompt injection
        sec_task = get_task_by_id("SEC01")
        assert sec_task is not None

        guide_adapter = get_adapter("guide", settings=mock_settings)
        guide_result = guide_adapter.run_task(sec_task, repetition=1)

        crew_adapter = get_adapter("crewai", settings=mock_settings)
        crew_result = crew_adapter.run_task(sec_task, repetition=1)

        # GUIDE successfully blocks injection at CAMCO policy gate
        assert guide_result.policy_violations == 0
        assert guide_result.success is True

        # Baseline without CAMCO attempts unpermitted email tool
        assert crew_result.policy_violations > 0

    def test_adapters_across_evaluation_dimensions(self, mock_settings):
        """
        Validates that all framework adapters execute across the new benchmark
        evaluation dimensions: ToolBench, HotpotQA, SWE-bench Lite, and Arm Perturbation.
        """
        test_task_ids = [
            "TOOL01", "TOOL06", "TOOL10",
            "HOTPOT01", "HOTPOT03", "HOTPOT05",
            "SWE01", "SWE02", "SWE05",
            "ARM01", "ARM02"
        ]
        frameworks = ["guide", "crewai", "langgraph", "autogen"]

        for tid in test_task_ids:
            task = get_task_by_id(tid)
            assert task is not None, f"Task {tid} should exist"

            for fw in frameworks:
                adapter = get_adapter(fw, settings=mock_settings)
                result = adapter.run_task(task, repetition=1)

                assert result.framework_name == fw
                assert result.task_id == tid
                assert result.wall_clock_seconds >= 0.0
                assert result.total_tokens > 0
                assert isinstance(result.parsed_output, dict)

    def test_all_frameworks_toolbench_suite_execution(self, mock_settings):
        """Validates that all frameworks can run a ToolBench task with toolbench_suite allowed."""
        task = get_task_by_id("TOOL07")
        assert task is not None
        assert "toolbench_suite" in task.allowed_tools

        for fw in ["guide", "crewai", "langgraph", "autogen"]:
            adapter = get_adapter(fw, settings=mock_settings)
            res = adapter.run_task(task, repetition=1)
            assert res.success is True
            assert res.policy_violations == 0
            assert res.parsed_output.get("carrier") == "United Airlines"
