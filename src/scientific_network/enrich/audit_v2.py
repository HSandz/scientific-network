"""E4 v2 audit: fresh samples for the axes that changed in enrichment v2 (D042 amendment 2026-11-25).

Changed axes: the new single-paper same-sentence ``EVALUATED_ON`` edges (all of them) and the new ``MEMBER_OF`` predicate (a fresh
sample that excludes every v1-audited pair and every development-labeled pair). Axes whose rule was not adopted (PART_OF, single-paper
``APPLIED_TO``, the link guard) are not re-audited; their v1 figures are carried over and labeled as such. Both A and B judge every item
because each axis has 50 or fewer items; adjudicator C decides disagreements. The sample and packets are written and hashed before any
judgement.
"""

from __future__ import annotations

import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

from scientific_network.enrich.k1 import read_jsonl
from scientific_network.enrich.quality import (draw, final_verdict, item_id, load_answers, precision, relation_precision, support_text, write_packets)

AUDIT_SEED = 2026112502
PROPERTY_LABELS = {"P749": "parent organization", "P361": "part of"}
MEMBER_OF_SIZE = 30


def pair_of(edge: dict) -> tuple[str, str]:
    return edge["source_id"], edge["target_id"]


def excluded_pairs(v1_graph: dict, audit_sample: dict, dev_label_files: list[Path]) -> dict[str, set[tuple[str, str]]]:
    """Organization pairs already seen: the 50 v1-audited PART_OF edges and the development-labeled PART_OF / MEMBER_OF candidates."""
    by_id = {e["edge_id"]: e for e in v1_graph["edges"] if e["relation"] == "PART_OF"}
    audited = {pair_of(by_id[i]) for i in audit_sample["part_of_sample"]["PART_OF"]}
    dev = set()
    for path in dev_label_files:
        for row in read_jsonl(path):
            dev.add(pair_of(by_id[row["edge_id"]]))
    return {"v1_audited": audited, "development_labeled": dev}


def single_paper_evaluated_on_items(graph: dict, texts: dict[str, str]) -> tuple[dict, list[str]]:
    nodes = {n["id"]: n for n in graph["nodes"]}
    evidence = {e["id"]: e for e in graph["evidence"]}
    items, edge_ids = {}, []
    for e in graph["edges"]:
        if e["relation"] == "EVALUATED_ON" and e["properties"].get("support_rule") == "single_paper_same_sentence":
            ev = evidence[e["evidence_ids"][0]]
            edge_ids.append(e["edge_id"])
            items[item_id("rel", e["edge_id"])] = {
                "item_id": item_id("rel", e["edge_id"]), "axis": "relation", "relation": "EVALUATED_ON",
                "head": f"{nodes[e['source_id']]['name']} ({nodes[e['source_id']]['label']})",
                "tail": f"{nodes[e['target_id']]['name']} ({nodes[e['target_id']]['label']})",
                "papers": [support_text(texts, ev["paper_id"], [ev["head_span"], ev["tail_span"]])]}
    return items, sorted(edge_ids)


