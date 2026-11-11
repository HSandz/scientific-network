"""Invented audit cases: denominators, hidden conflicts and immutable raw evidence."""

from copy import deepcopy
from hashlib import sha256
import json

import pytest

from scientific_network.quality.identity_audit import census, unused
from scientific_network.quality.pipeline_inventory import inventory
from test_release_graph import authorship, build, row


def test_audit_counts_missing_positions_and_conflicts_by_stratum(tmp_path):
    a = authorship("A1", "Ann One")
    a["author"]["observed_orcids"] = ["0000-0002-1825-0097", "0000-0001-5109-3700"]
    rows = [row(1, ["Ann One", "Bo Two"], [a, authorship(None, "Bo Two")]),
            row(2, ["Unmatched One"], [], status="review", reasons=["duplicate_doi_works"])]
    graph, _, _ = build(tmp_path, rows)
    result, details, _ = census(rows, graph)
    assert result["metrics"]["official_positions"] == 3
    assert result["metrics"]["matched_positions"] == 2
    assert result["metrics"]["withheld_positions"] == 2
    assert result["metrics"]["global_conflict_positions"] == 1
    assert result["metrics"]["missing_author_id"] == 1
    assert len(details) == 2
    assert result["by_venue_year"]["venue:aaai:2021"] == result["metrics"]
    assert result["semantic_metrics"]["authorship_precision"] is None


def test_source_validation_checks_bytes_and_not_only_record_hash(tmp_path):
    rows = [row(1, ["Ann One"], [authorship("A1", "Ann One")])]
    raw = deepcopy(rows[0]["openalex"])
    payload = json.dumps({"results": [raw]}).encode()
    digest = sha256(payload).hexdigest()
    source = rows[0]["openalex"]["source"]
    source["raw_sha256"] = digest
    cache = tmp_path / "cache"
    (cache / "objects").mkdir(parents=True)
    path = cache / "objects" / digest
    path.write_bytes(payload)
    graph, _, _ = build(tmp_path, rows)
    result, _, _ = census(rows, graph, cache)
    assert result["source_check"]["raw_objects_verified"] == 1
    rows[0]["openalex"]["authorships"][0]["raw_author_name"] = "Changed Name"
    with pytest.raises(ValueError, match="differs from cached"):
        census(rows, graph, cache)
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        census(rows, graph, cache)


def test_unused_rejects_symlinks_and_aliases(tmp_path):
    p = tmp_path / "dangling"
    p.symlink_to(tmp_path / "absent")
    with pytest.raises(ValueError, match="unused"):
        unused(p)
    with pytest.raises(ValueError, match="unused"):
        unused(tmp_path / "a", tmp_path / "x" / ".." / "a")
    with pytest.raises(ValueError, match="unused"):
        unused(tmp_path / "a",tmp_path / "a" / "b")


def test_pipeline_inventory_checks_citation_and_affiliation_support(tmp_path):
    from test_release_graph import rich_rows
    rows=rich_rows()
    graph,_,queue=build(tmp_path,rows)
    result=inventory(rows,graph.model_dump(mode="json"),queue)
    assert result["claim_support"]["citation_inventory_equal_source_filtered_core_targets"]
    assert result["claim_support"]["affiliation_triples_without_source_institution"]==0
    payload=graph.model_dump(mode="json")
    payload["affiliation_observations"][0]["organization_id"]="organization:I999"
    payload["edges"]=[e for e in payload["edges"] if e["relation"]!="CITES"]
    bad=inventory(rows,payload,queue)
    assert not bad["claim_support"]["citation_inventory_equal_source_filtered_core_targets"]
    assert bad["claim_support"]["missing_source_supported_core_citations"]==3
    assert bad["claim_support"]["affiliation_triples_without_source_institution"]==1
