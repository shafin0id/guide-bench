"""
HotpotQA Multi-Hop Benign Retrieval Benchmark Tasks Module.

Implements 5 curated multi-hop document chaining tasks (HOTPOT01 - HOTPOT05)
requiring 3 to 5 sequential knowledge graph traversals to benchmark token efficiency:
proving Content-Addressable Storage (CAS) input_refs[] maintain flat token growth
across hops O(1), contrasting against exponential/linear prompt accumulation in baselines.
"""

from typing import List
from core.schemas import ComplexityTier, DatasetSource, TaskFamily, UniversalTask


def get_hotpotqa_tasks() -> List[UniversalTask]:
    """Returns the 5 curated HotpotQA multi-hop benchmark tasks."""
    return [
        UniversalTask(
            task_id="HOTPOT01",
            name="3-Hop Filmmaker Academic Lineage Retrieval",
            dataset_source=DatasetSource.HOTPOTQA,
            family=TaskFamily.MULTI_HOP_RETRIEVAL,
            complexity=ComplexityTier.MEDIUM,
            objective="Trace film Inception across 3 hops to determine the founding year of its director's alma mater.",
            constraints=[
                "Hop 1: Query knowledge_graph_store for 'Inception' to identify director",
                "Hop 2: Query knowledge_graph_store for 'Christopher Nolan' to identify university",
                "Hop 3: Query knowledge_graph_store for 'University College London' to extract founded year",
                "Verify founded year is exactly 1826",
                "Maintain flat token footprint via CAS input_refs[]",
                "Enforce read-only retrieval"
            ],
            negative_constraints=[
                "Do NOT accumulate raw document dumps across hops",
                "Zero invocation of write tools"
            ],
            allowed_tools=["knowledge_graph_store", "document_store"],
            expected_schema={
                "type": "object",
                "properties": {
                    "hop_count": {"type": "integer"},
                    "film": {"type": "string"},
                    "director": {"type": "string"},
                    "alma_mater": {"type": "string"},
                    "founded_year": {"type": "integer"}
                },
                "required": ["hop_count", "film", "director", "alma_mater", "founded_year"]
            },
            frozen_rubric={
                "min_hops_required": 3,
                "expected_values": {
                    "hop_count": 3,
                    "film": "Inception",
                    "director": "Christopher Nolan",
                    "alma_mater": "University College London",
                    "founded_year": 1826
                }
            },
            input_data={"initial_entity": "Inception"},
            subtasks=[
                "Hop 1: Retrieve film entity and director",
                "Hop 2: Retrieve director entity and alma mater",
                "Hop 3: Retrieve university entity and founding year"
            ]
        ),
        UniversalTask(
            task_id="HOTPOT02",
            name="4-Hop Historical Treaty Geographic Reconciliation",
            dataset_source=DatasetSource.HOTPOTQA,
            family=TaskFamily.MULTI_HOP_RETRIEVAL,
            complexity=ComplexityTier.HIGH,
            objective="Trace Treaty of Portsmouth across 4 hops to determine the length of the river at its negotiator's birth city.",
            constraints=[
                "Hop 1: Query knowledge_graph_store for 'Treaty of Portsmouth' to identify negotiator",
                "Hop 2: Query knowledge_graph_store for 'Theodore Roosevelt' to identify birth city",
                "Hop 3: Query knowledge_graph_store for 'New York City' to identify situated river",
                "Hop 4: Query knowledge_graph_store for 'Hudson River' to extract river length (507 km)",
                "Preserve query intent S_0 across all 4 hops",
                "Maintain read-only data access"
            ],
            negative_constraints=[
                "Do NOT introduce external ungrounded facts",
                "Zero write operations"
            ],
            allowed_tools=["knowledge_graph_store", "document_store"],
            expected_schema={
                "type": "object",
                "properties": {
                    "hop_count": {"type": "integer"},
                    "treaty": {"type": "string"},
                    "negotiator": {"type": "string"},
                    "birth_city": {"type": "string"},
                    "river": {"type": "string"},
                    "length_km": {"type": "integer"}
                },
                "required": ["hop_count", "treaty", "negotiator", "birth_city", "river", "length_km"]
            },
            frozen_rubric={
                "min_hops_required": 4,
                "expected_values": {
                    "hop_count": 4,
                    "treaty": "Treaty of Portsmouth",
                    "negotiator": "Theodore Roosevelt",
                    "birth_city": "New York City",
                    "river": "Hudson River",
                    "length_km": 507
                }
            },
            input_data={"initial_entity": "Treaty of Portsmouth"},
            subtasks=[
                "Hop 1: Query treaty and mediator",
                "Hop 2: Query mediator and birth city",
                "Hop 3: Query city and adjacent river",
                "Hop 4: Query river and compute length"
            ]
        ),
        UniversalTask(
            task_id="HOTPOT03",
            name="3-Hop Scientific Discovery Nobel Prize Lineage",
            dataset_source=DatasetSource.HOTPOTQA,
            family=TaskFamily.MULTI_HOP_RETRIEVAL,
            complexity=ComplexityTier.MEDIUM,
            objective="Trace CRISPR-Cas9 across 3 hops to determine the Nobel Prize year awarded to its pioneer at UC Berkeley.",
            constraints=[
                "Hop 1: Query knowledge_graph_store for 'CRISPR-Cas9' to identify pioneer",
                "Hop 2: Query knowledge_graph_store for 'Jennifer Doudna' to identify research institution",
                "Hop 3: Query knowledge_graph_store for 'UC Berkeley' to extract Nobel Prize year (2020)",
                "Enforce strict read-only knowledge querying",
                "Pass CAS input_refs[] across hops to eliminate context bloating"
            ],
            negative_constraints=[
                "Zero disclosure of unverified citations",
                "Zero write mutations"
            ],
            allowed_tools=["knowledge_graph_store", "document_store"],
            expected_schema={
                "type": "object",
                "properties": {
                    "hop_count": {"type": "integer"},
                    "discovery": {"type": "string"},
                    "pioneer": {"type": "string"},
                    "institution": {"type": "string"},
                    "nobel_year": {"type": "integer"}
                },
                "required": ["hop_count", "discovery", "pioneer", "institution", "nobel_year"]
            },
            frozen_rubric={
                "min_hops_required": 3,
                "expected_values": {
                    "hop_count": 3,
                    "discovery": "CRISPR-Cas9",
                    "pioneer": "Jennifer Doudna",
                    "institution": "UC Berkeley",
                    "nobel_year": 2020
                }
            },
            input_data={"initial_entity": "CRISPR-Cas9"},
            subtasks=[
                "Hop 1: Query genome editing discovery pioneer",
                "Hop 2: Query researcher institution",
                "Hop 3: Query institution Nobel Prize recognition"
            ]
        ),
        UniversalTask(
            task_id="HOTPOT04",
            name="5-Hop Enterprise Corporate Acquisition Chain",
            dataset_source=DatasetSource.HOTPOTQA,
            family=TaskFamily.MULTI_HOP_RETRIEVAL,
            complexity=ComplexityTier.HIGH,
            objective="Trace mobile OS Android across 5 hops to determine corporate headquarters of its parent CEO's firm.",
            constraints=[
                "Hop 1: Query knowledge_graph_store for 'Android' to extract co-founder",
                "Hop 2: Query knowledge_graph_store for 'Andy Rubin' to extract acquiring corporate entity",
                "Hop 3: Query knowledge_graph_store for 'Google LLC' to extract holding company parent",
                "Hop 4: Query knowledge_graph_store for 'Alphabet Inc.' to extract active CEO",
                "Hop 5: Query knowledge_graph_store for 'Sundar Pichai' to extract headquarters city (Mountain View)",
                "Preserve S_0 intent anchor across all 5 delegation handoffs",
                "Maintain flat token consumption per hop"
            ],
            negative_constraints=[
                "Do NOT allow conversational context to grow quadratically across hops",
                "Zero write side effects"
            ],
            allowed_tools=["knowledge_graph_store", "document_store"],
            expected_schema={
                "type": "object",
                "properties": {
                    "hop_count": {"type": "integer"},
                    "product": {"type": "string"},
                    "founder": {"type": "string"},
                    "acquirer": {"type": "string"},
                    "parent_company": {"type": "string"},
                    "ceo": {"type": "string"},
                    "headquarters": {"type": "string"}
                },
                "required": ["hop_count", "product", "founder", "acquirer", "parent_company", "ceo", "headquarters"]
            },
            frozen_rubric={
                "min_hops_required": 5,
                "expected_values": {
                    "hop_count": 5,
                    "product": "Android",
                    "founder": "Andy Rubin",
                    "acquirer": "Google LLC",
                    "parent_company": "Alphabet Inc.",
                    "ceo": "Sundar Pichai",
                    "headquarters": "Mountain View"
                }
            },
            input_data={"initial_entity": "Android"},
            subtasks=[
                "Hop 1: Extract OS founder",
                "Hop 2: Extract corporate acquirer",
                "Hop 3: Extract holding company",
                "Hop 4: Extract executive leadership",
                "Hop 5: Extract corporate headquarters location"
            ]
        ),
        UniversalTask(
            task_id="HOTPOT05",
            name="4-Hop Geographic Mountain Range River Basin Audit",
            dataset_source=DatasetSource.HOTPOTQA,
            family=TaskFamily.MULTI_HOP_RETRIEVAL,
            complexity=ComplexityTier.HIGH,
            objective="Trace Mount Everest across 4 hops to determine the drainage basin area of its outflow river system.",
            constraints=[
                "Hop 1: Query knowledge_graph_store for 'Mount Everest' to extract mountain range",
                "Hop 2: Query knowledge_graph_store for 'Himalayas' to extract headwater river",
                "Hop 3: Query knowledge_graph_store for 'Ganges River' to extract outflow bay",
                "Hop 4: Query knowledge_graph_store for 'Bay of Bengal' to extract basin area (1633000 sq km)",
                "Verify numerical basin area matches 1633000",
                "Enforce read-only geographic querying"
            ],
            negative_constraints=[
                "Zero write operations",
                "Do NOT introduce fabricated hydrographic metrics"
            ],
            allowed_tools=["knowledge_graph_store", "document_store"],
            expected_schema={
                "type": "object",
                "properties": {
                    "hop_count": {"type": "integer"},
                    "peak": {"type": "string"},
                    "range": {"type": "string"},
                    "river": {"type": "string"},
                    "outflow": {"type": "string"},
                    "basin_area_sq_km": {"type": "integer"}
                },
                "required": ["hop_count", "peak", "range", "river", "outflow", "basin_area_sq_km"]
            },
            frozen_rubric={
                "min_hops_required": 4,
                "expected_values": {
                    "hop_count": 4,
                    "peak": "Mount Everest",
                    "range": "Himalayas",
                    "river": "Ganges River",
                    "outflow": "Bay of Bengal",
                    "basin_area_sq_km": 1633000
                }
            },
            input_data={"initial_entity": "Mount Everest"},
            subtasks=[
                "Hop 1: Query peak and parent range",
                "Hop 2: Query range and river system",
                "Hop 3: Query river and oceanic outflow",
                "Hop 4: Query outflow basin area"
            ]
        )
    ]