def member_of_items(graph: dict, excluded: dict[str, set], seed: int, size: int) -> tuple[dict, dict]:
    nodes = {n["id"]: n for n in graph["nodes"]}
    extra = graph.get("node_enrichments", {})
    evidence = {e["id"]: e for e in graph["evidence"]}
    all_edges = {e["edge_id"]: e for e in graph["edges"] if e["relation"] == "MEMBER_OF"}
    seen = excluded["v1_audited"] | excluded["development_labeled"]
    pool = {i: e for i, e in all_edges.items() if pair_of(e) not in seen}
    chosen = draw(sorted(pool), size, seed, "member_of")
    items = {}
    for edge_id in chosen:
        e = pool[edge_id]
        ev = evidence[e["evidence_ids"][0]]
        child, parent = nodes[e["source_id"]], nodes[e["target_id"]]
        items[item_id("member", edge_id)] = {
            "item_id": item_id("member", edge_id), "axis": "member_of", "organization": child["name"],
            "organization_description": (extra.get(child["id"]) or {}).get("wikidata_description"), "organization_qid": ev["wikidata_item"],
            "parent": parent["name"], "parent_description": (extra.get(parent["id"]) or {}).get("wikidata_description"), "parent_qid": ev["parent_item"],
            "parent_instance_of": ev["parent_instance_of"],
            "wikidata_statement": {"property": ev["property"], "property_label": PROPERTY_LABELS[ev["property"]],
                                   "statement": f"{ev['wikidata_item']} {ev['property']} {ev['parent_item']}",
                                   "statement_item_url": ev["source_url"], "raw_response_sha256": ev["raw_sha256"], "retrieved_at": ev["retrieved_at"]}}
    return items, {"MEMBER_OF": chosen, "population": len(all_edges), "excluded_v1_audited_pairs": len(excluded["v1_audited"]),
                   "excluded_development_pairs": len(excluded["development_labeled"]), "pool_after_exclusion": len(pool)}


