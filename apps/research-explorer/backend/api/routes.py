"""Typed REST endpoints for the Scientific Network Explorer."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..models.schemas import (
    CompareResponse,
    EdgeEvidenceResponse,
    GraphEdge,
    GraphSchemaResponse,
    GraphSummaryResponse,
    GraphViewResponse,
    HealthResponse,
    NeighborhoodResponse,
    NodeDetailResponse,
    NodeLabelEnum,
    PathRequest,
    PathResponse,
    RelationEnum,
    SearchResponse,
    TableEdgesResponse,
    TableNodesResponse,
    ViewModeEnum,
)
from ..services.explorer_service import ExplorerService, HETEROGENEOUS_PRESETS


router = APIRouter(prefix="/api", tags=["explorer"])


def get_service(request: Request) -> ExplorerService:
    return request.app.state.explorer_service


@router.get("/health", response_model=HealthResponse)
def health_check(service: Annotated[ExplorerService, Depends(get_service)]) -> HealthResponse:
    """Verify Neo4j connectivity, release v4 inventory, and local artifact readiness."""
    return service.get_health()


@router.get("/graph/summary", response_model=GraphSummaryResponse)
def graph_summary(service: Annotated[ExplorerService, Depends(get_service)]) -> GraphSummaryResponse:
    """Return release v4 graph inventory, quality metrics, and scientific caveats."""
    return service.get_summary()


@router.get("/graph/schema", response_model=GraphSchemaResponse)
def graph_schema(service: Annotated[ExplorerService, Depends(get_service)]) -> GraphSchemaResponse:
    """Return the 5 entity labels, 10 predicates, evidence classes, and presets."""
    return service.get_schema()


@router.get("/search", response_model=SearchResponse)
def search_entities(
    service: Annotated[ExplorerService, Depends(get_service)],
    q: Annotated[str, Query(max_length=200, description="Search query (name, title, ID, DOI, ORCID)")] = "",
    label: Annotated[list[NodeLabelEnum] | None, Query(description="Filter by node labels")] = None,
    year_min: Annotated[int | None, Query(ge=2021, le=2025)] = None,
    year_max: Annotated[int | None, Query(ge=2021, le=2025)] = None,
    venue: Annotated[str | None, Query(max_length=40)] = None,
    sector: Annotated[str | None, Query(max_length=40)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> SearchResponse:
    """Global search across all 47,875 entities in the release database."""
    labels_str = [item.value for item in label] if label else None
    return service.search(
        q,
        labels=labels_str,
        year_min=year_min,
        year_max=year_max,
        venue=venue,
        sector=sector,
        limit=limit,
    )


@router.get("/views")
def list_views(service: Annotated[ExplorerService, Depends(get_service)]) -> dict:
    """List available exploration modes, presets, and top communities."""
    return {
        "modes": [
            {
                "id": "researchers",
                "title": "Mode A — Researcher Collaboration",
                "relation": "COAUTHORED_WITH",
                "directed": False,
                "default_limit": 100,
                "description": "Explore coauthorship communities, bridge researchers, fractional collaboration weights, and shared core papers.",
            },
            {
                "id": "organizations",
                "title": "Mode B — Organization Collaboration",
                "relation": "COLLABORATED_WITH",
                "directed": False,
                "default_limit": 60,
                "description": "Explore institutional partnerships, sector mixing, cross-sector academia–industry links, and topic portfolios.",
            },
            {
                "id": "citations",
                "title": "Mode C — Citation Network",
                "relation": "CITES",
                "directed": True,
                "default_limit": 80,
                "description": "Explore directional within-corpus citation links (citing → cited) across AAAI and IJCAI 2021–2025 papers.",
            },
            {
                "id": "heterogeneous",
                "title": "Mode D — Heterogeneous Knowledge Graph",
                "relation": "MULTI_RELATION",
                "directed": True,
                "default_limit": 120,
                "description": "Explore all 5 entity labels and 10 relationship predicates using curated presets or custom predicate filters.",
            },
        ],
        "heterogeneous_presets": HETEROGENEOUS_PRESETS,
        "researcher_communities": service.store.get_available_communities("researchers", limit=25),
        "organization_communities": service.store.get_available_communities("organizations", limit=20),
    }


@router.get("/views/{view}", response_model=GraphViewResponse)
def get_view_subgraph(
    view: ViewModeEnum,
    service: Annotated[ExplorerService, Depends(get_service)],
    limit: Annotated[int | None, Query(ge=10, le=250)] = None,
    community_id: Annotated[str | None, Query(max_length=64)] = None,
    sector: Annotated[str | None, Query(max_length=40)] = None,
    cross_sector_only: Annotated[bool, Query()] = False,
    country_code: Annotated[str | None, Query(max_length=12)] = None,
    year_min: Annotated[int | None, Query(ge=2021, le=2025)] = None,
    year_max: Annotated[int | None, Query(ge=2021, le=2025)] = None,
    venue: Annotated[str | None, Query(max_length=40)] = None,
    topic_id: Annotated[str | None, Query(max_length=80)] = None,
    min_support: Annotated[int, Query(ge=1, le=100)] = 1,
    min_weight: Annotated[float, Query(ge=0.0, le=50.0)] = 0.0,
    include_isolates: Annotated[bool, Query()] = False,
    include_topics: Annotated[bool, Query()] = False,
    preset: Annotated[str, Query(max_length=64)] = "topic_taxonomy_ecosystem",
    relations: Annotated[list[RelationEnum] | None, Query()] = None,
    node_labels: Annotated[list[NodeLabelEnum] | None, Query()] = None,
) -> GraphViewResponse:
    """Load a bounded, filterable projection or heterogeneous view."""
    rels_str = [r.value for r in relations] if relations else None
    labels_str = [l.value for l in node_labels] if node_labels else None
    return service.get_view(
        view.value,
        limit=limit,
        community_id=community_id,
        sector=sector,
        cross_sector_only=cross_sector_only,
        country_code=country_code,
        year_min=year_min,
        year_max=year_max,
        venue=venue,
        topic_id=topic_id,
        min_support=min_support,
        min_weight=min_weight,
        include_isolates=include_isolates,
        include_topics=include_topics,
        preset=preset,
        relations=rels_str,
        node_labels=labels_str,
    )


@router.get("/nodes/{node_id}/neighbors", response_model=NeighborhoodResponse)
def get_node_neighbors(
    node_id: str,
    service: Annotated[ExplorerService, Depends(get_service)],
    relations: Annotated[list[RelationEnum] | None, Query()] = None,
    node_labels: Annotated[list[NodeLabelEnum] | None, Query()] = None,
    direction: Annotated[Literal["both", "outgoing", "incoming"], Query()] = "both",
    year_min: Annotated[int | None, Query(ge=2021, le=2025)] = None,
    year_max: Annotated[int | None, Query(ge=2021, le=2025)] = None,
    venue: Annotated[str | None, Query(max_length=40)] = None,
    sector: Annotated[str | None, Query(max_length=40)] = None,
    min_support: Annotated[int, Query(ge=1, le=100)] = 1,
    min_weight: Annotated[float, Query(ge=0.0, le=50.0)] = 0.0,
    limit: Annotated[int, Query(ge=1, le=250)] = 60,
    include_induced_edges: Annotated[bool, Query()] = True,
) -> NeighborhoodResponse:
    """Retrieve a bounded ego-network neighborhood around `node_id`."""
    rels_str = [r.value for r in relations] if relations else None
    labels_str = [l.value for l in node_labels] if node_labels else None
    result = service.get_neighbors(
        node_id,
        relations=rels_str,
        node_labels=labels_str,
        direction=direction,
        year_min=year_min,
        year_max=year_max,
        venue=venue,
        sector=sector,
        min_support=min_support,
        min_weight=min_weight,
        limit=limit,
        include_induced_edges=include_induced_edges,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Entity {node_id!r} not found in release graph.")
    return result


@router.get("/nodes/{node_id}", response_model=NodeDetailResponse)
def get_node_detail(
    node_id: str,
    service: Annotated[ExplorerService, Depends(get_service)],
) -> NodeDetailResponse:
    """Retrieve full entity metadata, full-projection metrics, and grouped connections."""
    result = service.get_node_detail(node_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Entity {node_id!r} not found in release graph.")
    return result


@router.get("/edges/{edge_id}/evidence", response_model=EdgeEvidenceResponse)
def get_edge_evidence(
    edge_id: str,
    service: Annotated[ExplorerService, Depends(get_service)],
) -> EdgeEvidenceResponse:
    """Mode E — Retrieve full provenance, supporting papers, base edges, and affiliation triples for an edge."""
    result = service.get_edge_evidence(edge_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Edge {edge_id!r} not found in release graph.")
    return result


@router.get("/edges/{edge_id}", response_model=GraphEdge)
def get_edge_detail(
    edge_id: str,
    service: Annotated[ExplorerService, Depends(get_service)],
) -> GraphEdge:
    """Retrieve metadata and properties for a single accepted relationship."""
    result = service.get_edge_detail(edge_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Edge {edge_id!r} not found in release graph.")
    return result


@router.get("/analytics/overview")
def get_analytics_overview(
    service: Annotated[ExplorerService, Depends(get_service)],
) -> dict:
    """Return precomputed full-graph analytics, distributions, sector mixing, and rankings."""
    return service.get_analytics_overview()


@router.post("/paths", response_model=PathResponse)
def discover_path(
    req: PathRequest,
    service: Annotated[ExplorerService, Depends(get_service)],
) -> PathResponse:
    """Discover a bounded shortest path between two entities."""
    return service.find_path(req)


@router.get("/compare", response_model=CompareResponse)
def compare_entities(
    left_id: Annotated[str, Query(min_length=1, max_length=200)],
    right_id: Annotated[str, Query(min_length=1, max_length=200)],
    service: Annotated[ExplorerService, Depends(get_service)],
) -> CompareResponse:
    """Compare two organizations or researchers (shared papers, neighbors, and topic portfolios)."""
    result = service.compare_nodes(left_id, right_id)
    if result is None:
        raise HTTPException(status_code=404, detail="One or both entities could not be found.")
    return result


@router.get("/table/nodes", response_model=TableNodesResponse)
def get_table_nodes(
    service: Annotated[ExplorerService, Depends(get_service)],
    label: Annotated[NodeLabelEnum | None, Query()] = None,
    q: Annotated[str, Query(max_length=200)] = "",
    year_min: Annotated[int | None, Query(ge=2021, le=2025)] = None,
    year_max: Annotated[int | None, Query(ge=2021, le=2025)] = None,
    sector: Annotated[str | None, Query(max_length=40)] = None,
    venue: Annotated[str | None, Query(max_length=40)] = None,
    sort_by: Annotated[Literal["score", "name", "year", "sector", "id"], Query()] = "score",
    sort_order: Annotated[Literal["asc", "desc"], Query()] = "desc",
    page: Annotated[int, Query(ge=1, le=5000)] = 1,
    page_size: Annotated[int, Query(ge=5, le=100)] = 25,
) -> TableNodesResponse:
    """Paginated, sortable table of graph nodes."""
    return service.get_table_nodes(
        label=label.value if label else None,
        query=q,
        year_min=year_min,
        year_max=year_max,
        sector=sector,
        venue=venue,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get("/table/edges", response_model=TableEdgesResponse)
def get_table_edges(
    service: Annotated[ExplorerService, Depends(get_service)],
    relation: Annotated[RelationEnum | None, Query()] = None,
    evidence_kind: Annotated[str | None, Query(max_length=40)] = None,
    q: Annotated[str, Query(max_length=200)] = "",
    min_support: Annotated[int, Query(ge=1, le=100)] = 1,
    min_weight: Annotated[float, Query(ge=0.0, le=50.0)] = 0.0,
    sort_by: Annotated[Literal["support_count", "fractional_weight", "relation", "edge_id"], Query()] = "support_count",
    sort_order: Annotated[Literal["asc", "desc"], Query()] = "desc",
    page: Annotated[int, Query(ge=1, le=5000)] = 1,
    page_size: Annotated[int, Query(ge=5, le=100)] = 25,
) -> TableEdgesResponse:
    """Paginated, sortable table of accepted graph relationships."""
    return service.get_table_edges(
        relation=relation.value if relation else None,
        evidence_kind=evidence_kind,
        query=q,
        min_support=min_support,
        min_weight=min_weight,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
