"""
Configuration settings for the Universal Multi-Agent Benchmarking Suite (guide-bench).

Provides strict Pydantic v2 configuration management ensuring model invariance,
deterministic seeds, temperature parity, and sandboxed execution boundaries.
"""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Automatically load environment variables from .env if present
load_dotenv()


class BenchSettings(BaseModel):
    """
    Benchmark execution configuration conforming to experimental parity requirements.
    """

    # Model & Inference Settings (Controlled Experimental Parity)
    llm_provider: str = Field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "deepseek" if os.getenv("DEEPSEEK_API_KEY") else "openai"),
        description="Underlying LLM provider for LiteLLM routing (e.g., deepseek, openai, anthropic)"
    )
    model_name: str = Field(
        default_factory=lambda: os.getenv("BENCH_MODEL", "deepseek/deepseek-chat" if os.getenv("DEEPSEEK_API_KEY") else "gpt-4o"),
        description="Foundation LLM checkpoint identifier across all adapters"
    )
    temperature: float = Field(
        default=0.0,
        description="Strict temperature invariant (0.0) to eliminate sampling variance"
    )
    top_p: float = Field(
        default=1.0,
        description="Nucleus sampling cutoff (1.0 for greedy decoding)"
    )
    seed: int = Field(
        default=42,
        description="Deterministic random seed for reproducibility"
    )
    max_tokens: int = Field(
        default=4096,
        description="Upper token budget cap per generation step"
    )
    max_retries: int = Field(
        default=2,
        description="Strict retry and exception budget per step"
    )
    timeout_seconds: float = Field(
        default=120.0,
        description="Maximum execution timeout per task run"
    )

    # Benchmark Matrix Execution Settings
    default_repetitions: int = Field(
        default=5,
        description="Number of paired experimental repetitions per task (N=5)"
    )
    mock_mode: bool = Field(
        default=False,
        description="When True, executes deterministic offline simulation without external API calls"
    )
    frameworks: List[str] = Field(
        default=["guide", "crewai", "langgraph", "autogen"],
        description="List of target framework adapter names in benchmark matrix"
    )
    suites: List[str] = Field(
        default=["enterprise", "injecagent", "gaia", "toolbench", "hotpotqa", "swebench"],
        description="Active benchmark suites to evaluate"
    )
    arm_perturbation: bool = Field(
        default=False,
        description="Whether dynamic specialist arm perturbation simulation is enabled"
    )

    # Output & Persistence Directories
    output_dir: Path = Field(
        default=Path("output"),
        description="Root output directory for artifacts, logs, and leaderboards"
    )
    results_filename: str = Field(
        default="benchmark_results.jsonl",
        description="Append-only streaming results log file"
    )
    manifest_filename: str = Field(
        default="benchmark_manifest.json",
        description="Run manifest file containing environment metadata"
    )
    enable_trace_validation: bool = Field(
        default=True,
        description="Whether to rigorously verify cryptographic trace integrity"
    )

    @property
    def results_path(self) -> Path:
        """Returns the full resolved path to the streaming results file."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir / self.results_filename

    @property
    def manifest_path(self) -> Path:
        """Returns the full resolved path to the run manifest file."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir / self.manifest_filename


_GLOBAL_SETTINGS: Optional[BenchSettings] = None


def get_settings() -> BenchSettings:
    """Retrieves the active global benchmark settings instance."""
    global _GLOBAL_SETTINGS
    if _GLOBAL_SETTINGS is None:
        _GLOBAL_SETTINGS = BenchSettings()
    return _GLOBAL_SETTINGS


def set_settings(settings: BenchSettings) -> None:
    """Updates the active global benchmark settings instance."""
    global _GLOBAL_SETTINGS
    _GLOBAL_SETTINGS = settings
