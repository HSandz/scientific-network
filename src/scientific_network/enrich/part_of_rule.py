"""Enrichment v2: PART_OF rule (D042 amendment 2026-11-25, Rule A).

A Wikidata parent statement ``child P749/P361 parent`` becomes a PART_OF edge only if the parent is an organization of an
allowed kind and the statement is current and has a plausible direction. Consortia and associations are not parts: they are
returned separately as ``MEMBER_OF`` candidates (the predicate is adopted or not by the declared criterion). Class lists live in
``configs/enrichment-v2.json`` so the rule is fixed before it is measured.
"""

from __future__ import annotations

from collections import Counter

REASONS = ("end_dated", "excluded_class", "not_organization", "reversed_direction", "consortium_or_association", "implausible_type_order")


def class_closure(qid: str, facts: dict, depth: int) -> set[str]:
    """Direct instance-of classes plus superclasses up to ``depth`` levels (facts come from ``org_facts.fetch_org_facts``)."""
    seen = set(facts["types"].get(qid, {}))
    frontier = set(seen)
    for _ in range(depth):
        step = set()
        for cls in frontier:
            step |= set(facts["superclasses"].get(cls, {})) - seen
        seen |= step
        frontier = step
    return seen


def active_statements(child: str, parent: str, facts: dict) -> list[dict]:
    """Current P749/P361 statements ``child -> parent``: not end-dated and not of deprecated rank."""
    return [s for s in facts["statements"].get(child, []) if s["prop"] in ("P749", "P361") and s["target"] == parent
            and not s.get("end") and s.get("rank") != "deprecated"]


def reverse_statement(child: str, parent: str, facts: dict) -> bool:
    """The child lists the parent as a subsidiary or part (P355/P527), or the parent says it is part of the child."""
    child_says = any(s["prop"] in ("P355", "P527") and s["target"] == parent for s in facts["statements"].get(child, []))
    parent_says = any(s["prop"] in ("P749", "P361") and s["target"] == child for s in facts["statements"].get(parent, []))
    return child_says or parent_says


def judge_edge(child: str, parent: str, facts: dict, rule: dict) -> dict:
    """Decision for one statement: ``{"decision": "keep"|"member_of"|"drop", "reason": ..., "property": preferred property}``."""
    depth = rule["superclass_depth"]
    parent_classes, child_classes = class_closure(parent, facts, depth), class_closure(child, facts, depth)
    active = active_statements(child, parent, facts)
    properties = sorted({s["prop"] for s in active})
    preferred = "P749" if "P749" in properties else (properties[0] if properties else None)
    if not active:
        return {"decision": "drop", "reason": "end_dated", "property": None}
    if parent_classes & set(rule["excluded_classes"]):
        return {"decision": "drop", "reason": "excluded_class", "property": preferred}
    if not parent_classes & set(rule["allowed_classes"]):
        return {"decision": "drop", "reason": "not_organization", "property": preferred}
    if reverse_statement(child, parent, facts):
        return {"decision": "drop", "reason": "reversed_direction", "property": preferred}
    if parent_classes & set(rule["consortium_classes"]):
        return {"decision": "member_of", "reason": "consortium_or_association", "property": preferred}
    # type order: the parent's *direct* class is subordinate (faculty, department, institute); closure would make a ministry a "department"
    if child_classes & set(rule["whole_organization_classes_via_closure"]) and set(facts["types"].get(parent, {})) & set(rule["subordinate_classes_direct_instance_of_only"]):
        return {"decision": "drop", "reason": "implausible_type_order", "property": preferred}
    return {"decision": "keep", "reason": "kept", "property": preferred}


def apply_rule(edges: list[dict], evidence: dict[str, dict], facts: dict, rule: dict) -> dict:
    """Judge every PART_OF edge. Returns decisions per edge id and counts by outcome and reason."""
    decisions = {}
    for edge in edges:
        ev = evidence[edge["evidence_ids"][0]]
        decisions[edge["edge_id"]] = judge_edge(ev["wikidata_item"], ev["parent_item"], facts, rule)
    counts = Counter(f"{d['decision']}:{d['reason']}" for d in decisions.values())
    return {"decisions": decisions, "counts": dict(sorted(counts.items())),
            "kept": sum(d["decision"] == "keep" for d in decisions.values()),
            "member_of": sum(d["decision"] == "member_of" for d in decisions.values()),
            "dropped": sum(d["decision"] == "drop" for d in decisions.values())}
