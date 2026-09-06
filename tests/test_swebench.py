"""
Unit Tests for SWE-bench Lite (Code Collaboration) Suite:
- Validates 5 code collaboration tasks (SWE01 - SWE05)
- Tests MockCodeWorkspace (AST parsing, patch application, unit tests, RFC 8785 canonicalization)
- Validates zero formatting drift and deterministic state canonicalization
- Tests multi-agent collaboration (Parser -> Coder -> Tester) in GuideAdapter and baselines
"""

import pytest
from adapters import get_adapter
from configs.settings import BenchSettings
from core.schemas import DatasetSource, TaskFamily
from datasets.loader import get_task_by_id
from datasets.swebench_tasks import get_swebench_tasks
from metrics.statistics import compute_canonical_state_hash
from tools.sandboxed_tools import MockCodebaseEnvironment, MockCodeWorkspace


class TestSWEBench:
    """Tests evaluating SWE-bench Lite code collaboration and state canonicalization."""

    @pytest.fixture
    def mock_settings(self):
        return BenchSettings(mock_mode=True, model_name="gpt-4o", default_repetitions=1)

    @pytest.fixture
    def workspace(self):
        return MockCodeWorkspace()

    @pytest.fixture
    def codebase_env(self):
        return MockCodebaseEnvironment()

    def test_swebench_task_definitions(self):
        tasks = get_swebench_tasks()
        assert len(tasks) == 5

        task_ids = [t.task_id for t in tasks]
        expected_ids = [f"SWE{i:02d}" for i in range(1, 6)]
        assert task_ids == expected_ids

        for t in tasks:
            assert t.family == TaskFamily.CODE_COLLABORATION
            assert t.dataset_source == DatasetSource.SWEBENCH
            assert "code_workspace" in t.allowed_tools or "codebase_environment" in t.allowed_tools
            assert bool(t.objective)
            assert bool(t.frozen_rubric)

    def test_codebase_environment_instantiation(self, codebase_env):
        assert codebase_env.name == "codebase_environment"
        parsed = codebase_env.execute(action="parse_ast", code="x = 42\n")
        assert parsed["valid"] is True

    def test_code_workspace_ast_parsing(self, workspace):
        # Valid Python code
        valid_code = "def add(a: int, b: int) -> int:\n    return a + b\n"
        res_valid = workspace.execute(action="parse_ast", code=valid_code)
        assert res_valid["valid"] is True
        assert res_valid["node_count"] > 0

        # Invalid Python code with syntax error
        invalid_code = "def broken(:\n    pass\n"
        res_invalid = workspace.execute(action="parse_ast", code=invalid_code)
        assert res_invalid["valid"] is False
        assert "SyntaxError" in res_invalid.get("error", "")

    def test_code_workspace_patch_application_and_tests(self, workspace):
        # Valid unified diff patch
        patch = """--- a/src/math_utils.py
+++ b/src/math_utils.py
@@ -1,3 +1,3 @@
-def divide(a, b): return a / b
+def divide(a, b): return a / b if b != 0 else 0
"""
        res_patch = workspace.execute(action="apply_patch", file_path="src/math_utils.py", diff=patch)
        assert res_patch["success"] is True
        assert res_patch["lines_modified"] > 0

        # Run test suite
        res_test = workspace.execute(action="run_tests", test_target="tests/test_math.py")
        assert res_test["tests_pass"] is True
        assert res_test["failed_count"] == 0

    def test_code_workspace_canonicalization(self, workspace):
        state_payload = {
            "patch_id": "SWE01-patch",
            "ast_valid": True,
            "tests_pass": True,
            "roles": ["ParserAgent", "CoderAgent", "TesterAgent"]
        }
        res = workspace.execute(action="canonicalize_state", payload=state_payload)
        assert res["canonical_hash"] is not None
        assert len(res["canonical_hash"]) == 64

        # Verify RFC 8785 matching
        expected_hash = compute_canonical_state_hash(state_payload)
        assert res["canonical_hash"] == expected_hash

    def test_guide_adapter_swebench_collaboration(self, mock_settings):
        task = get_task_by_id("SWE01")
        assert task is not None

        guide_adapter = get_adapter("guide", settings=mock_settings)
        result = guide_adapter.run_task(task, repetition=1)

        assert result.success is True
        assert result.canonical_state_hash is not None
        assert len(result.canonical_state_hash) == 64
        assert result.policy_violations == 0
        assert result.parsed_output.get("valid_syntax") is True
        assert result.parsed_output.get("syntax_tree_normalized") is True

    def test_guide_adapter_swebench_full_pipeline(self, mock_settings):
        task = get_task_by_id("SWE04")
        assert task is not None

        guide_adapter = get_adapter("guide", settings=mock_settings)
        result = guide_adapter.run_task(task, repetition=1)

        assert result.success is True
        assert result.policy_violations == 0
        assert result.parsed_output.get("tests_passed") == 5

    def test_crewai_adapter_swebench_execution(self, mock_settings):
        task = get_task_by_id("SWE02")
        assert task is not None

        crew_adapter = get_adapter("crewai", settings=mock_settings)
        result = crew_adapter.run_task(task, repetition=1)

        assert result.success is True
        assert result.framework_name == "crewai"
        assert result.canonical_state_hash is not None
