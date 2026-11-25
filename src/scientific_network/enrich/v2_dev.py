"""Enrichment v2 development checks and development samples (D042 amendment 2026-11-25).

Everything here uses material outside the v1 audit: the 100 development papers and their frozen reference labels, and seeded
draws that exclude every v1-audited item. Labels for the drawn samples come from the building session, are AI-assessed
development material only, and are frozen (hashed and committed) before a rule is applied to them.
"""

from __future__ import annotations

import json
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

from scientific_network.enrich.k1 import read_jsonl
from scientific_network.enrich.quality import draw, wilson
from scientific_network.enrich.scoring import score_relations
from scientific_network.enrich.textutil import acronym_map, expand, jaccard

DEV_SEED = 2026112501


def dev_relation_check(paper_relations: list[dict], labels: list[dict], texts: dict[str, str]) -> dict:
    """Paper-level precision of extracted relations on the dev papers, split by ``same_sentence`` (K1 lenient matching).

    Each stratum is matched to the reference one-to-one on its own, so the figure is the share of that stratum's predictions
    that correspond to a reference relation. ``reference`` counts all labeled relations of that predicate.
    """
    dev = {label["paper_id"] for label in labels}
    out: dict = {}
    for relation in ("APPLIED_TO", "EVALUATED_ON"):
        out[relation] = {}
        for stratum, flag in (("same_sentence", True), ("cross_sentence", False)):
            predictions: dict[str, list] = defaultdict(list)
            for rel in paper_relations:
                if rel["paper_id"] in dev and rel["relation"] == relation and bool(rel["same_sentence"]) == flag:
                    predictions[rel["paper_id"]].append((rel["head_key"], relation, rel["tail_key"]))
            scored = score_relations(predictions, labels, texts)[relation]
            out[relation][stratum] = {"predicted": scored["predicted"], "matched": scored["tp"], "reference": scored["reference"],
                                      "precision": wilson(scored["tp"], scored["predicted"])}
    return out


def freeze_labels(path: Path, rows: list[dict], *, purpose: str) -> dict:
    """Write labeled development rows and a hash receipt next to them (frozen before any rule is applied)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    receipt = {"purpose": purpose, "labels": str(path), "sha256": sha256(path.read_bytes()).hexdigest(), "rows": len(rows),
               "evaluation_kind": "ai_assessed_development_material", "labeler": "building session (Claude Sonnet 5.5)",
               "note": "development material only; not an independent audit; frozen before the rule was applied"}
    path.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def seeded_draw(pool: list[str], excluded: set[str], size: int, purpose: str, seed: int = DEV_SEED) -> list[str]:
    return draw(sorted(set(pool) - excluded), size, seed, purpose)
