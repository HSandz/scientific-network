"""Configuration and environment loading for the Research Explorer backend."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = Path(__file__).resolve().parents[1]

# Expected release v4 inventory constants (D040 corrected release graph)
EXPECTED_GRAPH_VERSION = "release-d3c788c3114a"
EXPECTED_GRAPH_SHA256 = "6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90"
EXPECTED_TOTAL_NODES = 47875
EXPECTED_TOTAL_EDGES = 225731
EXPECTED_FACTUAL_EDGES = 110026

EXPECTED_NODES_BY_LABEL: dict[str, int] = {
    "Researcher": 32189,
    "Paper": 13617,
    "Organization": 2047,
    "Topic": 20,
    "Venue": 2,
}

EXPECTED_EDGES_BY_RELATION: dict[str, int] = {
    "AUTHORED": 50437,
    "AFFILIATED_WITH": 38664,
    "PUBLISHED_IN": 13617,
    "CITES": 7308,
    "HAS_TOPIC": 14222,
    "SUBTOPIC_OF": 16,
    "COAUTHORED_WITH": 80482,
    "COLLABORATED_WITH": 13031,
    "RESEARCHES_TOPIC": 5622,
    "CONTRIBUTES_TO_TOPIC": 2332,
}


@dataclass(frozen=True)
class Settings:
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    neo4j_database: str
    host: str
    port: int
    cors_origins: tuple[str, ...]
    query_timeout_seconds: float
    max_neighbor_limit: int
    max_search_limit: int
    max_table_page_size: int
    graph_artifact_path: Path
    analysis_artifact_path: Path
    summary_artifact_path: Path
    network_views_path: Path
    audit_results_path: Path
    quality_config_path: Path = REPO_ROOT / "configs" / "quality-agent-release-v2.yaml"
    topic_eval_path: Path = REPO_ROOT / "reports" / "release-v3" / "topic-eval-agent.json"
    historical_topic_reuse_path: Path = REPO_ROOT / "reports" / "release-v4" / "historical-topic-reuse-v2.json"


def load_settings() -> Settings:
    """Load configuration from environment variables and ignored local .env files.

    Never hardcodes or logs database passwords.
    Note: The root .env sets NEO4J_URI=bolt://localhost:7687 for the historical pilot DB,
    so we check EXPLORER_NEO4J_URI first and default to bolt://127.0.0.1:7689 for the
    isolated neo4j-five-year release service unless NEO4J_URI explicitly targets port 7689
    or a custom container hostname.
    """
    app_env = APP_ROOT / ".env"
    root_env = REPO_ROOT / ".env"
    if app_env.exists():
        load_dotenv(app_env, override=False)
    if root_env.exists():
        load_dotenv(root_env, override=False)

    explicit_explorer_uri = os.environ.get("EXPLORER_NEO4J_URI")
    raw_neo4j_uri = os.environ.get("NEO4J_URI", "")
    if explicit_explorer_uri:
        neo4j_uri = explicit_explorer_uri
    elif raw_neo4j_uri and ":7687" not in raw_neo4j_uri and ":7688" not in raw_neo4j_uri:
        neo4j_uri = raw_neo4j_uri
    else:
        neo4j_uri = "bolt://127.0.0.1:7689"

    # Retrieve password from environment without any hardcoded fallback secret.
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "")
    neo4j_username = os.environ.get("NEO4J_USERNAME", "neo4j")
    neo4j_database = os.environ.get("NEO4J_DATABASE", "neo4j")

    # Bind strictly to 127.0.0.1 by default (never 0.0.0.0) per security guidelines.
    host = os.environ.get("EXPLORER_HOST", "127.0.0.1")
    if host == "0.0.0.0":
        host = "127.0.0.1"
    port = int(os.environ.get("EXPLORER_PORT", "8000"))

    raw_cors = os.environ.get(
        "EXPLORER_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
    )
    cors_origins = tuple(origin.strip() for origin in raw_cors.split(",") if origin.strip() and origin.strip() != "*")

    return Settings(
        neo4j_uri=neo4j_uri,
        neo4j_username=neo4j_username,
        neo4j_password=neo4j_password,
        neo4j_database=neo4j_database,
        host=host,
        port=port,
        cors_origins=cors_origins,
        query_timeout_seconds=float(os.environ.get("EXPLORER_QUERY_TIMEOUT", "15.0")),
        max_neighbor_limit=250,
        max_search_limit=100,
        max_table_page_size=100,
        graph_artifact_path=Path(
            os.environ.get(
                "EXPLORER_GRAPH_PATH",
                str(REPO_ROOT / "data" / "processed" / "release-graph-v4" / "graph.json"),
            )
        ),
        analysis_artifact_path=Path(
            os.environ.get(
                "EXPLORER_ANALYSIS_PATH",
                str(REPO_ROOT / "reports" / "release-v4" / "analysis.json"),
            )
        ),
        summary_artifact_path=Path(
            os.environ.get(
                "EXPLORER_SUMMARY_PATH",
                str(REPO_ROOT / "reports" / "release-v4" / "graph-summary.json"),
            )
        ),
        network_views_path=Path(
            os.environ.get(
                "EXPLORER_NETWORK_VIEWS_PATH",
                str(REPO_ROOT / "reports" / "final-report" / "network-views-v4-v1" / "network-views.json"),
            )
        ),
        audit_results_path=Path(
            os.environ.get(
                "EXPLORER_AUDIT_RESULTS_PATH",
                str(REPO_ROOT / "reports" / "release-v4" / "audit-results-agent-v2.json"),
            )
        ),
        quality_config_path=Path(
            os.environ.get(
                "EXPLORER_QUALITY_CONFIG_PATH",
                str(REPO_ROOT / "configs" / "quality-agent-release-v2.yaml"),
            )
        ),
        topic_eval_path=Path(
            os.environ.get(
                "EXPLORER_TOPIC_EVAL_PATH",
                str(REPO_ROOT / "reports" / "release-v3" / "topic-eval-agent.json"),
            )
        ),
        historical_topic_reuse_path=Path(
            os.environ.get(
                "EXPLORER_TOPIC_REUSE_PATH",
                str(REPO_ROOT / "reports" / "release-v4" / "historical-topic-reuse-v2.json"),
            )
        ),
    )
