"""Frozen test-benchmark QA evaluation harness (spec §6.6; M4 Phases 1 & 2).

Implements the comparative evaluation across:
- S1: SLM alone (Qwen3.5-4B, no retrieval)
- S2: Vector RAG over abstract chunks (SQLiteVectorStore top-k + Qwen3.5-4B)
- S3: GraphRAG local / global search
- S4: Full multi-hop system (automatic routing)

with a single unified text-to-graph-ID entity resolver applied identically across
all four systems, Wilson and seeded bootstrap intervals, AI-assessed citation validity
packets (abstracts restricted to ignored run logs), and blind AB/BA global pairwise
judging aggregation.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import fields as dataclass_fields
import hashlib
from itertools import combinations
import json
from pathlib import Path
import random
import re
import time
from typing import Any, Callable

import numpy as np
import yaml

from scientific_network.evaluation.edge_audit import cohens_kappa
from scientific_network.evaluation.precision import precision_interval
from scientific_network.rag.answer import (
    _extract_answer_numbers,
    _extract_candidate_entities,
    _norm_text,
    compose_grounded_answer,
    stream_ask,
    verify_answer_faithfulness,
)
from scientific_network.rag.llm import LLMClient, LLMConfig, LLMError
from scientific_network.rag.retrieval import global_search, local_search
from scientific_network.rag.sqlite_vectors import SQLiteVectorStore
from scientific_network.rag.tools import Neo4jToolBackend, RAGToolset

SYSTEM_ORDER: tuple[str, ...] = ("S1_slm_only", "S2_vector_rag", "S3_graphrag", "S4_multihop")

_PAPER_ID_RE = re.compile(r"paper:(?:aaai|ijcai):\d{4}:[A-Za-z0-9_.-]*[A-Za-z0-9_-]")
_ANY_GRAPH_ID_RE = re.compile(
    r"\b(?:paper|researcher|organization|method|task|dataset|topic|venue|community):[A-Za-z0-9_.:-]*[A-Za-z0-9_-]"
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")

_S1_SYSTEM_PROMPT = (
    "You are a concise scientific knowledge assistant answering questions about AAAI and IJCAI "
    "papers published from 2021 to 2025. Answer directly and concisely from your knowledge. "
    "For list or entity questions, present the entities clearly as bullet points; for count or "
    "year questions, state the numeric value clearly. Do not fabricate bracketed graph IDs."
)

_S2_SYSTEM_PROMPT = (
    "Answer the user question concisely using ONLY the retrieved abstract excerpts below.\n"
    "Rules:\n"
    "- Every number you state MUST appear verbatim in the retrieved excerpts.\n"
    "- Mention ONLY organizations, researchers, methods, tasks, datasets, and topics present in "
    "the excerpts or question; NEVER invent entities.\n"
    "- Cite supporting papers verbatim by copying their full ID in brackets, e.g. "
    "[paper:aaai:2024:29823]. NEVER write placeholder citations like [paper:...] or [...].\n"
    "- If the retrieved excerpts do not contain enough evidence, state what is missing honestly."
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for r in rows:
            handle.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_benchmark_questions(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Load the configured benchmark split cleanly and verify frozen reference SHA-256."""
    bench = cfg["benchmark"]
    ref_path = Path(bench["references_path"])
    expected_sha = bench.get("references_sha256")
    if expected_sha:
        actual_sha = _sha256_file(ref_path)
        if actual_sha != expected_sha:
            raise ValueError(f"references SHA-256 mismatch: expected {expected_sha}, got {actual_sha}")

    split = bench.get("split", "test")
    status_filter = bench.get("status_filter", "kept")
    rows = [
        r
        for r in _load_jsonl(ref_path)
        if r.get("split") == split and (not status_filter or r.get("status") == status_filter)
    ]
    return rows


# ---------------------------------------------------------------------------
# Phase 2 Step 1 helper: run all 4 systems cleanly with run-once guard
# ---------------------------------------------------------------------------


def _run_s1(question: str, *, llm: LLMClient, cfg: dict[str, Any]) -> dict[str, Any]:
    s1_cfg = cfg["systems"]["S1_slm_only"]
    t0 = time.perf_counter()
    try:
        res = llm.complete(
            prompt_version=s1_cfg["prompt_version"],
            system=_S1_SYSTEM_PROMPT,
            user=question,
            max_tokens=int(s1_cfg.get("max_tokens", 700)),
        )
        ans = res.content.strip()
        err = None
    except LLMError as exc:
        ans = f"Generation error: {exc}"
        err = str(exc)
    total_s = round(time.perf_counter() - t0, 3)
    cited = sorted(set(_PAPER_ID_RE.findall(ans)))
    return {
        "system": "S1_slm_only",
        "status": "ok" if err is None else "error",
        "error": err,
        "answer": ans,
        "paper_ids": cited,
        "faithfulness_passed": None,
        "faithfulness_errors": [],
        "first_event_s": total_s,
        "first_step_s": None,
        "first_token_s": total_s,
        "total_latency_s": total_s,
        "trace_summary": {"mode": "slm_only"},
    }


