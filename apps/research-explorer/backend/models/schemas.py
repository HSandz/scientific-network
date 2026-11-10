"""Typed Pydantic models for the Research Explorer REST API."""

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class NodeLabelEnum(StrEnum):
    RESEARCHER = "Researcher"
    PAPER = "Paper"
    ORGANIZATION = "Organization"
    TOPIC = "Topic"
    VENUE = "Venue"


class RelationEnum(StrEnum):
    AUTHORED = "AUTHORED"
    AFFILIATED_WITH = "AFFILIATED_WITH"
    PUBLISHED_IN = "PUBLISHED_IN"
    CITES = "CITES"
    HAS_TOPIC = "HAS_TOPIC"
    SUBTOPIC_OF = "SUBTOPIC_OF"
    COAUTHORED_WITH = "COAUTHORED_WITH"
    COLLABORATED_WITH = "COLLABORATED_WITH"
    RESEARCHES_TOPIC = "RESEARCHES_TOPIC"
    CONTRIBUTES_TO_TOPIC = "CONTRIBUTES_TO_TOPIC"


class EvidenceKindEnum(StrEnum):
    OBSERVED = "observed"
    INFERRED_TOPIC = "inferred_topic"
    CURATED_TAXONOMY = "curated_taxonomy"
    DERIVED = "derived"


class ViewModeEnum(StrEnum):
    RESEARCHERS = "researchers"
    ORGANIZATIONS = "organizations"
    CITATIONS = "citations"
    HETEROGENEOUS = "heterogeneous"


class FullProjectionMetrics(BaseModel):
    model_config = ConfigDict(extra="allow")

    projection: str | None = None
    degree_strength: float | None = None
    betweenness: float | None = None
    pagerank: float | None = None
    in_degree: int | None = None
    out_degree: int | None = None
    community_id: str | None = None
    community_size: int | None = None
    community_rank: int | None = None


