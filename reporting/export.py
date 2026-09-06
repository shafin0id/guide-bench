"""
Publication Export and Statistical Comparison Module.

Generates publication-ready LaTeX tables for IEEE TSC / ACM TOSEM submissions,
pairwise Wilcoxon signed-rank comparison tables, and structured CSV summaries.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd
from core.schemas import UniversalExecutionResult
from metrics.statistics import paired_wilcoxon_test


def generate_latex_table(
    results: List[UniversalExecutionResult],
    output_path: Optional[Union[str, Path]] = None
) -> str:
    """
    Generates a formal LaTeX table environment summarizing benchmark results.
    """
    if not results:
        return "% No results available to generate LaTeX table"

    data = []
    for r in results:
        data.append({
            "framework": r.framework_name.upper(),
            "success": 100.0 if r.success else 0.0,
            "ips": r.intent_fidelity_score * 100.0,
            "violations": 100.0 if r.policy_violations > 0 else 0.0,
            "lineage": 100.0 if r.trace_verified else 0.0,
            "prompt_tokens": r.prompt_tokens,
            "completion_tokens": r.completion_tokens,
            "cost_usd": r.cost_usd,
            "latency": r.wall_clock_seconds
        })
    df = pd.DataFrame(data)
    grouped = df.groupby("framework")

    latex_lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Empirical Multi-Agent Performance Comparison Across Controlled Benchmark Matrix}",
        r"\label{tab:mas_bench_results}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{lcccccccc}",
        r"\toprule",
        r"\textbf{Framework} & \textbf{Success (\%)} & \textbf{IPS (\%)} & \textbf{Violations (\%)} & \textbf{Lineage (\%)} & \textbf{Prompt Tok.} & \textbf{Comp. Tok.} & \textbf{Cost / Task (\$)} & \textbf{Latency (s)} \\",
        r"\midrule"
    ]

    for fw, group in grouped:
        line = (
            f"\\texttt{{{fw}}} & "
            f"{group['success'].mean():.1f}\\% & "
            f"{group['ips'].mean():.1f}\\% & "
            f"{group['violations'].mean():.1f}\\% & "
            f"{group['lineage'].mean():.1f}\\% & "
            f"{int(group['prompt_tokens'].mean()):,} & "
            f"{int(group['completion_tokens'].mean()):,} & "
            f"\\${group['cost_usd'].mean():.4f} & "
            f"{group['latency'].median():.2f} \\\\"
        )
        latex_lines.append(line)

    latex_lines.extend([
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
        r"\end{table*}"
    ])

    latex_output = "\n".join(latex_lines)

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(latex_output)

    return latex_output


def generate_statistical_comparison_table(
    results: List[UniversalExecutionResult],
    output_path: Optional[Union[str, Path]] = None
) -> str:
    """
    Computes pairwise Wilcoxon signed-rank tests comparing GUIDE against all competitors
    on Task Success, Intent Retention (IPS), and Policy Violations.
    """
    df = pd.DataFrame([r.model_dump() for r in results])
    if "framework_name" not in df or df.empty:
        return "% Insufficient data for statistical comparison"

    guide_runs = df[df["framework_name"].str.lower() == "guide"]
    if guide_runs.empty:
        return "% GUIDE framework results not found in dataset"

    competitors = [fw for fw in df["framework_name"].unique() if fw.lower() != "guide"]
    rows = []

    for comp in competitors:
        comp_runs = df[df["framework_name"] == comp]

        # Align paired observations by task_id and repetition
        merged = pd.merge(
            guide_runs, comp_runs,
            on=["task_id", "repetition"],
            suffixes=("_guide", "_comp")
        )

        if len(merged) < 2:
            continue

        # Wilcoxon on Success
        wilc_succ = paired_wilcoxon_test(
            merged["success_guide"].astype(int),
            merged["success_comp"].astype(int)
        )
        # Wilcoxon on IPS
        wilc_ips = paired_wilcoxon_test(
            merged["intent_fidelity_score_guide"],
            merged["intent_fidelity_score_comp"]
        )
        # Wilcoxon on Violations
        wilc_viol = paired_wilcoxon_test(
            merged["policy_violations_guide"],
            merged["policy_violations_comp"]
        )

        rows.append({
            "Pairwise Comparison": f"GUIDE vs {comp.upper()}",
            "N (Pairs)": len(merged),
            "Success W-Stat": wilc_succ["statistic"],
            "Success p-value": f"{wilc_succ['p_value']:.4e}",
            "IPS W-Stat": wilc_ips["statistic"],
            "IPS p-value": f"{wilc_ips['p_value']:.4e}",
            "Sig. (p < 0.05)": "Yes" if (wilc_succ["is_significant"] or wilc_ips["is_significant"]) else "No"
        })

    summary_df = pd.DataFrame(rows)
    latex_output = summary_df.to_latex(index=False)

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(latex_output)

    return latex_output


def export_results_summary(
    results: List[UniversalExecutionResult],
    output_dir: Union[str, Path]
) -> None:
    """Exports CSV and aggregated JSON summaries for external analytics."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records = [r.model_dump() for r in results]
    df = pd.DataFrame(records)

    # Exclude complex nested columns from CSV
    flat_cols = [c for c in df.columns if c not in ("tool_calls", "parsed_output", "metadata")]
    df[flat_cols].to_csv(out_dir / "benchmark_summary.csv", index=False)
