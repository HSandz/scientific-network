"""PART_OF packet v2: the same 50 frozen items with the Wikidata statement shown (2026-11-25).

v1 showed only organization names and descriptions, so 14 of 50 items came back "unclear". v2 changes only the evidence displayed: no item,
no sample and no other axis changes. It was created after the v1 results were seen.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from scientific_network.enrich.quality import agreement, final_verdict, item_id, precision

PROPERTY_LABELS = {"P749": "parent organization", "P361": "part of"}
ANSWERS_DIR = "answers-partof-v2"
INSTRUCTION = ("You are an independent evaluator. Judge only from the text shown. Do not open other files, do not look at other evaluators' "
               "answers, and do not guess what the extractor was confident about. Answer correct, incorrect or unclear (unclear only when the "
               "text and your general knowledge cannot decide it) and give a note of at most 20 words. Part of: the extractor claims the first "
               "organization is a part, unit, subsidiary or member of the second, and cites the Wikidata statement shown. Is the claim true "
               "(is the first a part, unit, subsidiary or member of the second)?")


def statement_index(manifest_path: Path, raw_dir: Path) -> dict[tuple[str, str, str], dict]:
    """(child QID, parent QID, property) -> raw response hash and retrieval time, from the raw-store SPARQL parent queries."""
    index: dict[tuple[str, str, str], dict] = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["source"] != "wikidata_sparql" or "?prop" not in row["params"].get("query", ""):
            continue
        body = json.loads((raw_dir / row["sha256"][:2] / f"{row['sha256']}.json").read_text(encoding="utf-8"))
        for binding in body["results"]["bindings"]:
            key = (binding["item"]["value"].rsplit("/", 1)[-1], binding["parent"]["value"].rsplit("/", 1)[-1], binding["prop"]["value"])
            index[key] = {"raw_response_sha256": row["sha256"], "retrieved_at": row["retrieved_at"],
                          "parent_label": (binding.get("parentLabel") or {}).get("value")}
    return index


def build_packets(audit_dir: Path, graph: dict, wikidata: dict, statements: dict, out_dir: Path | None = None) -> dict:
    """Write items and A/B packets for the 50 PART_OF items already frozen in sample.json."""
    sample = json.loads((audit_dir / "sample.json").read_text())
    v1_items = json.loads((audit_dir / "items.json").read_text())
    edges = {e["edge_id"]: e for e in graph["edges"]}
    nodes = {n["id"]: n for n in graph["nodes"]}
    items = []
    for edge_id in sample["part_of_sample"]["PART_OF"]:
        edge = edges[edge_id]
        v1 = v1_items[item_id("part", edge_id)]
        child_qid = wikidata["matches"][edge["source_id"]]["qid"]
        parent_qid = edge["target_id"].rsplit(":", 1)[-1] if edge["target_id"].startswith("organization:wikidata:") else \
            wikidata["matches"][edge["target_id"]]["qid"]
        properties = [p for p in ("P749", "P361") if p in edge["properties"]["wikidata_property"].split("+")]
        shown = []
        for prop in properties:
            found = statements.get((child_qid, parent_qid, prop), {})
            shown.append({"property": prop, "property_label": PROPERTY_LABELS[prop], "statement": f"{child_qid} {prop} {parent_qid}",
                          "statement_item_url": f"https://www.wikidata.org/wiki/{child_qid}", "raw_response_sha256": found.get("raw_response_sha256"),
                          "retrieved_at": found.get("retrieved_at")})
        items.append({**v1, "organization_qid": child_qid, "organization_wikidata_label": wikidata["matches"][edge["source_id"]]["label"],
                      "parent_qid": parent_qid, "parent_wikidata_label": nodes[edge["target_id"]]["name"], "wikidata_statements": shown})
    assert len(items) == 50 and {i["item_id"] for i in items} == {item_id("part", e) for e in sample["part_of_sample"]["PART_OF"]}
    out_dir = out_dir or audit_dir / "packets-partof-v2"
    out_dir.mkdir(parents=True, exist_ok=True)
    packets = {}
    for channel in ("A", "B"):
        body = {"channel": channel, "kind": "judgement", "axis_version": "part_of_v2", "instructions": {"part_of": INSTRUCTION},
                "answer_format": {"file": f"answers/{channel}-partof-v2.jsonl",
                                  "line": {"item_id": "...", "verdict": "correct|incorrect|unclear", "note": "<=20 words"}},
                "items": items}
        path = out_dir / f"{channel}-partof-v2.json"
        path.write_text(json.dumps(body, indent=1, ensure_ascii=False))
        packets[channel] = {"path": str(path), "items": len(items), "sha256": sha256(path.read_bytes()).hexdigest()}
    missing = [i["item_id"] for i in items if any(s["raw_response_sha256"] is None for s in i["wikidata_statements"])]
    return {"packets": packets, "items": len(items), "items_without_raw_statement_hash": missing,
            "item_ids_sha256": sha256("\n".join(sorted(i["item_id"] for i in items)).encode()).hexdigest()}


def load_v2_answers(directory: Path) -> dict[str, dict[str, dict]]:
    judged: dict[str, dict[str, dict]] = {}
    for path in sorted(directory.glob("*.jsonl")):
        channel = path.name.split("-")[0]
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if row.get("verdict") in ("correct", "incorrect", "unclear"):
                    judged[row["item_id"]] = {**judged.get(row["item_id"], {}), channel: row}
    return judged


def score(audit_dir: Path, v1_result: dict) -> dict | None:
    """Primary and unclear-as-incorrect precision of PART_OF v2 next to the v1 result, with raw A/B kappa."""
    directory = audit_dir / ANSWERS_DIR
    if not directory.is_dir():
        return None
    judged = load_v2_answers(directory)
    sample = json.loads((audit_dir / "sample.json").read_text())
    ids = [item_id("part", e) for e in sample["part_of_sample"]["PART_OF"]]
    both = {i: ["A", "B"] for i in ids}
    return {"kind": "supplementary", "note": "PART_OF re-evaluated with the Wikidata statement shown; v1 is kept and shown beside it. "
            "Created after the v1 results were seen; only the evidence shown changed.",
            "v1": v1_result, "v2": precision(ids, judged), "agreement_raw_ab": agreement({}, both, judged),
            "channel_c_items": sum(1 for i in ids if "C" in judged.get(i, {}))}
