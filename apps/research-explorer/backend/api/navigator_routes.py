"""Read-only REST & SSE endpoints for Research Trend Navigator (M3 spec §6.2-§6.5)."""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from ..services.navigator_service import NavigatorService

navigator_router = APIRouter(prefix="/api", tags=["navigator"])


def get_navigator_service(request: Request) -> NavigatorService:
    return request.app.state.navigator_service


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1500)
    mode: Literal["auto", "local", "global"] = "auto"
    stream: bool = True
    use_cache: bool = False
    resolved_overrides: dict[str, str] | None = None


@navigator_router.get("/trends")
def get_trends(
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
    kind: Annotated[Literal["Topic", "Method", "Task", "Dataset"], Query()] = "Method",
    venue: Annotated[Literal["all", "AAAI", "IJCAI"], Query()] = "all",
    period: Annotated[Literal["2021-2025", "2021-2023", "2022-2025", "2023-2025"], Query()] = "2021-2025",
    trend_class: Annotated[str | None, Query(max_length=32)] = None,
    q: Annotated[str, Query(max_length=150)] = "",
    limit: Annotated[int, Query(ge=5, le=200)] = 50,
) -> dict[str, Any]:
    return service.get_trends(kind=kind, venue=venue, period=period, trend_class=trend_class, q=q, limit=limit)


@navigator_router.get("/subjects")
def list_subjects(
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
    kind: Annotated[Literal["Topic", "Method", "Task", "Dataset"] | None, Query()] = None,
    q: Annotated[str, Query(max_length=150)] = "",
    limit: Annotated[int, Query(ge=1, le=200)] = 40,
) -> dict[str, Any]:
    return service.list_subjects(kind=kind, q=q, limit=limit)


@navigator_router.get("/subjects/{subject_id:path}")
def get_subject_detail(
    subject_id: str,
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
) -> dict[str, Any]:
    detail = service.get_subject_detail(subject_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Subject {subject_id!r} not found.")
    return detail


@navigator_router.get("/groups")
def list_groups(
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
    sector: Annotated[str | None, Query(max_length=40)] = None,
    country: Annotated[str | None, Query(max_length=20)] = None,
    notable_only: bool = False,
    q: Annotated[str, Query(max_length=150)] = "",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0, le=5000)] = 0,
) -> dict[str, Any]:
    return service.list_groups(
        sector=sector,
        country=country,
        notable_only=notable_only,
        q=q,
        limit=limit,
        offset=offset,
    )


@navigator_router.get("/groups/{group_id:path}")
def get_group_detail(
    group_id: str,
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
) -> dict[str, Any]:
    detail = service.get_group_detail(group_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Organization {group_id!r} not found.")
    return detail


@navigator_router.get("/communities")
def list_communities(
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
    source: Annotated[Literal["research_L1", "research_L0", "N1", "N2"], Query()] = "research_L1",
    q: Annotated[str, Query(max_length=150)] = "",
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> dict[str, Any]:
    return service.list_communities(source=source, q=q, limit=limit)


@navigator_router.get("/communities/{community_id:path}/members")
def get_community_members(
    community_id: str,
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 40,
    offset: Annotated[int, Query(ge=0, le=5000)] = 0,
) -> dict[str, Any]:
    result = service.get_community_members(community_id, limit=limit, offset=offset)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Community {community_id!r} not found.")
    return result


@navigator_router.get("/communities/{community_id:path}")
def get_community_detail(
    community_id: str,
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
) -> dict[str, Any]:
    detail = service.get_community_detail(community_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Community {community_id!r} not found.")
    return detail


@navigator_router.get("/network-science")
def get_network_science(
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
) -> dict[str, Any]:
    return service.get_network_science()


@navigator_router.get("/node360/{node_id:path}")
def get_node360(
    node_id: str,
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
) -> dict[str, Any]:
    detail = service.get_node360(node_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Node {node_id!r} not found.")
    return detail


@navigator_router.get("/about-data")
def get_about_data(
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
) -> dict[str, Any]:
    return service.get_about_data()


@navigator_router.get("/explorer-enriched/schema")
def get_explorer_enriched_schema(
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
) -> dict[str, Any]:
    return service.get_explorer_enriched_schema()


@navigator_router.get("/explorer-enriched/search")
def search_explorer_enriched(
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
    q: Annotated[str, Query(max_length=150)] = "",
    label: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> dict[str, Any]:
    return service.search_explorer_enriched(q=q, labels=label, limit=limit)


@navigator_router.get("/explorer-enriched/neighbors/{node_id:path}")
def get_explorer_enriched_neighbors(
    node_id: str,
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
    relation: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=120)] = 40,
) -> dict[str, Any]:
    return service.get_explorer_enriched_neighbors(node_id, relations=relation, limit=limit)


@navigator_router.get("/ask/demos")
def list_ask_demos(
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
) -> dict[str, Any]:
    return service.list_ask_demos()


@navigator_router.post("/ask", response_model=None)
def post_ask(
    req: AskRequest,
    service: Annotated[NavigatorService, Depends(get_navigator_service)],
):
    if not req.stream:
        res = service.ask(
            question=req.question,
            mode=req.mode,
            use_cache=req.use_cache,
            resolved_overrides=req.resolved_overrides,
        )
        return JSONResponse(content=res)

    def _event_stream():
        try:
            for ev in service.stream_ask_events(
                question=req.question,
                mode=req.mode,
                use_cache=req.use_cache,
                resolved_overrides=req.resolved_overrides,
            ):
                etype = ev.get("event", "message")
                payload = json.dumps(ev.get("data", {}), ensure_ascii=False)
                yield f"event: {etype}\ndata: {payload}\n\n"
        except Exception as exc:
            err_payload = json.dumps({"error": f"{type(exc).__name__}: {str(exc)[:200]}"})
            yield f"event: error\ndata: {err_payload}\n\n"

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
