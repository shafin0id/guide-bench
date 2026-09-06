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
    compute_cohens_kappa,
    compute_median_and_iqr,
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
]
