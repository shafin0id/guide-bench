"""
Benchmark Matrix Runner & Orchestrator.

Coordinates execution across:
Frameworks (4: GUIDE, CrewAI, LangGraph, AutoGen)
x Tasks (60 total: 18 Enterprise, 12 InjecAgent, 10 GAIA, 10 ToolBench, 5 HotpotQA, 5 SWE-bench Lite)
x Repetitions (5)
= 1,200 Formal Execution Runs (plus dynamic arm perturbation evaluation suite).

Enforces randomized execution ordering to prevent provider caching bias.
Streams real-time execution results into an append-only JSONL file and generates manifests.
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from adapters import get_adapter
from configs.settings import BenchSettings, get_settings, set_settings
from core.schemas import UniversalExecutionResult, UniversalTask
from datasets.loader import get_benchmark_suite, get_task_by_id
from reporting.export import (
    export_results_summary,
    generate_dimension_latex_table,
    generate_latex_table,
)
from reporting.leaderboard import generate_markdown_leaderboard


class BenchmarkRunner:
    """
    Orchestrates execution of the full benchmark matrix with streaming persistence.
    """

    def __init__(self, settings: Optional[BenchSettings] = None):
        self.settings = settings or get_settings()
        self.output_dir = self.settings.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_path = self.settings.results_path
        self.manifest_path = self.settings.manifest_path

    def run_matrix(
        self,
        framework_names: Optional[List[str]] = None,
        tasks: Optional[List[UniversalTask]] = None,
        repetitions: Optional[int] = None
    ) -> List[UniversalExecutionResult]:
        """
        Executes randomized benchmark runs across the requested frameworks, tasks, and repetitions.
        """
        target_frameworks = framework_names or self.settings.frameworks
        target_tasks = tasks or get_benchmark_suite("all")
        n_reps = repetitions if repetitions is not None else self.settings.default_repetitions

        # 1. Build Execution Plan
        execution_plan: List[Dict[str, Any]] = []
        for rep in range(1, n_reps + 1):
            for task in target_tasks:
                for fw in target_frameworks:
                    execution_plan.append({
                        "framework": fw,
                        "task": task,
                        "repetition": rep
                    })

        # 2. Randomize Execution Plan to eliminate provider caching bias
        rng = random.Random(self.settings.seed)
        rng.shuffle(execution_plan)

        total_runs = len(execution_plan)
        print(f"\n=======================================================")
        print(f" MAS-BENCH MATRIX EXECUTION: {total_runs} FORMAL RUNS")
        print(f" Frameworks: {target_frameworks}")
        print(f" Tasks: {len(target_tasks)} tasks | Repetitions: {n_reps}")
        if self.settings.arm_perturbation:
            print(f" Evaluation Mode: Arm Perturbation (Bayes-UCB vs Static Baselines)")
        print(f" Model Invariant: {self.settings.model_name} (temp={self.settings.temperature})")
        print(f" Output Target: {self.results_path}")
        print(f"=======================================================\n")

        # 3. Write Run Manifest
        self._write_manifest(target_frameworks, target_tasks, n_reps, total_runs)

        # 4. Initialize Adapters
        adapters = {fw: get_adapter(fw, settings=self.settings) for fw in target_frameworks}

        # 5. Execute Runs with Streaming Persistence
        completed_results: List[UniversalExecutionResult] = []

        for idx, item in enumerate(execution_plan, 1):
            fw_name = item["framework"]
            task: UniversalTask = item["task"]
            rep = item["repetition"]
            adapter = adapters[fw_name]

            print(f"[{idx:03d}/{total_runs:03d}] Running {fw_name.upper():<10} on {task.task_id} ({task.name[:32]:<32}) [rep {rep}]...", end="", flush=True)

            try:
                result = adapter.run_task(task=task, repetition=rep)
                completed_results.append(result)

                # Stream result to append-only JSONL file
                self._stream_result_to_disk(result)

                status_mark = "✓ PASS" if result.success else "✗ FAIL"
                print(f" {status_mark} | IPS: {result.intent_fidelity_score:.2f} | {result.wall_clock_seconds:.2f}s | {result.total_tokens} toks | violations: {result.policy_violations}")

            except Exception as err:
                print(f" ⚠ EXCEPTION: {err}")
                error_result = UniversalExecutionResult(
                    run_id=f"{fw_name}_{task.task_id}_rep{rep}_err",
                    task_id=task.task_id,
                    framework_name=fw_name,
                    repetition=rep,
                    success=False,
                    intent_fidelity_score=0.0,
                    policy_violations=1,
                    wall_clock_seconds=0.0,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    cost_usd=0.0,
                    trace_verified=False,
                    raw_output="",
                    parsed_output={},
                    error_log=str(err)
                )
                completed_results.append(error_result)
                self._stream_result_to_disk(error_result)

        print(f"\n=======================================================")
        print(f" MATRIX RUN COMPLETED: {len(completed_results)} runs logged.")
        print(f" Results written to: {self.results_path}")
        print(f"=======================================================\n")

        return completed_results

    def _stream_result_to_disk(self, result: UniversalExecutionResult) -> None:
        """Appends an execution record to the streaming JSONL file."""
        with open(self.results_path, "a", encoding="utf-8") as f:
            f.write(result.model_dump_json() + "\n")

    def _write_manifest(
        self,
        frameworks: List[str],
        tasks: List[UniversalTask],
        repetitions: int,
        total_runs: int
    ) -> None:
        """Writes run manifest metadata."""
        manifest = {
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "frameworks": frameworks,
            "task_count": len(tasks),
            "task_ids": [t.task_id for t in tasks],
            "repetitions": repetitions,
            "total_runs": total_runs,
            "model_name": self.settings.model_name,
            "temperature": self.settings.temperature,
            "seed": self.settings.seed,
            "mock_mode": self.settings.mock_mode,
            "arm_perturbation": self.settings.arm_perturbation,
            "python_version": sys.version
        }
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)


def main() -> None:
    """CLI Entrypoint for the Universal Multi-Agent Benchmarking Suite."""
    parser = argparse.ArgumentParser(
        prog="mas-bench",
        description="Universal Multi-Agent Systems Benchmarking Suite (GUIDE vs CrewAI vs LangGraph vs AutoGen)"
    )
    parser.add_argument(
        "--suite",
        type=str,
        default="enterprise",
        choices=["enterprise", "injecagent", "gaia", "toolbench", "hotpotqa", "swebench", "arm_perturbation", "all"],
        help="Benchmark task suite to execute (default: enterprise)"
    )
    parser.add_argument(
        "--arm-perturbation",
        action="store_true",
        help="Simulate dynamic specialist arm degradation (95%% -> 20%%) to evaluate Bayes-UCB logarithmic regret O(ln T) vs static linear regret"
    )
    parser.add_argument(
        "--frameworks",
        type=str,
        default="guide,crewai,langgraph,autogen",
        help="Comma-separated list of frameworks to evaluate (default: guide,crewai,langgraph,autogen)"
    )
    parser.add_argument(
        "--task",
        "--tasks",
        dest="task",
        type=str,
        default=None,
        help="Execute specific task ID(s), comma-separated (e.g., T01, SEC01, GAIA01, TOOL01, HOTPOT01, SWE01, ARM01)"
    )
    parser.add_argument(
        "--repetitions",
        "-n",
        type=int,
        default=5,
        help="Number of experimental repetitions per task (default: 5)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Target foundation LLM checkpoint (defaults to active provider or deepseek/deepseek-chat)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Execute in offline deterministic mock simulation mode"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save logs, leaderboards, and manifests"
    )
    parser.add_argument(
        "--generate-reports",
        action="store_true",
        default=True,
        help="Automatically generate Markdown and LaTeX leaderboards upon completion"
    )

    args = parser.parse_args()

    # Configure global settings
    settings_kwargs = {
        "default_repetitions": args.repetitions,
        "mock_mode": args.mock,
        "arm_perturbation": bool(args.arm_perturbation or args.suite in ("arm_perturbation", "arm", "perturbation")),
        "output_dir": Path(args.output_dir)
    }
    if args.model:
        settings_kwargs["model_name"] = args.model

    settings = BenchSettings(**settings_kwargs)
    set_settings(settings)

    # Determine tasks
    if args.task:
        task_ids = [t.strip() for t in args.task.split(",") if t.strip()]
        tasks = []
        for tid in task_ids:
            task = get_task_by_id(tid)
            if not task:
                print(f"Error: Task ID '{tid}' not found in benchmark repository.")
                sys.exit(1)
            tasks.append(task)
    elif args.arm_perturbation and args.suite == "enterprise":
        tasks = get_benchmark_suite("arm_perturbation")
    else:
        tasks = get_benchmark_suite(args.suite)

    target_frameworks = [f.strip() for f in args.frameworks.split(",") if f.strip()]

    runner = BenchmarkRunner(settings=settings)
    results = runner.run_matrix(
        framework_names=target_frameworks,
        tasks=tasks,
        repetitions=args.repetitions
    )

    if args.generate_reports and results:
        md_table = generate_markdown_leaderboard(results, output_path=settings.output_dir / "leaderboard.md")
        latex_table = generate_latex_table(results, output_path=settings.output_dir / "table_comparison.tex")
        dim_latex_table = generate_dimension_latex_table(results, output_path=settings.output_dir / "table_dimensions.tex")
        export_results_summary(results, output_dir=settings.output_dir)
        print("\n" + md_table + "\n")


if __name__ == "__main__":
    main()
