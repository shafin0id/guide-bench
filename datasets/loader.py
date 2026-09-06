"""
Unified Dataset Loader and Validation Module.

Provides single-point access to the 60 benchmark tasks across Enterprise,
InjecAgent (Security), GAIA (Multi-Hop), ToolBench (Open-Domain Tool Use),
HotpotQA (Multi-Hop Retrieval), SWE-bench Lite (Code Collaboration), and
MultiAgentBench Arm Perturbation evaluation suites.
"""

from typing import List, Optional
from core.schemas import ComplexityTier, DatasetSource, TaskFamily, UniversalTask
from datasets.arm_perturbation_tasks import get_arm_perturbation_tasks
from datasets.enterprise_tasks import get_enterprise_tasks
from datasets.gaia_tasks import get_gaia_tasks
from datasets.hotpotqa_tasks import get_hotpotqa_tasks
from datasets.injecagent_tasks import get_injecagent_tasks
from datasets.swebench_tasks import get_swebench_tasks
from datasets.toolbench_tasks import get_toolbench_tasks


def get_benchmark_suite(suite_name: str) -> List[UniversalTask]:
    """
    Retrieves the designated benchmark suite by name.

    Args:
        suite_name: 'enterprise' (18 tasks), 'injecagent' (12 tasks),
                    'gaia' (10 tasks), 'toolbench' (10 tasks),
                    'hotpotqa' (5 tasks), 'swebench' (5 tasks),
                    'arm_perturbation' (5 tasks), or 'all'/'full' (60 tasks).

    Returns:
        List of UniversalTask objects conforming to the universal task schema.
    """
    normalized = suite_name.strip().lower()

    if normalized in ("enterprise", "ent"):
        return get_enterprise_tasks()
    elif normalized in ("injecagent", "security", "sec"):
        return get_injecagent_tasks()
    elif normalized in ("gaia", "multihop", "multi_hop"):
        return get_gaia_tasks()
    elif normalized in ("toolbench", "tools", "tool"):
        return get_toolbench_tasks()
    elif normalized in ("hotpotqa", "hotpot"):
        return get_hotpotqa_tasks()
    elif normalized in ("swebench", "swe", "code"):
        return get_swebench_tasks()
    elif normalized in ("arm_perturbation", "arm", "perturbation"):
        return get_arm_perturbation_tasks()
    elif normalized in ("all", "full", "matrix"):
        return get_all_tasks()
    else:
        raise ValueError(
            f"Unknown benchmark suite '{suite_name}'. Valid options are: "
            "'enterprise', 'injecagent', 'gaia', 'toolbench', 'hotpotqa', "
            "'swebench', 'arm_perturbation', 'all'."
        )


def get_all_tasks() -> List[UniversalTask]:
    """
    Aggregates the complete 60 standardized benchmark tasks across the 6 formal suites:
    - 18 Enterprise tasks (T01 - T18)
    - 12 InjecAgent tasks (SEC01 - SEC12)
    - 10 GAIA multi-hop tasks (GAIA01 - GAIA10)
    - 10 ToolBench open-domain tasks (TOOL01 - TOOL10)
    - 5 HotpotQA retrieval tasks (HOTPOT01 - HOTPOT05)
    - 5 SWE-bench Lite collaboration tasks (SWE01 - SWE05)
    Total = 60 tasks.
    """
    return (
        get_enterprise_tasks()
        + get_injecagent_tasks()
        + get_gaia_tasks()
        + get_toolbench_tasks()
        + get_hotpotqa_tasks()
        + get_swebench_tasks()
    )


def get_task_by_id(task_id: str) -> Optional[UniversalTask]:
    """Finds a task by its unique task identifier (case-insensitive)."""
    target = task_id.strip().upper()
    pool = get_all_tasks() + get_arm_perturbation_tasks()
    for task in pool:
        if task.task_id.upper() == target:
            return task
    return None


def filter_tasks(
    source: Optional[DatasetSource] = None,
    family: Optional[TaskFamily] = None,
    complexity: Optional[ComplexityTier] = None,
    include_arm_perturbation: bool = True
) -> List[UniversalTask]:
    """Filters the universal task repository by metadata attributes."""
    pool = (get_all_tasks() + get_arm_perturbation_tasks()) if include_arm_perturbation else get_all_tasks()
    filtered = []
    for t in pool:
        if source and t.dataset_source != source:
            continue
        if family and t.family != family:
            continue
        if complexity and t.complexity != complexity:
            continue
        filtered.append(t)
    return filtered
