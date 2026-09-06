"""
Abstract Base Tool Interface for Sandboxed Enterprise Evaluations.

Ensures all framework adapters interact with tools through an identical contract,
with consistent schemas, parameter validation, and security metadata.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseSandboxedTool(ABC):
    """
    Abstract base class for all sandboxed tools in the evaluation harness.
    """

    def __init__(
        self,
        name: str,
        description: str,
        resource_class: str,
        is_write_effect: bool = False,
        sensitivity_level: str = "INTERNAL"
    ):
        self.name = name
        self.description = description
        self.resource_class = resource_class
        self.is_write_effect = is_write_effect
        self.sensitivity_level = sensitivity_level
        self.invocation_log: list[Dict[str, Any]] = []

    @abstractmethod
    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Executes the tool logic with sandboxed parameters.
        Must return a structured dictionary containing 'status' and results.
        """
        pass

    @abstractmethod
    def to_openai_function_spec(self) -> Dict[str, Any]:
        """
        Returns the OpenAI / LiteLLM function calling schema for this tool.
        """
        pass

    def log_invocation(self, parameters: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Records an execution trace in the tool's internal telemetry."""
        self.invocation_log.append({
            "parameters": parameters,
            "result_status": result.get("status", "UNKNOWN"),
            "is_write": self.is_write_effect
        })

    def reset_log(self) -> None:
        """Clears invocation telemetry between benchmark runs."""
        self.invocation_log.clear()
