"""
Universal Schemas for Multi-Agent Systems Benchmarking.

Defines Pydantic v2 models for tasks, tool execution records, and standardized
framework execution results across GUIDE, CrewAI, LangGraph, and AutoGen.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskFamily(str, Enum):
    """Categorical classification of workflow task families."""
    CONSTRAINED_SYNTHESIS = "constrained_synthesis"
    EVIDENCE_RECONCILIATION = "evidence_reconciliation"
    POLICY_PLANNING = "policy_planning"
    SECURITY_INJECTION = "security_injection"
    MULTI_HOP_CONTEXT = "multi_hop_context"
    OPEN_DOMAIN_TOOL_USE = "open_domain_tool_use"
    MULTI_HOP_RETRIEVAL = "multi_hop_retrieval"
    CODE_COLLABORATION = "code_collaboration"
    FAULT_TOLERANT_ROUTING = "fault_tolerant_routing"


class ComplexityTier(str, Enum):
    """Complexity tiers defining constraint density and delegation depth."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DatasetSource(str, Enum):
    """Benchmark dataset provenance."""
    ENTERPRISE = "enterprise"
    INJECAGENT = "injecagent"
    GAIA = "gaia"
    TOOLBENCH = "toolbench"
    HOTPOTQA = "hotpotqa"
    SWEBENCH = "swebench"
    ARM_PERTURBATION = "arm_perturbation"


class ToolCallRecord(BaseModel):
    """Immutable audit record of a tool invocation attempt by an agent."""
    tool_name: str = Field(description="Name of the invoked tool")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool")
    result: Any = Field(default=None, description="Output payload returned from the tool")
    is_authorized: bool = Field(default=True, description="Whether invocation adhered to permitted_tools and policies")
    is_write: bool = Field(default=False, description="Whether the tool mutates external system state")
    violation_reason: Optional[str] = Field(default=None, description="Detailed explanation if policy check failed")
    timestamp: float = Field(description="Epoch timestamp of invocation")


class UniversalTask(BaseModel):
    """
    Standardized task representation across all benchmark suites and frameworks.
    """
    task_id: str = Field(description="Unique task identifier (e.g., T01, SEC01, GAIA01)")
    name: str = Field(description="Descriptive task title")
    dataset_source: DatasetSource = Field(description="Suite origin (ENTERPRISE, INJECAGENT, GAIA)")
    family: TaskFamily = Field(description="Workflow domain family")
    complexity: ComplexityTier = Field(description="Complexity tier (LOW, MEDIUM, HIGH)")
    objective: str = Field(description="Root task intent anchor (S_0)")
    constraints: List[str] = Field(default_factory=list, description="Mandatory constraints that must be preserved")
    negative_constraints: List[str] = Field(default_factory=list, description="Explicit operational prohibitions")
    allowed_tools: List[str] = Field(default_factory=list, description="Permitted sandboxed tools")
    expected_schema: Dict[str, Any] = Field(default_factory=dict, description="Structural schema required in output")
    adversarial_vector: Optional[str] = Field(default=None, description="Injected adversarial prompt or security vector")
    frozen_rubric: Dict[str, Any] = Field(default_factory=dict, description="Deterministic evaluation rubric specification")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input entities, IDs, or contextual parameters")
    subtasks: List[str] = Field(default_factory=list, description="Ordered delegation subtasks or hops")


class UniversalExecutionResult(BaseModel):
    """
    Standardized execution metric output captured from any framework adapter.
    """
    run_id: str = Field(description="Globally unique identifier for this execution run")
    task_id: str = Field(description="Target task identifier")
    framework_name: str = Field(description="Target framework under evaluation (e.g., guide, crewai, langgraph, autogen)")
    repetition: int = Field(default=1, description="Repetition index (1..N)")
    success: bool = Field(description="Binary task pass/fail evaluated against deterministic frozen rubric")
    intent_fidelity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Intent Preservation Score (IPS) measuring ratio of preserved initial constraints"
    )
    policy_violations: int = Field(
        default=0,
        description="Count of unauthorized tool calls, write operations, or privilege escalation attempts"
    )
    wall_clock_seconds: float = Field(
        ge=0.0,
        description="Total elapsed wall-clock execution time in seconds"
    )
    prompt_tokens: int = Field(default=0, description="Total prompt tokens consumed across all model calls")
    completion_tokens: int = Field(default=0, description="Total generated completion tokens")
    total_tokens: int = Field(default=0, description="Cumulative tokens (prompt + completion)")
    cache_read_tokens: int = Field(default=0, description="Prompt tokens retrieved from provider cache")
    cost_usd: float = Field(
        default=0.0,
        ge=0.0,
        description="Total execution cost in USD calculated deterministically via model pricing table"
    )
    trace_verified: bool = Field(
        default=False,
        description="Whether cryptographic lineage and signature ledger validation succeeded"
    )
    tool_calls: List[ToolCallRecord] = Field(
        default_factory=list,
        description="Chronological audit log of all attempted and executed tool invocations"
    )
    raw_output: str = Field(default="", description="Raw output text returned by the framework")
    parsed_output: Dict[str, Any] = Field(default_factory=dict, description="Structured parsed JSON payload")
    error_log: Optional[str] = Field(default=None, description="Detailed traceback or error if execution failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional framework-specific diagnostic metadata")
    regret: Optional[float] = Field(default=None, description="Cumulative regret under multi-armed bandit routing evaluation")
    hop_tokens: List[int] = Field(default_factory=list, description="Per-hop token breakdown for scaling analysis across delegation depth")
    canonical_state_hash: Optional[str] = Field(default=None, description="RFC 8785 deterministic canonical hash of output state payload")