def _run_s2(
    question: str,
    *,
    llm: LLMClient,
    vector_store: SQLiteVectorStore,
    embed_fn: Callable[[str], np.ndarray],
    paper_titles: dict[str, str],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    s2_cfg = cfg["systems"]["S2_vector_rag"]
    t0 = time.perf_counter()
    q_vec = embed_fn(question)
    top_k = int(s2_cfg.get("top_k_chunks", 10))
    hits = vector_store.search("abstract_chunk", q_vec, top_k=top_k)
    first_step_s = round(time.perf_counter() - t0, 3)

    excerpt_rows = []
    paper_ids: list[str] = []
    for idx, h in enumerate(hits, start=1):
        meta = h.get("metadata") or {}
        pid = str(meta.get("paper_id") or h["id"].split("#", 1)[0])
        paper_ids.append(pid)
        excerpt_rows.append({
            "rank": idx,
            "paper_id": pid,
            "title": paper_titles.get(pid, ""),
            "year": meta.get("year"),
            "score": round(float(h.get("score", 0.0)), 4),
            "text": h.get("text", ""),
        })

    trace_payload = {
        "steps": [{
            "step": 1,
            "tool": "vector_abstract_chunks",
            "row_count": len(excerpt_rows),
            "rows": excerpt_rows,
            "paper_ids": list(dict.fromkeys(paper_ids)),
        }]
    }
    user_msg = (
        f"Question: {question}\n\nRetrieved abstract excerpts:\n"
        + json.dumps(excerpt_rows, ensure_ascii=False, separators=(",", ":"))
    )
    err = None
    try:
        res = llm.complete(
            prompt_version=s2_cfg["prompt_version"],
            system=_S2_SYSTEM_PROMPT,
            user=user_msg,
            max_tokens=int(s2_cfg.get("max_tokens", 700)),
        )
        ans = res.content.strip()
    except LLMError as exc:
        ans = f"Generation error: {exc}"
        err = str(exc)

    total_s = round(time.perf_counter() - t0, 3)
    errs = verify_answer_faithfulness(ans, trace_payload, question) if err is None else [err]
    return {
        "system": "S2_vector_rag",
        "status": "ok" if err is None else "error",
        "error": err,
        "answer": ans,
        "paper_ids": list(dict.fromkeys(paper_ids + _PAPER_ID_RE.findall(ans))),
        "faithfulness_passed": len(errs) == 0,
        "faithfulness_errors": errs,
        "first_event_s": first_step_s,
        "first_step_s": first_step_s,
        "first_token_s": total_s,
        "total_latency_s": total_s,
        "trace_summary": {"mode": "vector_rag", "chunk_count": len(excerpt_rows), "paper_ids": list(dict.fromkeys(paper_ids))},
    }


def _run_s3(
    question: str,
    hops: str,
    *,
    toolset: RAGToolset,
    llm: LLMClient,
    vector_store: SQLiteVectorStore,
    embed_fn: Callable[[str], np.ndarray],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    s3_cfg = cfg["systems"]["S3_graphrag"]
    reports_path = Path(cfg["rag_dir"]) / "community-reports.json"
    t0 = time.perf_counter()
    if str(hops) == "global":
        g_res = global_search(
            question,
            llm=llm,
            reports_path=reports_path,
            vector_store=vector_store,
            embed_fn=embed_fn,
            top_reports=int(s3_cfg.get("global_top_reports", 14)),
            batch_size=int(s3_cfg.get("global_batch_size", 5)),
            prompt_version=str(s3_cfg.get("global_prompt_version", "rag-global-v2")),
        )
        total_s = round(time.perf_counter() - t0, 3)
        errs = verify_answer_faithfulness(g_res["answer"], g_res["points"], question)
        return {
            "system": "S3_graphrag",
            "status": "ok",
            "error": None,
            "answer": g_res["answer"],
            "paper_ids": g_res["paper_ids"],
            "faithfulness_passed": len(errs) == 0,
            "faithfulness_errors": errs,
            "first_event_s": total_s,
            "first_step_s": total_s,
            "first_token_s": total_s,
            "total_latency_s": total_s,
            "trace_summary": {"mode": "global", "reports_used": g_res.get("reports_used", [])},
        }

    l_res = local_search(
        question,
        toolset=toolset,
        vector_store=vector_store,
        embed_fn=embed_fn,
        char_budget=int(s3_cfg.get("char_budget", 14000)),
        top_reports=int(s3_cfg.get("top_reports", 4)),
        top_entities=int(s3_cfg.get("top_entities", 6)),
        top_chunks=int(s3_cfg.get("top_chunks", 10)),
    )
    first_step_s = round(time.perf_counter() - t0, 3)
    composed = compose_grounded_answer(
        question,
        l_res,
        llm,
        prompt_version=str(s3_cfg.get("local_prompt_version", "rag-local-answer-v2")),
    )
    total_s = round(time.perf_counter() - t0, 3)
    return {
        "system": "S3_graphrag",
        "status": "ok",
        "error": None,
        "answer": composed["answer"],
        "paper_ids": l_res["paper_ids"],
        "faithfulness_passed": bool(composed["faithfulness_passed"]),
        "faithfulness_errors": list(composed["faithfulness_errors"]),
        "first_event_s": first_step_s,
        "first_step_s": first_step_s,
        "first_token_s": total_s,
        "total_latency_s": total_s,
        "trace_summary": {
            "mode": "local",
            "linked_entity_ids": l_res.get("linked_entity_ids", []),
            "sections_used": l_res.get("sections_used", []),
        },
    }


def _run_s4(
    question: str,
    *,
    toolset: RAGToolset,
    llm: LLMClient,
    vector_store: SQLiteVectorStore,
    embed_fn: Callable[[str], np.ndarray],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    reports_path = Path(cfg["rag_dir"]) / "community-reports.json"
    t0 = time.perf_counter()
    first_event_s: float | None = None
    first_step_s: float | None = None
    first_token_s: float | None = None
    res: dict[str, Any] = {}
    for ev in stream_ask(
        question,
        toolset=toolset,
        llm=llm,
        mode=str(cfg["systems"]["S4_multihop"].get("mode", "auto")),
        vector_store=vector_store,
        embed_fn=embed_fn,
        reports_path=reports_path,
    ):
        now = round(time.perf_counter() - t0, 3)
        etype = ev.get("event")
        if first_event_s is None and etype in ("parsed", "plan", "step", "disambiguate"):
            first_event_s = now
        if first_step_s is None and etype == "step":
            first_step_s = now
        if first_token_s is None and etype == "token":
            first_token_s = now
        if etype == "done":
            res = ev["data"]
    total_s = round(time.perf_counter() - t0, 3)
    if first_event_s is None:
        first_event_s = total_s
    return {
        "system": "S4_multihop",
        "status": res.get("status", "ok"),
        "error": None if res.get("status") in ("ok", "needs_disambiguation") else res.get("status"),
        "answer": res.get("answer") or "",
        "paper_ids": list(res.get("paper_ids") or []),
        "faithfulness_passed": bool(res.get("faithfulness_passed", False)),
        "faithfulness_errors": list(res.get("faithfulness_errors") or []),
        "first_event_s": first_event_s,
        "first_step_s": first_step_s,
        "first_token_s": first_token_s,
        "total_latency_s": total_s,
        "trace_summary": {
            "mode": res.get("mode"),
            "stopped_reason": res.get("stopped_reason"),
            "step_count": len(res.get("steps") or []),
            "plan_tools": [s.get("tool") for s in (res.get("plan") or [])],
        },
    }


def run_benchmark_systems(
    cfg: dict[str, Any],
    *,
    out_dir: Path,
    run_dir: Path,
    allow_overwrite: bool = False,
) -> Path:
    """Run S1–S4 sequentially on the configured benchmark split, enforcing run-once protection."""
    out_path = out_dir / "raw-outputs.jsonl"
    if out_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"{out_path} already exists; refusing to overwrite frozen benchmark run-once outputs. "
            "Pass --allow-overwrite only if explicitly authorized."
        )

    questions = load_benchmark_questions(cfg)
    rag_cfg = yaml.safe_load(Path(cfg["rag_config_path"]).read_text(encoding="utf-8"))
    sg_cfg = rag_cfg.get("share_growth") or {}

    graph_data = json.loads(Path(cfg["graph"]["path"]).read_text(encoding="utf-8"))
    paper_titles = {n["id"]: n.get("name", "") for n in graph_data.get("nodes", []) if n.get("label") == "Paper"}

    from sentence_transformers import SentenceTransformer

    st_model = SentenceTransformer(cfg["embeddings"]["model_name"], device="cpu")
    embed_fn = lambda text: st_model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]

    backend = Neo4jToolBackend()
    valid_llm_keys = {f.name for f in dataclass_fields(LLMConfig)}
    llm_cfg_dict = {k: v for k, v in cfg["llm"].items() if k in valid_llm_keys}
    llm = LLMClient(LLMConfig.from_mapping(llm_cfg_dict))
    vstore = SQLiteVectorStore(Path(cfg["vectors_sqlite_path"]))
    toolset = RAGToolset(
        backend,
        analysis_dir=Path(cfg["analysis_dir"]),
        rag_dir=Path(cfg["rag_dir"]),
        min_post_total_papers=int(sg_cfg.get("min_post_total_papers", 10)),
        min_post_subject_papers=int(sg_cfg.get("min_post_subject_papers", 2)),
    )

    records: list[dict[str, Any]] = []
    try:
        for q in questions:
            qid = q["question_id"]
            qtext = q["text"]
            hops = str(q["hops"])
            s1 = _run_s1(qtext, llm=llm, cfg=cfg)
            s2 = _run_s2(qtext, llm=llm, vector_store=vstore, embed_fn=embed_fn, paper_titles=paper_titles, cfg=cfg)
            s3 = _run_s3(qtext, hops, toolset=toolset, llm=llm, vector_store=vstore, embed_fn=embed_fn, cfg=cfg)
            s4 = _run_s4(qtext, toolset=toolset, llm=llm, vector_store=vstore, embed_fn=embed_fn, cfg=cfg)
            for payload in (s1, s2, s3, s4):
                records.append({
                    "question_id": qid,
                    "hops": hops,
                    "answer_type": q["answer_type"],
                    "judged": q["judged"],
                    **payload,
                })
    finally:
        backend.close()
        llm.close()

    _write_jsonl(out_path, records)
    run_meta = {
        "protocol_version": cfg["protocol_version"],
        "code_commit": cfg["code_commit"],
        "split": cfg["benchmark"]["split"],
        "question_count": len(questions),
        "record_count": len(records),
        "raw_outputs_sha256": _sha256_file(out_path),
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run-systems-meta.json").write_text(json.dumps(run_meta, indent=2) + "\n", encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Unified Text-to-Graph-ID Entity Resolver & Factual Scoring
# ---------------------------------------------------------------------------


def build_entity_catalog(graph_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build deterministic normalized-name and alias catalog for unified entity resolution."""
    catalog: list[dict[str, Any]] = []
    for n in graph_nodes:
        nid = str(n.get("id") or "")
        label = str(n.get("label") or "")
        name = str(n.get("name") or "")
        if not nid or not name or label == "Paper":
            continue
        aliases: list[str] = [name]
        props = n.get("properties") or {}
        if isinstance(props.get("key"), str) and props["key"].strip():
            aliases.append(props["key"].strip())
        # Parenthetical alias/acronym e.g. "Large Language Models (LLMs)"
        m = re.match(r"^(.*?)\s*\(([^()]{2,24})\)\s*$", name)
        if m:
            base, paren = m.group(1).strip(), m.group(2).strip()
            if base:
                aliases.append(base)
            if paren:
                aliases.append(paren)

        norm_aliases: list[str] = []
        seen_norms: set[str] = set()
        for a in aliases:
            na = _norm_text(a)
            if na and na not in seen_norms:
                seen_norms.add(na)
                norm_aliases.append(na)
        catalog.append({
            "id": nid,
            "label": label,
            "name": name,
            "aliases": aliases,
            "norm_aliases": norm_aliases,
        })
    return catalog


def _extract_answer_spans(answer_text: str) -> list[str]:
    """Extract candidate entity phrases identically from any system's answer text."""
    stripped = _PAPER_ID_RE.sub(" ", answer_text)
    stripped = _ANY_GRAPH_ID_RE.sub(" ", stripped)
    spans = list(_extract_candidate_entities(stripped))
    seen = {_norm_text(s) for s in spans}
    for line in stripped.splitlines():
        m = re.match(r"^\s*(?:[-*]|\d+\.)\s+([^\n:;(]{2,90})", line)
        if m:
            raw = m.group(1).replace("**", "").strip(" \t.,;:!?\"'")
            key = _norm_text(raw)
            if key and key not in seen:
                seen.add(key)
                spans.append(raw)
    return spans


class UnifiedEntityResolver:
    """Resolve entities from free-text answers identically across S1–S4."""

    def __init__(
        self,
        catalog: list[dict[str, Any]],
        *,
        embed_fn: Callable[[str], np.ndarray] | None = None,
        embedding_threshold: float = 0.80,
    ) -> None:
        self.catalog = catalog
        self.by_id = {c["id"]: c for c in catalog}
        self.embed_fn = embed_fn
        self.threshold = float(embedding_threshold)
        self._label_index: dict[str, tuple[list[dict[str, Any]], np.ndarray]] = {}
        self._alias_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in catalog:
            for na in item["norm_aliases"]:
                self._alias_map[na].append(item)
        for na in self._alias_map:
            self._alias_map[na].sort(key=lambda item: item["id"])

    def _get_label_matrix(self, target_labels: frozenset[str]) -> tuple[list[dict[str, Any]], np.ndarray]:
        key = "|".join(sorted(target_labels))
        if key not in self._label_index:
            subset = sorted(
                [c for c in self.catalog if not target_labels or c["label"] in target_labels],
                key=lambda c: c["id"],
            )
            if subset and self.embed_fn is not None:
                mat = np.vstack([self.embed_fn(c["name"]) for c in subset]).astype(np.float32)
                norms = np.linalg.norm(mat, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                mat = mat / norms
            else:
                mat = np.zeros((0, 384), dtype=np.float32)
            self._label_index[key] = (subset, mat)
        return self._label_index[key]

    def resolve(
        self,
        answer_text: str,
        *,
        target_labels: set[str] | None = None,
    ) -> list[str]:
        """Return ordered unique graph IDs resolved from ``answer_text``."""
        labels_fset = frozenset(target_labels or ())
        resolved: list[str] = []
        seen: set[str] = set()

        def _accept(item: dict[str, Any]) -> None:
            if labels_fset and item["label"] not in labels_fset:
                return
            if item["id"] not in seen:
                seen.add(item["id"])
                resolved.append(item["id"])

        # Step 1: exact graph ID tokens present in answer_text
        for gid in _ANY_GRAPH_ID_RE.findall(answer_text):
            if gid in self.by_id:
                _accept(self.by_id[gid])

        # Step 2: exact normalized alias / surface match against normalized answer text
        cleaned_text = _PAPER_ID_RE.sub(" ", answer_text)
        cleaned_text = _ANY_GRAPH_ID_RE.sub(" ", cleaned_text)
        ans_norm = f" {_norm_text(cleaned_text)} "
        spans = _extract_answer_spans(answer_text)
        span_norms = {_norm_text(s) for s in spans if _norm_text(s)}

        matched_norms: set[str] = set()
        for sn in sorted(span_norms):
            for item in self._alias_map.get(sn, ()):
                _accept(item)
                matched_norms.add(sn)

        subset_catalog = sorted(
            [c for c in self.catalog if not labels_fset or c["label"] in labels_fset],
            key=lambda c: c["id"],
        )
        for item in subset_catalog:
            if item["id"] in seen:
                continue
            for na in item["norm_aliases"]:
                if len(na) >= 4 and f" {na} " in ans_norm:
                    _accept(item)
                    matched_norms.add(na)
                    break

        # Step 3: embedding cosine fallback on unresolved candidate spans
        if self.embed_fn is not None:
            unresolved_spans = [s for s in spans if _norm_text(s) and _norm_text(s) not in matched_norms]
            if unresolved_spans:
                subset, mat = self._get_label_matrix(labels_fset)
                if subset and len(mat):
                    for sp in unresolved_spans:
                        vec = np.asarray(self.embed_fn(sp), dtype=np.float32)
                        nrm = float(np.linalg.norm(vec))
                        if nrm > 0:
                            vec = vec / nrm
                        scores = mat @ vec
                        best_idx = int(np.argmax(scores))
                        if float(scores[best_idx]) >= self.threshold:
                            _accept(subset[best_idx])

        return resolved


def set_f1(pred_ids: set[str], ref_ids: set[str]) -> tuple[float, float, float]:
    """Return (f1, precision, recall) for entity sets."""
    if not pred_ids and not ref_ids:
        return 1.0, 1.0, 1.0
    if not pred_ids or not ref_ids:
        return 0.0, 0.0, 0.0
    tp = len(pred_ids & ref_ids)
    prec = tp / len(pred_ids)
    rec = tp / len(ref_ids)
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
    return f1, prec, rec


def seeded_bootstrap_ci(
    values: list[float],
    *,
    confidence: float = 0.95,
    n_resamples: int = 2000,
    seed: int = 20261125,
) -> tuple[float, float]:
    """Deterministic percentile bootstrap CI for the mean of ``values``."""
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return float(values[0]), float(values[0])
    rng = random.Random(seed)
    n = len(values)
    means = sorted(
        sum(values[rng.randrange(n)] for _ in range(n)) / n
        for _ in range(n_resamples)
    )
    alpha = (1.0 - confidence) / 2.0
    lo_idx = max(0, int(alpha * n_resamples))
    hi_idx = min(n_resamples - 1, int((1.0 - alpha) * n_resamples))
    return round(means[lo_idx], 4), round(means[hi_idx], 4)


def _infer_target_labels(ref_row: dict[str, Any], id_to_label: dict[str, str]) -> set[str]:
    ref_ans = ref_row.get("reference_answer")
    if not isinstance(ref_ans, list):
        return set()
    labels: set[str] = set()
    for item in ref_ans:
        gid = str(item.get("id") or "")
        if gid in id_to_label:
            labels.add(id_to_label[gid])
        else:
            prefix = gid.split(":", 1)[0].capitalize()
            if prefix:
                labels.add(prefix)
    return labels


def _score_numeric_exact(answer_text: str, target: int, *, abs_tol: int = 0) -> float:
    nums = _extract_answer_numbers(answer_text)
    for v in nums:
        if abs(v - float(target)) <= abs_tol:
            return 1.0
    return 0.0


def score_factual_results(
    cfg: dict[str, Any],
    *,
    out_dir: Path,
    resolver: UnifiedEntityResolver | None = None,
) -> dict[str, Any]:
    """Score all factual test outputs using the unified entity resolver and numeric exact-match."""
    refs = {r["question_id"]: r for r in load_benchmark_questions(cfg)}
    raw_rows = _load_jsonl(out_dir / "raw-outputs.jsonl")

    if resolver is None:
        graph_data = json.loads(Path(cfg["graph"]["path"]).read_text(encoding="utf-8"))
        catalog = build_entity_catalog(graph_data.get("nodes", []))
        from sentence_transformers import SentenceTransformer

        st_model = SentenceTransformer(cfg["embeddings"]["model_name"], device="cpu")
        embed_fn = lambda text: st_model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]
        thresh = float(cfg["factual_scoring"]["unified_entity_resolver"].get("embedding_threshold", 0.80))
        resolver = UnifiedEntityResolver(catalog, embed_fn=embed_fn, embedding_threshold=thresh)

    id_to_label = {cid: c["label"] for cid, c in resolver.by_id.items()}
    abs_tol = int(cfg["factual_scoring"]["numeric_exact_match"].get("abs_tol", 0))
    bs_seed = int(cfg["factual_scoring"]["intervals"].get("bootstrap_seed", 20261125))
    bs_n = int(cfg["factual_scoring"]["intervals"].get("bootstrap_resamples", 2000))

    per_item: list[dict[str, Any]] = []
    for rec in raw_rows:
        qid = rec["question_id"]
        ref = refs[qid]
        hops = str(ref["hops"])
        judged = ref["judged"]
        ans = rec.get("answer") or ""
        sys_name = rec["system"]

        item_score: float | None = None
        prec = rec_val = None
        resolved_ids: list[str] = []
        ref_ids: list[str] = []

        if judged == "exact":
            target = int(ref["reference_answer"])
            item_score = _score_numeric_exact(ans, target, abs_tol=abs_tol)
        elif judged == "set_f1":
            target_labels = _infer_target_labels(ref, id_to_label)
            resolved_ids = resolver.resolve(ans, target_labels=target_labels)
            top_k = len(ref["reference_answer"]) if ref.get("answer_type") == "ranked_list" else None
            pred_slice = set(resolved_ids[:top_k] if top_k else resolved_ids)
            ref_id_set = {str(x["id"]) for x in ref["reference_answer"]}
            ref_ids = sorted(ref_id_set)
            item_score, prec, rec_val = set_f1(pred_slice, ref_id_set)

        per_item.append({
            "question_id": qid,
            "system": sys_name,
            "hops": hops,
            "answer_type": ref["answer_type"],
            "judged": judged,
            "score": round(item_score, 4) if item_score is not None else None,
            "precision": round(prec, 4) if prec is not None else None,
            "recall": round(rec_val, 4) if rec_val is not None else None,
            "resolved_ids": resolved_ids,
            "reference_ids": ref_ids,
            "faithfulness_passed": rec.get("faithfulness_passed"),
            "first_event_s": rec.get("first_event_s"),
            "first_step_s": rec.get("first_step_s"),
            "total_latency_s": rec.get("total_latency_s"),
            "cited_paper_count": len(rec.get("paper_ids") or []),
        })

    summary: dict[str, dict[str, Any]] = {}
    for sys_name in SYSTEM_ORDER:
        sys_rows = [x for x in per_item if x["system"] == sys_name]
        by_hop: dict[str, dict[str, Any]] = {}
        for h in ("1", "2", "3", "factual_overall", "global"):
            if h == "factual_overall":
                sub = [x for x in sys_rows if x["hops"] in ("1", "2", "3") and x["score"] is not None]
            elif h == "global":
                sub = [x for x in sys_rows if x["hops"] == "global"]
            else:
                sub = [x for x in sys_rows if x["hops"] == h and x["score"] is not None]

            scores = [float(x["score"]) for x in sub if x["score"] is not None]
            lo, hi = seeded_bootstrap_ci(scores, n_resamples=bs_n, seed=bs_seed) if scores else (0.0, 0.0)
            faith_sub = [x for x in (sys_rows if h == "factual_overall" else [r for r in sys_rows if r["hops"] == h]) if x["faithfulness_passed"] is not None]
            faith_n = len(faith_sub)
            faith_ok = sum(1 for x in faith_sub if x["faithfulness_passed"])
            faith_ci = precision_interval(faith_ok, faith_n) if faith_n else None
            lat_src = [r for r in sys_rows if (h == "factual_overall" and r["hops"] in ("1", "2", "3")) or r["hops"] == h]
            lat_vals = [float(r["total_latency_s"]) for r in lat_src if r.get("total_latency_s") is not None]
            fe_vals = [float(r["first_event_s"]) for r in lat_src if r.get("first_event_s") is not None]
            by_hop[h] = {
                "count": len(sub) if h != "global" else len(lat_src),
                "mean_score": round(sum(scores) / len(scores), 4) if scores else None,
                "bootstrap_95_ci": [lo, hi] if scores else None,
                "faithfulness_passed": faith_ok if faith_n else None,
                "faithfulness_total": faith_n if faith_n else None,
                "faithfulness_rate": round(faith_ok / faith_n, 4) if faith_n else None,
                "faithfulness_wilson_95": (
                    [round(faith_ci["wilson_lower"], 4), round(faith_ci["wilson_upper"], 4)]
                    if faith_ci is not None
                    else None
                ),
                "mean_first_event_s": round(sum(fe_vals) / len(fe_vals), 3) if fe_vals else None,
                "mean_latency_s": round(sum(lat_vals) / len(lat_vals), 3) if lat_vals else None,
            }
        # Overall faithfulness across all 69 evaluated items where trace exists
        all_faith = [x for x in sys_rows if x["faithfulness_passed"] is not None]
        all_f_ok = sum(1 for x in all_faith if x["faithfulness_passed"])
        all_f_ci = precision_interval(all_f_ok, len(all_faith)) if all_faith else None
        summary[sys_name] = {
            "by_hop": by_hop,
            "overall_faithfulness": {
                "passed": all_f_ok if all_faith else None,
                "total": len(all_faith) if all_faith else None,
                "rate": round(all_f_ok / len(all_faith), 4) if all_faith else None,
                "wilson_95_ci": (
                    [round(all_f_ci["wilson_lower"], 4), round(all_f_ci["wilson_upper"], 4)]
                    if all_f_ci is not None
                    else None
                ),
                "status": "not_applicable" if not all_faith else "evaluated",
            },
        }

    payload = {
        "protocol_version": cfg["protocol_version"],
        "scored_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "systems": summary,
        "items": per_item,
    }
    (out_dir / "factual-scores.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


# ---------------------------------------------------------------------------
# Phase 2 Step 3: Deterministic Citation Validity & Blind Global Pairwise Prep
# ---------------------------------------------------------------------------


def extract_citation_pairs(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract (question_id, system, claim, paper_id) pairs from answers."""
    pairs: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for row in raw_rows:
        ans = row.get("answer") or ""
        qid = row["question_id"]
        sys_name = row["system"]
        for seg in _SENTENCE_SPLIT_RE.split(ans):
            claim = seg.strip()
            if not claim:
                continue
            for pid in _PAPER_ID_RE.findall(claim):
                key = (sys_name, qid, pid, claim)
                if key in seen:
                    continue
                seen.add(key)
                pairs.append({
                    "system": sys_name,
                    "question_id": qid,
                    "paper_id": pid,
                    "claim": claim,
                })
    return pairs


def sample_citation_pairs(
    pairs: list[dict[str, Any]],
    *,
    max_per_system: int = 25,
    seed: int = 20261125,
) -> list[dict[str, Any]]:
    """Stratified round-robin across questions using deterministic SHA-256 rank."""
    sampled: list[dict[str, Any]] = []
    for sys_name in SYSTEM_ORDER:
        sys_pairs = [p for p in pairs if p["system"] == sys_name]
        by_q: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for p in sys_pairs:
            by_q[p["question_id"]].append(p)
        for qid in by_q:
            by_q[qid].sort(
                key=lambda x: hashlib.sha256(f"{seed}\0{sys_name}\0{qid}\0{x['paper_id']}\0{x['claim']}".encode("utf-8")).digest()
            )
        q_order = sorted(
            by_q.keys(),
            key=lambda qid: hashlib.sha256(f"{seed}\0q\0{sys_name}\0{qid}".encode("utf-8")).digest(),
        )
        chosen: list[dict[str, Any]] = []
        depth = 0
        while len(chosen) < max_per_system:
            added_this_round = False
            for qid in q_order:
                if depth < len(by_q[qid]):
                    chosen.append(by_q[qid][depth])
                    added_this_round = True
                    if len(chosen) >= max_per_system:
                        break
            if not added_this_round:
                break
            depth += 1
        for idx, item in enumerate(chosen, start=1):
            sampled.append({
                "sample_id": f"cit-{sys_name}-{idx:02d}",
                **item,
            })
    return sampled


def load_works_metadata(works_path: Path, target_paper_ids: set[str]) -> dict[str, dict[str, Any]]:
    """Load title, abstract, year, doi ONLY for requested paper_ids."""
    out: dict[str, dict[str, Any]] = {}
    if not target_paper_ids or not works_path.exists():
        return out
    with works_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            obj = json.loads(line)
            pid = obj.get("paper_id")
            if pid in target_paper_ids:
                oa = obj.get("openalex") or {}
                out[pid] = {
                    "paper_id": pid,
                    "title": oa.get("title") or "",
                    "year": oa.get("publication_year") or obj.get("year"),
                    "doi": obj.get("doi") or oa.get("doi") or "",
                    "abstract": oa.get("abstract") or "",
                }
                if len(out) == len(target_paper_ids):
                    break
    return out


def prepare_judging_packets(
    cfg: dict[str, Any],
    *,
    out_dir: Path,
    run_dir: Path,
) -> dict[str, Any]:
    """Generate citation validity and blind global pairwise packets and freeze manifests."""
    raw_rows = _load_jsonl(out_dir / "raw-outputs.jsonl")
    refs = {r["question_id"]: r for r in load_benchmark_questions(cfg)}
    run_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Citation validity sample
    cit_cfg = cfg["citation_validity"]
    cit_seed = int(cit_cfg["sample_seed"])
    cit_max = int(cit_cfg["max_pairs_per_system"])
    all_pairs = extract_citation_pairs(raw_rows)
    sampled_pairs = sample_citation_pairs(all_pairs, max_per_system=cit_max, seed=cit_seed)
    paper_meta = load_works_metadata(Path(cfg["works_jsonl_path"]), {p["paper_id"] for p in sampled_pairs})

    cit_packet: list[dict[str, Any]] = []
    cit_manifest_items: list[dict[str, Any]] = []
    for p in sampled_pairs:
        meta = paper_meta.get(p["paper_id"], {})
        cit_packet.append({
            "sample_id": p["sample_id"],
            "question_id": p["question_id"],
            "question_text": refs[p["question_id"]]["text"],
            "system": p["system"],
            "paper_id": p["paper_id"],
            "claim": p["claim"],
            "paper_title": meta.get("title", ""),
            "paper_year": meta.get("year"),
            "paper_abstract": meta.get("abstract", ""),
            "in_works_corpus": p["paper_id"] in paper_meta,
        })
        cit_manifest_items.append({
            "sample_id": p["sample_id"],
            "question_id": p["question_id"],
            "system": p["system"],
            "paper_id": p["paper_id"],
            "paper_title": meta.get("title", ""),
            "has_abstract": bool(meta.get("abstract")),
            "in_works_corpus": p["paper_id"] in paper_meta,
        })

    cit_packet_path = run_dir / "citation-packet.jsonl"
    _write_jsonl(cit_packet_path, cit_packet)
    cit_manifest = {
        "ai_assessed": True,
        "sample_seed": cit_seed,
        "max_pairs_per_system": cit_max,
        "total_extracted_pairs_by_system": {
            s: sum(1 for p in all_pairs if p["system"] == s) for s in SYSTEM_ORDER
        },
        "sampled_count_by_system": {
            s: sum(1 for p in cit_manifest_items if p["system"] == s) for s in SYSTEM_ORDER
        },
        "packet_sha256": _sha256_file(cit_packet_path),
        "publish_packet_abstracts": False,
        "items": cit_manifest_items,
    }
    (out_dir / "citation-sample-manifest.json").write_text(json.dumps(cit_manifest, indent=2) + "\n", encoding="utf-8")

    # 2. Blind global pairwise AB+BA packet
    pw_cfg = cfg["global_pairwise"]
    pw_seed = int(pw_cfg["seed"])
    by_q_sys: dict[tuple[str, str], dict[str, Any]] = {
        (r["question_id"], r["system"]): r
        for r in raw_rows
        if str(r["hops"]) == "global"
    }
    global_qids = sorted(qid for qid, ref in refs.items() if str(ref["hops"]) == "global")
    rng = random.Random(pw_seed)

    raw_items: list[dict[str, Any]] = []
    for qid in global_qids:
        qtext = refs[qid]["text"]
        for pair_idx, (s1, s2) in enumerate(combinations(SYSTEM_ORDER, 2)):
            for order_tag, (sys_a, sys_b) in (("AB", (s1, s2)), ("BA", (s2, s1))):
                ans_a = (by_q_sys.get((qid, sys_a)) or {}).get("answer") or ""
                ans_b = (by_q_sys.get((qid, sys_b)) or {}).get("answer") or ""
                raw_items.append({
                    "question_id": qid,
                    "question_text": qtext,
                    "pair_key": f"{qid}__{s1}__vs__{s2}",
                    "order": order_tag,
                    "sys_a": sys_a,
                    "sys_b": sys_b,
                    "answer_a": ans_a,
                    "answer_b": ans_b,
                })

    rng.shuffle(raw_items)
    pw_packet: list[dict[str, Any]] = []
    pw_key: list[dict[str, Any]] = []
    pw_manifest_items: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_items, start=1):
        pid_str = f"pw-{idx:03d}"
        pw_packet.append({
            "pair_item_id": pid_str,
            "question_id": item["question_id"],
            "question_text": item["question_text"],
            "answer_a": item["answer_a"],
            "answer_b": item["answer_b"],
        })
        pw_key.append({
            "pair_item_id": pid_str,
            "question_id": item["question_id"],
            "pair_key": item["pair_key"],
            "order": item["order"],
            "sys_a": item["sys_a"],
            "sys_b": item["sys_b"],
        })
        pw_manifest_items.append({
            "pair_item_id": pid_str,
            "question_id": item["question_id"],
            "pair_key_sha256": _sha256_text(f"{pid_str}:{item['pair_key']}:{item['order']}"),
        })

    pw_packet_path = run_dir / "pairwise-packet.jsonl"
    _write_jsonl(pw_packet_path, pw_packet)
    _write_jsonl(run_dir / "pairwise-key.jsonl", pw_key)
    pw_manifest = {
        "ai_assessed": True,
        "seed": pw_seed,
        "global_question_count": len(global_qids),
        "total_blind_items": len(pw_packet),
        "packet_sha256": _sha256_file(pw_packet_path),
        "items": pw_manifest_items,
    }
    (out_dir / "pairwise-manifest.json").write_text(json.dumps(pw_manifest, indent=2) + "\n", encoding="utf-8")
    return {"citation_samples": len(cit_packet), "pairwise_items": len(pw_packet)}


# ---------------------------------------------------------------------------
# Phase 2 Step 4: Adjudication & Final Results Aggregation
# ---------------------------------------------------------------------------


def adjudicate_citation_judgments(
    manifest: dict[str, Any],
    a_rows: dict[str, str],
    b_rows: dict[str, str],
    c_rows: dict[str, str],
) -> dict[str, Any]:
    """Resolve citation validity verdicts ('supported'|'unsupported'|'unclear') across A/B/C."""
    resolved_items: list[dict[str, Any]] = []
    ab_pairs: list[tuple[str, str]] = []
    disagreements = 0
    for item in manifest["items"]:
        sid = item["sample_id"]
        if not item.get("in_works_corpus", True):
            verdict = "unsupported"
            va = vb = vc = "unsupported"
        else:
            va = a_rows[sid]
            vb = b_rows[sid]
            ab_pairs.append((va, vb))
            if va == vb:
                verdict = va
                vc = None
            else:
                disagreements += 1
                vc = c_rows[sid]
                verdict = vc
        resolved_items.append({
            **item,
            "verdict_a": va,
            "verdict_b": vb,
            "verdict_c": vc,
            "final_verdict": verdict,
        })

    by_system: dict[str, Any] = {}
    for sys_name in SYSTEM_ORDER:
        sub = [x for x in resolved_items if x["system"] == sys_name]
        if not sub:
            by_system[sys_name] = {
                "supported": 0,
                "total": 0,
                "rate": None,
                "wilson_95_ci": None,
                "status": "zero_citations_emitted",
            }
            continue
        sup = sum(1 for x in sub if x["final_verdict"] == "supported")
        ci = precision_interval(sup, len(sub))
        by_system[sys_name] = {
            "supported": sup,
            "total": len(sub),
            "rate": round(ci["precision"], 4),
            "wilson_95_ci": [round(ci["wilson_lower"], 4), round(ci["wilson_upper"], 4)],
            "status": "evaluated",
        }
    kappa = cohens_kappa(ab_pairs)
    return {
        "ai_assessed": True,
        "by_system": by_system,
        "disagreements": disagreements,
        "cohens_kappa_ab": round(kappa, 4) if kappa is not None else None,
        "items": resolved_items,
    }


def _winner_to_system(label: str, sys_a: str, sys_b: str) -> str:
    low = label.strip().upper()
    if low == "A":
        return sys_a
    if low == "B":
        return sys_b
    return "tie"


def adjudicate_pairwise_judgments(
    key_rows: list[dict[str, Any]],
    a_rows: dict[str, str],
    b_rows: dict[str, str],
    c_rows: dict[str, str],
) -> dict[str, Any]:
    """Adjudicate AB+BA pairwise judgments into overall and position-consistent win rates."""
    ab_sys_pairs: list[tuple[str, str]] = []
    resolved_items: list[dict[str, Any]] = []
    disagreements = 0

    for k in key_rows:
        pid = k["pair_item_id"]
        sys_a, sys_b = k["sys_a"], k["sys_b"]
        wa = _winner_to_system(a_rows[pid], sys_a, sys_b)
        wb = _winner_to_system(b_rows[pid], sys_a, sys_b)
        ab_sys_pairs.append((wa, wb))
        if wa == wb:
            final_w = wa
            wc = None
        else:
            disagreements += 1
            wc = _winner_to_system(c_rows[pid], sys_a, sys_b)
            final_w = wc
        resolved_items.append({
            **k,
            "winner_a": wa,
            "winner_b": wb,
            "winner_c": wc,
            "final_winner": final_w,
        })

    # Per-system overall item wins (out of 90 appearances: 15 questions * 3 opponents * 2 orders)
    by_system: dict[str, Any] = {}
    for sys_name in SYSTEM_ORDER:
        appearances = [x for x in resolved_items if sys_name in (x["sys_a"], x["sys_b"])]
        wins = sum(1 for x in appearances if x["final_winner"] == sys_name)
        ties = sum(1 for x in appearances if x["final_winner"] == "tie")
        losses = len(appearances) - wins - ties
        by_system[sys_name] = {
            "wins": wins,
            "ties": ties,
            "losses": losses,
            "total_appearances": len(appearances),
            "win_rate": round(wins / len(appearances), 4) if appearances else 0.0,
            "non_loss_rate": round((wins + ties) / len(appearances), 4) if appearances else 0.0,
        }

    # Position consistency across AB vs BA for each unordered (question_id, s1, s2)
    by_pair_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in resolved_items:
        by_pair_key[x["pair_key"]].append(x)

    consistent_wins: dict[str, int] = {s: 0 for s in SYSTEM_ORDER}
    consistent_ties = 0
    position_inconsistent = 0
    for items in by_pair_key.values():
        if len(items) != 2:
            continue
        w1, w2 = items[0]["final_winner"], items[1]["final_winner"]
        if w1 == w2:
            if w1 == "tie":
                consistent_ties += 1
            else:
                consistent_wins[w1] += 1
        else:
            position_inconsistent += 1

    # Head-to-head matrix (AB+BA resolved wins + consistent pairs)
    head_to_head: dict[str, dict[str, Any]] = {}
    for s1, s2 in combinations(SYSTEM_ORDER, 2):
        sub = [x for x in resolved_items if {x["sys_a"], x["sys_b"]} == {s1, s2}]
        w_s1 = sum(1 for x in sub if x["final_winner"] == s1)
        w_s2 = sum(1 for x in sub if x["final_winner"] == s2)
        ties = sum(1 for x in sub if x["final_winner"] == "tie")
        pk_sub = [by_pair_key[k] for k in by_pair_key if f"__{s1}__vs__{s2}" in k]
        cw_s1 = sum(1 for pair in pk_sub if len(pair) == 2 and pair[0]["final_winner"] == pair[1]["final_winner"] == s1)
        cw_s2 = sum(1 for pair in pk_sub if len(pair) == 2 and pair[0]["final_winner"] == pair[1]["final_winner"] == s2)
        inconsistent = sum(1 for pair in pk_sub if len(pair) == 2 and pair[0]["final_winner"] != pair[1]["final_winner"])
        head_to_head[f"{s1}__vs__{s2}"] = {
            f"{s1}_wins": w_s1,
            f"{s2}_wins": w_s2,
            "ties": ties,
            f"{s1}_consistent_pairs": cw_s1,
            f"{s2}_consistent_pairs": cw_s2,
            "position_inconsistent_pairs": inconsistent,
        }

    kappa = cohens_kappa(ab_sys_pairs)
    total_unordered = len(by_pair_key)
    for sys_name in SYSTEM_ORDER:
        by_system[sys_name]["position_consistent_wins"] = consistent_wins[sys_name]
        by_system[sys_name]["position_consistent_win_rate"] = (
            round(consistent_wins[sys_name] / (total_unordered / 2), 4) if total_unordered else 0.0
        )

    return {
        "ai_assessed": True,
        "total_blind_items": len(resolved_items),
        "total_unordered_pairs": total_unordered,
        "consistent_ties": consistent_ties,
        "position_inconsistent_pairs": position_inconsistent,
        "disagreements_ab": disagreements,
        "cohens_kappa_ab": round(kappa, 4) if kappa is not None else None,
        "by_system": by_system,
        "head_to_head": head_to_head,
    }


def _load_verdict_map(path: Path, id_field: str, val_field: str) -> dict[str, str]:
    return {row[id_field]: str(row[val_field]) for row in _load_jsonl(path)}


def aggregate_benchmark_results(
    cfg: dict[str, Any],
    *,
    out_dir: Path,
    run_dir: Path,
) -> dict[str, Any]:
    """Combine factual scores, citation validity, and pairwise judging into results.{json,md}."""
    factual = json.loads((out_dir / "factual-scores.json").read_text(encoding="utf-8"))
    cit_manifest = json.loads((out_dir / "citation-sample-manifest.json").read_text(encoding="utf-8"))
    cit_res = adjudicate_citation_judgments(
        cit_manifest,
        _load_verdict_map(run_dir / "citation-judgments-a.jsonl", "sample_id", "verdict"),
        _load_verdict_map(run_dir / "citation-judgments-b.jsonl", "sample_id", "verdict"),
        _load_verdict_map(run_dir / "citation-judgments-c.jsonl", "sample_id", "verdict") if (run_dir / "citation-judgments-c.jsonl").exists() else {},
    )

    pw_keys = _load_jsonl(run_dir / "pairwise-key.jsonl")
    pw_res = adjudicate_pairwise_judgments(
        pw_keys,
        _load_verdict_map(run_dir / "pairwise-judgments-a.jsonl", "pair_item_id", "winner"),
        _load_verdict_map(run_dir / "pairwise-judgments-b.jsonl", "pair_item_id", "winner"),
        _load_verdict_map(run_dir / "pairwise-judgments-c.jsonl", "pair_item_id", "winner") if (run_dir / "pairwise-judgments-c.jsonl").exists() else {},
    )

    results = {
        "protocol_version": cfg["protocol_version"],
        "code_commit": cfg["code_commit"],
        "graph_version": cfg["graph"]["graph_version"],
        "graph_sha256": cfg["graph"]["graph_sha256"],
        "llm": cfg["llm"]["model"],
        "llm_hf_revision": cfg["llm"]["revision"],
        "ai_assessed_disclosure": (
            "Citation validity and global pairwise comparisons are AI-assessed by isolated LLM "
            "evaluators (not independent human annotations or verified course accuracy). "
            "Wilson and bootstrap 95% intervals reflect sampling uncertainty only and exclude evaluator error."
        ),
        "evaluator_independence_disclosure": (
            "Evaluator A: fresh isolated claude-opus-5-5. Evaluator B: fresh isolated codex exec "
            "(gpt-6.2-sol via 9router). Adjudicator C: separate fresh isolated codex exec session "
            "(gpt-6.2-sol via 9router, used because local gemini CLI 0.26.0 returned exit 41 unauthenticated). "
            "C differs in model family from A but shares B's model family and is therefore not independent of B."
        ),
        "coverage_and_extraction_caveats": (
            "Results are measured on the 69 kept benchmark test questions (11 dropped for empty/ambiguous references) "
            "over AAAI and IJCAI 2021-2025 main-track papers; affiliation coverage (73.71%) and historical topic "
            "precision (68.63%) bound completeness, and unified text entity resolution uses normalized aliases plus "
            "all-MiniLM-L6-v2 cosine >= 0.80."
        ),
        "factual": factual["systems"],
        "citation_validity_ai_assessed": {k: v for k, v in cit_res.items() if k != "items"},
        "global_pairwise_ai_assessed": pw_res,
    }
    (out_dir / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Test Benchmark Evaluation Results (qa-eval-v1)",
        "",
        f"- **Protocol**: `{cfg['protocol_version']}` (commit `{cfg['code_commit']}`)",
        f"- **Graph**: `{cfg['graph']['graph_version']}` (`{cfg['graph']['graph_sha256']}`)",
        f"- **Local LLM**: `{cfg['llm']['model']}` (`{cfg['llm']['hf_repo']}` rev `{cfg['llm']['revision']}`, temp `{cfg['llm']['temperature']}`, seed `{cfg['llm']['seed']}`, `enable_thinking={cfg['llm']['enable_thinking']}`)",
        "",
        "> [!IMPORTANT]",
        f"> **AI-assessed quality statement**: {results['ai_assessed_disclosure']}",
        f"> **Evaluator family & independence disclosure**: {results['evaluator_independence_disclosure']}",
        f"> **Coverage & extraction caveats**: {results['coverage_and_extraction_caveats']}",
        "",
        "## 1. Factual Accuracy by Hop Class (Unified Entity Resolver, Mean Score & 95% Bootstrap CI)",
        "",
        "| System | Hop 1 (14) | Hop 2 (22) | Hop 3 (18) | Overall Factual (54) | Mean Latency (Factual) |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for sys_name in SYSTEM_ORDER:
        bh = factual["systems"][sys_name]["by_hop"]
        def _fmt(h: str) -> str:
            entry = bh[h]
            ci = entry.get("bootstrap_95_ci") or [0.0, 0.0]
            return f"{entry['mean_score']:.4f} [{ci[0]:.4f}, {ci[1]:.4f}]"
        lines.append(
            f"| {sys_name} | {_fmt('1')} | {_fmt('2')} | {_fmt('3')} | {_fmt('factual_overall')} | {bh['factual_overall']['mean_latency_s']}s |"
        )

    lines.extend([
        "",
        "## 2. Automatic Faithfulness & AI-Assessed Citation Validity (95% Wilson CI)",
        "",
        "| System | Automatic Faithfulness (95% Wilson CI) | AI-Assessed Citation Validity (95% Wilson CI) |",
        "| --- | --- | --- |",
    ])
    for sys_name in SYSTEM_ORDER:
        f = factual["systems"][sys_name]["overall_faithfulness"]
        f_str = (
            "N/A (no retrieval trace)"
            if f["status"] == "not_applicable"
            else f"{f['passed']}/{f['total']} ({f['rate']:.4f} [{f['wilson_95_ci'][0]:.4f}, {f['wilson_95_ci'][1]:.4f}])"
        )
        c = cit_res["by_system"][sys_name]
        c_str = (
            "0 citations emitted"
            if c["total"] == 0
            else f"{c['supported']}/{c['total']} ({c['rate']:.4f} [{c['wilson_95_ci'][0]:.4f}, {c['wilson_95_ci'][1]:.4f}])"
        )
        lines.append(f"| {sys_name} | {f_str} | {c_str} |")

    lines.extend([
        "",
        f"Citation A–B Cohen's kappa (AI-assessed): `{cit_res['cohens_kappa_ab']}` (disagreements adjudicated by C: `{cit_res['disagreements']}`).",
        "",
        "## 3. AI-Assessed Global Pairwise Comparison (15 Global Questions, AB+BA = 180 Blind Items)",
        "",
        "| System | Wins / Ties / Losses (of 90) | Win Rate | Position-Consistent Wins (of 45 pairs) |",
        "| --- | --- | --- | --- |",
    ])
    for sys_name in SYSTEM_ORDER:
        ps = pw_res["by_system"][sys_name]
        lines.append(
            f"| {sys_name} | {ps['wins']} / {ps['ties']} / {ps['losses']} | {ps['win_rate']:.4f} | {ps['position_consistent_wins']} ({ps['position_consistent_win_rate']:.4f}) |"
        )
    lines.append("")
    lines.append(
        f"Global pairwise A–B Cohen's kappa (AI-assessed): `{pw_res['cohens_kappa_ab']}`; disagreements resolved by C: `{pw_res['disagreements_ab']}`; position-inconsistent pairs: `{pw_res['position_inconsistent_pairs']}` / `{pw_res['total_unordered_pairs']}`."
    )

    (out_dir / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Frozen QA benchmark evaluation CLI (qa-eval-v1).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("run-systems", "score-factual", "prepare-judging", "aggregate-results"):
        sp = sub.add_parser(name)
        sp.add_argument("--config", type=Path, default=Path("configs/qa-eval-v1.yaml"))
        sp.add_argument("--out-dir", type=Path, default=Path("reports/final-exam/qa-eval-v1"))
        sp.add_argument("--run-dir", type=Path, default=Path("reports/runs/WORK-2026-11-25-006/eval"))
        if name == "run-systems":
            sp.add_argument("--allow-overwrite", action="store_true")

    args = parser.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.cmd == "run-systems":
        p = run_benchmark_systems(cfg, out_dir=args.out_dir, run_dir=args.run_dir, allow_overwrite=args.allow_overwrite)
        print(json.dumps({"raw_outputs": str(p)}))
    elif args.cmd == "score-factual":
        res = score_factual_results(cfg, out_dir=args.out_dir)
        print(json.dumps({"scored_items": len(res["items"])}))
    elif args.cmd == "prepare-judging":
        print(json.dumps(prepare_judging_packets(cfg, out_dir=args.out_dir, run_dir=args.run_dir)))
    elif args.cmd == "aggregate-results":
        res = aggregate_benchmark_results(cfg, out_dir=args.out_dir, run_dir=args.run_dir)
        print(json.dumps({"results_systems": list(res["factual"].keys())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
