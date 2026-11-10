"""FastAPI application entrypoint for the Scientific Network Explorer backend."""

from collections import OrderedDict
from contextlib import asynccontextmanager
import sys
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from neo4j.exceptions import DriverError, Neo4jError
import uvicorn

# Ensure package imports work whether launched via `uvicorn backend.main:app --app-dir apps/research-explorer`
# or `python apps/research-explorer/backend/main.py`
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from backend.api.routes import router as api_router  # noqa: E402
from backend.config import Settings, load_settings  # noqa: E402
from backend.repositories.artifact_store import ArtifactStore  # noqa: E402
from backend.repositories.neo4j_repo import Neo4jRepository  # noqa: E402
from backend.services.explorer_service import ExplorerService  # noqa: E402


ALLOWED_HTTP_METHODS: frozenset[str] = frozenset({"GET", "POST", "OPTIONS", "HEAD"})
RATE_LIMIT_WINDOW_SECONDS = 60.0
RATE_LIMIT_MAX_REQUESTS = 180


def create_app(
    settings: Settings | None = None,
    *,
    repo: Neo4jRepository | None = None,
    store: ArtifactStore | None = None,
    background_warmup: bool = True,
) -> FastAPI:
    """Create and configure the read-only Research Explorer FastAPI application.

    Public deployments expose read-only scientific data with bounded queries.
    There are no accounts, uploads, or state-mutating routes. CORS is not authentication.
    """
    cfg = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if getattr(app.state, "explorer_service", None) is None:
            active_repo = repo or Neo4jRepository(cfg)
            active_store = store or ArtifactStore(
                summary_path=cfg.summary_artifact_path,
                analysis_path=cfg.analysis_artifact_path,
                network_views_path=cfg.network_views_path,
                audit_results_path=cfg.audit_results_path,
                graph_artifact_path=cfg.graph_artifact_path,
                quality_config_path=cfg.quality_config_path,
                topic_eval_path=cfg.topic_eval_path,
                historical_topic_reuse_path=cfg.historical_topic_reuse_path,
                ledger_sqlite_path=cfg.ledger_sqlite_path,
            )
            if background_warmup:
                active_store.start_background_ledger_warmup()
            app.state.neo4j_repo = active_repo
            app.state.artifact_store = active_store
            app.state.explorer_service = ExplorerService(active_repo, active_store)
        yield
        active_repo_ref = getattr(app.state, "neo4j_repo", None)
        if active_repo_ref is not None and repo is None:
            active_repo_ref.close()

    app = FastAPI(
        title="Scientific Network Explorer API",
        description="Read-only knowledge graph exploration API over AAAI & IJCAI 2021–2025 (Release v4).",
        version="1.0.0",
        docs_url=None if cfg.production else "/docs",
        redoc_url=None if cfg.production else "/redoc",
        openapi_url=None if cfg.production else "/openapi.json",
        lifespan=lifespan,
    )

    # Pre-initialize state if custom repo/store passed (e.g. in unit tests)
    if repo is not None and store is not None:
        app.state.neo4j_repo = repo
        app.state.artifact_store = store
        app.state.explorer_service = ExplorerService(repo, store)

    # Strict CORS allowlist (never wildcard '*')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cfg.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
        allow_headers=["Content-Type", "Accept"],
    )

    request_log: OrderedDict[str, list[float]] = OrderedDict()

    @app.middleware("http")
    async def security_and_rate_limit_middleware(request: Request, call_next):
        # 1. Enforce HTTP method allow-list (disable TRACE, PUT, DELETE, PATCH)
        if request.method not in ALLOWED_HTTP_METHODS or (request.method == "POST" and request.url.path != "/api/paths"):
            return JSONResponse(
                status_code=405,
                content={"detail": f"HTTP method {request.method} is not permitted on this read-only API."},
            )

        # 2. Sliding-window rate limiting per client IP
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.monotonic()
        # Bound memory even when many distinct public clients visit the service.
        timestamps = request_log.setdefault(client_ip, [])
        request_log.move_to_end(client_ip)
        if len(request_log) > 4096:
            request_log.popitem(last=False)
        cutoff = now - RATE_LIMIT_WINDOW_SECONDS
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)
        if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down requests."},
            )
        timestamps.append(now)

        if len(request.url.query) > 8192:
            return JSONResponse(status_code=414, content={"detail": "Query string too long."})
        if request.method == "POST":
            # Stream a bounded body before letting Pydantic parse it.
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 4096:
                    return JSONResponse(status_code=413, content={"detail": "Request body too large."})
            request._body = bytes(body)

        response = await call_next(request)

        # 3. Strict security headers (CSP, anti-clickjacking, nosniff, permissions policy)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none';"
        )
        return response

    @app.exception_handler(ValueError)
    async def handle_value_error(_request: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)[:240]})

    @app.exception_handler(Neo4jError)
    async def handle_neo4j_error(_request: Request, _exc: Neo4jError):
        # Never expose raw database query internals or credentials to the client
        return JSONResponse(
            status_code=503,
            content={"detail": "Database query error or timeout occurred while reading from Neo4j."},
        )

    @app.exception_handler(DriverError)
    async def handle_driver_error(_request: Request, _exc: DriverError):
        return JSONResponse(
            status_code=503,
            content={"detail": "Neo4j database service is currently unreachable."},
        )

    @app.exception_handler(RuntimeError)
    async def handle_runtime_error(_request: Request, exc: RuntimeError):
        return JSONResponse(
            status_code=503,
            content={"detail": "A required backend service is unavailable."},
        )

    @app.get("/api/live", include_in_schema=False)
    def liveness():
        return {"status": "ok"}

    @app.get("/api/ready", include_in_schema=False)
    def readiness(request: Request):
        active = request.app.state.explorer_service
        # Cheap fresh probe catches a stopped DB; full release inventory is checked
        # once per process and separately by the exhaustive deployment verifier.
        active.repo.run_read("RETURN 1 AS ready")
        inventory = active.repo.verify_inventory()
        artifacts = active.store
        ready = inventory["database_verified"] and artifacts.ledger_available and all((
            artifacts.summary_data, artifacts.analysis_data, artifacts.network_views_data,
            artifacts.audit_results_data, artifacts.quality_config_data,
            artifacts.topic_eval_data, artifacts.historical_topic_reuse_data,
        ))
        return JSONResponse(status_code=200 if ready else 503, content={"status": "ok" if ready else "unavailable"})

    app.include_router(api_router)
    return app


app = create_app()


def main() -> None:
    cfg = load_settings()
    uvicorn.run(
        "backend.main:app",
        app_dir=str(APP_DIR),
        host=cfg.host,
        port=cfg.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
