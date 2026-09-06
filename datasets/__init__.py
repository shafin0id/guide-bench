"""
Benchmark datasets package for multi-agent evaluation suites.
"""

from datasets.enterprise_tasks import get_enterprise_tasks
from datasets.gaia_tasks import get_gaia_tasks
from datasets.injecagent_tasks import get_injecagent_tasks
from datasets.loader import filter_tasks, get_all_tasks, get_benchmark_suite, get_task_by_id

__all__ = [
    "get_benchmark_suite",
    "get_all_tasks",
    "get_task_by_id",
    "filter_tasks",
    "get_enterprise_tasks",
    "get_injecagent_tasks",
    "get_gaia_tasks",
]
