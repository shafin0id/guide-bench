"""
SWE-bench Lite Multi-Agent Code Collaboration Benchmark Tasks Module.

Implements 5 deterministic code collaboration tasks (SWE01 - SWE05)
evaluating the Parser -> Coder -> Tester multi-agent pipeline:
verifying patch integrity, AST schema consistency, and RFC 8785 state
canonicalization without escaping or formatting drift.
"""

from typing import List
from core.schemas import ComplexityTier, DatasetSource, TaskFamily, UniversalTask


def get_swebench_tasks() -> List[UniversalTask]:
    """Returns the 5 curated SWE-bench Lite multi-agent evaluation tasks."""
    return [
        UniversalTask(
            task_id="SWE01",
            name="AST Node Parsing and Syntax Tree Normalization",
            dataset_source=DatasetSource.SWEBENCH,
            family=TaskFamily.CODE_COLLABORATION,
            complexity=ComplexityTier.LOW,
            objective="Parse target Python source code into an abstract syntax tree and verify schema normalization.",
            constraints=[
                "Invoke code_workspace with action='parse_ast'",
                "Extract function definitions and class nodes",
                "Verify AST syntax normalization without formatting drift",
                "Enforce sandboxed read-only code analysis"
            ],
            negative_constraints=[
                "Do NOT execute arbitrary un-sandboxed shell scripts",
                "Zero file system write mutations"
            ],
            allowed_tools=["code_workspace"],
            expected_schema={
                "type": "object",
                "properties": {
                    "valid_syntax": {"type": "boolean"},
                    "syntax_tree_normalized": {"type": "boolean"},
                    "ast_nodes": {"type": "integer"}
                },
                "required": ["valid_syntax", "syntax_tree_normalized", "ast_nodes"]
            },
            frozen_rubric={
                "expected_values": {
                    "valid_syntax": True,
                    "syntax_tree_normalized": True
                }
            },
            input_data={
                "action": "parse_ast",
                "code": "def calculate_tax(subtotal: float) -> float:\n    return subtotal * 0.15\n"
            },
            subtasks=["Parse abstract syntax tree", "Normalize AST schema", "Verify structural integrity"]
        ),
        UniversalTask(
            task_id="SWE02",
            name="Unified Diff Patch Integrity and Application Verification",
            dataset_source=DatasetSource.SWEBENCH,
            family=TaskFamily.CODE_COLLABORATION,
            complexity=ComplexityTier.MEDIUM,
            objective="Generate and apply a unified diff patch to core engine, verifying strict patch integrity.",
            constraints=[
                "Invoke code_workspace with action='apply_patch'",
                "Verify unified diff contains valid hunk headers (@@)",
                "Ensure zero whitespace or formatting drift",
                "Confirm patch applies cleanly to target file"
            ],
            negative_constraints=[
                "Do NOT emit non-unified diff formats or conversational code snippets",
                "Zero unhandled patch merge conflicts"
            ],
            allowed_tools=["code_workspace"],
            expected_schema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "patch_applied": {"type": "boolean"},
                    "patch_integrity": {"type": "boolean"},
                    "format_drift": {"type": "boolean"}
                },
                "required": ["file_path", "patch_applied", "patch_integrity", "format_drift"]
            },
            frozen_rubric={
                "expected_values": {
                    "file_path": "core/engine.py",
                    "patch_applied": True,
                    "patch_integrity": True,
                    "format_drift": False
                }
            },
            input_data={
                "action": "apply_patch",
                "file_path": "core/engine.py",
                "diff": "--- a/core/engine.py\n+++ b/core/engine.py\n@@ -1,4 +1,4 @@\n-def compute(): return None\n+def compute(): return True\n"
            },
            subtasks=["Generate unified diff", "Audit patch hunk syntax", "Apply patch cleanly to workspace"]
        ),
        UniversalTask(
            task_id="SWE03",
            name="RFC 8785 Multi-Agent State Canonicalization",
            dataset_source=DatasetSource.SWEBENCH,
            family=TaskFamily.CODE_COLLABORATION,
            complexity=ComplexityTier.HIGH,
            objective="Canonicalize multi-agent shared state under RFC 8785 without formatting drift.",
            constraints=[
                "Invoke code_workspace with action='canonicalize_state'",
                "Sort dictionary keys deterministically at all nesting levels",
                "Eliminate superfluous whitespace outside string literals",
                "Compute SHA-256 cryptographic state digest",
                "Verify RFC 8785 compliance"
            ],
            negative_constraints=[
                "Zero tolerance for key-order non-determinism",
                "Do NOT alter data types during canonicalization"
            ],
            allowed_tools=["code_workspace"],
            expected_schema={
                "type": "object",
                "properties": {
                    "rfc8785_verified": {"type": "boolean"},
                    "canonical_json": {"type": "string"},
                    "sha256_hash": {"type": "string"}
                },
                "required": ["rfc8785_verified", "canonical_json", "sha256_hash"]
            },
            frozen_rubric={
                "expected_values": {
                    "rfc8785_verified": True
                }
            },
            input_data={
                "action": "canonicalize_state",
                "payload": {"status": "ACTIVE", "task": "SWE03", "priority": 1, "nested": {"b": 2, "a": 1}}
            },
            subtasks=["Order JSON keys per RFC 8785", "Format compact UTF-8 bytes", "Generate cryptographic digest"]
        ),
        UniversalTask(
            task_id="SWE04",
            name="Multi-Agent Refactor Pipeline (Parser -> Coder -> Tester)",
            dataset_source=DatasetSource.SWEBENCH,
            family=TaskFamily.CODE_COLLABORATION,
            complexity=ComplexityTier.HIGH,
            objective="Execute a 3-agent software refactoring pipeline from AST inspection to patch test verification.",
            constraints=[
                "Agent 1 (Parser): Inspect AST and identify target syntax nodes",
                "Agent 2 (Coder): Formulate minimal unified patch without formatting drift",
                "Agent 3 (Tester): Run automated test target and confirm 5/5 passing tests",
                "Preserve root task objective S_0 across all 3 handoffs",
                "Enforce sandboxed tool permissions"
            ],
            negative_constraints=[
                "Do NOT skip unit test execution",
                "Zero test assertion regressions"
            ],
            allowed_tools=["code_workspace"],
            expected_schema={
                "type": "object",
                "properties": {
                    "parser_completed": {"type": "boolean"},
                    "coder_completed": {"type": "boolean"},
                    "tester_completed": {"type": "boolean"},
                    "tests_passed": {"type": "integer"}
                },
                "required": ["parser_completed", "coder_completed", "tester_completed", "tests_passed"]
            },
            frozen_rubric={
                "expected_values": {
                    "parser_completed": True,
                    "coder_completed": True,
                    "tester_completed": True,
                    "tests_passed": 5
                }
            },
            input_data={"pipeline": "parser_coder_tester", "target": "core/math_utils.py"},
            subtasks=["Parser AST analysis", "Coder unified diff generation", "Tester test verification"]
        ),
        UniversalTask(
            task_id="SWE05",
            name="Defensive Regression Invariant Test Execution",
            dataset_source=DatasetSource.SWEBENCH,
            family=TaskFamily.CODE_COLLABORATION,
            complexity=ComplexityTier.MEDIUM,
            objective="Execute automated regression test suite to verify bug fix preserves all system invariants.",
            constraints=[
                "Invoke code_workspace with action='run_tests'",
                "Verify test target tests/test_engine.py runs 5 tests",
                "Confirm 0 failures and 0 errors",
                "Confirm 100% test coverage achieved",
                "Confirm regression verification succeeds"
            ],
            negative_constraints=[
                "Do NOT modify or weaken test assertions",
                "Zero unhandled exceptions"
            ],
            allowed_tools=["code_workspace"],
            expected_schema={
                "type": "object",
                "properties": {
                    "tests_run": {"type": "integer"},
                    "tests_passed": {"type": "integer"},
                    "failures": {"type": "integer"},
                    "coverage_pct": {"type": "number"},
                    "regression_verified": {"type": "boolean"}
                },
                "required": ["tests_run", "tests_passed", "failures", "coverage_pct", "regression_verified"]
            },
            frozen_rubric={
                "expected_values": {
                    "tests_run": 5,
                    "tests_passed": 5,
                    "failures": 0,
                    "coverage_pct": 100.0,
                    "regression_verified": True
                }
            },
            input_data={"action": "run_tests", "test_target": "tests/test_engine.py"},
            subtasks=["Initialize test runner", "Execute invariant assertions", "Emit test coverage report"]
        )
    ]
