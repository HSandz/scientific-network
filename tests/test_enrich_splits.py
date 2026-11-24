import json

import pytest

from scientific_network.enrich.splits import (
    allocate_quotas, draw_splits, eligible_papers, freeze_enrichment_splits,
)


def synthetic_works():
    works = []
    for venue, year, count in (("venue:a", 2021, 40), ("venue:a", 2022, 25), ("venue:b", 2021, 15), ("venue:b", 2022, 20)):
        for index in range(count):
            works.append({"paper_id": f"paper:{venue[-1]}:{year}:{index}", "venue_id": venue, "year": year,
                          "openalex": {"abstract": f"abstract {index}" if index % 10 else ""}})
    works.append({"paper_id": "paper:none", "venue_id": "venue:a", "year": 2021, "openalex": None})
    return works


def test_quotas_are_proportional_and_exact():
    quota = allocate_quotas({"a": 50, "b": 30, "c": 20}, 10)
    assert quota == {"a": 5, "b": 3, "c": 2}
    assert sum(allocate_quotas({"a": 7, "b": 7, "c": 7}, 10).values()) == 10
    with pytest.raises(ValueError):
        allocate_quotas({"a": 2}, 3)


def test_eligible_excludes_missing_abstract():
    works = synthetic_works()
    eligible = eligible_papers(works)
    assert all(row["paper_id"] != "paper:none" for row in eligible)
    assert len(eligible) == sum(1 for w in works if (w["openalex"] or {}).get("abstract"))


def test_draw_is_deterministic_disjoint_and_stratified():
    eligible = eligible_papers(synthetic_works())
    first = draw_splits(eligible, seed=7, n_dev=6, n_test=12)
    second = draw_splits(list(reversed(eligible)), seed=7, n_dev=6, n_test=12)
    assert first == second
    dev = {r["paper_id"] for r in first["development"]}
    test = {r["paper_id"] for r in first["test"]}
    assert len(dev) == 6 and len(test) == 12 and not dev & test
    assert {r["stratum"] for r in first["test"]} == {"venue:a|2021", "venue:a|2022", "venue:b|2021", "venue:b|2022"}
    assert draw_splits(eligible, seed=8, n_dev=6, n_test=12) != first


def test_freeze_writes_receipt_and_refuses_overwrite(tmp_path):
    works_path = tmp_path / "works.jsonl"
    works = synthetic_works()
    works_path.write_text("".join(json.dumps(w) + "\n" for w in works))
    membership = tmp_path / "membership.jsonl"
    membership.write_text(json.dumps({"paper_id": works[1]["paper_id"], "split": "test"}) + "\n")
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps({"paper_id": works[1]["paper_id"]}) + "\n")
    out = tmp_path / "splits"
    receipt = freeze_enrichment_splits(works_path, membership, out, seed=3, n_dev=5, n_test=10, audit_ledgers=[ledger])
    assert receipt["sizes"] == {"development": 5, "test": 10}
    assert receipt["papers_without_abstract"] > 0
    rerun = freeze_enrichment_splits(works_path, membership, tmp_path / "splits2", seed=3, n_dev=5, n_test=10, audit_ledgers=[ledger])
    assert rerun["file_sha256"] == receipt["file_sha256"]
    assert (out / "development.jsonl").exists() and (out / "test.jsonl").exists()
    with pytest.raises(ValueError, match="refusing to overwrite"):
        freeze_enrichment_splits(works_path, membership, out, seed=3, n_dev=5, n_test=10)


def test_benchmark_counts_and_freeze(tmp_path):
    from scientific_network.enrich.benchmark import build_questions, freeze_benchmark, validate_questions
    questions = build_questions()
    validate_questions(questions)
    assert sum(q["split"] == "test" for q in questions) == 80
    assert sum(q["split"] == "development" for q in questions) == 20
    assert all(q["reference_status"] == "pending_v5" for q in questions)
    assert build_questions() == questions
    receipt = freeze_benchmark(tmp_path / "bench")
    assert receipt["counts"]["test"] == {"1": 20, "2": 25, "3": 20, "global": 15}
    texts = {q["text"] for q in questions if q["split"] == "test"}
    assert not texts & {q["text"] for q in questions if q["split"] == "development"}
    with pytest.raises(ValueError, match="refusing to overwrite"):
        freeze_benchmark(tmp_path / "bench")
