"""Offline unit tests for the frozen Phase 1 QA benchmark evaluation harness."""

import json
from pathlib import Path

import numpy as np
import pytest

from scientific_network.evaluation.qa_eval import (
    UnifiedEntityResolver,
    adjudicate_citation_judgments,
    adjudicate_pairwise_judgments,
    build_entity_catalog,
    extract_citation_pairs,
    prepare_judging_packets,
    run_benchmark_systems,
    sample_citation_pairs,
    score_factual_results,
    seeded_bootstrap_ci,
    set_f1,
)


def _synth_embed(text: str) -> np.ndarray:
    t = text.lower()
    if "tsinghua" in t or "tsing-hua" in t:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    if "diffusion" in t:
        return np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    if "peking" in t:
        return np.array([0.0, 0.0, 1.0, 0.0], dtype=np.float32)
    if "close" in t:
        return np.array([0.85, 0.5268, 0.0, 0.0], dtype=np.float32)  # cosine ~0.85 with Tsinghua
    return np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)


def test_unified_entity_resolver_exact_id_alias_and_threshold():
    nodes = [
        {"id": "organization:tsinghua", "label": "Organization", "name": "Tsinghua University", "properties": {}},
        {"id": "method:llm", "label": "Method", "name": "Large Language Models (LLMs)", "properties": {"key": "large language model"}},
        {"id": "organization:pku", "label": "Organization", "name": "Peking University", "properties": {}},
    ]
    catalog = build_entity_catalog(nodes)
    resolver = UnifiedEntityResolver(catalog, embed_fn=_synth_embed, embedding_threshold=0.80)

    # Exact graph ID match
    assert resolver.resolve("See organization:pku.", target_labels={"Organization"}) == ["organization:pku"]
    # Exact alias + parenthetical acronym match
    assert resolver.resolve("* Large Language Models\n* Peking University", target_labels={"Method"}) == ["method:llm"]
    # Embedding cosine fallback >= 0.80 (tsing-hua alias matches Tsinghua, "Close Match" >= 0.80 vs below threshold)
    resolved = resolver.resolve("* **Tsing-Hua Univ**\n* **Unrelated Institute**", target_labels={"Organization"})
    assert "organization:tsinghua" in resolved
    assert "organization:pku" not in resolved
    # Below 0.80 threshold is rejected
    strict = UnifiedEntityResolver(catalog, embed_fn=_synth_embed, embedding_threshold=0.95)
    assert strict.resolve("* **Close Match Institute**", target_labels={"Organization"}) == []


