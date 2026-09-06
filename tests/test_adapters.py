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
