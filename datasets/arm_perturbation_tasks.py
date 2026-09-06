"""
MultiAgentBench Arm Perturbation Dynamic Adaptation Tasks Module.

Implements 5 dynamic adaptation and fault tolerance benchmark tasks (ARM01 - ARM05)
where specialist agent success drops from 95% to 20% mid-run to empirically validate
Bayes-UCB O(ln T) logarithmic regret vs static baselines' O(T) linear regret.
"""

from typing import List
from core.schemas import ComplexityTier, DatasetSource, TaskFamily, UniversalTask


def get_arm_perturbation_tasks() -> List[UniversalTask]:
    """Returns the 5 dynamic arm perturbation fault tolerance tasks."""
    return [
        UniversalTask(
            task_id="ARM01",
            name="Dynamic Specialist Degradation and Bayes-UCB Rerouting",
            dataset_source=DatasetSource.ARM_PERTURBATION,
            family=TaskFamily.FAULT_TOLERANT_ROUTING,
            complexity=ComplexityTier.HIGH,
            objective="Detect specialist reliability drop from 95% to 20% mid-run and adaptively reroute via Bayes-UCB.",
            constraints=[
                "Monitor specialist agent execution outcomes in real time",
                "Detect when primary specialist success drops from 0.95 to 0.20",
                "Update conjugate Beta posterior parameters (alpha, beta)",
                "Shift traffic dynamically to secondary specialist when upper bound inverts",
                "Verify cumulative regret follows logarithmic scaling O(ln T)"
            ],
            negative_constraints=[
                "Do NOT retain static hardcoded routing to failing specialist",
                "Zero unhandled system crashes during specialist degradation"
            ],
            allowed_tools=["incident_log_store", "procurement_db"],
            expected_schema={
                "type": "object",
                "properties": {
                    "perturbation_detected": {"type": "boolean"},
                    "rerouted_to_secondary": {"type": "boolean"},
                    "logarithmic_regret_verified": {"type": "boolean"},
                    "final_success_rate": {"type": "number"}
                },
                "required": ["perturbation_detected", "rerouted_to_secondary", "logarithmic_regret_verified"]
            },
            frozen_rubric={
                "expected_values": {
                    "perturbation_detected": True,
                    "rerouted_to_secondary": True,
                    "logarithmic_regret_verified": True
                }
            },
            input_data={
                "arm_perturbation": True,
                "degraded_agent": "specialist_synthesis_alpha",
                "degraded_success_prob": 0.20,
                "baseline_success_prob": 0.95
            },
            subtasks=[
                "Step 1: Route initial requests to primary specialist",
                "Step 2: Inject mid-run degradation anomaly",
                "Step 3: Update Bayesian Beta evidence",
                "Step 4: Reroute execution to secondary specialist",
                "Step 5: Compute cumulative regret curve"
            ]
        ),
        UniversalTask(
            task_id="ARM02",
            name="Transient Fault Burst and Rapid Policy Recovery",
            dataset_source=DatasetSource.ARM_PERTURBATION,
            family=TaskFamily.FAULT_TOLERANT_ROUTING,
            complexity=ComplexityTier.HIGH,
            objective="Mitigate transient 5-failure burst on primary agent without incurring linear regret.",
            constraints=[
                "Absorb transient error burst on primary arm",
                "Evaluate upper credible quantile (1 - 1/t) for alternative specialist",
                "Divert execution load to backup agent within 2 steps",
                "Confirm system maintains > 80% overall task completion rate"
            ],
            negative_constraints=[
                "Do NOT permanently discard recoverable specialist without exploratory probe",
                "Zero cascading downtime"
            ],
            allowed_tools=["incident_log_store"],
            expected_schema={
                "type": "object",
                "properties": {
                    "fault_burst_contained": {"type": "boolean"},
                    "diverted_within_steps": {"type": "integer"},
                    "sublinear_regret": {"type": "boolean"}
                },
                "required": ["fault_burst_contained", "diverted_within_steps", "sublinear_regret"]
            },
            frozen_rubric={
                "expected_values": {
                    "fault_burst_contained": True,
                    "sublinear_regret": True
                }
            },
            input_data={"burst_length": 5, "fault_rate": 0.80},
            subtasks=["Trigger fault burst", "Detect quantile inversion", "Execute adaptive shift"]
        ),
        UniversalTask(
            task_id="ARM03",
            name="Multi-Arm Preference Inversion under Environment Drift",
            dataset_source=DatasetSource.ARM_PERTURBATION,
            family=TaskFamily.FAULT_TOLERANT_ROUTING,
            complexity=ComplexityTier.HIGH,
            objective="Adapt to environmental drift where backup agent becomes strictly superior to primary agent.",
            constraints=[
                "Track multi-arm rewards across 10 sequential rounds",
                "Simulate environment drift where Arm 1 drops to 0.20 and Arm 2 rises to 0.95",
                "Demonstrate Bayes-UCB inverts preference within 3 decision steps",
                "Empirically contrast against static baseline linear loss"
            ],
            negative_constraints=[
                "Zero linear regret accumulation O(T)"
            ],
            allowed_tools=["procurement_db"],
            expected_schema={
                "type": "object",
                "properties": {
                    "preference_inverted": {"type": "boolean"},
                    "adaptation_steps": {"type": "integer"},
                    "bayes_ucb_superior": {"type": "boolean"}
                },
                "required": ["preference_inverted", "bayes_ucb_superior"]
            },
            frozen_rubric={
                "expected_values": {
                    "preference_inverted": True,
                    "bayes_ucb_superior": True
                }
            },
            input_data={"drift_round": 5, "arm1_post_drift": 0.20, "arm2_post_drift": 0.95},
            subtasks=["Monitor baseline rounds", "Apply environment drift", "Verify preference inversion"]
        ),
        UniversalTask(
            task_id="ARM04",
            name="Cascading Specialist Failure Isolation and Bounding",
            dataset_source=DatasetSource.ARM_PERTURBATION,
            family=TaskFamily.FAULT_TOLERANT_ROUTING,
            complexity=ComplexityTier.HIGH,
            objective="Isolate degrading specialist to prevent cascading failure across multi-agent workflow.",
            constraints=[
                "Identify failing specialist arm before timeout propagation",
                "Penalize unfaithful specialist in BayesUCBCoordinator",
                "Maintain end-to-end task SLA under degraded agent condition",
                "Log anomaly event in cryptographic ledger"
            ],
            negative_constraints=[
                "Do NOT allow degraded arm to stall coordinator pipeline"
            ],
            allowed_tools=["incident_log_store"],
            expected_schema={
                "type": "object",
                "properties": {
                    "arm_isolated": {"type": "boolean"},
                    "sla_preserved": {"type": "boolean"},
                    "ledger_logged": {"type": "boolean"}
                },
                "required": ["arm_isolated", "sla_preserved", "ledger_logged"]
            },
            frozen_rubric={
                "expected_values": {
                    "arm_isolated": True,
                    "sla_preserved": True,
                    "ledger_logged": True
                }
            },
            input_data={"degrade_mode": "latency_and_failure"},
            subtasks=["Detect latency and error anomaly", "Apply Bayesian arm freeze", "Confirm SLA preservation"]
        ),
        UniversalTask(
            task_id="ARM05",
            name="Post-Perturbation Recovery and Credible Bound Re-Exploration",
            dataset_source=DatasetSource.ARM_PERTURBATION,
            family=TaskFamily.FAULT_TOLERANT_ROUTING,
            complexity=ComplexityTier.HIGH,
            objective="Probe previously degraded specialist after simulated recovery to resume optimal exploitation.",
            constraints=[
                "Restore perturbed specialist back to 0.95 success probability",
                "Validate that Bayes-UCB upper credible bound allows principled re-exploration",
                "Resume primary exploitation once posterior evidence confirms recovery",
                "Confirm optimal asymptotic routing convergence"
            ],
            negative_constraints=[
                "Do NOT permanently starve recovered specialist"
            ],
            allowed_tools=["procurement_db", "incident_log_store"],
            expected_schema={
                "type": "object",
                "properties": {
                    "recovery_detected": {"type": "boolean"},
                    "re_explored_successfully": {"type": "boolean"},
                    "optimal_convergence": {"type": "boolean"}
                },
                "required": ["recovery_detected", "re_explored_successfully", "optimal_convergence"]
            },
            frozen_rubric={
                "expected_values": {
                    "recovery_detected": True,
                    "re_explored_successfully": True,
                    "optimal_convergence": True
                }
            },
            input_data={"recovery_step": 8, "recovered_prob": 0.95},
            subtasks=["Simulate agent recovery", "Execute credible bound exploration", "Confirm optimal convergence"]
        )
    ]
