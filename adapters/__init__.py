"""
Pluggable multi-agent framework adapters package.
"""

from typing import Optional
from adapters.autogen_adapter import AutoGenAdapter
from adapters.base import BaseFrameworkAdapter
from adapters.crewai_adapter import CrewAIAdapter
from adapters.guide_adapter import GUIDEAdapter
from adapters.langgraph_adapter import LangGraphAdapter
from configs.settings import BenchSettings


def get_adapter(name: str, settings: Optional[BenchSettings] = None) -> BaseFrameworkAdapter:
    """
    Factory function instantiating the requested framework adapter.

    Args:
        name: One of 'guide', 'crewai', 'langgraph', 'autogen'.
        settings: Optional configuration settings.

    Returns:
        BaseFrameworkAdapter instance.
    """
    normalized = name.strip().lower()
    if normalized in ("guide", "guide_mas"):
        return GUIDEAdapter(settings=settings)
    elif normalized in ("crewai", "crew"):
        return CrewAIAdapter(settings=settings)
    elif normalized in ("langgraph", "lang_graph"):
        return LangGraphAdapter(settings=settings)
    elif normalized in ("autogen", "pyautogen"):
        return AutoGenAdapter(settings=settings)
    else:
        raise ValueError(
            f"Unsupported framework adapter '{name}'. Supported adapters are: "
            "'guide', 'crewai', 'langgraph', 'autogen'."
        )


__all__ = [
    "BaseFrameworkAdapter",
    "GUIDEAdapter",
    "CrewAIAdapter",
    "LangGraphAdapter",
    "AutoGenAdapter",
    "get_adapter",
]
