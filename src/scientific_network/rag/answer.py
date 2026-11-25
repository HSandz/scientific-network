"""Grounded answer synthesis, faithfulness verifier, and streaming orchestrator (spec §6.3 & §6.5)."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Callable, Iterator

import numpy as np

from scientific_network.rag.executor import execute_plan
from scientific_network.rag.llm import LLMClient, LLMError
from scientific_network.rag.planner import build_plan, link_entities, parse_question, route_mode
from scientific_network.rag.retrieval import global_search, local_search
from scientific_network.rag.sqlite_vectors import SQLiteVectorStore
from scientific_network.rag.tools import RAGToolset

_NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_:])-?\d+(?:\.\d+)?%?")
_PAPER_ID_RE = re.compile(r"paper:(?:aaai|ijcai):\d{4}:[A-Za-z0-9_.-]+")
_ENTITY_ID_RE = re.compile(r"\b(?:method|task|dataset|organization|researcher|topic|venue|research|N1|N2):[A-Za-z0-9_:-]+")


def _extract_allowed_numbers(obj: Any) -> set[float]:
    nums: set[float] = set()
    if isinstance(obj, bool):
        return nums
    if isinstance(obj, (int, float)):
        v = float(obj)
        nums.update({v, round(v, 1), round(v, 2), round(v, 3), round(v * 100.0, 1), round(v * 100.0, 2)})
        return nums
    if isinstance(obj, str):
        cleaned = _PAPER_ID_RE.sub(" ", obj)
        cleaned = _ENTITY_ID_RE.sub(" ", cleaned)
        for m in _NUMBER_RE.findall(cleaned):
            try:
                nums.add(float(m.rstrip("%")))
            except ValueError:
                continue
        return nums
    if isinstance(obj, list):
        for item in obj:
            nums |= _extract_allowed_numbers(item)
    elif isinstance(obj, dict):
        for v in obj.values():
            nums |= _extract_allowed_numbers(v)
    return nums


def _extract_answer_numbers(text: str) -> list[float]:
    cleaned = _PAPER_ID_RE.sub(" ", text)
    cleaned = _ENTITY_ID_RE.sub(" ", cleaned)
    # Ignore markdown ordered list prefixes ("1. ", "12. ") and hyphenated tokens (GPT-4, 3D)
    cleaned = re.sub(r"(?m)^\s*\d+\.\s+", " ", cleaned)
    cleaned = re.sub(r"\b[A-Za-z]+-\d+\b|\b\d+[Dd]\b", " ", cleaned)
    out = []
    for m in _NUMBER_RE.findall(cleaned):
        try:
            out.append(float(m.rstrip("%")))
        except ValueError:
            continue
    return out


def verify_answer_faithfulness(answer: str, trace_payload: Any, question: str) -> list[str]:
    """Check that every number and cited paper_id in the answer appears in the retrieved trace or question."""
    errors: list[str] = []
    allowed_nums = _extract_allowed_numbers(trace_payload) | _extract_allowed_numbers(question)
    for val in _extract_answer_numbers(answer):
        if any(abs(val - a) <= max(0.01, 0.005 * abs(a)) for a in allowed_nums):
            continue
        errors.append(f"number {val:g} not in trace")

    trace_text = json.dumps(trace_payload, ensure_ascii=False)
    for pid in set(_PAPER_ID_RE.findall(answer)):
        if pid not in trace_text:
            errors.append(f"cited paper {pid} not in trace")
    return errors


_ANSWER_SYS = (
    "Answer the user question concisely using ONLY the retrieved graph trace below. "
    "Rules:\n"
    "- Every number you state MUST appear verbatim in the trace.\n"
    "- Cite supporting papers using their exact IDs in brackets like [paper:...] when available in the trace.\n"
    "- If the trace stopped on an empty step, clearly state that no matching records were found rather than guessing."
)


def _compact_trace_for_prompt(trace_payload: Any) -> Any:
    """Keep all step summaries intact within the LLM prompt budget without truncating later steps."""
    if not isinstance(trace_payload, dict) or "steps" not in trace_payload:
        return trace_payload
    compacted_steps = []
    for st in trace_payload.get("steps") or []:
        rows = list(st.get("rows") or [])
        compacted_steps.append({
            "step": st.get("step"),
            "tool": st.get("tool"),
            "row_count": st.get("row_count", len(rows)),
            "note": st.get("note", ""),
            "rows": rows[:12],
            "paper_ids": list(st.get("paper_ids") or [])[:15],
        })
    return {"steps": compacted_steps}


def compose_grounded_answer(
    question: str,
    trace_payload: Any,
    llm: LLMClient,
    *,
    prompt_version: str = "rag-answer-v2",
) -> dict[str, Any]:
    """Compose an answer from the trace with automatic faithfulness check + 1 retry."""
    prompt_trace = _compact_trace_for_prompt(trace_payload)
    trace_json = json.dumps(prompt_trace, ensure_ascii=False)
    if len(trace_json) > 12000:
        trace_json = trace_json[:12000] + "...(truncated)"

    last_errs: list[str] = []
    for attempt in (0, 1):
        pv = prompt_version if attempt == 0 else f"{prompt_version}-retry"
        user_msg = f"Question: {question}\n\nTrace:\n{trace_json}"
        if attempt == 1:
            user_msg += (
                f"\n\nYour previous answer failed faithfulness checks ({'; '.join(last_errs)}). "
                "Rewrite using ONLY exact numbers and paper IDs present in the trace."
            )
        try:
            res = llm.complete(prompt_version=pv, system=_ANSWER_SYS, user=user_msg, max_tokens=600)
            ans = res.content.strip()
        except LLMError as exc:
            last_errs = [str(exc)]
            continue
        errs = verify_answer_faithfulness(ans, trace_payload, question)
        if not errs:
            return {
                "answer": ans,
                "faithfulness_passed": True,
                "faithfulness_errors": [],
                "attempts": attempt + 1,
                "ai_generated_label": "AI-generated from graph data",
            }
        last_errs = errs

    return {
        "answer": "Could not compose a faithful answer from the retrieved graph trace; inspect the step tables below.",
        "faithfulness_passed": False,
        "faithfulness_errors": last_errs,
        "attempts": 2,
        "ai_generated_label": "AI-generated from graph data",
    }


def run_ask(
    question: str,
    *,
    toolset: RAGToolset,
    llm: LLMClient,
    mode: str = "auto",
    resolved_overrides: dict[str, str] | None = None,
    vector_store: SQLiteVectorStore | None = None,
    embed_fn: Callable[[str], np.ndarray] | None = None,
    reports_path: Path = Path("reports/final-exam/rag-v1/community-reports.json"),
) -> dict[str, Any]:
    """Run parse -> link -> route -> plan/retrieve -> execute -> grounded answer."""
    parsed = parse_question(question, llm)
    link_res = link_entities(parsed, toolset, resolved_overrides=resolved_overrides)
    if link_res["needs_disambiguation"]:
        return {
            "status": "needs_disambiguation",
            "question": question,
            "parsed": parsed,
            "disambiguation": link_res["disambiguation"],
            "answer": "Multiple researchers match that name; please select the intended researcher.",
            "faithfulness_passed": True,
            "steps": [],
            "subgraph_nodes": [],
            "subgraph_edges": [],
            "paper_ids": [],
            "ai_generated_label": "AI-generated from graph data",
        }

    chosen_mode = route_mode(question, mode, parsed, link_res["linked"])
    if chosen_mode == "global":
        g_res = global_search(question, llm=llm, reports_path=reports_path, vector_store=vector_store, embed_fn=embed_fn)
        errs = verify_answer_faithfulness(g_res["answer"], g_res["points"], question)
        return {
            "status": "ok",
            "question": question,
            "mode": "global",
            "parsed": parsed,
            "linked": link_res["linked"],
            "plan": [],
            "steps": [{"step": 1, "tool": "community_report", "purpose": "global map-reduce", "empty": False,
                       "row_count": len(g_res["points"]), "rows": g_res["points"], "source_kind": "global_search",
                       "note": f"Synthesized over {len(g_res['reports_used'])} community reports.",
                       "paper_ids": g_res["paper_ids"], "evidence_ids": []}],
            "stopped_reason": None,
            "answer": g_res["answer"],
            "faithfulness_passed": len(errs) == 0,
            "faithfulness_errors": errs,
            "subgraph_nodes": [],
            "subgraph_edges": [],
            "paper_ids": g_res["paper_ids"],
            "ai_generated_label": "AI-generated from graph data",
        }

    if chosen_mode == "local" and vector_store is not None and embed_fn is not None:
        l_res = local_search(question, toolset=toolset, vector_store=vector_store, embed_fn=embed_fn)
        composed = compose_grounded_answer(question, l_res, llm, prompt_version="rag-local-answer-v1")
        return {
            "status": "ok",
            "question": question,
            "mode": "local",
            "parsed": parsed,
            "linked": link_res["linked"],
            "plan": [],
            "steps": [{"step": 1, "tool": "local_search", "purpose": "entity-centric neighborhood + chunks",
                       "empty": False, "row_count": len(l_res["paper_ids"]),
                       "rows": [{"section": s} for s in l_res["sections_used"]],
                       "source_kind": "local_search",
                       "note": f"Packed {len(l_res['sections_used'])} context sections.",
                       "paper_ids": l_res["paper_ids"], "evidence_ids": []}],
            "stopped_reason": None,
            "answer": composed["answer"],
            "faithfulness_passed": composed["faithfulness_passed"],
            "faithfulness_errors": composed["faithfulness_errors"],
            "subgraph_nodes": l_res["subgraph_nodes"],
            "subgraph_edges": l_res["subgraph_edges"],
            "paper_ids": l_res["paper_ids"],
            "ai_generated_label": "AI-generated from graph data",
        }

    plan = build_plan(question, parsed, link_res["linked"], llm)
    exec_res = execute_plan(plan, toolset)

    if exec_res["stopped_reason"] == "empty_step":
        step_no = exec_res["stopped_at_step"]
        st = exec_res["steps"][-1]
        answer_text = (
            f"Stopped at step {step_no} (`{st['tool']}`): no matching records were found in the graph "
            f"({st['note']})."
        )
        composed = {
            "answer": answer_text,
            "faithfulness_passed": True,
            "faithfulness_errors": [],
            "ai_generated_label": "AI-generated from graph data",
        }
    else:
        composed = compose_grounded_answer(
            question,
            {"steps": [{k: s[k] for k in ("step", "tool", "rows", "note", "paper_ids")} for s in exec_res["steps"]]},
            llm,
        )

    return {
        "status": "ok",
        "question": question,
        "mode": chosen_mode,
        "parsed": parsed,
        "linked": link_res["linked"],
        "plan": plan,
        "steps": exec_res["steps"],
        "stopped_reason": exec_res["stopped_reason"],
        "stopped_at_step": exec_res["stopped_at_step"],
        "answer": composed["answer"],
        "faithfulness_passed": composed["faithfulness_passed"],
        "faithfulness_errors": composed["faithfulness_errors"],
        "subgraph_nodes": exec_res["subgraph_nodes"],
        "subgraph_edges": exec_res["subgraph_edges"],
        "paper_ids": exec_res["paper_ids"],
        "ai_generated_label": composed["ai_generated_label"],
    }


def stream_ask(
    question: str,
    **kwargs,
) -> Iterator[dict[str, Any]]:
    """Yield SSE-friendly stage events (parse -> plan -> step -> subgraph -> token -> citations -> done)."""
    yield {"event": "stage", "data": {"stage": "parsing"}}
    result = run_ask(question, **kwargs)
    if result["status"] == "needs_disambiguation":
        yield {"event": "disambiguate", "data": result}
        yield {"event": "done", "data": result}
        return
    if result.get("plan"):
        yield {"event": "plan", "data": {"mode": result["mode"], "plan": result["plan"]}}
    for st in result.get("steps", []):
        yield {"event": "step", "data": st}
    yield {"event": "subgraph", "data": {"nodes": result["subgraph_nodes"], "edges": result["subgraph_edges"]}}
    # Stream answer in small word chunks for responsive UI updates
    words = result["answer"].split(" ")
    for i in range(0, len(words), 6):
        chunk = (" " if i > 0 else "") + " ".join(words[i:i + 6])
        yield {"event": "token", "data": {"text": chunk}}
    yield {"event": "citations", "data": {"paper_ids": result["paper_ids"]}}
    yield {"event": "done", "data": result}
