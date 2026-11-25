"""E4 v3 audit (D042 amendment 2026-11-25): fresh items only, four axes, every item judged by A and B, adjudicated by a non-Claude C.

Axes: PART_OF v3 kept edges (50), MEMBER_OF (up to 30, excluding the 30 v2-audited pairs), linking v3 (up to 100) and single-paper
same-sentence APPLIED_TO (up to 100). Every axis excludes every item already audited or used in any development or informational
sample. The sample and packets are written and hashed before any judgement.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

from scientific_network.enrich.audit_v2 import PROPERTY_LABELS, excluded_pairs, pair_of
from scientific_network.enrich.k1 import read_jsonl
from scientific_network.enrich.quality import (TYPES, draw, item_id, load_answers, precision, relation_precision, write_packets)
from scientific_network.enrich.v3 import AUDIT_SEED_V3, applied_to_candidates, relation_items_for, seen_papers

PART_OF_SIZE, MEMBER_OF_SIZE, LINK_SIZE, APPLIED_SIZE = 50, 30, 100, 100
SHARD = 80


def org_pair_items(graph: dict, edge_ids: list[str], axis: str, prefix: str) -> dict:
    """PART_OF or MEMBER_OF items: the two organizations, their Wikidata descriptions, the statement(s) and the parent's classes."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    extra = graph.get("node_enrichments", {})
    evidence = {e["id"]: e for e in graph["evidence"]}
    edges = {e["edge_id"]: e for e in graph["edges"]}
    items = {}
    for edge_id in edge_ids:
        e = edges[edge_id]
        child, parent = nodes[e["source_id"]], nodes[e["target_id"]]
        evs = [evidence[r] for r in e["evidence_ids"]]
        items[item_id(prefix, edge_id)] = {
            "item_id": item_id(prefix, edge_id), "axis": axis, "organization": child["name"],
            "organization_description": (extra.get(child["id"]) or {}).get("wikidata_description"), "organization_qid": evs[0]["wikidata_item"],
            "parent": parent["name"], "parent_description": (extra.get(parent["id"]) or {}).get("wikidata_description"), "parent_qid": evs[0]["parent_item"],
            "parent_instance_of": evs[0].get("parent_instance_of", []),
            "wikidata_statements": [{"property": ev["property"], "property_label": PROPERTY_LABELS.get(ev["property"], ev["property"]),
                                     "statement": f"{ev['wikidata_item']} {ev['property']} {ev['parent_item']}", "statement_item_url": ev["source_url"],
                                     "raw_response_sha256": ev.get("raw_sha256"), "retrieved_at": ev.get("retrieved_at")} for ev in evs]}
    return items


def link_items_v3(graph: dict, texts: dict[str, str], leads: dict[str, str], node_ids: list[str]) -> dict:
    papers_of: dict[str, list[str]] = defaultdict(list)
    for e in graph["edges"]:
        if e["relation"] in ("USES_METHOD", "ADDRESSES_TASK", "USES_DATASET"):
            papers_of[e["target_id"]].append(e["source_id"])
    nodes = {n["id"]: n for n in graph["nodes"]}
    items = {}
    for node_id in node_ids:
        n = nodes[node_id]
        titles = [texts[p].split("\n")[0] for p in sorted(papers_of[node_id])[:3]]
        items[item_id("link", node_id)] = {"item_id": item_id("link", node_id), "axis": "link", "entity": n["name"], "type": n["label"],
                                           "example_paper_titles": titles, "wikipedia_title": n["properties"]["wikipedia_title"],
                                           "wikipedia_lead": leads.get(n["properties"]["wikipedia_title"], "")[:500]}
    return items


def _rows(path: Path) -> list[dict]:
    return read_jsonl(path) if path.exists() else []


