"""Step-by-step plan executor with variable binding, empty-step termination, and hop-tagged union subgraph (spec §6.3)."""

from __future__ import annotations

import inspect
from typing import Any

from scientific_network.rag.tools import RAGToolset, ToolResult


def _resolve_refs(value: Any, step_results: list[ToolResult]) -> Any:
    """Resolve '$stepK.ids', '$stepK.first_id', '$stepK.paper_ids' recursively inside step args."""
    if isinstance(value, str) and value.startswith("$step"):
        parts = value[5:].split(".", 1)
        try:
            idx = int(parts[0]) - 1
        except ValueError:
            return value
        if idx < 0 or idx >= len(step_results):
            return value
        prev = step_results[idx]
        attr = parts[1] if len(parts) > 1 else "ids"
        if attr == "ids":
            return list(prev.ids)
        if attr == "first_id":
            return prev.ids[0] if prev.ids else ""
        if attr == "paper_ids":
            return list(prev.paper_ids)
        if attr == "rows":
            return list(prev.rows)
        return value
    if isinstance(value, list):
        return [_resolve_refs(v, step_results) for v in value]
    if isinstance(value, dict):
        return {k: _resolve_refs(v, step_results) for k, v in value.items()}
    return value


def _extract_id(val: Any) -> Any:
    if isinstance(val, dict) and "id" in val:
        return val["id"]
    if isinstance(val, list):
        return [_extract_id(x) for x in val]
    return val


def _coerce_tool_args(tool_name: str, raw_args: dict[str, Any]) -> dict[str, Any]:
    """Filter/map LLM arg names onto exact RAGToolset method signature so harmless aliases work safely."""
    fn = getattr(RAGToolset, tool_name)
    sig = inspect.signature(fn)
    params = set(sig.parameters) - {"self"}
    args = dict(raw_args)

    if tool_name == "find":
        if "type" in args and "entity_type" not in args:
            args["entity_type"] = args.pop("type")
        if "label" in args and "entity_type" not in args:
            args["entity_type"] = args.pop("label")
        for k in ("query", "name", "term", "mention", "entity"):
            if k in args and "text" not in args:
                args["text"] = args.pop(k)
                break
        args.setdefault("entity_type", None)
        args.setdefault("text", "")

    elif tool_name == "neighbors":
        for k in ("id", "entity_id", "ids", "node_ids", "source_id"):
            if k in args and "node_id" not in args:
                args["node_id"] = args.pop(k)
                break
        if "node_id" in args:
            args["node_id"] = _extract_id(args["node_id"])
        if isinstance(args.get("filters"), dict):
            if "predicates" in args["filters"] and "predicates" not in args:
                args["predicates"] = args["filters"].pop("predicates")
            t_labs = set(args["filters"].get("target_labels") or [])
            if "Dataset" in t_labs and args.get("predicates") == ["APPLIED_TO"]:
                args["predicates"] = None

    elif tool_name == "path":
        if "a" in args and "source_id" not in args:
            args["source_id"] = args.pop("a")
        if "b" in args and "target_id" not in args:
            args["target_id"] = args.pop("b")

    elif tool_name == "papers":
        known_filter_keys = {
            "researcher_id", "organization_id", "topic_id", "method_id",
            "task_id", "dataset_id", "year_min", "year_max", "venue", "query_text",
        }
        flt = dict(args.get("filters") or {})
        for k in list(args):
            if k in known_filter_keys and k not in flt:
                flt[k] = args.pop(k)
        # Drop None values from LLM filters
        flt = {k: v for k, v in flt.items() if v is not None}
        args["filters"] = flt

    elif tool_name == "aggregate":
        for k in ("entity_set", "ids", "entity_id"):
            if k in args and "entity_ids" not in args:
                args["entity_ids"] = args.pop(k)
                break
        if args.get("entity_ids") is None:
            args["entity_ids"] = []
        if isinstance(args.get("entity_ids"), str):
            args["entity_ids"] = [args["entity_ids"]] if args["entity_ids"] else []
        args.setdefault("entity_ids", [])
        args["entity_ids"] = _extract_id(args["entity_ids"])
        flt = dict(args.get("filters") or {})
        for k in ("topic_id", "method_id", "task_id", "dataset_id", "year_min", "year_max", "after_year", "only_increased"):
            if k in args and k not in flt:
                flt[k] = args.pop(k)
        if "cutoff_year" in flt and "after_year" not in flt:
            flt["after_year"] = flt.pop("cutoff_year")
        if flt:
            args["filters"] = {k: v for k, v in flt.items() if v is not None}

    elif tool_name == "rank":
        for k in ("subject", "subject_id", "topic", "topic_id", "method_id", "task_id"):
            if k in args and "scope" not in args:
                args["scope"] = args.pop(k)
                break

    elif tool_name == "community":
        for k in ("id", "community_id", "cid", "entity_id", "topic_id"):
            if k in args and "node_or_community_id" not in args:
                args["node_or_community_id"] = args.pop(k)
                break
        args.setdefault("node_or_community_id", "")

    elif tool_name == "community_report":
        if "community_id" in args and "cid" not in args:
            args["cid"] = args.pop("community_id")

    elif tool_name == "trend":
        for k in ("subject", "subject_id", "entity_type", "kind", "topic"):
            if k in args and "subject_or_kind" not in args:
                args["subject_or_kind"] = args.pop(k)
                break
        args.setdefault("subject_or_kind", "Method")

    return {k: v for k, v in args.items() if k in params}


