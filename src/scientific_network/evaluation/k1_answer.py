"""K1 answer-quality arm of the model comparison (specification §6.1; protocol k1-answer-v1).

Runs the qa-eval-v1 S4 multi-hop system (automatic mode) on the kept DEVELOPMENT
questions only, once per served model, and scores the answers with the qa-eval-v1
unified entity resolver and numeric exact match. Only the model changes; the
pipeline, prompts, decoding and scorer are those of qa-eval-v1.

Subcommands:
  run    --model-key KEY   run one model (the llama.cpp server must already serve it)
  score                    score every model that has raw outputs; write results.{json,md}

Never loads or runs a test question: the configured split must be ``development``
and every loaded row is checked.
"""

from __future__ import annotations

import argparse
from dataclasses import fields as dataclass_fields
import json
from pathlib import Path
import re
import subprocess
import threading
import time
from typing import Any

import httpx
import yaml

from scientific_network.evaluation.precision import precision_interval
from scientific_network.evaluation.qa_eval import (
    UnifiedEntityResolver,
    _infer_target_labels,
    _load_jsonl,
    _run_s4,
    _score_numeric_exact,
    _sha256_file,
    build_entity_catalog,
    seeded_bootstrap_ci,
    set_f1,
)
from scientific_network.rag.llm import LLMClient, LLMConfig

HOP_CLASSES: tuple[str, ...] = ("1", "2", "3")


def load_config(path: Path) -> dict[str, Any]:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    base = yaml.safe_load(Path(cfg["base_protocol_config"]).read_text(encoding="utf-8"))
    cfg["_base"] = base
    return cfg


def load_dev_questions(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    bench = cfg["benchmark"]
    if bench.get("split") != "development":
        raise ValueError("k1-answer-v1 runs on the development split only")
    ref_path = Path(bench["references_path"])
    actual = _sha256_file(ref_path)
    if actual != bench["references_sha256"]:
        raise ValueError(f"references SHA-256 mismatch: expected {bench['references_sha256']}, got {actual}")
    rows = [
        r for r in _load_jsonl(ref_path)
        if r.get("split") == "development" and r.get("status") == bench.get("status_filter", "kept")
    ]
    if any(r.get("split") != "development" for r in rows):
        raise AssertionError("non-development question loaded")
    expected = bench["expected_counts"]
    counts = {"total": len(rows), **{f"hop_{h}": sum(1 for r in rows if str(r["hops"]) == h) for h in HOP_CLASSES},
              "global": sum(1 for r in rows if str(r["hops"]) == "global")}
    if counts != expected:
        raise ValueError(f"development counts {counts} differ from expected {expected}")
    return rows


def _model_entry(cfg: dict[str, Any], key: str) -> dict[str, Any]:
    for m in cfg["models"]:
        if m["key"] == key:
            return m
    raise KeyError(f"unknown model key {key!r}")


def _gpu_used_mib() -> int | None:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout.strip().splitlines()
        return int(out[0]) if out else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


class _GPUSampler(threading.Thread):
    def __init__(self, interval: float = 0.5) -> None:
        super().__init__(daemon=True)
        self.interval = interval
        self.samples: list[int] = []
        self._halt = threading.Event()

    def run(self) -> None:
        while not self._halt.is_set():
            v = _gpu_used_mib()
            if v is not None:
                self.samples.append(v)
            self._halt.wait(self.interval)

    def stop(self) -> None:
        self._halt.set()
        self.join(timeout=5)


_METRIC_RE = re.compile(r"^(llamacpp:[a-z_]+)\s+([0-9.eE+-]+)$")


def _server_metrics(base_url: str) -> dict[str, float]:
    root = base_url.rstrip("/").removesuffix("/v1")
    try:
        text = httpx.get(f"{root}/metrics", timeout=10).text
    except httpx.HTTPError:
        return {}
    out: dict[str, float] = {}
    for line in text.splitlines():
        m = _METRIC_RE.match(line.strip())
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


def _served_models(base_url: str) -> list[str]:
    data = httpx.get(f"{base_url.rstrip('/')}/models", timeout=10).json()
    return [str(x.get("id")) for x in data.get("data", [])]


def _git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _read_log(path: Path, start: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(x) for x in lines[start:] if x.strip()]


def _count_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines()) if path.exists() else 0