def test_set_f1_bootstrap_ci_and_numeric_exact_scoring(tmp_path: Path):
    f1, p, r = set_f1({"a", "b"}, {"b", "c"})
    assert round(f1, 4) == 0.5 and p == 0.5 and r == 0.5
    lo1, hi1 = seeded_bootstrap_ci([0.2, 0.6, 0.8, 1.0], seed=20261125, n_resamples=500)
    lo2, hi2 = seeded_bootstrap_ci([0.2, 0.6, 0.8, 1.0], seed=20261125, n_resamples=500)
    assert (lo1, hi1) == (lo2, hi2)
    assert 0.2 <= lo1 <= hi1 <= 1.0

    # Synthetic score_factual_results check with references + raw-outputs
    ref_path = tmp_path / "refs.jsonl"
    refs = [
        {
            "question_id": "q1",
            "split": "test",
            "status": "kept",
            "hops": "1",
            "answer_type": "number",
            "judged": "exact",
            "text": "How many papers?",
            "reference_answer": 8,
        },
        {
            "question_id": "q2",
            "split": "test",
            "status": "kept",
            "hops": "2",
            "answer_type": "set",
            "judged": "set_f1",
            "text": "Which orgs?",
            "reference_answer": [{"id": "organization:tsinghua", "name": "Tsinghua University"}],
        },
    ]
    ref_path.write_text("\n".join(json.dumps(x) for x in refs) + "\n", encoding="utf-8")

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    raw_rows = [
        {"question_id": "q1", "system": "S1_slm_only", "hops": "1", "answer_type": "number", "judged": "exact", "answer": "8 papers.", "faithfulness_passed": None, "total_latency_s": 1.0, "first_event_s": 1.0, "paper_ids": []},
        {"question_id": "q1", "system": "S2_vector_rag", "hops": "1", "answer_type": "number", "judged": "exact", "answer": "9 papers.", "faithfulness_passed": True, "total_latency_s": 1.5, "first_event_s": 1.0, "paper_ids": []},
        {"question_id": "q1", "system": "S3_graphrag", "hops": "1", "answer_type": "number", "judged": "exact", "answer": "8.", "faithfulness_passed": True, "total_latency_s": 2.0, "first_event_s": 1.0, "paper_ids": []},
        {"question_id": "q1", "system": "S4_multihop", "hops": "1", "answer_type": "number", "judged": "exact", "answer": "Total is 8.", "faithfulness_passed": True, "total_latency_s": 2.5, "first_event_s": 1.0, "paper_ids": []},
        {"question_id": "q2", "system": "S1_slm_only", "hops": "2", "answer_type": "set", "judged": "set_f1", "answer": "Peking University", "faithfulness_passed": None, "total_latency_s": 1.0, "first_event_s": 1.0, "paper_ids": []},
        {"question_id": "q2", "system": "S2_vector_rag", "hops": "2", "answer_type": "set", "judged": "set_f1", "answer": "Tsinghua University", "faithfulness_passed": True, "total_latency_s": 1.0, "first_event_s": 1.0, "paper_ids": []},
        {"question_id": "q2", "system": "S3_graphrag", "hops": "2", "answer_type": "set", "judged": "set_f1", "answer": "Tsinghua University", "faithfulness_passed": True, "total_latency_s": 1.0, "first_event_s": 1.0, "paper_ids": []},
        {"question_id": "q2", "system": "S4_multihop", "hops": "2", "answer_type": "set", "judged": "set_f1", "answer": "Tsinghua University", "faithfulness_passed": False, "total_latency_s": 1.0, "first_event_s": 1.0, "paper_ids": []},
    ]
    (out_dir / "raw-outputs.jsonl").write_text("\n".join(json.dumps(x) for x in raw_rows) + "\n", encoding="utf-8")

    catalog = build_entity_catalog([
        {"id": "organization:tsinghua", "label": "Organization", "name": "Tsinghua University", "properties": {}},
        {"id": "organization:pku", "label": "Organization", "name": "Peking University", "properties": {}},
    ])
    resolver = UnifiedEntityResolver(catalog)
    cfg = {
        "protocol_version": "qa-eval-v1",
        "benchmark": {"references_path": str(ref_path), "split": "test", "status_filter": "kept"},
        "factual_scoring": {
            "numeric_exact_match": {"abs_tol": 0},
            "intervals": {"bootstrap_seed": 20261125, "bootstrap_resamples": 200},
        },
    }
    scored = score_factual_results(cfg, out_dir=out_dir, resolver=resolver)
    assert scored["systems"]["S4_multihop"]["by_hop"]["1"]["mean_score"] == 1.0
    assert scored["systems"]["S2_vector_rag"]["by_hop"]["1"]["mean_score"] == 0.0
    assert scored["systems"]["S1_slm_only"]["by_hop"]["2"]["mean_score"] == 0.0
    assert scored["systems"]["S4_multihop"]["by_hop"]["2"]["mean_score"] == 1.0
    assert scored["systems"]["S1_slm_only"]["overall_faithfulness"]["status"] == "not_applicable"
    assert scored["systems"]["S4_multihop"]["overall_faithfulness"]["passed"] == 1


