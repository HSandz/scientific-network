"""Question parser, entity linker, mode router, and 1-4 step closed-tool planner (spec §6.3).

The SLM never writes Cypher; it produces a JSON-schema plan over the closed 9-tool set.
Same-name researchers always halt for user disambiguation instead of auto-merging.
"""

from __future__ import annotations

import json
import re
from typing import Any

from scientific_network.rag.llm import LLMClient, LLMError
from scientific_network.rag.tools import ALLOWED_LABELS, RAGToolset

PARSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["entities", "intent"],
    "properties": {
        "entities": {
            "type": "array",
            "maxItems": 6,
            "items": {
                "type": "object",
                "required": ["text", "entity_type"],
                "properties": {
                    "text": {"type": "string"},
                    "entity_type": {
                        "type": "string",
                        "enum": ["Method", "Task", "Dataset", "Organization", "Topic", "Researcher", "Venue"],
                    },
                },
            },
        },
        "year_min": {"type": ["integer", "null"]},
        "year_max": {"type": ["integer", "null"]},
        "after_year": {"type": ["integer", "null"]},
        "venue": {"type": ["string", "null"]},
        "intent": {
            "type": "string",
            "enum": ["lookup", "count", "ranking", "path", "trend", "comparison", "global_summary", "local_summary"],
        },
    },
}

PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["steps"],
    "properties": {
        "steps": {
            "type": "array",
            "minItems": 1,
            "maxItems": 4,
            "items": {
                "type": "object",
                "required": ["tool", "args"],
                "properties": {
                    "tool": {"type": "string", "enum": list(RAGToolset.TOOL_NAMES)},
                    "args": {"type": "object"},
                    "purpose": {"type": "string"},
                },
            },
        },
    },
}

_PARSE_SYS = (
    "Extract research entities, year bounds, venue, and intent from the question about AAAI/IJCAI 2021-2025 papers.\n"
    "Entity types: Method, Task, Dataset, Organization, Topic, Researcher, Venue (NEVER extract years like 2022 or 2024 as Venue).\n"
    "Examples:\n"
    "Q: 'How many papers in the corpus use Q-learning?'\n"
    "-> entities=[{'text':'Q-learning','entity_type':'Method'}], intent='count'\n"
    "Q: 'Which five organizations published the most papers addressing summarization in 2024?'\n"
    "-> entities=[{'text':'summarization','entity_type':'Task'}], year_min=2024, year_max=2024, intent='ranking'\n"
    "Q: 'Which tasks co-occur most with diffusion models, and what datasets are used with diffusion models?'\n"
    "-> entities=[{'text':'diffusion models','entity_type':'Method'}], intent='lookup'\n"
    "Return strict JSON."
)