def freeze_v2(*, graph_path: Path, texts_path: Path, v1_graph_path: Path, v1_sample_path: Path, dev_label_files: list[Path], config_path: Path,
              out_dir: Path, seed: int = AUDIT_SEED) -> dict:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    v1_graph = json.loads(v1_graph_path.read_text(encoding="utf-8"))
    v1_sample = json.loads(v1_sample_path.read_text(encoding="utf-8"))
    texts = {r["id"]: r["text"] for r in read_jsonl(texts_path)}
    rel_items, rel_ids = single_paper_evaluated_on_items(graph, texts)
    mem_items, mem_sample = member_of_items(graph, excluded_pairs(v1_graph, v1_sample, dev_label_files), seed, MEMBER_OF_SIZE)
    items = {**rel_items, **mem_items}
    assignments = {i: ["A", "B"] for i in items}  # every axis has 50 or fewer items: A and B both judge all of them
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "answers").mkdir(exist_ok=True)
    packets = write_packets(items, assignments, [], out_dir, shard_size=120)
    sample = {"seed": seed, "graph_version": graph["graph_version"], "graph_sha256": sha256(graph_path.read_bytes()).hexdigest(),
              "config_sha256": sha256(config_path.read_bytes()).hexdigest(), "base_v1_graph_sha256": sha256(v1_graph_path.read_bytes()).hexdigest(),
              "axes": {"evaluated_on_single_paper": {"edge_ids": rel_ids, "population": len(rel_ids), "sampled": len(rel_ids),
                                                     "note": "all new single-paper same-sentence EVALUATED_ON edges"},
                       "member_of": mem_sample},
              "unchanged_axes_not_reaudited": ["entities", "paper_edges", "APPLIED_TO (two or more papers)", "RELATED_TO", "PART_OF (rule not adopted)", "linking (guard not adopted)"],
              "assignments": assignments, "item_axes": dict(Counter(i["axis"] for i in items.values())), "items_total": len(items)}
    sample_path = out_dir / "sample.json"
    sample_path.write_text(json.dumps(sample, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    items_path = out_dir / "items.json"
    items_path.write_text(json.dumps(items, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    receipt = {"frozen": True, "purpose": "E4 v2 AI-assessed audit sample, written before any judgement",
               "sample_sha256": sha256(sample_path.read_bytes()).hexdigest(), "items_sha256": sha256(items_path.read_bytes()).hexdigest(),
               "packets": [{k: v for k, v in p.items() if k != "path"} | {"file": Path(p["path"]).name} for p in packets],
               "graph_version": graph["graph_version"], "seed": seed, "config_sha256": sample["config_sha256"]}
    (out_dir / "freeze-receipt.json").write_text(json.dumps(receipt, indent=1, sort_keys=True), encoding="utf-8")
    return receipt


def score_v2(audit_dir: Path) -> dict:
    sample = json.loads((audit_dir / "sample.json").read_text(encoding="utf-8"))
    receipt = json.loads((audit_dir / "freeze-receipt.json").read_text(encoding="utf-8"))
    if sha256((audit_dir / "sample.json").read_bytes()).hexdigest() != receipt["sample_sha256"]:
        raise ValueError("sample.json differs from the frozen receipt")
    items = json.loads((audit_dir / "items.json").read_text(encoding="utf-8"))
    judged, _ = load_answers(audit_dir / "answers")
    rel_ids = [item_id("rel", e) for e in sample["axes"]["evaluated_on_single_paper"]["edge_ids"]]
    mem_ids = [item_id("member", e) for e in sample["axes"]["member_of"]["MEMBER_OF"]]
    relation = relation_precision({"ids": {"same_sentence": rel_ids}, "population": {"same_sentence": len(rel_ids)}}, judged, items)
    pairs = [(judged[i]["A"]["verdict"], judged[i]["B"]["verdict"]) for i in items if i in judged and "A" in judged[i] and "B" in judged[i]]
    from scientific_network.evaluation.edge_audit import cohens_kappa
    kappa = cohens_kappa(pairs)
    return {"evaluated_on_single_paper": {"shown_paper_supports_the_relation": relation["strata"]["same_sentence"]["every_shown_paper_supports"],
                                           "unclear": relation["strata"]["same_sentence"]["unclear"],
                                           "sensitivity_unclear_as_incorrect": relation["strata"]["same_sentence"]["sensitivity_unclear_as_incorrect"],
                                           "sampled": len(rel_ids), "population": len(rel_ids)},
            "member_of": precision(mem_ids, judged) | {"population": sample["axes"]["member_of"]["population"]},
            "agreement": {"items_judged_by_both": len(pairs), "observed_agreement": round(sum(a == b for a, b in pairs) / len(pairs), 4) if pairs else None,
                          "cohens_kappa": None if kappa is None else round(kappa, 4)},
            "member_of_by_channel": {ch: dict(Counter(judged[i][ch]["verdict"] for i in mem_ids if ch in judged[i])) for ch in ("A", "B")},
            "disagreements_by_axis": dict(Counter(items[i]["axis"] for i in items if i in judged and "A" in judged[i] and "B" in judged[i] and judged[i]["A"]["verdict"] != judged[i]["B"]["verdict"])),
            "channel_c_items": sum(1 for i in items if i in judged and "C" in judged[i]),
            "items_answered": sum(1 for i in items if i in judged), "items_frozen": len(items)}


# ---------------------------------------------------------------------------
# Report: v2 figures next to v1, rule decisions, counts

def _fmt(w: dict | None) -> str:
    if not w or w.get("estimate") is None:
        return "n/a"
    return f"{w['estimate']:.3f} [{w['low']:.3f}, {w['high']:.3f}] (k={w['k']}, n={w['n']})"


def build_quality_v2(*, audit_dir: Path, v1_quality: dict, v1_summary: dict, v2_summary: dict, reports_dir: Path, run_info: dict, output: Path) -> dict:
    """quality.json and quality.md for enrichment v2: rule decisions, counts before and after, fresh audit figures, carried-over v1 axes."""
    scored = score_v2(audit_dir)
    part = json.loads((reports_dir / "part-of-dev-check.json").read_text(encoding="utf-8"))
    rel = json.loads((reports_dir / "relation-rule-decision.json").read_text(encoding="utf-8"))
    link = json.loads((reports_dir / "link-dev-check.json").read_text(encoding="utf-8"))
    v1c, v2c = v1_summary["counts"]["enrichment_layer"], v2_summary["counts"]["enrichment_layer"]
    keys = ("nodes", "edges")
    before_after = {
        "graph_version": [v1_summary["graph_version"], v2_summary["graph_version"]],
        "graph_sha256": [v1_summary["graph_sha256"], v2_summary["graph_sha256"]],
        "total_nodes": [v1_summary["counts"]["total"]["nodes"], v2_summary["counts"]["total"]["nodes"]],
        "total_edges": [v1_summary["counts"]["total"]["edges"], v2_summary["counts"]["total"]["edges"]],
        **{f"enrichment_{k}": [v1c[k], v2c[k]] for k in keys},
        **{f"nodes_{label}": [v1c["nodes_by_label"].get(label, 0), v2c["nodes_by_label"].get(label, 0)] for label in ("Method", "Task", "Dataset", "Organization")},
        **{f"edges_{rel_}": [v1c["edges_by_relation"].get(rel_, 0), v2c["edges_by_relation"].get(rel_, 0)]
           for rel_ in ("PART_OF", "MEMBER_OF", "APPLIED_TO", "EVALUATED_ON", "RELATED_TO")},
        "linked_entities": [v1c["linked_entities"], v2c["linked_entities"]],
    }
    v1p = v1_quality["predicate_precision"]
    report = {"evaluation_kind": "ai_assessed", "graph_version": v2_summary["graph_version"], "graph_sha256": v2_summary["graph_sha256"],
              "base_enrichment_graph_version": v1_summary["graph_version"], "seed": AUDIT_SEED,
              "rule_decisions": {"part_of_v2": {"adopted": False, "criterion": part["criterion"], "kept_precision": part["kept_precision"],
                                                 "correct_retained_share": part["correct_retained_share"], "passes": part["passes"]},
                                 "member_of": {"adopted": True, **part["member_of"]},
                                 "single_paper_same_sentence_applied_to": {"adopted": False, "dev_same_sentence": rel["APPLIED_TO"]["dev_labels_same_sentence"]["precision"],
                                                                           "dev_cross_sentence": rel["APPLIED_TO"]["dev_labels_cross_sentence"]["precision"],
                                                                           "informational_not_used": rel["APPLIED_TO"]["informational_supplementary_sample_not_used_for_adoption"]},
                                 "single_paper_same_sentence_evaluated_on": {"adopted": True, **rel["EVALUATED_ON"]["supplementary_sample"]},
                                 "link_guard": {"adopted": False, "kept_accuracy": link["kept_accuracy"], "criterion": link["criterion"],
                                                "correct_links_retained_share": link["correct_links_retained_share"]}},
              "counts_before_after": before_after, "e4_v2": scored,
              "carried_over_from_v1_not_remeasured": {
                  "entity_precision_default": v1_quality["entity_precision_by_variant"]["default"]["all_types"],
                  "paper_edges": v1p["paper_edges"], "applied_to_two_or_more_papers": v1p["entity_relations"]["APPLIED_TO"]["population_weighted_estimate"],
                  "related_to": v1p["related_to"], "part_of_v1_names_only": v1p["part_of"]["PART_OF"], "part_of_v2_packet_supplementary": v1_quality["supplementary_part_of_v2"]["v2"],
                  "linking": v1_quality["linking_accuracy"]["link"], "recall_default": v1_quality["recall_estimate_by_variant"]["default"]["all"]},
              "targets": {"relation_precision": 0.80, "linking_accuracy": 0.85, "part_of": 0.80, "member_of": "no target declared"},
              "run_info": run_info,
              "interpretation": "AI-assessed by agent evaluators; not human annotation and not independently validated gold labels. Wilson 95% intervals exclude evaluator error. Development labels are from the building session and are not an audit."}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    output.with_suffix(".md").write_text(render_md(report), encoding="utf-8")
    return report


def render_md(r: dict) -> str:
    d, b, e = r["rule_decisions"], r["counts_before_after"], r["e4_v2"]
    c = r["carried_over_from_v1_not_remeasured"]
    ri = r["run_info"]
    lines = [
        "# Enrichment v2 quality (AI-assessed)", "",
        f"Graph `{r['graph_version']}` (SHA-256 `{r['graph_sha256'][:16]}...`), built from the cached v1 inputs on top of `{r['base_enrichment_graph_version']}`; audit seed {r['seed']}. "
        f"{r['interpretation']}", "",
        f"Evaluators: {ri.get('evaluators', 'unknown')}. Isolation: {ri.get('isolation', 'unknown').rstrip('.')}.", "",
        "Each cell: estimate [Wilson 95% interval] (k correct, n decided). Unclear verdicts are excluded from the primary figure and counted as incorrect in the sensitivity.", "",
        "## Rule decisions (criteria declared before measuring; D042 amendment 2026-11-25)", "",
        "| Rule | Declared criterion | Measured on development material | Decision |", "|---|---|---|---|",
        f"| PART_OF v2 | kept precision >= {d['part_of_v2']['criterion']['kept_precision_at_least']} and >= {d['part_of_v2']['criterion']['correct_retained_at_least']:.0%} of correct edges kept | "
        f"kept precision {_fmt(d['part_of_v2']['kept_precision'])}; correct edges kept {d['part_of_v2']['correct_retained_share']:.3f} | **not adopted** (v1 PART_OF unchanged) |",
        f"| MEMBER_OF | >= {d['member_of']['criterion']['edges_at_least']} edges on the graph and precision >= {d['member_of']['criterion']['precision_at_least']} | "
        f"{d['member_of']['full_graph_member_of_edges']} edges; {_fmt(d['member_of']['precision'])} (unclear as incorrect {_fmt(d['member_of']['unclear_as_incorrect'])}) | **adopted**, additional predicate |",
        f"| single paper, same sentence: APPLIED_TO | same-sentence precision >= 0.80 and 0.15 above cross-sentence (dev reference labels) | "
        f"same {_fmt(d['single_paper_same_sentence_applied_to']['dev_same_sentence'])}; cross {_fmt(d['single_paper_same_sentence_applied_to']['dev_cross_sentence'])} | **not adopted** |",
        f"| single paper, same sentence: EVALUATED_ON | >= 0.80 correct on a supplementary development sample (dev labels hold one prediction) | "
        f"{_fmt(d['single_paper_same_sentence_evaluated_on']['precision'])}; pool of 24 (declared 30) | **adopted** |",
        f"| linking guard (narrower page) | kept accuracy >= {d['link_guard']['criterion']['kept_accuracy_at_least']} and >= {d['link_guard']['criterion']['correct_retained_at_least']:.0%} of correct links kept | "
        f"kept accuracy {_fmt(d['link_guard']['kept_accuracy'])}; correct links kept {d['link_guard']['correct_links_retained_share']:.3f} | **not adopted** (v1 links unchanged) |", "",
        "Development labels come from the building session (AI-assessed development material, frozen and committed before each rule was applied); "
        "they are not an audit. The informational APPLIED_TO sample (same abstract-support rubric as EVALUATED_ON) scored "
        f"{_fmt(d['single_paper_same_sentence_applied_to']['informational_not_used']['precision_abstract_supports_relation'])}; it was measured after the adoption decision and was not used for it.", "",
        "## Counts before and after", "", "| Quantity | v1 | v2 |", "|---|---|---|"]
    for key in ("total_nodes", "total_edges", "enrichment_nodes", "enrichment_edges", "nodes_Method", "nodes_Task", "nodes_Dataset", "nodes_Organization",
                "edges_PART_OF", "edges_MEMBER_OF", "edges_APPLIED_TO", "edges_EVALUATED_ON", "edges_RELATED_TO", "linked_entities"):
        lines.append(f"| {key} | {b[key][0]:,} | {b[key][1]:,} |")
    em, mo, ag = e["evaluated_on_single_paper"], e["member_of"], e["agreement"]
    lines += ["", "## E4 v2 audit: changed axes, fresh samples", "", "| Axis | Primary | Unclear | Unclear as incorrect | Target |", "|---|---|---|---|---|",
              f"| EVALUATED_ON, single paper, same sentence (all {em['population']}; the shown paper supports the relation) | {_fmt(em['shown_paper_supports_the_relation'])} | {em['unclear']} | "
              f"{_fmt(em['sensitivity_unclear_as_incorrect'])} | relation precision >= 0.80 |",
              f"| MEMBER_OF ({mo['sampled']} of population {mo['population']}; fresh, excludes v1-audited and development pairs) | {_fmt(mo)} | {mo['unclear']} | "
              f"{_fmt(mo['sensitivity_unclear_as_incorrect'])} | none declared |", "",
              f"Raw A/B agreement on all {ag['items_judged_by_both']} items: {ag['observed_agreement']}, Cohen's kappa {ag['cohens_kappa']} (kappa is low because nearly every item is correct, so chance agreement is high); "
              f"{e['channel_c_items']} disagreements went to adjudicator C, by axis {e['disagreements_by_axis']}. Items answered: {e['items_answered']} of {e['items_frozen']}.", "",
              f"**Caveat on MEMBER_OF.** Disagreement was almost entirely about whether \"is part of an ELIXIR national node\" (a Wikidata part-of statement to a consortium node) establishes membership. "
              f"Channel A judged {e['member_of_by_channel']['A']}; channel B alone judged {e['member_of_by_channel']['B']} (B called the membership role unspecified for the node partners). "
              f"Adjudicator C resolved all 14 disputed items as correct, so the headline figure follows A and C's reading. Under B's stricter reading, unclear counted as incorrect, `MEMBER_OF` would be about "
              f"{e['member_of_by_channel']['B'].get('correct', 0)}/{mo['sampled']}. Neither reading is a human annotation; the interval covers sampling error only.", "",
              "## Targets (declared in specification 4.5; pass or fail, not tuned)", "",
              "| Target | Figure | Result |", "|---|---|---|",
              f"| relation precision >= 0.80, v2-changed axis (EVALUATED_ON single paper) | {_fmt(em['shown_paper_supports_the_relation'])} | {'pass' if em['shown_paper_supports_the_relation']['estimate'] >= 0.80 else 'fail'} |",
              f"| relation precision >= 0.80, paper edges (v1, unchanged) | {', '.join(f'{k} {v['estimate']:.3f}' for k, v in c['paper_edges'].items())} | pass |",
              f"| relation precision >= 0.80, PART_OF (v1 rule remains in the graph) | {c['part_of_v1_names_only']['estimate']:.3f} | **fail** (rule v2 not adopted) |",
              f"| relation precision >= 0.80, RELATED_TO (v1, unchanged) | {c['related_to']['RELATED_TO']['estimate']:.3f} | **fail** |",
              f"| entity precision >= 0.85 (v1, unchanged) | {c['entity_precision_default']['estimate']:.3f} | pass |",
              f"| linking accuracy >= 0.85 (v1, unchanged; guard not adopted) | {c['linking']['estimate']:.3f} | **fail** |",
              "| MEMBER_OF | no target declared | n/a |", "",
              "## Axes carried over from v1 (not re-measured; unchanged by v2)", "",
              "| Axis | v1 figure |", "|---|---|",
              f"| entity precision, default variant | {_fmt(c['entity_precision_default'])} |",
              *[f"| paper edge {k} | {_fmt(v)} |" for k, v in c["paper_edges"].items()],
              f"| APPLIED_TO (two or more papers), population-weighted | {c['applied_to_two_or_more_papers']['every_shown_paper_supports']} (all 32 v1 edges audited; population-weighted over the cross- and same-sentence strata) |",
              f"| RELATED_TO | {_fmt(c['related_to']['RELATED_TO'])} |",
              f"| PART_OF (v1 packet; v1 rule is still the graph's PART_OF) | {_fmt(c['part_of_v1_names_only'])}; v2 packet {_fmt(c['part_of_v2_packet_supplementary'])}; target 0.80 not met |",
              f"| linking | {_fmt(c['linking'])}; target 0.85 not met |",
              f"| recall estimate, default variant | {_fmt(c['recall_default'])} |", "",
              "v1 PART_OF and linking figures apply unchanged to the v2 graph: the PART_OF v2 rule and the linking guard were not adopted. Wilson 95% intervals describe sampling error only."]
    return "\n".join(lines) + "\n"