def test_citation_and_blind_pairwise_packets_and_adjudication(tmp_path: Path):
    ref_path = tmp_path / "refs.jsonl"
    refs = [
        {"question_id": "qg1", "split": "test", "status": "kept", "hops": "global", "answer_type": "narrative", "judged": "pairwise_ai", "text": "Summarize trends?", "reference_answer": None},
    ]
    ref_path.write_text(json.dumps(refs[0]) + "\n", encoding="utf-8")

    works_path = tmp_path / "works.jsonl"
    works_path.write_text(
        json.dumps({
            "paper_id": "paper:aaai:2024:101",
            "doi": "10.1609/aaai.101",
            "year": 2024,
            "openalex": {"title": "Diffusion Survey", "publication_year": 2024, "abstract": "SECRET_ABSTRACT_DO_NOT_LEAK_INTO_MANIFEST"},
        }) + "\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    run_dir = tmp_path / "run"
    out_dir.mkdir()
    raw_rows = [
        {"question_id": "qg1", "system": s, "hops": "global", "answer": f"{s} cites [paper:aaai:2024:101]."}
        for s in ("S1_slm_only", "S2_vector_rag", "S3_graphrag", "S4_multihop")
    ]
    (out_dir / "raw-outputs.jsonl").write_text("\n".join(json.dumps(x) for x in raw_rows) + "\n", encoding="utf-8")

    pairs = extract_citation_pairs(raw_rows)
    assert len(pairs) == 4
    s1 = sample_citation_pairs(pairs, max_per_system=1, seed=20261125)
    s2 = sample_citation_pairs(pairs, max_per_system=1, seed=20261125)
    assert s1 == s2

    cfg = {
        "protocol_version": "qa-eval-v1",
        "benchmark": {"references_path": str(ref_path), "split": "test", "status_filter": "kept"},
        "works_jsonl_path": str(works_path),
        "citation_validity": {"sample_seed": 20261125, "max_pairs_per_system": 25},
        "global_pairwise": {"seed": 20261125},
    }
    res = prepare_judging_packets(cfg, out_dir=out_dir, run_dir=run_dir)
    assert res["citation_samples"] == 4
    assert res["pairwise_items"] == 12  # 1 global question * 6 system pairs * 2 orders (AB & BA)

    # Tracked manifest MUST NOT contain raw abstract text
    cit_manifest_text = (out_dir / "citation-sample-manifest.json").read_text(encoding="utf-8")
    assert "SECRET_ABSTRACT_DO_NOT_LEAK_INTO_MANIFEST" not in cit_manifest_text
    assert "SECRET_ABSTRACT_DO_NOT_LEAK_INTO_MANIFEST" in (run_dir / "citation-packet.jsonl").read_text(encoding="utf-8")

    # Verify pairwise blind packet hides system names
    pw_packet = [json.loads(line) for line in (run_dir / "pairwise-packet.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all(set(row.keys()) == {"pair_item_id", "question_id", "question_text", "answer_a", "answer_b"} for row in pw_packet)

    # Verify adjudication + position-consistency logic
    cit_manifest = json.loads(cit_manifest_text)
    a_cit = {x["sample_id"]: "supported" for x in cit_manifest["items"]}
    b_cit = {x["sample_id"]: ("unsupported" if idx == 0 else "supported") for idx, x in enumerate(cit_manifest["items"])}
    c_cit = {cit_manifest["items"][0]["sample_id"]: "supported"}
    cit_adj = adjudicate_citation_judgments(cit_manifest, a_cit, b_cit, c_cit)
    assert cit_adj["disagreements"] == 1
    assert cit_adj["by_system"]["S1_slm_only"]["supported"] == 1

    pw_keys = [json.loads(line) for line in (run_dir / "pairwise-key.jsonl").read_text(encoding="utf-8").splitlines()]
    a_pw = {k["pair_item_id"]: ("A" if k["sys_a"] == "S4_multihop" else ("B" if k["sys_b"] == "S4_multihop" else "tie")) for k in pw_keys}
    pw_adj = adjudicate_pairwise_judgments(pw_keys, a_pw, a_pw, {})
    assert pw_adj["by_system"]["S4_multihop"]["wins"] == 6
    assert pw_adj["by_system"]["S4_multihop"]["position_consistent_wins"] == 3
    assert pw_adj["position_inconsistent_pairs"] == 0


def test_run_once_overwrite_guard(tmp_path: Path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "raw-outputs.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="run-once"):
        run_benchmark_systems({}, out_dir=out_dir, run_dir=tmp_path / "run", allow_overwrite=False)
