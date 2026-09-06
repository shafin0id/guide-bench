"""
Pytest configuration and environment fixtures for guide-bench.
Ensures local framework repositories (guide) and benchmark suites are on sys.path.
"""

import sys
from pathlib import Path

# Add guide framework repo to sys.path
guide_repo = Path("/Users/shafinoid/Documents/GitHub/guide")
if guide_repo.exists() and str(guide_repo) not in sys.path:
    sys.path.insert(0, str(guide_repo))

# Add guide-bench repo to sys.path
bench_repo = Path("/Users/shafinoid/Documents/GitHub/guide-bench")
if bench_repo.exists() and str(bench_repo) not in sys.path:
    sys.path.insert(0, str(bench_repo))
