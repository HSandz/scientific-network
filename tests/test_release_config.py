"""Release configs and the isolated Neo4j service (D040, release plan Phase 0)."""

import hashlib
from pathlib import Path

import pytest
import yaml

from scientific_network.analysis.analyze import _load_config as load_analysis_config
from scientific_network.analysis.analyze import _validated_strict_filter
from scientific_network.evaluation.edge_audit import _load_quality

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "configs/release-v1.yaml"
QUALITY = ROOT / "configs/quality-release-v1.yaml"
ANALYSIS = ROOT / "configs/analysis-release-v1.yaml"
COMPOSE = ROOT / "compose.yaml"


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_release_scope_counts_add_up_to_the_roster_total() -> None:
    config = _yaml(RELEASE)
    scope = config["scope"]
    by_venue_year = scope["expected_papers_by_venue_year"]
    assert set(by_venue_year) == set(scope["venues"])
    for counts in by_venue_year.values():
        assert sorted(counts) == scope["years"]
    assert sum(sum(counts.values()) for counts in by_venue_year.values()) == scope["expected_papers"] == 13617


def test_release_config_pins_the_final_roster_and_isolated_paths() -> None:
    config = _yaml(RELEASE)
    assert config["roster"]["config"] == "configs/corpus-five-year-v10.yaml"
    assert len(config["roster"]["sha256"]) == 64
    roster_config = ROOT / config["roster"]["config"]
    assert roster_config.is_file()
    # the manifest is local and rebuildable, so only check its hash when present
    manifest = ROOT / config["roster"]["manifest"]
    if manifest.is_file():
        assert hashlib.sha256(manifest.read_bytes()).hexdigest() == config["roster"]["sha256"]
    assert config["openalex"]["batch_size"] == 50
    # the config names the environment variable; it never holds a key value
    assert config["openalex"]["api_key_env"] == "OPENALEX_API_KEY"
    assert not {"api_key", "key", "token", "password"} & set(config["openalex"])
    assert config["neo4j"]["default_uri"] == "bolt://localhost:7689"
    for key in ("cache_dir", "works", "graph_v1_dir", "graph_v2_dir"):
        assert "release" in config["paths"][key]


def test_release_quality_config_satisfies_the_audit_loader_and_d040_design() -> None:
    config, audit = _load_quality(QUALITY)
    assert config["status"] == "frozen"
    assert audit["review_design"] == "split_with_overlap"
    assert (audit["global_sample_size"], audit["per_type_sample_size"], audit["overlap_sample_size"]) == (200, 10, 50)
    assert audit["overlap_sample_size"] <= audit["global_sample_size"]
    assert audit["reviewer_ids"] == ["A", "B"]
    assert audit["course_point_estimate_must_exceed"] == 0.90
    assert audit["wilson_lower_bound_must_exceed"] == 0.90
    assert audit["min_precision"] == 0.95


def test_release_quality_keeps_size_and_coverage_targets_from_the_base_config() -> None:
    base, release = _yaml(ROOT / "configs/quality.yaml"), _yaml(QUALITY)
    for section in ("size", "coverage_targets", "component_precision_targets", "derived"):
        assert release[section] == base[section]


def test_release_analysis_config_is_frozen_with_a_valid_strict_filter() -> None:
    config, _ = load_analysis_config(ANALYSIS)
    assert config["status"] == "frozen"
    assert config["robustness"]["stricter_evidence_filter_status"] == "frozen"
    assert _validated_strict_filter(config["robustness"]["strict_evidence_filter"]) == {"minimum_support_count": 2}
    base = _yaml(ROOT / "configs/analysis.yaml")
    for section in ("projections", "communities", "betweenness"):
        assert config[section] == base[section]


@pytest.fixture(scope="module")
def compose() -> dict:
    return _yaml(COMPOSE)


def test_release_neo4j_service_is_isolated_from_pilot_and_extended(compose: dict) -> None:
    services = compose["services"]
    release = services["neo4j-five-year"]
    assert release["image"] == services["neo4j"]["image"] == "neo4j:5.26.12-community"
    assert release["profiles"] == ["five-year"]
    assert release["ports"] == ["127.0.0.1:7476:7474", "127.0.0.1:7689:7687"]
    assert "healthcheck" in release
    others = [service for name, service in services.items() if name.startswith("neo4j") and name != "neo4j-five-year"]
    release_ports = {port.split(":")[1] for port in release["ports"]}
    release_volumes = {volume.split(":")[0] for volume in release["volumes"] if not volume.startswith(".")}
    assert release_volumes == {"neo4j-five-year-data", "neo4j-five-year-logs"}
    assert release_volumes <= set(compose["volumes"])
    for other in others:
        assert release_ports.isdisjoint({port.split(":")[1] for port in other["ports"]})
        assert release_volumes.isdisjoint({volume.split(":")[0] for volume in other["volumes"]})