def run_model(cfg: dict[str, Any], model_key: str, *, idle_gpu_mib: int | None, allow_overwrite: bool = False) -> Path:
    model = _model_entry(cfg, model_key)
    base = cfg["_base"]
    results_dir = Path(cfg["outputs"]["results_dir"])
    run_dir = Path(cfg["outputs"]["run_dir"]) / model_key
    raw_path = results_dir / f"raw-{model_key}.jsonl"
    if raw_path.exists() and not allow_overwrite:
        raise FileExistsError(f"{raw_path} exists; k1-answer-v1 runs each model once")
    base_url = cfg["server"]["base_url"]
    served = _served_models(base_url)
    if model["alias"] not in served:
        raise RuntimeError(f"server at {base_url} serves {served}, not {model['alias']}")

    questions = load_dev_questions(cfg)
    rag_cfg = yaml.safe_load(Path(cfg["rag_config_path"]).read_text(encoding="utf-8"))
    sg_cfg = rag_cfg.get("share_growth") or {}

    from sentence_transformers import SentenceTransformer

    from scientific_network.rag.sqlite_vectors import SQLiteVectorStore
    from scientific_network.rag.tools import Neo4jToolBackend, RAGToolset

    st_model = SentenceTransformer(base["embeddings"]["model_name"], device="cpu")
    embed_fn = lambda text: st_model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]  # noqa: E731

    dec = cfg["decoding"]
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "llm-calls.jsonl"
    cache_dir = run_dir / "llm-cache"
    if allow_overwrite:
        log_path.unlink(missing_ok=True)
    elif log_path.exists() or cache_dir.exists():
        raise FileExistsError(f"{run_dir} already holds a log or cache; k1-answer-v1 runs uncached once")
    llm_cfg = {
        "base_url": base_url, "model": model["alias"], "revision": model["gguf_revision"],
        "provider": "local-llama.cpp", "temperature": dec["temperature"], "seed": dec["seed"],
        "enable_thinking": dec["enable_thinking"], "max_tokens": dec["max_tokens"], "timeout": dec["timeout"],
        "cache_dir": str(cache_dir), "log_path": str(log_path),
    }
    valid = {f.name for f in dataclass_fields(LLMConfig)}
    llm = LLMClient(LLMConfig.from_mapping({k: v for k, v in llm_cfg.items() if k in valid}))
    backend = Neo4jToolBackend()
    vstore = SQLiteVectorStore(Path(base["vectors_sqlite_path"]))
    toolset = RAGToolset(
        backend,
        analysis_dir=Path(base["analysis_dir"]),
        rag_dir=Path(base["rag_dir"]),
        min_post_total_papers=int(sg_cfg.get("min_post_total_papers", 10)),
        min_post_subject_papers=int(sg_cfg.get("min_post_subject_papers", 2)),
    )
    s4_cfg = {"rag_dir": base["rag_dir"], "systems": {"S4_multihop": {"mode": "auto"}}}

    metrics_before = _server_metrics(base_url)
    sampler = _GPUSampler()
    sampler.start()
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    records: list[dict[str, Any]] = []
    try:
        for q in questions:
            assert q["split"] == "development"
            log_start = _count_lines(log_path)
            out = _run_s4(q["text"], toolset=toolset, llm=llm, vector_store=vstore, embed_fn=embed_fn, cfg=s4_cfg)
            calls = _read_log(log_path, log_start)
            records.append({
                "question_id": q["question_id"],
                "split": q["split"],
                "hops": str(q["hops"]),
                "answer_type": q["answer_type"],
                "judged": q["judged"],
                "model_key": model_key,
                "model_alias": model["alias"],
                **out,
                "llm_calls": [
                    {k: c.get(k) for k in ("prompt_version", "attempts", "error", "cache_hit",
                                           "prompt_tokens", "completion_tokens", "latency_s", "finish_reason")}
                    for c in calls
                ],
            })
    finally:
        sampler.stop()
        backend.close()
        llm.close()
    metrics_after = _server_metrics(base_url)

    results_dir.mkdir(parents=True, exist_ok=True)
    with raw_path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    peak = max(sampler.samples) if sampler.samples else None
    meta = {
        "protocol_version": cfg["protocol_version"],
        "model_key": model_key,
        "model": {k: model[k] for k in ("alias", "hf_repo", "gguf_repo", "gguf_revision", "gguf_sha256",
                                        "quantization", "total_params_b", "eligible", "role")},
        "server": cfg["server"],
        "decoding": dec,
        "code_commit": _git_head(),
        "started_at": started,
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "question_count": len(records),
        "raw_outputs_sha256": _sha256_file(raw_path),
        "gpu": {
            "idle_baseline_mib": idle_gpu_mib,
            "peak_used_mib": peak,
            "peak_over_idle_mib": (peak - idle_gpu_mib) if (peak is not None and idle_gpu_mib is not None) else None,
            "samples": len(sampler.samples),
        },
        "server_metrics_before": metrics_before,
        "server_metrics_after": metrics_after,
    }
    (results_dir / f"run-meta-{model_key}.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return raw_path


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _mean(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 4) if xs else None


def _rate_ci(ok: int, n: int) -> dict[str, Any]:
    if not n:
        return {"passed": 0, "total": 0, "rate": None, "wilson_95_ci": None}
    ci = precision_interval(ok, n)
    return {"passed": ok, "total": n, "rate": round(ok / n, 4),
            "wilson_95_ci": [round(ci["wilson_lower"], 4), round(ci["wilson_upper"], 4)]}


def _json_validity(rows: list[dict[str, Any]], prefix: str, retry_pv: str | None) -> dict[str, Any]:
    reached = 0
    first_pass = 0
    valid_eventually = 0
    fallback = 0
    for r in rows:
        calls = [c for c in r.get("llm_calls") or [] if str(c.get("prompt_version")) == prefix]
        retries = [c for c in r.get("llm_calls") or [] if retry_pv and str(c.get("prompt_version")) == retry_pv]
        if not calls:
            continue
        reached += 1
        c0 = calls[0]
        if c0.get("error") is None and int(c0.get("attempts") or 1) == 1:
            first_pass += 1
        if c0.get("error") is None or any(x.get("error") is None for x in retries):
            valid_eventually += 1
        else:
            fallback += 1
    return {
        "prompt_version": prefix,
        "questions_reaching_call": reached,
        "first_pass_valid": _rate_ci(first_pass, reached),
        "valid_after_retries": _rate_ci(valid_eventually, reached),
        "deterministic_fallback": fallback,
    }


def _plan_json_validity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    res = _json_validity(rows, "rag-plan-v4", "rag-plan-v4-retry")
    # A schema-valid plan can still normalize to zero known tools; that triggers the retry prompt.
    res["rag_plan_v4_retry_used"] = sum(
        1 for r in rows if any(str(c.get("prompt_version")) == "rag-plan-v4-retry" for c in r.get("llm_calls") or [])
    )
    return res


def _throughput(rows: list[dict[str, Any]], meta: dict[str, Any]) -> dict[str, Any]:
    calls = [c for r in rows for c in r.get("llm_calls") or [] if not c.get("cache_hit")]
    comp = sum(int(c.get("completion_tokens") or 0) for c in calls)
    prompt = sum(int(c.get("prompt_tokens") or 0) for c in calls)
    lat = sum(float(c.get("latency_s") or 0.0) for c in calls)
    before = meta.get("server_metrics_before") or {}
    after = meta.get("server_metrics_after") or {}

    def _delta(name: str) -> float | None:
        if name in before and name in after:
            return after[name] - before[name]
        return None

    pred_tok = _delta("llamacpp:tokens_predicted_total")
    pred_sec = _delta("llamacpp:tokens_predicted_seconds_total")
    prm_tok = _delta("llamacpp:prompt_tokens_total")
    prm_sec = _delta("llamacpp:prompt_seconds_total")
    return {
        "uncached_calls": len(calls),
        "cache_hits": sum(1 for r in rows for c in r.get("llm_calls") or [] if c.get("cache_hit")),
        "prompt_tokens": prompt,
        "completion_tokens": comp,
        "decode_tokens_per_s": round(pred_tok / pred_sec, 2) if pred_tok and pred_sec else None,
        "prompt_tokens_per_s": round(prm_tok / prm_sec, 2) if prm_tok and prm_sec else None,
        "end_to_end_completion_tokens_per_s": round(comp / lat, 2) if lat else None,
        "source": "llama.cpp /metrics counter deltas over the run; end-to-end = completion tokens / summed call latency",
    }


def score_all(cfg: dict[str, Any]) -> dict[str, Any]:
    base = cfg["_base"]
    results_dir = Path(cfg["outputs"]["results_dir"])
    refs = {r["question_id"]: r for r in load_dev_questions(cfg)}

    graph_data = json.loads(Path(base["graph"]["path"]).read_text(encoding="utf-8"))
    catalog = build_entity_catalog(graph_data.get("nodes", []))
    from sentence_transformers import SentenceTransformer

    st_model = SentenceTransformer(base["embeddings"]["model_name"], device="cpu")
    embed_fn = lambda text: st_model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]  # noqa: E731
    thresh = float(base["factual_scoring"]["unified_entity_resolver"].get("embedding_threshold", 0.80))
    resolver = UnifiedEntityResolver(catalog, embed_fn=embed_fn, embedding_threshold=thresh)
    id_to_label = {cid: c["label"] for cid, c in resolver.by_id.items()}
    abs_tol = int(base["factual_scoring"]["numeric_exact_match"].get("abs_tol", 0))
    bs_seed = int(base["factual_scoring"]["intervals"].get("bootstrap_seed", 20261125))
    bs_n = int(base["factual_scoring"]["intervals"].get("bootstrap_resamples", 2000))

    models_out: dict[str, Any] = {}
    items_out: list[dict[str, Any]] = []
    for m in cfg["models"]:
        key = m["key"]
        raw_path = results_dir / f"raw-{key}.jsonl"
        if not raw_path.exists():
            continue
        rows = _load_jsonl(raw_path)
        if any(r.get("split") != "development" for r in rows):
            raise AssertionError("non-development row in K1 raw outputs")
        meta = json.loads((results_dir / f"run-meta-{key}.json").read_text(encoding="utf-8"))
        scored: list[dict[str, Any]] = []
        for r in rows:
            ref = refs[r["question_id"]]
            ans = r.get("answer") or ""
            score: float | None = None
            if ref["judged"] == "exact":
                score = _score_numeric_exact(ans, int(ref["reference_answer"]), abs_tol=abs_tol)
            elif ref["judged"] == "set_f1":
                labels = _infer_target_labels(ref, id_to_label)
                resolved = resolver.resolve(ans, target_labels=labels)
                top_k = len(ref["reference_answer"]) if ref.get("answer_type") == "ranked_list" else None
                pred = set(resolved[:top_k] if top_k else resolved)
                score, _, _ = set_f1(pred, {str(x["id"]) for x in ref["reference_answer"]})
            item = {
                "model_key": key,
                "question_id": r["question_id"],
                "hops": r["hops"],
                "judged": ref["judged"],
                "score": round(score, 4) if score is not None else None,
                "status": r.get("status"),
                "mode": (r.get("trace_summary") or {}).get("mode"),
                "faithfulness_passed": bool(r.get("faithfulness_passed")),
                "first_event_s": r.get("first_event_s"),
                "total_latency_s": r.get("total_latency_s"),
            }
            scored.append(item)
            items_out.append(item)

        by_hop: dict[str, Any] = {}
        for h in (*HOP_CLASSES, "factual_overall", "global"):
            if h == "factual_overall":
                sub = [x for x in scored if x["hops"] in HOP_CLASSES]
            else:
                sub = [x for x in scored if x["hops"] == h]
            vals = [float(x["score"]) for x in sub if x["score"] is not None]
            fe = [float(x["first_event_s"]) for x in sub if x.get("first_event_s") is not None]
            tot = [float(x["total_latency_s"]) for x in sub if x.get("total_latency_s") is not None]
            by_hop[h] = {
                "count": len(sub),
                "mean_score": _mean(vals),
                "bootstrap_95_ci": list(seeded_bootstrap_ci(vals, n_resamples=bs_n, seed=bs_seed)) if vals else None,
                "faithfulness": _rate_ci(sum(1 for x in sub if x["faithfulness_passed"]), len(sub)),
                "status_ok": sum(1 for x in sub if x["status"] == "ok"),
                "mean_first_event_s": round(sum(fe) / len(fe), 3) if fe else None,
                "mean_total_s": round(sum(tot) / len(tot), 3) if tot else None,
                "max_total_s": round(max(tot), 3) if tot else None,
            }
        fe_all = [float(x["first_event_s"]) for x in scored if x.get("first_event_s") is not None]
        tot_all = [float(x["total_latency_s"]) for x in scored if x.get("total_latency_s") is not None]
        models_out[key] = {
            "model": meta["model"],
            "code_commit": meta["code_commit"],
            "raw_outputs_sha256": meta["raw_outputs_sha256"],
            "by_hop": by_hop,
            "faithfulness_all": _rate_ci(sum(1 for x in scored if x["faithfulness_passed"]), len(scored)),
            "planner_json_validity": _plan_json_validity(rows),
            "parser_json_validity": _json_validity(rows, "rag-parse-v2", None),
            "latency_all": {
                "mean_first_event_s": round(sum(fe_all) / len(fe_all), 3) if fe_all else None,
                "mean_total_s": round(sum(tot_all) / len(tot_all), 3) if tot_all else None,
                "max_total_s": round(max(tot_all), 3) if tot_all else None,
            },
            "gpu": meta["gpu"],
            "throughput": _throughput(rows, meta),
        }

    outcome = apply_decision_rule(models_out)
    payload = {
        "protocol_version": cfg["protocol_version"],
        "development_figures_only": True,
        "split": "development",
        "pipeline": cfg["pipeline"],
        "scorer": cfg["scorer"],
        "references_sha256": cfg["benchmark"]["references_sha256"],
        "graph_version": base["graph"]["graph_version"],
        "scored_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "models": models_out,
        "decision": outcome,
        "caveats": cfg["caveats"],
        "items": items_out,
    }
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (results_dir / "results.md").write_text(render_markdown(payload), encoding="utf-8")
    return payload


