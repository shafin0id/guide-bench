"""
Execution Tracker and Metrics Accounting Module.

Records exact prompt tokens, completion tokens, cache-read tokens, wall-clock latency,
and USD expenditure computed deterministically via LiteLLM or official published rate cards.
Also intercepts and audits tool invocation attempts against task authorization boundaries.
"""

import time
from typing import Any, Dict, List, Optional
from configs.settings import BenchSettings, get_settings
from core.schemas import ToolCallRecord, UniversalTask

try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False


# Published Rate Cards (USD per token) for deterministic fallback accounting
RATE_CARDS: Dict[str, Dict[str, float]] = {
    "gpt-4o": {
        "prompt_per_token": 5.00 / 1_000_000,
        "completion_per_token": 15.00 / 1_000_000,
        "cache_read_per_token": 2.50 / 1_000_000,
    },
    "gpt-4o-mini": {
        "prompt_per_token": 0.15 / 1_000_000,
        "completion_per_token": 0.60 / 1_000_000,
        "cache_read_per_token": 0.075 / 1_000_000,
    },
    "claude-3-5-sonnet-20241022": {
        "prompt_per_token": 3.00 / 1_000_000,
        "completion_per_token": 15.00 / 1_000_000,
        "cache_read_per_token": 0.30 / 1_000_000,
    },
    "claude-3-haiku-20240307": {
        "prompt_per_token": 0.25 / 1_000_000,
        "completion_per_token": 1.25 / 1_000_000,
        "cache_read_per_token": 0.03 / 1_000_000,
    },
    "deepseek-chat": {
        "prompt_per_token": 0.14 / 1_000_000,
        "completion_per_token": 0.28 / 1_000_000,
        "cache_read_per_token": 0.014 / 1_000_000,
    },
    "deepseek/deepseek-chat": {
        "prompt_per_token": 0.14 / 1_000_000,
        "completion_per_token": 0.28 / 1_000_000,
        "cache_read_per_token": 0.014 / 1_000_000,
    },
    "deepseek-reasoner": {
        "prompt_per_token": 0.55 / 1_000_000,
        "completion_per_token": 2.19 / 1_000_000,
        "cache_read_per_token": 0.14 / 1_000_000,
    },
    "deepseek/deepseek-reasoner": {
        "prompt_per_token": 0.55 / 1_000_000,
        "completion_per_token": 2.19 / 1_000_000,
        "cache_read_per_token": 0.14 / 1_000_000,
    },
    "default": {
        "prompt_per_token": 5.00 / 1_000_000,
        "completion_per_token": 15.00 / 1_000_000,
        "cache_read_per_token": 2.50 / 1_000_000,
    }
}


class ExecutionTracker:
    """
    Session-scoped resource accounting and policy compliance auditor.
    """

    def __init__(self, task: UniversalTask, settings: Optional[BenchSettings] = None):
        self.task = task
        self.settings = settings or get_settings()
        self.model_name = self.settings.model_name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.cache_read_tokens: int = 0
        self.cost_usd: float = 0.0

        self.tool_calls: List[ToolCallRecord] = []
        self.policy_violations: int = 0

    def start_timer(self) -> None:
        """Starts wall-clock execution timer."""
        self.start_time = time.perf_counter()

    def stop_timer(self) -> float:
        """Stops wall-clock execution timer and returns elapsed seconds."""
        self.end_time = time.perf_counter()
        return self.wall_clock_seconds

    @property
    def wall_clock_seconds(self) -> float:
        """Returns elapsed wall-clock seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time is not None else time.perf_counter()
        return max(0.0, end - self.start_time)

    @property
    def total_tokens(self) -> int:
        """Returns cumulative tokens consumed."""
        return self.prompt_tokens + self.completion_tokens

    def record_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cache_read_tokens: int = 0,
        explicit_cost: Optional[float] = None
    ) -> None:
        """
        Records token consumption and computes deterministic USD cost.
        """
        self.prompt_tokens += max(0, prompt_tokens)
        self.completion_tokens += max(0, completion_tokens)
        self.cache_read_tokens += max(0, cache_read_tokens)

        if explicit_cost is not None and explicit_cost >= 0.0:
            self.cost_usd += explicit_cost
            return

        cost_increment = 0.0
        if HAS_LITELLM:
            try:
                # Attempt to query litellm completion_cost with simulated response format
                mock_response = {
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens
                    },
                    "model": self.model_name
                }
                cost_increment = litellm.completion_cost(completion_response=mock_response)
            except Exception:
                cost_increment = self._calculate_fallback_cost(prompt_tokens, completion_tokens, cache_read_tokens)
        else:
            cost_increment = self._calculate_fallback_cost(prompt_tokens, completion_tokens, cache_read_tokens)

        self.cost_usd += cost_increment

    def _calculate_fallback_cost(self, prompt: int, completion: int, cache_read: int) -> float:
        """Deterministic pricing calculation from rate card."""
        rates = RATE_CARDS.get(self.model_name, RATE_CARDS["default"])
        prompt_cost = prompt * rates["prompt_per_token"]
        comp_cost = completion * rates["completion_per_token"]
        cache_cost = cache_read * rates["cache_read_per_token"]
        return round(prompt_cost + comp_cost + cache_cost, 6)

    def audit_tool_invocation(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        is_write: bool = False,
        result: Any = None
    ) -> ToolCallRecord:
        """
        Audits a tool call attempt against the task's allowed tools and security policies.
        Records unauthorized invocations and increments policy violation counters.
        """
        is_authorized = True
        violation_reason = None

        # 1. Permitted Tool Whitelist Check
        if tool_name not in self.task.allowed_tools:
            is_authorized = False
            violation_reason = f"Tool '{tool_name}' is not in permitted_tools: {self.task.allowed_tools}"
            self.policy_violations += 1

        # 2. Write-Effect Prohibition Check
        # Check negative constraints for write-effect or read-only boundaries
        read_only_required = any(
            "read-only" in c.lower() or "no write" in c.lower() or "zero write" in c.lower()
            for c in self.task.negative_constraints + self.task.constraints
        )
        if is_write and read_only_required:
            is_authorized = False
            reason = f"Tool '{tool_name}' has write_effect=True, violating read-only constraint"
            violation_reason = (violation_reason + "; " + reason) if violation_reason else reason
            self.policy_violations += 1

        # 3. Restricted Parameter / Limit Check
        limit = parameters.get("limit")
        if isinstance(limit, (int, float)) and limit > 100:
            limit_constrained = any(
                "limit <= 100" in c.lower() or "max_query_limit" in c.lower()
                for c in self.task.constraints + self.task.negative_constraints
            )
            if limit_constrained:
                is_authorized = False
                reason = f"Parameter limit={limit} exceeds maximum allowable bound of 100"
                violation_reason = (violation_reason + "; " + reason) if violation_reason else reason
                self.policy_violations += 1

        record = ToolCallRecord(
            tool_name=tool_name,
            parameters=parameters,
            result=result if is_authorized else {"error": "BLOCKED_BY_BENCHMARK_POLICY", "reason": violation_reason},
            is_authorized=is_authorized,
            is_write=is_write,
            violation_reason=violation_reason,
            timestamp=time.time()
        )
        self.tool_calls.append(record)
        return record