class GraphNode(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    label: NodeLabelEnum
    name: str
    group: str = "default"
    score: float = 0.0
    displayed_degree: int = 0
    displayed_strength: float = 0.0
    x: float = 0.0
    y: float = 0.0
    year: int | None = None
    sector: str | None = None
    country_code: str | None = None
    venue: str | None = None
    url: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    full_metrics: FullProjectionMetrics | None = None


class GraphEdge(BaseModel):
    model_config = ConfigDict(extra="allow")

    edge_id: str
    relation: RelationEnum
    source: str
    target: str
    source_name: str | None = None
    target_name: str | None = None
    source_label: str | None = None
    target_label: str | None = None
    directed: bool = True
    symmetric: bool = False
    evidence_kind: EvidenceKindEnum
    evidence_ids: list[str] = Field(default_factory=list)
    support_count: int = 1
    fractional_weight: float | None = None
    method_version: str = ""
    graph_version: str = ""
    validation_status: str = "accepted"
    properties: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"]
    neo4j_connected: bool
    neo4j_endpoint: str
    expected_graph_version: str
    observed_graph_versions: list[str]
    database_verified: bool
    total_nodes: int
    total_edges: int
    warnings: list[str] = Field(default_factory=list)
    artifacts: dict[str, bool] = Field(default_factory=dict)


class GraphSummaryResponse(BaseModel):
    graph_version: str
    graph_sha256: str
    database_verified: bool
    warnings: list[str] = Field(default_factory=list)
    nodes_by_label: dict[str, int]
    edges_by_relation: dict[str, int]
    edges_by_evidence_kind: dict[str, int]
    total_nodes: int
    total_edges: int
    unique_core_factual_edges: int
    core_papers: int
    resolved_core_researchers: int
    quality: dict[str, Any]
    size_gates: dict[str, Any]
    scientific_caveats: list[str]


class PredicateSpecItem(BaseModel):
    id: str
    predicate: RelationEnum
    source_label: NodeLabelEnum
    target_label: NodeLabelEnum
    evidence_kind: EvidenceKindEnum
    symmetric: bool
    directed: bool
    description: str
    weight_rule: str
    count: int


class LabelSpecItem(BaseModel):
    label: NodeLabelEnum
    description: str
    id_prefix: str
    key_properties: list[str]
    count: int


class GraphSchemaResponse(BaseModel):
    graph_version: str
    labels: list[LabelSpecItem]
    predicates: list[PredicateSpecItem]
    heterogeneous_presets: list[dict[str, Any]]
    evidence_classes: dict[str, str]


class SearchResultItem(BaseModel):
    id: str
    label: NodeLabelEnum
    name: str
    subtitle: str | None = None
    year: int | None = None
    sector: str | None = None
    country_code: str | None = None
    venue: str | None = None
    score: float = 0.0
    url: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    full_metrics: FullProjectionMetrics | None = None


class SearchResponse(BaseModel):
    query: str
    total_matches: int
    grouped_counts: dict[str, int]
    results: list[SearchResultItem]


class GraphViewResponse(BaseModel):
    view: str
    title: str
    description: str
    relation: str
    directed: bool
    full_node_count: int
    full_edge_count: int
    displayed_node_count: int
    displayed_edge_count: int
    score_name: str
    color_meaning: str
    metric_scope_note: str
    scientific_caveat: str
    layout_seed: int
    applied_filters: dict[str, Any] = Field(default_factory=dict)
    available_communities: list[dict[str, Any]] = Field(default_factory=list)
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ConnectedEntityGroup(BaseModel):
    relation: RelationEnum
    direction: Literal["outgoing", "incoming", "undirected"]
    evidence_kind: EvidenceKindEnum
    total_count: int
    items: list[dict[str, Any]]


class NodeDetailResponse(BaseModel):
    node: GraphNode
    relation_counts: dict[str, int]
    total_degree: int
    connected_groups: list[ConnectedEntityGroup]
    affiliation_observations: list[dict[str, Any]] = Field(default_factory=list)
    topic_portfolio: list[dict[str, Any]] = Field(default_factory=list)
    external_links: list[dict[str, str]] = Field(default_factory=list)
    scientific_notes: list[str] = Field(default_factory=list)


class NeighborhoodResponse(BaseModel):
    center_id: str
    center_node: GraphNode
    total_incident_edges: int
    returned_neighbor_count: int
    truncated: bool
    metric_scope_note: str
    applied_filters: dict[str, Any]
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class EvidenceRecordItem(BaseModel):
    id: str
    kind: EvidenceKindEnum
    source_url: str | None = None
    retrieved_at: str | None = None
    raw_sha256: str | None = None
    source_locator: str | None = None
    excerpt: str | None = None
    support_edge_ids: list[str] = Field(default_factory=list)
    support_paper_ids: list[str] = Field(default_factory=list)


class EdgeEvidenceResponse(BaseModel):
    edge: GraphEdge
    source_node: GraphNode
    target_node: GraphNode
    ledger_source: Literal["artifact_ledger", "neo4j_fallback"]
    evidence_records: list[EvidenceRecordItem]
    supporting_papers: list[dict[str, Any]]
    supporting_base_edges: list[dict[str, Any]]
    affiliation_observations: list[dict[str, Any]]
    derivation_explanation: str
    scientific_limitations: list[str]


class PathRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1, max_length=200)
    target_id: str = Field(min_length=1, max_length=200)
    mode: Literal["collaboration", "citation_directed", "citation_undirected", "heterogeneous"] = "heterogeneous"
    max_hops: int = Field(default=3, ge=1, le=4)


class PathResponse(BaseModel):
    source_id: str
    target_id: str
    mode: str
    max_hops: int
    found: bool
    hop_count: int
    direction_note: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    step_descriptions: list[str] = Field(default_factory=list)


class CompareResponse(BaseModel):
    left_node: GraphNode
    right_node: GraphNode
    direct_edges: list[GraphEdge]
    shared_neighbors: list[GraphNode]
    shared_papers: list[dict[str, Any]]
    left_topics: list[dict[str, Any]]
    right_topics: list[dict[str, Any]]
    comparison_notes: list[str]
    comparison_sets: dict[str, Any] = Field(default_factory=dict)


class TableNodesResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    sort_by: str
    sort_order: str
    items: list[GraphNode]


class TableEdgesResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    sort_by: str
    sort_order: str
    items: list[GraphEdge]
