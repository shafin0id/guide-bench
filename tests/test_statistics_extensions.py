"""
Unit Tests for Extended Statistical Metrics:
- compute_cumulative_regret
- fit_regret_scaling (Bayes-UCB O(ln T) vs static O(T))
- compute_token_scaling_per_hop (CAS O(1) flat vs baseline growth)
- compute_canonical_state_hash (RFC 8785 JSON canonicalization)
"""

import math
import numpy as np
import pytest
from metrics.statistics import (
    compute_canonical_state_hash,
    compute_cumulative_regret,
    compute_token_scaling_per_hop,
    fit_regret_scaling,
)


class TestStatisticsExtensions:
    """Tests for advanced metric computations supporting peer-reviewed evaluations."""

    def test_compute_cumulative_regret_basic(self):
        rewards = [1.0, 1.0, 0.8, 0.5, 0.0]
        # Regret per step: 0.0, 0.0, 0.2, 0.5, 1.0
        # Cumulative: [0.0, 0.0, 0.2, 0.7, 1.7]
        cum_regrets = compute_cumulative_regret(rewards, optimal_reward=1.0)
        assert len(cum_regrets) == 5
        assert cum_regrets == [0.0, 0.0, 0.2, 0.7, 1.7]

    def test_compute_cumulative_regret_empty_and_zeros(self):
        assert compute_cumulative_regret([]) == []
        assert compute_cumulative_regret([1.0, 1.0, 1.0]) == [0.0, 0.0, 0.0]

    def test_fit_regret_scaling_logarithmic(self):
        # Simulated Bayes-UCB logarithmic trajectory: R(t) = 2.0 * ln(t)
        t = np.arange(1, 30, dtype=float)
        y = 2.0 * np.log(t) + np.random.RandomState(42).normal(0, 0.05, size=len(t))
        # Ensure monotonically non-decreasing
        y = np.maximum.accumulate(y)
        res = fit_regret_scaling(list(y))

        assert res["is_logarithmic"] is True
        assert res["r2_log"] > 0.90
        assert res["log_coeff"] > 0.0

    def test_fit_regret_scaling_linear(self):
        # Simulated Static Routing linear trajectory: R(t) = 0.8 * t
        t = np.arange(1, 30, dtype=float)
        y = 0.8 * t
        res = fit_regret_scaling(list(y))

        assert res["is_logarithmic"] is False
        assert res["r2_linear"] > 0.95
        assert res["linear_slope"] > 0.5

    def test_fit_regret_scaling_edge_cases(self):
        # Short sequence (< 3 items)
        short_res = fit_regret_scaling([0.1, 0.2])
        assert short_res["is_logarithmic"] is True
        assert short_res["r2_log"] == 1.0

        # Constant zero regret
        zero_res = fit_regret_scaling([0.0, 0.0, 0.0, 0.0, 0.0])
        assert zero_res["is_logarithmic"] is True
        assert zero_res["r2_log"] == 1.0

    def test_compute_token_scaling_per_hop_flat_cas(self):
        # Content-Addressable Storage (CAS) input_refs[] gives flat O(1) per-hop consumption
        cas_hops = [150, 155, 148, 152, 150]
        res = compute_token_scaling_per_hop(cas_hops)

        assert res["is_flat_scaling"] is True
        assert abs(res["slope_tokens_per_hop"]) < 10.0
        assert res["ratio_final_to_initial"] < 1.25

    def test_compute_token_scaling_per_hop_accumulating_baseline(self):
        # Full prompt re-submission leads to linear or quadratic token growth
        accum_hops = [150, 320, 520, 780, 1100]
        res = compute_token_scaling_per_hop(accum_hops)

        assert res["is_flat_scaling"] is False
        assert res["slope_tokens_per_hop"] > 100.0
        assert res["ratio_final_to_initial"] > 2.0

    def test_compute_token_scaling_per_hop_edge_cases(self):
        # Single hop
        single = compute_token_scaling_per_hop([200])
        assert single["is_flat_scaling"] is True
        assert single["mean_tokens"] == 200.0

        # Empty hops
        empty = compute_token_scaling_per_hop([])
        assert empty["is_flat_scaling"] is True
        assert empty["mean_tokens"] == 0.0

    def test_compute_canonical_state_hash_order_invariance(self):
        # RFC 8785 canonical hash must be invariant to dictionary key insertion order
        dict_a = {
            "status": "APPROVED",
            "metadata": {"author": "ParserAgent", "version": 2},
            "hops": [1, 2, 3],
            "action": "commit"
        }
        dict_b = {
            "action": "commit",
            "hops": [1, 2, 3],
            "metadata": {"version": 2, "author": "ParserAgent"},
            "status": "APPROVED"
        }

        hash_a = compute_canonical_state_hash(dict_a)
        hash_b = compute_canonical_state_hash(dict_b)

        assert hash_a == hash_b
        assert len(hash_a) == 64  # SHA-256 hex string

    def test_compute_canonical_state_hash_content_sensitivity(self):
        dict_orig = {"patch_id": "P01", "tests_pass": True}
        dict_mod = {"patch_id": "P01", "tests_pass": False}

        hash_orig = compute_canonical_state_hash(dict_orig)
        hash_mod = compute_canonical_state_hash(dict_mod)

        assert hash_orig != hash_mod