_FLT_KEY_TO_LABEL = {
    "method_id": "Method",
    "task_id": "Task",
    "dataset_id": "Dataset",
    "topic_id": "Topic",
    "organization_id": "Organization",
    "researcher_id": "Researcher",
}
_LABEL_TO_FLT_KEY = {v: k for k, v in _FLT_KEY_TO_LABEL.items()}


def _resolve_one_id(raw: str, expected_label: str | None, toolset: RAGToolset) -> tuple[str, str | None]:
    if not raw or ":" in raw or raw.startswith("$step"):
        return raw, None
    res = toolset.find(expected_label, raw, limit=1)
    if res.empty and expected_label is not None:
        res = toolset.find(None, raw, limit=1)
    if not res.empty:
        return str(res.rows[0]["id"]), str(res.rows[0].get("label") or "")
    return raw, None


def _resolve_unlinked_ids(tool_name: str, call_args: dict[str, Any], toolset: RAGToolset) -> dict[str, Any]:
    """Resolve raw text strings emitted by the planner when an entity wasn't linked upfront."""
    args = dict(call_args)
    for key in ("node_id", "source_id", "target_id"):
        val = args.get(key)
        if isinstance(val, str) and val and ":" not in val:
            nid, _ = _resolve_one_id(val, None, toolset)
            args[key] = nid
    if isinstance(args.get("entity_ids"), list):
        resolved_list = []
        for item in args["entity_ids"]:
            if isinstance(item, str) and item and ":" not in item:
                nid, _ = _resolve_one_id(item, None, toolset)
                resolved_list.append(nid)
            else:
                resolved_list.append(item)
        args["entity_ids"] = resolved_list
    if isinstance(args.get("filters"), dict):
        new_flt: dict[str, Any] = {}
        for fk, fv in args["filters"].items():
            if fk in _FLT_KEY_TO_LABEL and isinstance(fv, str) and fv and ":" not in fv:
                nid, actual_lbl = _resolve_one_id(fv, _FLT_KEY_TO_LABEL[fk], toolset)
                actual_fk = _LABEL_TO_FLT_KEY.get(actual_lbl or "", fk)
                new_flt[actual_fk] = nid
            else:
                new_flt[fk] = fv
        args["filters"] = new_flt
    return args


def execute_plan(steps: list[str] | list[dict[str, Any]], toolset: RAGToolset) -> dict[str, Any]:
    """Execute 1-4 steps sequentially; stop immediately if any step returns empty."""
    step_results: list[ToolResult] = []
    trace_steps: list[dict[str, Any]] = []
    union_nodes: dict[str, dict[str, Any]] = {}
    union_edges: dict[str, dict[str, Any]] = {}
    all_paper_ids: list[str] = []
    all_evidence_ids: list[str] = []
    stopped_reason: str | None = None
    stopped_at_step: int | None = None

    for step_idx, step in enumerate(steps, start=1):
        tool_name = step["tool"]
        resolved_args = _resolve_refs(step.get("args") or {}, step_results)
        call_args = _coerce_tool_args(tool_name, resolved_args)
        call_args = _resolve_unlinked_ids(tool_name, call_args, toolset)

        try:
            res = toolset.call(tool_name, **call_args)
        except Exception as exc:
            stopped_reason = f"tool_error: {exc}"
            stopped_at_step = step_idx
            trace_steps.append({
                "step": step_idx,
                "tool": tool_name,
                "purpose": step.get("purpose", ""),
                "args": call_args,
                "empty": True,
                "row_count": 0,
                "rows": [],
                "source_kind": "error",
                "note": stopped_reason,
                "paper_ids": [],
                "evidence_ids": [],
            })
            break

        step_results.append(res)
        for n in res.subgraph_nodes:
            nid = n["id"]
            if nid not in union_nodes:
                union_nodes[nid] = {**n, "hop": step_idx}
        for e in res.subgraph_edges:
            eid = e["edge_id"]
            if eid not in union_edges:
                union_edges[eid] = {**e, "hop": step_idx}
        all_paper_ids.extend(res.paper_ids)
        all_evidence_ids.extend(res.evidence_ids)

        trace_steps.append({
            "step": step_idx,
            "tool": tool_name,
            "purpose": step.get("purpose", ""),
            "args": call_args,
            "empty": res.empty,
            "row_count": len(res.rows),
            "rows": res.rows[:50],
            "source_kind": res.source_kind,
            "note": res.note,
            "paper_ids": res.paper_ids[:30],
            "evidence_ids": res.evidence_ids[:30],
        })

        if res.empty:
            stopped_reason = "empty_step"
            stopped_at_step = step_idx
            break

    return {
        "steps": trace_steps,
        "stopped_reason": stopped_reason,
        "stopped_at_step": stopped_at_step,
        "subgraph_nodes": list(union_nodes.values()),
        "subgraph_edges": list(union_edges.values()),
        "paper_ids": list(dict.fromkeys(all_paper_ids))[:60],
        "evidence_ids": list(dict.fromkeys(all_evidence_ids))[:60],
    }