_PLAN_SYS = (
    "Create a 1-4 step JSON plan using ONLY these exact tool signatures:\n"
    "1. find(entity_type, text) -> entity_type in {Method,Task,Dataset,Organization,Topic,Researcher,Venue,null}\n"
    "2. neighbors(node_id, predicates, filters, limit) -> node_id (single ID or $stepK.ids), predicates (list e.g. ['APPLIED_TO'] or ['EVALUATED_ON'] or ['COLLABORATED_WITH']), filters ({target_labels, year_min, year_max, venue, min_support})\n"
    "3. path(source_id, target_id, max_len, predicates)\n"
    "4. papers(filters, limit) -> filters dict {method_id, task_id, dataset_id, topic_id, organization_id, researcher_id, venue, year_min, year_max}\n"
    "5. aggregate(entity_ids, by, metric, filters, limit) -> entity_ids (list or $stepK.ids or []), by in {year,organization,researcher,topic,method,task,dataset,venue,organization_year}, metric in {paper_count,share,share_growth}, filters ({method_id, topic_id, task_id, dataset_id, year_min, year_max, after_year, only_increased})\n"
    "6. rank(network, scope, measure, limit) -> network in {N1,N2,N3,N4}, scope (subject ID or name for PPR lift)\n"
    "7. community(node_or_community_id, network)\n"
    "8. community_report(cid)\n"
    "9. trend(subject_or_kind, period, trend_class, limit) -> subject_or_kind is 'Topic'|'Method'|'Task'|'Dataset' OR a subject name/ID\n\n"
    "Critical rules:\n"
    "- ALWAYS use resolved graph IDs from `linked_entities` when present (else exact short surface string).\n"
    "- Chain steps ONLY to earlier steps via '$step1.ids', '$step1.first_id', '$step2.ids' (NEVER use '$step1.ids' inside step 1!).\n"
    "- 'Which methods/topics/tasks/datasets grew fastest / gained most share (across AAAI and IJCAI 2021-2025)': single step trend(subject_or_kind='Method' or 'Topic', period='2021-2025', trend_class='rising', limit=15).\n"
    "- 'Which organizations specialize most in X by lift': rank(network='N2', scope=X_id_or_name, measure='lift', limit=15).\n"
    "- 'Which tasks co-occur most with M, and what datasets are used with M': step 1 neighbors(node_id=M_id, predicates=null, filters={'target_labels':['Task'],'include_cooccurrence':true}, limit=15), step 2 neighbors(node_id=M_id, predicates=null, filters={'target_labels':['Dataset'],'include_cooccurrence':true}, limit=15) (NEVER use APPLIED_TO for co-occurrence).\n"
    "- 'Which tasks is Method M literally applied to' / 'evaluated on': neighbors(M_id, predicates=['APPLIED_TO']) or ['EVALUATED_ON'].\n"
    "- 'How many papers use/address X': aggregate(entity_ids=[X_id], by='year').\n"
    "- 'Which top K organizations/researchers authored/published the most papers that use/address X (in year Y)': step 1 papers(filters={method_id/task_id: X_id, year_min: Y, year_max: Y}, limit=200), step 2 aggregate(entity_ids='$step1.ids', by='organization' or 'researcher', limit=K).\n"
    "- 'Which organizations collaborating with X increased share of Y after YEAR': step 1 neighbors(X_id, predicates=['COLLABORATED_WITH'], filters={'target_labels':['Organization']}, limit=100), step 2 aggregate(entity_ids='$step1.ids', by='organization_year', metric='share_growth', filters={'method_id'/'topic_id': Y_id, 'after_year': YEAR, 'only_increased': true}, limit=15)."
)

_YEAR_SINGLE_RE = re.compile(r"\b(202[1-5])\b")
_AFTER_YEAR_RE = re.compile(r"\b(?:after|since)\s+(202[1-5])\b", re.I)


def parse_question(question: str, llm: LLMClient | None = None) -> dict[str, Any]:
    """Extract entities, time constraints, venue, and intent via SLM + deterministic regex checks."""
    parsed: dict[str, Any] = {"entities": [], "year_min": None, "year_max": None, "after_year": None, "venue": None, "intent": "lookup"}
    if llm is not None:
        try:
            res = llm.complete(
                prompt_version="rag-parse-v2",
                system=_PARSE_SYS,
                user=f"Question: {question}",
                schema=PARSE_SCHEMA,
                schema_name="question_parse",
                max_tokens=300,
            )
            if isinstance(res.parsed, dict):
                parsed.update(res.parsed)
                parsed["entities"] = [
                    e for e in (parsed.get("entities") or [])
                    if not re.fullmatch(r"202[1-5]", str(e.get("text") or "").strip())
                ]
        except LLMError:
            pass

    q_low = question.lower()
    after_m = _AFTER_YEAR_RE.search(question)
    if after_m and not parsed.get("after_year"):
        ay = int(after_m.group(1))
        parsed["after_year"] = ay
        if not parsed.get("year_min"):
            parsed["year_min"] = ay + 1
    else:
        yrs = [int(y) for y in _YEAR_SINGLE_RE.findall(question)]
        if len(yrs) == 1 and not parsed.get("year_min") and not parsed.get("year_max") and "between" not in q_low and "from" not in q_low:
            parsed["year_min"] = yrs[0]
            parsed["year_max"] = yrs[0]
        elif len(yrs) >= 2 and not parsed.get("year_min"):
            parsed["year_min"] = min(yrs)
            parsed["year_max"] = max(yrs)

    if not parsed.get("venue"):
        has_aaai = "aaai" in q_low
        has_ijcai = "ijcai" in q_low
        if has_aaai and not has_ijcai:
            parsed["venue"] = "AAAI"
        elif has_ijcai and not has_aaai:
            parsed["venue"] = "IJCAI"
    return parsed


