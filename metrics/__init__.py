"""
Evaluation metrics and statistical analysis package.
"""

from metrics.scorers import (
    calculate_intent_fidelity,
    evaluate_policy_violations,
    evaluate_task_success,
)
from metrics.statistics import (
    bootstrap_ci_95,
    compute_canonical_state_hash,
    compute_cohens_kappa,
    compute_cumulative_regret,
    compute_median_and_iqr,
    compute_token_scaling_per_hop,
    compute_total_regret,
    fit_regret_scaling,
    paired_wilcoxon_test,
)

__all__ = [
    "evaluate_task_success",
    "calculate_intent_fidelity",
    "evaluate_policy_violations",
    "compute_median_and_iqr",
    "bootstrap_ci_95",
    "paired_wilcoxon_test",
    "compute_cohens_kappa",
    "compute_cumulative_regret",
    "compute_total_regret",
    "fit_regret_scaling",
    "compute_token_scaling_per_hop",
    "compute_canonical_state_hash",
]
