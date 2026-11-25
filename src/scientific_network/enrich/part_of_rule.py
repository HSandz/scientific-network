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
    # consortium: the parent's *direct* class; closure made Fraunhofer a "voluntary association" and a campus a "group"
    if set(facts["types"].get(parent, {})) & set(rule["consortium_classes_direct_instance_of_only"]):
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


def member_of_edges(part_edges: list[dict], evidence: dict[str, dict], decisions: dict, facts: dict, statements: dict, rule_id: str, *,
                    method_version: str, graph_version: str) -> tuple[list[dict], list[dict]]:
    """``MEMBER_OF`` edges for the PART_OF statements the rule routes to consortia, associations and groups.

    The evidence is the Wikidata statement (per-statement raw response hash from the v2 raw store) plus the parent's instance-of classes
    that made it a consortium; the PART_OF edge itself is not touched here.
    """
    from scientific_network.enrich.relations import edge_id, evidence_id
    edges, out = [], []
    for edge in part_edges:
        decision = decisions[edge["edge_id"]]
        if decision["decision"] != "member_of":
            continue
        old = evidence[edge["evidence_ids"][0]]
        child, parent = old["wikidata_item"], old["parent_item"]
        props = [p for p in ("P749", "P361") if p in edge["properties"]["wikidata_property"].split("+")]
        prop = decision["property"] or props[0]
        found = statements.get((child, parent, prop), {})
        ev = {"id": evidence_id("wikidata-member", edge["source_id"], prop, parent), "kind": "wikidata", "source_url": f"https://www.wikidata.org/wiki/{child}",
              "wikidata_item": child, "property": prop, "parent_item": parent, "source": "wikidata_sparql",
              "retrieved_at": found.get("retrieved_at"), "raw_sha256": found.get("raw_response_sha256"), "rule": rule_id,
              "parent_instance_of": sorted(facts["types"].get(parent, {}).values())}
        out.append(ev)
        edges.append({"edge_id": edge_id("MEMBER_OF", edge["source_id"], edge["target_id"], method_version), "relation": "MEMBER_OF",
                      "source_id": edge["source_id"], "target_id": edge["target_id"], "evidence_kind": "wikidata", "evidence_ids": [ev["id"]],
                      "method_version": method_version, "graph_version": graph_version, "validation_status": "accepted",
                      "properties": {"wikidata_property": prop, "rule": rule_id, "parent_in_v4": edge["properties"]["parent_in_v4"]}})
    return edges, out


def kept_part_of(part_edges: list[dict], evidence: dict[str, dict], decisions: dict, facts: dict, rule_id: str) -> tuple[list[dict], list[dict], Counter]:
    """PART_OF edges the rule keeps (decision ``keep``), with the rule id and the parent's instance-of labels added to their evidence.

    Every other edge is either routed to ``MEMBER_OF`` (see ``member_of_edges``) or dropped; the second return value is the evidence
    of the kept edges and the third counts the dropped edges by reason.
    """
    edges, out, dropped = [], [], Counter()
    for edge in part_edges:
        decision = decisions[edge["edge_id"]]
        if decision["decision"] == "drop":
            dropped[decision["reason"]] += 1
        if decision["decision"] != "keep":
            continue
        for ref in edge["evidence_ids"]:
            old = evidence[ref]
            out.append({**old, "rule": rule_id, "parent_instance_of": sorted(facts["types"].get(old["parent_item"], {}).values())})
        edges.append(edge)
    return edges, out, dropped


def check_integrity(graph: dict, facts: dict, rule: dict) -> list[str]:
    """Enrichment v3 integrity: re-judge every PART_OF and MEMBER_OF edge with the rule and report any that it would not give.

    PART_OF targets must have no excluded class (index, list, enumeration), and the rule must still return ``keep`` for PART_OF and
    ``member_of`` for MEMBER_OF. This is a structural check against the cached Wikidata facts, not a semantic accuracy claim.
    """
    evidence = {e["id"]: e for e in graph["evidence"]}
    errors = []
    excluded = set(rule["excluded_classes"])
    for edge in graph["edges"]:
        if edge["relation"] not in ("PART_OF", "MEMBER_OF"):
            continue
        ev = evidence[edge["evidence_ids"][0]]
        child, parent = ev["wikidata_item"], ev["parent_item"]
        if edge["relation"] == "PART_OF" and excluded & class_closure(parent, facts, rule["superclass_depth"]):
            errors.append(f"{edge['edge_id']}: PART_OF target {parent} has an excluded class")
        want = "keep" if edge["relation"] == "PART_OF" else "member_of"
        got = judge_edge(child, parent, facts, rule)["decision"]
        if got != want:
            errors.append(f"{edge['edge_id']}: {edge['relation']} {child}->{parent} but the rule gives {got}")
    return errors
