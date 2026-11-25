"""Development-only QA evaluation and scripted demo trace caching (M3 Phase 4).

Strictly restricted to ``split == 'development'`` in ``references-v1.jsonl``.
Never touches or executes on ``split == 'test'`` questions.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import time
from typing import Any

import yaml

from scientific_network.rag.answer import run_ask, stream_ask
from scientific_network.rag.llm import LLMClient, LLMConfig
from scientific_network.rag.sqlite_vectors import SQLiteVectorStore
from scientific_network.rag.tools import Neo4jToolBackend, RAGToolset

SCRIPTED_DEMO_QUESTIONS: list[dict[str, str]] = [
    {
        "demo_id": "demo-01-worked-example",
        "mode": "auto",
        "title": "Tsinghua collaborators increasing LLM share after 2022 (§6.3 worked example)",
        "question": "Which organizations collaborating with Tsinghua University increased their share of large-language-model papers after 2022?",
    },
    {
        "demo_id": "demo-02-rising-methods-diffusion-orgs",
        "mode": "auto",
        "title": "Fastest-growing methods and diffusion model specialists",
        "question": "Which methods grew fastest as a share of AAAI and IJCAI papers from 2021 to 2025?",
    },
    {
        "demo_id": "demo-03-method-task-cooccurrence",
        "mode": "auto",
        "title": "Diffusion models co-occurring tasks and datasets",
        "question": "Which tasks co-occur most with diffusion models, and what datasets are used with diffusion models?",
    },
    {
        "demo_id": "demo-04-researcher-path",
        "mode": "auto",
        "title": "Co-authorship path between Shirui Pan and Chengjie Wang",
        "question": "How is Shirui Pan connected to Chengjie Wang in the co-authorship network?",
    },
    {
        "demo_id": "demo-05-causal-lift",
        "mode": "auto",
        "title": "Organizations specialized in causal inference by lift",
        "question": "Which organizations specialize most in Causal inference by lift?",
    },
    {
        "demo_id": "demo-06-global-communities",
        "mode": "global",
        "title": "Main research communities in AAAI/IJCAI 2021-2025 (Global Search)",
        "question": "What are the main research communities in the enriched AAAI and IJCAI 2021-2025 knowledge graph?",
    },
    {
        "demo_id": "demo-07-local-gnn",
        "mode": "local",
        "title": "Local GraphRAG overview of graph neural networks",
        "question": "Summarize graph neural networks research and related benchmarks in this corpus.",
    },
]


def assert_demos_disjoint_from_test(questions_path: Path = Path("data/manifests/qa-benchmark-v1/questions.jsonl")) -> None:
    test_texts = {
        json.loads(line)["text"].strip().lower()
        for line in questions_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line)["split"] == "test"
    }
    for d in SCRIPTED_DEMO_QUESTIONS:
        if d["question"].strip().lower() in test_texts:
            raise ValueError(f"Demo question {d['demo_id']} overlaps with a test benchmark question!")


def _extract_predicted_ids_and_names(res: dict[str, Any], top_k: int | None = None) -> tuple[set[str], set[str]]:
    steps = res.get("steps") or []
    if not steps:
        return set(), set()
    # Use the last non-empty step's rows
    rows: list[dict[str, Any]] = []
    for st in reversed(steps):
        if st.get("rows"):
            rows = st["rows"]
            break
    if top_k is not None:
        rows = rows[:top_k]
    ids: set[str] = set()
    names: set[str] = set()
    for r in rows:
        for k in ("id", "neighbor_id", "entity_id", "group_key"):
            if r.get(k):
                ids.add(str(r[k]))
        for k in ("name", "neighbor_name", "entity_name", "label"):
            if r.get(k):
                names.add(str(r[k]).strip().lower())
    return ids, names


def _score_dev_item(ref_row: dict[str, Any], res: dict[str, Any]) -> dict[str, Any]:
    ans_type = ref_row["answer_type"]
    ref = ref_row["reference_answer"]
    ans_text = res.get("answer") or ""

    if ref_row["hops"] == "global":
        complete = res.get("status") == "ok" and len(ans_text.strip()) > 20
        return {
            "question_id": ref_row["question_id"],
            "hops": "global",
            "template_id": ref_row["template_id"],
            "judged": "global_completeness",
            "score": 1.0 if (complete and res.get("faithfulness_passed")) else 0.0,
            "faithfulness_passed": bool(res.get("faithfulness_passed")),
            "latency_s": res.get("latency_s"),
        }

    if ans_type in ("number", "year"):
        target = int(ref)
        nums = {int(float(m)) for m in re.findall(r"\b\d+\b", ans_text)}
        # Also check last step rows for count/year
        for st in (res.get("steps") or []):
            for r in st.get("rows") or []:
                for v in r.values():
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        nums.add(int(v))
        hit = target in nums
        return {
            "question_id": ref_row["question_id"],
            "hops": ref_row["hops"],
            "template_id": ref_row["template_id"],
            "judged": "exact",
            "score": 1.0 if hit else 0.0,
            "expected": target,
            "faithfulness_passed": bool(res.get("faithfulness_passed")),
            "latency_s": res.get("latency_s"),
        }

    # set or ranked_list -> set F1 by ID (fallback to name if ID absent)
    ref_ids = {str(x["id"]) for x in ref}
    ref_names = {str(x["name"]).strip().lower() for x in ref}
    top_k = len(ref) if ans_type == "ranked_list" else None
    pred_ids, pred_names = _extract_predicted_ids_and_names(res, top_k=top_k)

    # Check ID match first, else name match
    if pred_ids & ref_ids or not pred_names:
        tp = len(pred_ids & ref_ids)
        p_len, r_len = len(pred_ids), len(ref_ids)
    else:
        tp = len(pred_names & ref_names)
        p_len, r_len = len(pred_names), len(ref_names)
    prec = (tp / p_len) if p_len else 0.0
    rec = (tp / r_len) if r_len else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
    return {
        "question_id": ref_row["question_id"],
        "hops": ref_row["hops"],
        "template_id": ref_row["template_id"],
        "judged": "set_f1",
        "score": round(f1, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "expected_count": len(ref_ids),
        "predicted_count": p_len,
        "faithfulness_passed": bool(res.get("faithfulness_passed")),
        "latency_s": res.get("latency_s"),
    }


def _make_embed_fn(model_name: str):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name, device="cpu")
    return lambda text: model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]


def run_dev_eval_and_demos(
    config_path: Path = Path("configs/rag-v1.yaml"),
    references_path: Path = Path("data/manifests/qa-benchmark-v1/references-v1.jsonl"),
    *,
    use_llm_cache: bool = True,
    uncached_out: Path | None = None,
) -> dict[str, Any]:
    """Run Phase 4 evaluation on kept development questions ONLY, then cache scripted demo traces."""
    assert_demos_disjoint_from_test()
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    refs = [json.loads(line) for line in references_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    dev_refs = [r for r in refs if r["split"] == "development" and r["status"] == "kept"]
    # Explicit guard: assert zero test questions are ever passed to run_ask here
    assert all(r["split"] == "development" for r in dev_refs)

    sg_cfg = cfg.get("share_growth") or {}
    backend = Neo4jToolBackend()
    llm_cfg = dict(cfg["llm"])
    if not use_llm_cache:
        llm_cfg["cache_dir"] = None
    llm = LLMClient(LLMConfig.from_mapping(llm_cfg))
    vstore = SQLiteVectorStore(Path(cfg["vectors_sqlite_path"]))
    embed_fn = _make_embed_fn(cfg["embeddings"]["model_name"])
    toolset = RAGToolset(
        backend,
        analysis_dir=Path(cfg["analysis_dir"]),
        rag_dir=out_dir,
        min_post_total_papers=int(sg_cfg.get("min_post_total_papers", 10)),
        min_post_subject_papers=int(sg_cfg.get("min_post_subject_papers", 2)),
    )

    def _run_stream_timed(q_text: str, q_mode: str) -> tuple[dict[str, Any], dict[str, float | None]]:
        t0 = time.perf_counter()
        first_event_s: float | None = None
        first_step_s: float | None = None
        first_token_s: float | None = None
        res: dict[str, Any] = {}
        for ev in stream_ask(
            q_text,
            toolset=toolset,
            llm=llm,
            mode=q_mode,
            vector_store=vstore,
            embed_fn=embed_fn,
            reports_path=out_dir / "community-reports.json",
        ):
            now = time.perf_counter() - t0
            etype = ev.get("event")
            if first_event_s is None and etype in ("parsed", "plan", "step", "disambiguate"):
                first_event_s = round(now, 3)
            if first_step_s is None and etype == "step":
                first_step_s = round(now, 3)
            if first_token_s is None and etype == "token":
                first_token_s = round(now, 3)
            if etype == "done":
                res = ev["data"]
        total_s = round(time.perf_counter() - t0, 3)
        if first_event_s is None:
            first_event_s = total_s
        res["latency_s"] = total_s
        return res, {
            "first_event_s": first_event_s,
            "first_step_s": first_step_s,
            "first_token_s": first_token_s,
            "total_s": total_s,
        }

    try:
        dev_items: list[dict[str, Any]] = []
        for r in dev_refs:
            res, timing = _run_stream_timed(r["text"], "auto")
            scored = _score_dev_item(r, res)
            scored["mode"] = res.get("mode")
            scored["stopped_reason"] = res.get("stopped_reason")
            scored["plan_tools"] = [s["tool"] for s in res.get("plan") or []]
            scored["faithfulness_errors"] = res.get("faithfulness_errors") or []
            scored.update(timing)
            dev_items.append(scored)

        by_hop: dict[str, dict[str, Any]] = {}
        for h in ("1", "2", "3", "global"):
            sub = [x for x in dev_items if x["hops"] == h]
            if sub:
                fe_vals = [x["first_event_s"] for x in sub if x.get("first_event_s") is not None]
                fs_vals = [x["first_step_s"] for x in sub if x.get("first_step_s") is not None]
                by_hop[h] = {
                    "count": len(sub),
                    "mean_score": round(sum(x["score"] for x in sub) / len(sub), 4),
                    "faithfulness_rate": round(sum(1 for x in sub if x["faithfulness_passed"]) / len(sub), 4),
                    "mean_first_event_s": round(sum(fe_vals) / len(fe_vals), 3) if fe_vals else None,
                    "mean_first_step_s": round(sum(fs_vals) / len(fs_vals), 3) if fs_vals else None,
                    "mean_latency_s": round(sum(x["latency_s"] for x in sub) / len(sub), 3),
                }

        dev_report = {
            "development_only_not_test_results": True,
            "note": "Measured strictly on the 19 kept development questions after Phase 0 fixes; test questions were NOT touched.",
            "model": cfg["llm"]["model"],
            "kept_dev_count": len(dev_items),
            "by_hop_class": by_hop,
            "overall_faithfulness_rate": round(sum(1 for x in dev_items if x["faithfulness_passed"]) / max(len(dev_items), 1), 4),
            "items": dev_items,
        }
        # Run scripted demo questions
        demos_out: list[dict[str, Any]] = []
        for d in SCRIPTED_DEMO_QUESTIONS:
            res, timing = _run_stream_timed(d["question"], d["mode"])
            demos_out.append({
                "demo_id": d["demo_id"],
                "title": d["title"],
                "question": d["question"],
                "requested_mode": d["mode"],
                "first_event_s": timing["first_event_s"],
                "first_step_s": timing["first_step_s"],
                "first_token_s": timing["first_token_s"],
                "total_latency_s": timing["total_s"],
                "result": res,
            })

        if uncached_out is not None:
            uncached_out.parent.mkdir(parents=True, exist_ok=True)
            demo_summary = [
                {
                    "demo_id": x["demo_id"],
                    "status": x["result"].get("status"),
                    "mode": x["result"].get("mode"),
                    "faithfulness_passed": x["result"].get("faithfulness_passed"),
                    "first_event_s": x["first_event_s"],
                    "first_step_s": x["first_step_s"],
                    "first_token_s": x["first_token_s"],
                    "total_latency_s": x["total_latency_s"],
                }
                for x in demos_out
            ]
            uncached_payload = {
                "uncached_llm": not use_llm_cache,
                "model": cfg["llm"]["model"],
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "by_hop_class": by_hop,
                "overall_faithfulness_rate": dev_report["overall_faithfulness_rate"],
                "demos": demo_summary,
                "dev_items": dev_items,
            }
            uncached_out.write_text(json.dumps(uncached_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            existing_dev = json.loads((out_dir / "dev-eval.json").read_text(encoding="utf-8")) if (out_dir / "dev-eval.json").exists() else dev_report
            existing_dev["uncached_timing"] = {
                "by_hop_class": by_hop,
                "overall_faithfulness_rate": dev_report["overall_faithfulness_rate"],
                "demos": demo_summary,
            }
            (out_dir / "dev-eval.json").write_text(json.dumps(existing_dev, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return {"dev_eval": by_hop, "demos_timing": demo_summary, "uncached_out": str(uncached_out)}

        (out_dir / "dev-eval.json").write_text(json.dumps(dev_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        demo_payload = {
            "model": cfg["llm"]["model"],
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "demos": demos_out,
        }
        (out_dir / "demo-cache.json").write_text(json.dumps(demo_payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return {"dev_eval": by_hop, "demos_cached": len(demos_out)}
    finally:
        backend.close()
        llm.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run development-only QA eval and scripted demo caching.")
    parser.add_argument("--config", type=Path, default=Path("configs/rag-v1.yaml"))
    parser.add_argument("--references", type=Path, default=Path("data/manifests/qa-benchmark-v1/references-v1.jsonl"))
    parser.add_argument("--no-llm-cache", action="store_true", help="Disable LLM response cache for uncached latency timing.")
    parser.add_argument("--uncached-out", type=Path, default=None, help="Write uncached timing summary without overwriting demo-cache.json.")
    args = parser.parse_args()
    print(
        json.dumps(
            run_dev_eval_and_demos(
                config_path=args.config,
                references_path=args.references,
                use_llm_cache=not args.no_llm_cache,
                uncached_out=args.uncached_out,
            ),
            indent=2,
        )
    )