def link_entities(
    parsed: dict[str, Any],
    toolset: RAGToolset,
    *,
    resolved_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Link parsed entities to graph IDs via toolset.find; flag ambiguous Researchers."""
    overrides = resolved_overrides or {}
    linked: list[dict[str, Any]] = []
    disambiguation: list[dict[str, Any]] = []

    for ent in parsed.get("entities", []):
        text = str(ent.get("text") or "").strip()
        etype = ent.get("entity_type")
        if not text:
            continue
        if etype == "Venue":
            vid = f"venue:{text.lower()}"
            linked.append({"text": text, "entity_type": "Venue", "id": vid, "name": text.upper()})
            continue
        if etype not in ALLOWED_LABELS:
            etype = None

        if text in overrides:
            chosen_id = overrides[text]
            nodes = toolset.backend.get_nodes_by_ids([chosen_id])
            if nodes:
                linked.append({"text": text, "entity_type": nodes[0]["label"], "id": nodes[0]["id"], "name": nodes[0]["name"]})
                continue

        res = toolset.find(etype, text, limit=5)
        if res.empty and etype is not None:
            # Retry without strict type if initial type missed
            res = toolset.find(None, text, limit=5)

        if res.ambiguous:
            disambiguation.append({
                "mention": text,
                "entity_type": etype or "Researcher",
                "candidates": res.rows,
            })
        elif not res.empty:
            top = res.rows[0]
            linked.append({
                "text": text,
                "entity_type": top["label"],
                "id": top["id"],
                "name": top["name"],
                "alternatives": res.rows[1:3],
            })
        else:
            linked.append({"text": text, "entity_type": etype, "id": None, "name": None})

    return {
        "linked": linked,
        "needs_disambiguation": len(disambiguation) > 0,
        "disambiguation": disambiguation,
    }


def route_mode(question: str, requested_mode: str, parsed: dict[str, Any], linked: list[dict[str, Any]]) -> str:
    """Route 'auto' into 'global', 'local', or 'multi_hop'."""
    if requested_mode in ("local", "global", "multi_hop"):
        return requested_mode
    q_low = question.lower()
    intent = parsed.get("intent")
    has_ids = any(x.get("id") and x.get("entity_type") != "Venue" for x in linked)
    global_cues = (
        "main research directions",
        "main research communities",
        "research communities in the",
        "which research communities work on",
        "overall themes",
        "summarize the corpus",
        "method portfolios of aaai and ijcai",
    )
    if any(cue in q_low for cue in global_cues) or (intent == "global_summary" and not has_ids):
        return "global"
    if intent == "local_summary" and has_ids and not any(w in q_low for w in ("how many", "which", "top ", "path", "collaborat", "trend", "grew", "after ")):
        return "local"
    return "multi_hop"


def _normalize_plan(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for st in steps[:4]:
        tool = st.get("tool")
        if tool not in RAGToolset.TOOL_NAMES:
            continue
        args = dict(st.get("args") or {})
        cleaned.append({"tool": tool, "args": args, "purpose": st.get("purpose", "")})
    return cleaned


def build_plan(
    question: str,
    parsed: dict[str, Any],
    linked: list[dict[str, Any]],
    llm: LLMClient,
) -> list[dict[str, Any]]:
    """Generate a validated 1-4 step closed-tool plan via Qwen3.5-4B."""
    resolved_summary = [
        {"mention": x["text"], "label": x["entity_type"], "id": x["id"], "name": x["name"]}
        for x in linked if x.get("id")
    ]
    user_msg = json.dumps({
        "question": question,
        "parsed": {k: v for k, v in parsed.items() if k != "entities"},
        "linked_entities": resolved_summary,
    }, ensure_ascii=False)

    last_err = ""
    for attempt in (0, 1):
        pv = "rag-plan-v4" if attempt == 0 else "rag-plan-v4-retry"
        msg = user_msg if attempt == 0 else (user_msg + f"\n\nPrevious plan error: {last_err}. Return a valid 1-4 step JSON plan.")
        try:
            res = llm.complete(
                prompt_version=pv,
                system=_PLAN_SYS,
                user=msg,
                schema=PLAN_SCHEMA,
                schema_name="tool_plan",
                max_tokens=512,
            )
            if isinstance(res.parsed, dict):
                steps = _normalize_plan(res.parsed.get("steps", []))
                if steps:
                    return steps
            last_err = "empty or unknown tool names"
        except LLMError as exc:
            last_err = str(exc)

    # Deterministic safe fallback if SLM fails to emit valid tool plan
    first_ent = next((x for x in linked if x.get("id") and x["entity_type"] != "Venue"), None)
    if first_ent:
        return [{"tool": "neighbors", "args": {"node_id": first_ent["id"], "limit": 25}, "purpose": "fallback neighborhood lookup"}]
    return [{"tool": "trend", "args": {"subject_or_kind": "Method", "trend_class": "rising", "limit": 10}, "purpose": "fallback trend lookup"}]
