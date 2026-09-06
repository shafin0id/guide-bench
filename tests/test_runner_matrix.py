"""
Unit Tests for Benchmark Matrix Runner and Leaderboard Reporting.
"""

import json
from pathlib import Path
import pytest
from configs.settings import BenchSettings
from core.runner import BenchmarkRunner
from datasets.loader import get_task_by_id
from reporting.export import generate_latex_table, generate_statistical_comparison_table
from reporting.leaderboard import generate_markdown_leaderboard


class TestRunnerMatrix:
    """Tests evaluating benchmark orchestration and reporting artifacts."""

    @pytest.fixture
    def runner_env(self, tmp_path):
        settings = BenchSettings(
            mock_mode=True,
            model_name="gpt-4o",
            default_repetitions=1,
            output_dir=tmp_path / "bench_output"
        )
        runner = BenchmarkRunner(settings=settings)
        return runner, settings

    def test_run_matrix_orchestration_and_streaming(self, runner_env):
        runner, settings = runner_env
        tasks = [get_task_by_id("T01"), get_task_by_id("T07")]
        frameworks = ["guide", "crewai"]

        # Run 2 frameworks x 2 tasks x 1 repetition = 4 runs
        results = runner.run_matrix(
            framework_names=frameworks,
            tasks=tasks,
            repetitions=1
        )

        assert len(results) == 4

        # Verify streaming JSONL exists and has 4 lines
        assert settings.results_path.exists()
        with open(settings.results_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) == 4

        # Verify manifest file exists and has correct metadata
        assert settings.manifest_path.exists()
        with open(settings.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        assert manifest["total_runs"] == 4
        assert set(manifest["frameworks"]) == set(frameworks)

    def test_leaderboard_and_latex_reporting(self, runner_env):
        runner, settings = runner_env
        tasks = [get_task_by_id("T01"), get_task_by_id("T02")]
        results = runner.run_matrix(
            framework_names=["guide", "crewai", "langgraph", "autogen"],
            tasks=tasks,
            repetitions=1
        )

        # Markdown Leaderboard
        md_table = generate_markdown_leaderboard(
            results,
            output_path=settings.output_dir / "test_leaderboard.md"
        )
        assert "MAS-BENCH UNIVERSAL MULTI-AGENT LEADERBOARD" in md_table
        assert "GUIDE" in md_table
        assert "CREWAI" in md_table
        assert (settings.output_dir / "test_leaderboard.md").exists()

        # LaTeX Table
        latex_str = generate_latex_table(
            results,
            output_path=settings.output_dir / "test_table.tex"
        )
        assert r"\begin{table*}" in latex_str
        assert (settings.output_dir / "test_table.tex").exists()

        # Statistical Comparison Table
        stat_latex = generate_statistical_comparison_table(
            results,
            output_path=settings.output_dir / "test_wilcoxon.tex"
        )
        assert "Pairwise Comparison" in stat_latex or "GUIDE" in stat_latex

        # Dimension Breakdown LaTeX Table
        from reporting.export import generate_dimension_latex_table
        dim_latex = generate_dimension_latex_table(
            results,
            output_path=settings.output_dir / "test_dim_table.tex"
        )
        assert r"\begin{table*}" in dim_latex
        assert "Enterprise Lineage" in dim_latex
        assert (settings.output_dir / "test_dim_table.tex").exists()

    def test_run_matrix_across_all_six_dimensions(self, runner_env):
        """
        Validates matrix execution and dimension reporting across all 6 core benchmark suites:
        Enterprise, InjecAgent, GAIA, ToolBench, HotpotQA, SWE-bench Lite.
        """
        runner, settings = runner_env
        six_dim_tasks = [
            get_task_by_id("T01"),
            get_task_by_id("SEC01"),
            get_task_by_id("GAIA01"),
            get_task_by_id("TOOL01"),
            get_task_by_id("HOTPOT01"),
            get_task_by_id("SWE01")
        ]
        assert all(t is not None for t in six_dim_tasks)

        results = runner.run_matrix(
            framework_names=["guide", "crewai"],
            tasks=six_dim_tasks,
            repetitions=1
        )
        assert len(results) == 12  # 2 frameworks x 6 tasks x 1 rep

        md_leaderboard = generate_markdown_leaderboard(results)
        assert "ToolBench" in md_leaderboard
        assert "HotpotQA" in md_leaderboard
        assert "SWE-bench" in md_leaderboard
