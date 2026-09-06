"""
Leaderboard Generation Module.

Aggregates raw experimental results from UniversalExecutionResult records into
formatted Markdown leaderboards for academic publications and engineering reports.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd
from tabulate import tabulate
from core.schemas import UniversalExecutionResult


def generate_markdown_leaderboard(
    results: List[UniversalExecutionResult],
    output_path: Optional[Union[str, Path]] = None
) -> str:
    """
    Computes summary metrics per framework and formats an ASCII/Markdown leaderboard table.

    Columns:
    - Framework
    - Task Success (%)
    - Intent Retention (IPS %)
    - Policy Violation Rate (%)
    - Cryptographic Lineage (%)
    - Mean Prompt Tokens
    - Mean Completion Tokens
    - USD Cost / Task ($)
    - Median Wall-Clock Latency (s)
    """
    if not results:
        return "No execution results available to generate leaderboard."

    # Convert to pandas DataFrame for aggregation
    data = []
    for r in results:
        data.append({
            "framework": r.framework_name.upper(),
            "task_id": r.task_id,
            "success": 100.0 if r.success else 0.0,
            "ips": r.intent_fidelity_score * 100.0,
            "violations": 100.0 if r.policy_violations > 0 else 0.0,
            "lineage": 100.0 if r.trace_verified else 0.0,
            "prompt_tokens": r.prompt_tokens,
            "completion_tokens": r.completion_tokens,
            "total_tokens": r.total_tokens,
            "cost_usd": r.cost_usd,
            "latency": r.wall_clock_seconds
        })
    df = pd.DataFrame(data)

    grouped = df.groupby("framework")
    summary_rows = []

    for fw, group in grouped:
        summary_rows.append({
            "Framework": fw,
            "Task Success (%)": f"{group['success'].mean():.1f}%",
            "Intent Retention (IPS %)": f"{group['ips'].mean():.1f}%",
            "Policy Violation Rate (%)": f"{group['violations'].mean():.1f}%",
            "Cryptographic Lineage (%)": f"{group['lineage'].mean():.1f}%",
            "Mean Prompt Tokens": f"{int(group['prompt_tokens'].mean()):,}",
            "Mean Completion Tokens": f"{int(group['completion_tokens'].mean()):,}",
            "USD Cost / Task": f"${group['cost_usd'].mean():.4f}",
            "Median Latency (s)": f"{group['latency'].median():.2f}s",
            "_raw_success": group["success"].mean()  # for sorting
        })

    # Sort descending by Task Success
    summary_rows.sort(key=lambda x: x["_raw_success"], reverse=True)
    for row in summary_rows:
        del row["_raw_success"]

    headers = [
        "Framework",
        "Task Success (%)",
        "Intent Retention (IPS %)",
        "Policy Violation Rate (%)",
        "Cryptographic Lineage (%)",
        "Mean Prompt Tokens",
        "Mean Completion Tokens",
        "USD Cost / Task",
        "Median Latency (s)"
    ]

    table_data = [[row[h] for h in headers] for row in summary_rows]
    markdown_table = tabulate(table_data, headers=headers, tablefmt="github")
    # Dimension-level breakdown table
    dimension_table = generate_dimension_breakdown_leaderboard(results)

    leaderboard_output = (
        "# 🏆 MAS-BENCH UNIVERSAL MULTI-AGENT LEADERBOARD\n\n"
        f"**Evaluation Parameters:** Model Invariance (temp=0.0, seed=42) | Total Runs: {len(results):,}\n\n"
        f"{markdown_table}\n\n"
        f"{dimension_table}\n\n"
        "> *Note: Cryptographic Lineage denotes Ed25519 hash-linked trace audit verification. "
        "Policy Violation Rate counts executions attempting unpermitted tools, unauthorized write mutations, or unbounded queries.*\n"
    )

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(leaderboard_output)

    return leaderboard_output


def _get_dimension_name(task_id: str) -> str:
    """Resolves benchmark evaluation dimension name from task identifier prefix."""
    tid = str(task_id).upper()
    if tid.startswith("SEC"):
        return "InjecAgent (Security)"
    elif tid.startswith("GAIA"):
        return "GAIA (Multi-Hop Reasoning)"
    elif tid.startswith("TOOL"):
        return "ToolBench (Open-Domain)"
    elif tid.startswith("HOTPOT"):
        return "HotpotQA (Retrieval)"
    elif tid.startswith("SWE"):
        return "SWE-bench Lite (Code)"
    elif tid.startswith("ARM"):
        return "Arm Perturbation (Fault Tolerance)"
    elif tid.startswith("T"):
        return "Enterprise (Data Lineage)"
    return "General"


def generate_dimension_breakdown_leaderboard(
    results: List[UniversalExecutionResult],
    output_path: Optional[Union[str, Path]] = None
) -> str:
    """
    Computes performance metrics broken down across the 6+ benchmark evaluation dimensions.
    """
    if not results:
        return ""

    data = []
    for r in results:
        dim = _get_dimension_name(r.task_id)
        data.append({
            "dimension": dim,
            "framework": r.framework_name.upper(),
            "success": 100.0 if r.success else 0.0,
            "ips": r.intent_fidelity_score * 100.0,
            "violations": 100.0 if r.policy_violations > 0 else 0.0,
            "tokens": r.total_tokens
        })
    df = pd.DataFrame(data)
    grouped = df.groupby(["dimension", "framework"])

    rows = []
    for (dim, fw), group in grouped:
        rows.append({
            "Dimension": dim,
            "Framework": fw,
            "Success (%)": f"{group['success'].mean():.1f}%",
            "IPS (%)": f"{group['ips'].mean():.1f}%",
            "Violations (%)": f"{group['violations'].mean():.1f}%",
            "Mean Tokens": f"{int(group['tokens'].mean()):,}"
        })

    headers = ["Dimension", "Framework", "Success (%)", "IPS (%)", "Violations (%)", "Mean Tokens"]
    table_data = [[row[h] for h in headers] for row in rows]
    dim_md = tabulate(table_data, headers=headers, tablefmt="github")

    section = f"### 📊 Performance Breakdown Across Evaluation Dimensions\n\n{dim_md}"

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(section)

    return section
