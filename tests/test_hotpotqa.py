"""
Unit Tests for HotpotQA (Multi-Hop Benign Retrieval) Suite:
- Validates 5 multi-hop retrieval tasks (HOTPOT01 - HOTPOT05)
- Tests MockKnowledgeGraphStore multi-hop chaining (3 to 5 hops)
- Validates token scaling: Flat CAS input_refs[] O(1) in GUIDE vs baseline accumulation
- Tests GuideAdapter and baseline adapter execution on HotpotQA tasks
"""

import pytest
from adapters import get_adapter
from configs.settings import BenchSettings
from core.schemas import DatasetSource, TaskFamily
from datasets.hotpotqa_tasks import get_hotpotqa_tasks
from datasets.loader import get_task_by_id
from metrics.statistics import compute_token_scaling_per_hop
from tools.sandboxed_tools import MockDocumentStore, MockKnowledgeGraphStore


class TestHotpotQA:
    """Tests evaluating HotpotQA multi-hop retrieval and token scaling metrics."""

    @pytest.fixture
    def mock_settings(self):
        return BenchSettings(mock_mode=True, model_name="gpt-4o", default_repetitions=1)

    @pytest.fixture
    def kg_store(self):
        return MockKnowledgeGraphStore()

    @pytest.fixture
    def doc_store(self):
        return MockDocumentStore()

    def test_hotpotqa_task_definitions(self):
        tasks = get_hotpotqa_tasks()
        assert len(tasks) == 5

        task_ids = [t.task_id for t in tasks]
        expected_ids = [f"HOTPOT{i:02d}" for i in range(1, 6)]
        assert task_ids == expected_ids

        for t in tasks:
            assert t.family == TaskFamily.MULTI_HOP_RETRIEVAL
            assert t.dataset_source == DatasetSource.HOTPOTQA
            assert "knowledge_graph_store" in t.allowed_tools or "document_store" in t.allowed_tools
            assert bool(t.objective)
            assert bool(t.frozen_rubric)

    def test_knowledge_graph_store_multi_hop_querying(self, kg_store, doc_store):
        # Query primary entity via Knowledge Graph Store
        res = kg_store.execute(entity="Alan Turing", max_hops=3)
        assert res["found"] is True
        assert res["entity"] == "Alan Turing"
        assert len(res["relations"]) > 0

        # Query via Document Store
        doc_res = doc_store.query_document("Inception", max_hops=3)
        assert doc_res["found"] is True
        assert doc_res["entity"] == "Inception"
        assert len(doc_res["relations"]) > 0

        # Multi-hop traversal test
        hop_entities = [h["entity"] for h in res.get("hop_history", [])]
        assert "Alan Turing" in hop_entities

        # Unknown entity handling
        unknown_res = kg_store.execute(entity="NonExistentEntityX99")
        assert unknown_res["found"] is False

    def test_cas_flat_token_scaling_vs_baseline_growth(self, mock_settings):
        """
        Contrasts GUIDE's Content-Addressable Storage input_refs[] flat token scaling
        against baseline adapters' full-prompt context re-submission.
        """
        task = get_task_by_id("HOTPOT01")
        assert task is not None

        # 1. GUIDE adapter with CAS input_refs[]
        guide_adapter = get_adapter("guide", settings=mock_settings)
        guide_res = guide_adapter.run_task(task, repetition=1)

        assert guide_res.success is True
        assert guide_res.hop_tokens is not None
        assert len(guide_res.hop_tokens) >= 3

        guide_scaling = compute_token_scaling_per_hop(guide_res.hop_tokens)
        assert guide_scaling["is_flat_scaling"] is True
        assert abs(guide_scaling["slope_tokens_per_hop"]) < 20.0

        # 2. CrewAI baseline with context accumulation
        crew_adapter = get_adapter("crewai", settings=mock_settings)
        crew_res = crew_adapter.run_task(task, repetition=1)

        assert crew_res.hop_tokens is not None
        assert len(crew_res.hop_tokens) >= 3

        crew_scaling = compute_token_scaling_per_hop(crew_res.hop_tokens)
        assert crew_scaling["is_flat_scaling"] is False
        assert crew_scaling["slope_tokens_per_hop"] > 50.0

    def test_guide_adapter_hotpot_task_success_and_citations(self, mock_settings):
        task = get_task_by_id("HOTPOT03")
        assert task is not None

        guide_adapter = get_adapter("guide", settings=mock_settings)
        res = guide_adapter.run_task(task, repetition=1)

        assert res.success is True
        assert res.policy_violations == 0
        assert "discovery" in res.parsed_output or "nobel_year" in res.parsed_output
        assert "pioneer" in res.parsed_output or "institution" in res.parsed_output

    def test_document_store_title_and_passage_resolution(self, doc_store):
        """
        Validates that MockDocumentStore correctly resolves entity and passages
        via title, document_title, or passage keyword arguments without defaulting to Inception.
        """
        res_treaty = doc_store.execute(title="Treaty of Portsmouth")
        assert res_treaty["found"] is True
        assert res_treaty["entity"] == "Treaty of Portsmouth"

        res_crispr = doc_store.execute(document="CRISPR-Cas9")
        assert res_crispr["found"] is True
        assert res_crispr["entity"] == "CRISPR-Cas9"

        res_everest = doc_store.execute(passage="Mount Everest")
        assert res_everest["found"] is True
        assert res_everest["entity"] == "Mount Everest"

    def test_langgraph_and_autogen_hotpot_execution(self, mock_settings):
        """Validates that LangGraph and AutoGen adapters execute on HotpotQA tasks."""
        for tid in ["HOTPOT02", "HOTPOT04"]:
            task = get_task_by_id(tid)
            assert task is not None

            for fw in ["langgraph", "autogen"]:
                adapter = get_adapter(fw, settings=mock_settings)
                res = adapter.run_task(task, repetition=1)
                assert res.success is True
                assert res.framework_name == fw
                assert res.policy_violations == 0