def apply_decision_rule(models: dict[str, Any]) -> dict[str, Any]:
    """Apply specification §6.1 to development answer accuracy (factual_overall mean)."""
    def acc(key: str) -> float | None:
        m = models.get(key)
        return None if m is None else m["by_hop"]["factual_overall"]["mean_score"]

    a4, ag, a9 = acc("qwen3.5-4b"), acc("gemma-4-e4b"), acc("qwen3.5-9b")
    eligible = {k: v for k, v in (("qwen3.5-4b", a4), ("gemma-4-e4b", ag)) if v is not None}
    best_key = max(eligible, key=lambda k: eligible[k]) if eligible else None
    best = eligible.get(best_key) if best_key else None
    out: dict[str, Any] = {
        "answer_accuracy": {"qwen3.5-4b": a4, "gemma-4-e4b": ag, "qwen3.5-9b": a9},
        "best_eligible_model": best_key,
        "margin_required": 0.10,
    }
    if a9 is not None and best is not None:
        gain = round(a9 - best, 4)
        out["reference_9b_gain_over_best_eligible"] = gain
        out["reference_9b_meets_margin"] = gain >= 0.10
    if a4 is not None and ag is not None:
        g = round(ag - a4, 4)
        out["gemma_gain_over_4b"] = g
        out["gemma_flag_for_user"] = g >= 0.10
    flagged = bool(out.get("reference_9b_meets_margin")) or bool(out.get("gemma_flag_for_user"))
    out["outcome"] = (
        "A margin is met; a model change needs a recorded team decision (not made by the agent)."
        if flagged else
        "No margin is met; Qwen3.5-4B stays the chosen model (M0 choice confirmed on the answer arm)."
    )
    return out