def freeze_v3(*, graph_path: Path, texts_path: Path, link_dir: Path, v1_graph_path: Path, v1_sample_path: Path, v2_graph_path: Path, v2_sample_path: Path,
              dev_label_files: list[Path], link_dev_labels: Path, applied_dev_sample: Path, applied_informational: Path, config_path: Path,
              out_dir: Path, seed: int = AUDIT_SEED_V3) -> dict:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    v1_graph = json.loads(v1_graph_path.read_text(encoding="utf-8"))
    v1_sample = json.loads(v1_sample_path.read_text(encoding="utf-8"))
    v2_graph = json.loads(v2_graph_path.read_text(encoding="utf-8"))
    v2_sample = json.loads(v2_sample_path.read_text(encoding="utf-8"))
    texts = {r["id"]: r["text"] for r in read_jsonl(texts_path)}
    leads = {r["id"]: r["text"] for r in read_jsonl(link_dir / "link-leads.jsonl")}
    nodes = {n["id"]: n for n in graph["nodes"]}

    # --- organization axes: pairs seen in v1 audit, v1/v2 development samples and the v2 MEMBER_OF audit
    seen = excluded_pairs(v1_graph, v1_sample, dev_label_files)
    v2_edges = {e["edge_id"]: e for e in v2_graph["edges"]}
    v2_audited = {pair_of(v2_edges[i]) for i in v2_sample["axes"]["member_of"]["MEMBER_OF"]}
    seen_pairs = seen["v1_audited"] | seen["development_labeled"] | v2_audited
    part_pool = {e["edge_id"]: e for e in graph["edges"] if e["relation"] == "PART_OF" and pair_of(e) not in seen_pairs}
    member_pool = {e["edge_id"]: e for e in graph["edges"] if e["relation"] == "MEMBER_OF" and pair_of(e) not in seen_pairs}
    part_ids = draw(sorted(part_pool), PART_OF_SIZE, seed, "part_of_v3")
    member_ids = draw(sorted(member_pool), MEMBER_OF_SIZE, seed, "member_of_v3")

    # --- linking: linked entities not in the v1 link audit or the link development sample (by node ID or Wikipedia page)
    v1_nodes = {n["id"]: n for n in v1_graph["nodes"]}
    seen_nodes = set(v1_sample["link_sample"]["link"]) | {r["node_id"] for r in _rows(link_dev_labels)}
    seen_titles = {(v1_nodes[i]["properties"].get("wikipedia_title")) for i in v1_sample["link_sample"]["link"] if i in v1_nodes} | {r["wikipedia_title"] for r in _rows(link_dev_labels)}
    link_pool = [n["id"] for n in graph["nodes"] if n["label"] in TYPES and n["properties"].get("linked") and n["id"] not in seen_nodes
                 and n["properties"].get("wikipedia_title") not in seen_titles]
    link_ids = draw(sorted(link_pool), LINK_SIZE, seed, "link_v3")

    # --- single-paper APPLIED_TO: not the development 40, not the 30 informational items (their papers are excluded too)
    dev = json.loads(applied_dev_sample.read_text(encoding="utf-8"))
    informational = _rows(applied_informational)
    dev_edges = set(dev["edge_ids"])
    candidates = applied_to_candidates(graph)
    used_papers = {c["paper_id"] for c in candidates if c["edge_id"] in dev_edges} | {r["paper_id"] for r in informational}
    applied_pool = {c["edge_id"]: c for c in candidates if c["edge_id"] not in dev_edges and c["paper_id"] not in used_papers}
    applied_ids = draw(sorted(applied_pool), APPLIED_SIZE, seed, "applied_to_v3")

    items = {**org_pair_items(graph, part_ids, "part_of", "part"), **org_pair_items(graph, member_ids, "member_of", "member"),
             **link_items_v3(graph, texts, leads, link_ids), **relation_items_for(graph, texts, applied_ids)}
    assignments = {i: ["A", "B"] for i in items}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "answers").mkdir(exist_ok=True)
    packets = write_packets(items, assignments, [], out_dir, shard_size=SHARD)
    sample = {"seed": seed, "graph_version": graph["graph_version"], "graph_sha256": sha256(graph_path.read_bytes()).hexdigest(),
              "config_sha256": sha256(config_path.read_bytes()).hexdigest(),
              "axes": {"part_of": {"edge_ids": part_ids, "population": sum(e["relation"] == "PART_OF" for e in graph["edges"]), "pool_after_exclusion": len(part_pool), "requested": PART_OF_SIZE},
                       "member_of": {"edge_ids": member_ids, "population": sum(e["relation"] == "MEMBER_OF" for e in graph["edges"]), "pool_after_exclusion": len(member_pool), "requested": MEMBER_OF_SIZE},
                       "link": {"node_ids": link_ids, "population": sum(1 for n in graph["nodes"] if n["label"] in TYPES and n["properties"].get("linked")), "pool_after_exclusion": len(link_pool), "requested": LINK_SIZE},
                       "applied_to_single_paper": {"edge_ids": applied_ids, "population": len(candidates), "pool_after_exclusion": len(applied_pool), "requested": APPLIED_SIZE,
                                                   "excluded": {"development_edges": len(dev_edges), "informational_items": len(informational), "papers_of_those": len(used_papers)}}},
              "excluded_pairs": {"v1_audited": len(seen["v1_audited"]), "development_labeled": len(seen["development_labeled"]), "v2_audited_member_of": len(v2_audited)},
              "excluded_link_nodes": len(seen_nodes), "unchanged_axes_not_reaudited": ["entities", "paper_edges", "RELATED_TO", "EVALUATED_ON single-paper (27 audited in v2)", "APPLIED_TO (two or more papers)"],
              "assignments": assignments, "item_axes": dict(Counter(i["axis"] for i in items.values())), "items_total": len(items)}
    sample_path, items_path = out_dir / "sample.json", out_dir / "items.json"
    sample_path.write_text(json.dumps(sample, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    items_path.write_text(json.dumps(items, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    receipt = {"frozen": True, "purpose": "E4 v3 AI-assessed audit sample, written before any judgement", "sample_sha256": sha256(sample_path.read_bytes()).hexdigest(),
               "items_sha256": sha256(items_path.read_bytes()).hexdigest(),
               "packets": [{k: v for k, v in p.items() if k != "path"} | {"file": Path(p["path"]).name} for p in packets],
               "graph_version": graph["graph_version"], "seed": seed, "config_sha256": sample["config_sha256"]}
    (out_dir / "freeze-receipt.json").write_text(json.dumps(receipt, indent=1, sort_keys=True), encoding="utf-8")
    return receipt


# ---------------------------------------------------------------------------
# Scoring

def _axis_agreement(ids: list[str], judged: dict) -> dict:
    from scientific_network.evaluation.edge_audit import cohens_kappa
    pairs = [(judged[i]["A"]["verdict"], judged[i]["B"]["verdict"]) for i in ids if i in judged and "A" in judged[i] and "B" in judged[i]]
    kappa = cohens_kappa(pairs)
    return {"items_judged_by_both": len(pairs), "observed_agreement": round(sum(a == b for a, b in pairs) / len(pairs), 4) if pairs else None,
            "cohens_kappa": None if kappa is None else round(kappa, 4), "disputes_sent_to_c": sum(a != b for a, b in pairs),
            "kappa_note": "undefined (no variation in the verdicts)" if kappa is None and pairs else None}


def score_v3(audit_dir: Path) -> dict:
    sample = json.loads((audit_dir / "sample.json").read_text(encoding="utf-8"))
    receipt = json.loads((audit_dir / "freeze-receipt.json").read_text(encoding="utf-8"))
    if sha256((audit_dir / "sample.json").read_bytes()).hexdigest() != receipt["sample_sha256"]:
        raise ValueError("sample.json differs from the frozen receipt")
    items = json.loads((audit_dir / "items.json").read_text(encoding="utf-8"))
    judged, _ = load_answers(audit_dir / "answers")
    by_axis = {axis: sorted(i for i, it in items.items() if it["axis"] == axis) for axis in ("part_of", "member_of", "link", "relation")}
    out = {}
    for axis, name in (("part_of", "part_of"), ("member_of", "member_of"), ("link", "link")):
        ids = by_axis[axis]
        out[name] = precision(ids, judged) | {"population": sample["axes"][name]["population"], "pool_after_exclusion": sample["axes"][name]["pool_after_exclusion"],
                                               "requested": sample["axes"][name]["requested"]}
    rel = relation_precision({"ids": {"same_sentence": by_axis["relation"]}, "population": {"same_sentence": len(by_axis["relation"])}}, judged, items)["strata"]["same_sentence"]
    rel_axis = sample["axes"]["applied_to_single_paper"]
    out["applied_to_single_paper"] = {"shown_paper_supports_the_relation": rel["every_shown_paper_supports"], "unclear": rel["unclear"],
                                      "sensitivity_unclear_as_incorrect": rel["sensitivity_unclear_as_incorrect"], "sampled": len(by_axis["relation"]),
                                      "population": rel_axis["population"], "pool_after_exclusion": rel_axis["pool_after_exclusion"], "requested": rel_axis["requested"]}
    axis_name = {"part_of": "part_of", "member_of": "member_of", "link": "link", "relation": "applied_to_single_paper"}
    for axis, ids in by_axis.items():
        out[axis_name[axis]]["agreement"] = _axis_agreement(ids, judged)
        out[axis_name[axis]]["verdicts_by_channel"] = {ch: dict(Counter(judged[i][ch]["verdict"] for i in ids if ch in judged[i])) for ch in ("A", "B", "C")}
    out["pooled_agreement"] = _axis_agreement(sorted(items), judged)
    out["items_answered"], out["items_frozen"] = sum(1 for i in items if i in judged), len(items)
    return out


def member_of_v2_readings(v2_audit_dir: Path, c_nonclaude: Path) -> dict:
    """The v2 MEMBER_OF figure under four readings; the original figure is reported first and left unchanged.

    Disputed items are the A/B disagreements; ``C`` is the original Claude adjudicator, ``C(non-Claude)`` the fresh Codex session that
    received the same packet.
    """
    sample = json.loads((v2_audit_dir / "sample.json").read_text(encoding="utf-8"))
    judged, _ = load_answers(v2_audit_dir / "answers")
    ids = [item_id("member", e) for e in sample["axes"]["member_of"]["MEMBER_OF"]]
    new_c = {r["item_id"]: r for r in read_jsonl(c_nonclaude)}

    def figure(pick) -> dict:
        verdicts = [pick(judged[i], i) for i in ids]
        decided = [v for v in verdicts if v in ("correct", "incorrect")]
        from scientific_network.enrich.quality import wilson
        return {"primary": wilson(sum(v == "correct" for v in decided), len(decided)),
                "unclear_as_incorrect": wilson(sum(v == "correct" for v in decided), len(verdicts)), "unclear": len(verdicts) - len(decided)}

    def adjudicated(a, i, c):
        return c[i]["verdict"] if a["A"]["verdict"] != a["B"]["verdict"] and i in c else (a["A"]["verdict"])
    disputed = [i for i in ids if judged[i]["A"]["verdict"] != judged[i]["B"]["verdict"]]
    return {"items": len(ids), "disputed_member_of_items": len(disputed),
            "disputed_resolved_by_non_claude_c": {"correct": sum(new_c[i]["verdict"] == "correct" for i in disputed if i in new_c),
                                                  "incorrect": sum(new_c[i]["verdict"] == "incorrect" for i in disputed if i in new_c),
                                                  "unclear": sum(new_c[i]["verdict"] == "unclear" for i in disputed if i in new_c)},
            "A_plus_C_claude (original v2 figure)": figure(lambda a, i: (a["C"]["verdict"] if a["A"]["verdict"] != a["B"]["verdict"] and "C" in a else a["A"]["verdict"])),
            "A_plus_C_non_claude": figure(lambda a, i: adjudicated(a, i, new_c)),
            "B_alone": figure(lambda a, i: a["B"]["verdict"]), "A_alone": figure(lambda a, i: a["A"]["verdict"])}


# ---------------------------------------------------------------------------
# Report

def _fmt(w: dict | None) -> str:
    if not w or w.get("estimate") is None:
        return "n/a"
    return f"{w['estimate']:.3f} [{w['low']:.3f}, {w['high']:.3f}] ({w['k']}/{w['n']})"


def _verdict(w: dict, target: float, sensitivity: dict | None = None) -> str:
    if not w or w.get("estimate") is None:
        return "n/a"
    primary = "pass" if w["estimate"] >= target else "**fail**"
    if sensitivity is None or sensitivity.get("estimate") is None:
        return primary
    return f"{primary} (primary); {'pass' if sensitivity['estimate'] >= target else '**fail**'} (unclear as incorrect)"


def build_quality_v3(*, audit_dir: Path, v1_quality: dict, v2_quality: dict, summaries: dict, reports_dir: Path, run_info: dict, c_nonclaude_v2: Path,
                     v2_audit_dir: Path, output: Path) -> dict:
    scored = score_v3(audit_dir)
    readings = member_of_v2_readings(v2_audit_dir, c_nonclaude_v2)
    layer = {k: s["counts"]["enrichment_layer"] for k, s in summaries.items()}
    total = {k: s["counts"]["total"] for k, s in summaries.items()}
    counts = {"graph_version": {k: s["graph_version"] for k, s in summaries.items()}, "graph_sha256": {k: s["graph_sha256"] for k, s in summaries.items()},
              "total_nodes": {k: total[k]["nodes"] for k in summaries}, "total_edges": {k: total[k]["edges"] for k in summaries},
              "enrichment_nodes": {k: layer[k]["nodes"] for k in summaries}, "linked_entities": {k: layer[k]["linked_entities"] for k in summaries},
              **{f"nodes_{lab}": {k: layer[k]["nodes_by_label"].get(lab, 0) for k in summaries} for lab in ("Method", "Task", "Dataset", "Organization")},
              **{f"edges_{rel}": {k: layer[k]["edges_by_relation"].get(rel, 0) for k in summaries}
                 for rel in ("PART_OF", "MEMBER_OF", "APPLIED_TO", "EVALUATED_ON", "RELATED_TO", "USES_METHOD", "ADDRESSES_TASK", "USES_DATASET")}}
    guard = json.loads((reports_dir / "link-guard.json").read_text(encoding="utf-8"))
    applied = json.loads((reports_dir / "applied-to-decision.json").read_text(encoding="utf-8"))
    report = {"evaluation_kind": "ai_assessed", "graph_version": summaries["v3"]["graph_version"], "graph_sha256": summaries["v3"]["graph_sha256"], "seed": AUDIT_SEED_V3,
              "post_hoc_adoption": ("A reviewer judged the v2 absolute criteria badly chosen. The PART_OF and link rules are adopted on a relative criterion decided after the v2 "
                                    "development results were seen, and the APPLIED_TO criterion was re-declared on the E4 scale after its first result. The development checks are "
                                    "not evidence for v3; accuracy rests only on the fresh E4 v3 audit below."),
              "counts_v1_v2_v3": counts, "part_of_dropped_by_reason": summaries["v3"].get("part_of_dropped_by_reason"),
              "links": {"raw_linked_before_guard": guard["linked_before"], "raw_linked_after_guard": guard["linked_after"], "raw_links_lost": len(guard["lost"]),
                        "final_linked_entities": {k: layer[k]["linked_entities"] for k in summaries}},
              "applied_to_development_decision": applied, "e4_v3": scored, "member_of_v2_readings": readings,
              "carried_over": {"entity_precision": v1_quality["entity_precision_by_variant"]["default"]["all_types"], "paper_edges": v1_quality["predicate_precision"]["paper_edges"],
                               "related_to": v1_quality["predicate_precision"]["related_to"]["RELATED_TO"], "applied_to_v1_two_or_more_papers": v1_quality["predicate_precision"]["entity_relations"]["APPLIED_TO"]["population_weighted_estimate"],
                               "evaluated_on_v1": v1_quality["predicate_precision"]["entity_relations"]["EVALUATED_ON"]["population_weighted_estimate"],
                               "v1_part_of_names_only": v1_quality["predicate_precision"]["part_of"]["PART_OF"], "v1_part_of_with_statement": v1_quality["supplementary_part_of_v2"]["v2"],
                               "v1_linking": v1_quality["linking_accuracy"]["link"], "v1_recall": v1_quality["recall_estimate_by_variant"]["default"]["all"],
                               "v2_evaluated_on_single_paper": v2_quality["e4_v2"]["evaluated_on_single_paper"]["shown_paper_supports_the_relation"],
                               "v2_member_of": {k: v2_quality["e4_v2"]["member_of"][k] for k in ("estimate", "low", "high", "k", "n")}},
              "targets": {"relation_precision": 0.80, "part_of": 0.80, "linking_accuracy": 0.85, "entity_precision": 0.85}, "run_info": run_info,
              "interpretation": "AI-assessed by agent evaluators; not human annotation and not independently validated gold labels. Wilson 95% intervals exclude evaluator error."}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    output.with_suffix(".md").write_text(render_v3(report), encoding="utf-8")
    return report


def _agree(a: dict) -> str:
    kappa = "undefined (no variation)" if a["cohens_kappa"] is None else f"{a['cohens_kappa']:.3f}"
    return f"{a['observed_agreement']:.3f} / {kappa} / {a['disputes_sent_to_c']}"


def render_v3(r: dict) -> str:
    e, c, k = r["e4_v3"], r["carried_over"], r["counts_v1_v2_v3"]
    ri, rd = r["run_info"], r["member_of_v2_readings"]
    p, m, l, a = e["part_of"], e["member_of"], e["link"], e["applied_to_single_paper"]
    lines = [
        "# Enrichment v3 quality (AI-assessed)", "",
        f"Graph `{r['graph_version']}` (SHA-256 `{r['graph_sha256'][:16]}...`); audit seed {r['seed']}. {r['interpretation']}", "",
        "## Post-hoc adoption", "", r["post_hoc_adoption"], "",
        f"Evaluators: {ri['evaluators']}. Isolation: {ri['isolation']} {ri['c_note']}", "",
        "Each cell: estimate [Wilson 95% interval] (k correct / n decided). Unclear verdicts are excluded from the primary figure and counted as incorrect in the sensitivity.", "",
        "## E4 v3 audit: fresh items only", "",
        "| Axis | Fresh items (requested; pool) | Primary | Unclear | Unclear as incorrect | Target | Result |", "|---|---|---|---|---|---|---|",
        f"| PART_OF v3 kept edges | {p['sampled']} ({p['requested']}; pool {p['pool_after_exclusion']} of {p['population']}) | {_fmt(p)} | {p['unclear']} | {_fmt(p['sensitivity_unclear_as_incorrect'])} | 0.80 | {_verdict(p, 0.80, p['sensitivity_unclear_as_incorrect'])} |",
        f"| MEMBER_OF | {m['sampled']} ({m['requested']}; pool {m['pool_after_exclusion']} of {m['population']}) | {_fmt(m)} | {m['unclear']} | {_fmt(m['sensitivity_unclear_as_incorrect'])} | none declared | n/a |",
        f"| linking v3 | {l['sampled']} ({l['requested']}; pool {l['pool_after_exclusion']} of {l['population']}) | {_fmt(l)} | {l['unclear']} | {_fmt(l['sensitivity_unclear_as_incorrect'])} | 0.85 | {_verdict(l, 0.85, l['sensitivity_unclear_as_incorrect'])} |",
        f"| APPLIED_TO single paper, same sentence (shown paper supports the relation) | {a['sampled']} ({a['requested']}; pool {a['pool_after_exclusion']} of {a['population']}) | {_fmt(a['shown_paper_supports_the_relation'])} | {a['unclear']} | {_fmt(a['sensitivity_unclear_as_incorrect'])} | 0.80 | {_verdict(a['shown_paper_supports_the_relation'], 0.80, a['sensitivity_unclear_as_incorrect'])} |", "",
        "Pass or fail compares the point estimate with the declared target; read it with the interval. Fewer fresh items existed than were requested on every axis except PART_OF, so the intervals are wide.", "",
        f"**PART_OF** passes on the decided items but {p['unclear']} of {p['sampled']} are unclear (five have a ministry as the Wikidata parent of a university or institute; A called most of the nine incorrect, B and C unclear), so counting unclear as incorrect gives {p['sensitivity_unclear_as_incorrect']['estimate']:.2f}, below 0.80. "
        f"**MEMBER_OF**: {m['unclear']} of {m['sampled']} items are unclear in the final reading (C marked every ELIXIR national-node dispute unclear), so 1.000 on the {m['judged'] - m['unclear']} decided items is not a reliable summary; no `MEMBER_OF` item was judged incorrect by any channel, and the sensitivity is {m['sensitivity_unclear_as_incorrect']['estimate']:.2f}.", "",
        "### Agreement per axis (A and B judged every item; C adjudicated the disputes)", "",
        "| Axis | Observed agreement / Cohen's kappa / disputes sent to C | A verdicts | B verdicts | C verdicts |", "|---|---|---|---|---|"]
    for name, label in (("part_of", "PART_OF"), ("member_of", "MEMBER_OF"), ("link", "linking"), ("applied_to_single_paper", "APPLIED_TO single paper")):
        x = e[name]
        lines.append(f"| {label} | {_agree(x['agreement'])} | {x['verdicts_by_channel']['A']} | {x['verdicts_by_channel']['B']} | {x['verdicts_by_channel']['C']} |")
    lines += ["", "### Single-channel readings (how much the final figure depends on the adjudicator)", "",
              "| Axis | A alone: correct / incorrect / unclear | B alone: correct / incorrect / unclear | Final (A/B, C decides disputes) |", "|---|---|---|---|"]
    for name, label in (("part_of", "PART_OF"), ("member_of", "MEMBER_OF"), ("link", "linking"), ("applied_to_single_paper", "APPLIED_TO single paper")):
        x = e[name]
        cell = lambda ch: " / ".join(str(x["verdicts_by_channel"][ch].get(v, 0)) for v in ("correct", "incorrect", "unclear"))
        final = x["shown_paper_supports_the_relation"] if "shown_paper_supports_the_relation" in x else x
        lines.append(f"| {label} | {cell('A')} | {cell('B')} | {_fmt(final)}, {x['unclear']} unclear |")
    pa = e["pooled_agreement"]
    lines += ["", f"Kappa is uninformative where one rater has no variation (APPLIED_TO single paper: A judged all 60 correct). Pooled: agreement {pa['observed_agreement']}, kappa {pa['cohens_kappa']}, {pa['disputes_sent_to_c']} disputes. Items answered: {e['items_answered']} of {e['items_frozen']}.",
              ri["c_family_caveat"], "",
              "## MEMBER_OF in the v2 audit under four readings", "",
              f"The 14 v2 disputes (13 `MEMBER_OF` items) were sent to the same non-Claude adjudicator with the same packet. The original v2 figure is unchanged in `reports/enrichment-v2/quality.md`; "
              f"here it is the first row. Of the {rd['disputed_member_of_items']} disputed `MEMBER_OF` items the new adjudicator ruled {rd['disputed_resolved_by_non_claude_c']}.", "",
              "| Reading | Primary | Unclear | Unclear as incorrect |", "|---|---|---|---|"]
    for key, label in (("A_plus_C_claude (original v2 figure)", "A + C (Claude), the original v2 figure"), ("A_plus_C_non_claude", "A + C (non-Claude)"), ("B_alone", "B alone"), ("A_alone", "A alone (informational)")):
        v = rd[key]
        lines.append(f"| {label} | {_fmt(v['primary'])} | {v['unclear']} | {_fmt(v['unclear_as_incorrect'])} |")
    lines += ["", "## Counts v1 / v2 / v3", "", "| Quantity | v1 | v2 | v3 |", "|---|---|---|---|"]
    for key in ("total_nodes", "total_edges", "enrichment_nodes", "nodes_Method", "nodes_Task", "nodes_Dataset", "nodes_Organization", "edges_PART_OF", "edges_MEMBER_OF",
                "edges_APPLIED_TO", "edges_EVALUATED_ON", "edges_RELATED_TO", "edges_USES_METHOD", "edges_ADDRESSES_TASK", "edges_USES_DATASET", "linked_entities"):
        lines.append(f"| {key} | {k[key]['v1']:,} | {k[key]['v2']:,} | {k[key]['v3']:,} |")
    lk = r["links"]
    lines += ["", f"PART_OF edges dropped by the v3 rule, by reason: {r['part_of_dropped_by_reason']}. The 85 consortium and association pairs are `MEMBER_OF` only (no `PART_OF`).",
              f"Links: the guard removed {lk['raw_links_lost']} of {lk['raw_linked_before_guard']} raw links (final linked entities {lk['final_linked_entities']['v2']} to {lk['final_linked_entities']['v3']}); "
              "unlinking a QID undoes some merges, so entity node counts moved (see the table).", "",
              "## All axes: v1, v2 and v3 side by side", "", "| Axis | v1 | v2 | v3 | Target |", "|---|---|---|---|---|",
              f"| entity precision, default | {_fmt(c['entity_precision'])} | carried over (unchanged) | carried over from v1 (unchanged) | 0.85 |"]
    for rel, w in c["paper_edges"].items():
        lines.append(f"| paper edge {rel} | {_fmt(w)} | carried over | carried over | 0.80 |")
    lines += [f"| linking | {_fmt(c['v1_linking'])} | carried over (guard not adopted in v2: same as v1) | **fresh:** {_fmt(l)} on {l['sampled']} items | 0.85 |",
              f"| PART_OF | {_fmt(c['v1_part_of_names_only'])} (unclear as incorrect {c['v1_part_of_names_only']['sensitivity_unclear_as_incorrect']['estimate']:.2f}); with the statement shown {_fmt(c['v1_part_of_with_statement'])} | carried over (v1 rule) | **fresh:** {_fmt(p)} on {p['sampled']} items (unclear as incorrect {p['sensitivity_unclear_as_incorrect']['estimate']:.2f}) | 0.80 |",
              f"| MEMBER_OF | n/a | {_fmt(c['v2_member_of'])} (original reading; see the readings above) | **fresh:** {_fmt(m)} on {m['sampled']} items | none declared |",
              f"| APPLIED_TO two or more papers | {c['applied_to_v1_two_or_more_papers']['every_shown_paper_supports']} (32 edges audited) | carried over | carried over from v1 (the v3 graph has a different edge set; not re-audited) | 0.80 |",
              f"| APPLIED_TO single paper, same sentence | n/a | not adopted | **fresh:** {_fmt(a['shown_paper_supports_the_relation'])} on {a['sampled']} items | 0.80 |",
              f"| EVALUATED_ON (two or more papers) | {c['evaluated_on_v1']['every_shown_paper_supports']} (4 edges) | carried over | carried over | 0.80 |",
              f"| EVALUATED_ON single paper | n/a | {_fmt(c['v2_evaluated_on_single_paper'])} (all 27 audited) | carried over from v2 (not re-audited) | 0.80 |",
              f"| RELATED_TO | {_fmt(c['related_to'])} | carried over | carried over | 0.80 |",
              f"| recall estimate, default | {_fmt(c['v1_recall'])} | carried over | carried over | none declared |", "",
              "Wilson 95% intervals describe sampling error only; they exclude evaluator error. Development checks (v2 and the v3 APPLIED_TO sample) are not part of this table."]
    return "\n".join(lines) + "\n"