def _f(v: float | None, nd: int = 3) -> str:
    return "–" if v is None else f"{v:.{nd}f}"


def render_markdown(p: dict[str, Any]) -> str:
    order = [k for k in ("qwen3.5-4b", "gemma-4-e4b", "qwen3.5-9b") if k in p["models"]]
    lines = [
        "# K1 answer-quality arm (development figures, k1-answer-v1)",
        "",
        "**Development figures only.** 19 kept development questions of qa-benchmark-v1 (15 factual, 4 global); "
        "no test question was run. Pipeline: the qa-eval-v1 S4 multi-hop system in automatic mode; "
        "scorer: the qa-eval-v1 unified entity resolver and integer exact match. Decoding identical for every model "
        "(temperature 0, seed 0, thinking off, uncached). Only the model changes. "
        f"Graph `{p['graph_version']}`; references SHA-256 `{p['references_sha256'][:16]}…`. "
        "The factual score measures agreement with the graph's edges, not truth.",
        "",
        "## Answer accuracy by hop class (mean score, seeded bootstrap 95% CI)",
        "",
        "| Model (total params) | Hop 1 (4) | Hop 2 (6) | Hop 3 (5) | Factual overall (15) | Global ok + faithful (4) |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for k in order:
        m = p["models"][k]
        bh = m["by_hop"]
        name = f"{m['model']['hf_repo']} {m['model']['quantization']} ({m['model']['total_params_b']:.2f}B)"
        if not m["model"]["eligible"]:
            name += ", reference only"
        cells = []
        for h in ("1", "2", "3", "factual_overall"):
            ci = bh[h]["bootstrap_95_ci"]
            cells.append(f"{_f(bh[h]['mean_score'])} [{_f(ci[0])}, {_f(ci[1])}]" if ci else _f(bh[h]["mean_score"]))
        g = bh["global"]
        cells.append(f"{g['status_ok']} ok, {g['faithfulness']['passed']}/{g['faithfulness']['total']} faithful")
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Faithfulness, planner JSON validity, latency, memory and throughput",
        "",
        "| Model | Faithfulness (19, Wilson 95%) | Planner JSON first-pass valid | Planner valid after retry / fallback | Parser JSON first-pass valid | Mean first event s | Mean total s (max) | GPU peak MiB (over idle) | Decode tok/s | Prompt tok/s |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for k in order:
        m = p["models"][k]
        fa = m["faithfulness_all"]
        pj = m["planner_json_validity"]
        pa = m["parser_json_validity"]
        la = m["latency_all"]
        gpu = m["gpu"]
        th = m["throughput"]
        lines.append(
            f"| {k} | {fa['passed']}/{fa['total']} ({_f(fa['rate'])} [{_f(fa['wilson_95_ci'][0])}, {_f(fa['wilson_95_ci'][1])}]) "
            f"| {pj['first_pass_valid']['passed']}/{pj['first_pass_valid']['total']} "
            f"| {pj['valid_after_retries']['passed']}/{pj['valid_after_retries']['total']} / {pj['deterministic_fallback']} "
            f"| {pa['first_pass_valid']['passed']}/{pa['first_pass_valid']['total']} "
            f"| {_f(la['mean_first_event_s'], 2)} | {_f(la['mean_total_s'], 2)} ({_f(la['max_total_s'], 1)}) "
            f"| {gpu['peak_used_mib']} ({gpu['peak_over_idle_mib']}) "
            f"| {_f(th['decode_tokens_per_s'], 1)} | {_f(th['prompt_tokens_per_s'], 1)} |"
        )
    d = p["decision"]
    lines += [
        "",
        "## §6.1 decision rule",
        "",
        f"- Development answer accuracy (factual overall): "
        + ", ".join(f"{k} {_f(v)}" for k, v in d["answer_accuracy"].items() if v is not None) + ".",
        f"- Best eligible model on this arm: `{d['best_eligible_model']}`.",
    ]
    if "reference_9b_gain_over_best_eligible" in d:
        lines.append(
            f"- Qwen3.5-9B (reference only, 9.65B) gain over the best eligible model: "
            f"{d['reference_9b_gain_over_best_eligible']:+.3f} (margin 0.10 {'met' if d['reference_9b_meets_margin'] else 'not met'})."
        )
    if "gemma_gain_over_4b" in d:
        lines.append(
            f"- Gemma-4-E4B-it gain over Qwen3.5-4B: {d['gemma_gain_over_4b']:+.3f} "
            f"(flag-for-user margin 0.10 {'met' if d['gemma_flag_for_user'] else 'not met'})."
        )
    lines += [f"- **Outcome:** {d['outcome']}", "", "## Caveats", ""]
    lines += [f"- {c}" for c in p["caveats"]]
    lines += [
        "- Planner JSON validity counts the first `rag-plan-v4` call per question: first-pass valid means schema-valid "
        "JSON without the client's correction retry. llama.cpp enforces the JSON schema with a grammar, so validity is "
        "expected to be high for every model.",
        "- GPU memory is total device use from `nvidia-smi`; the host display holds part of it (idle baseline shown "
        "in `results.json`).",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="K1 answer-quality arm (k1-answer-v1, development only).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    rp = sub.add_parser("run")
    rp.add_argument("--config", type=Path, default=Path("configs/k1-answer-v1.yaml"))
    rp.add_argument("--model-key", required=True)
    rp.add_argument("--idle-gpu-mib", type=int, default=None)
    rp.add_argument("--allow-overwrite", action="store_true")
    sp = sub.add_parser("score")
    sp.add_argument("--config", type=Path, default=Path("configs/k1-answer-v1.yaml"))
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    if args.cmd == "run":
        p = run_model(cfg, args.model_key, idle_gpu_mib=args.idle_gpu_mib, allow_overwrite=args.allow_overwrite)
        print(json.dumps({"raw_outputs": str(p)}))
    else:
        res = score_all(cfg)
        print(json.dumps(res["decision"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
