"""Frozen deterministic venue-balanced splits; test papers never enter the pilot."""

from collections import Counter, defaultdict
from pathlib import Path
import re
import unicodedata

from scientific_network.collect.storage import digest, read_config, read_jsonl, write_json, write_table


def title_group(title: str) -> str:
    # Conservative leakage guard, NOT a claim that equal titles prove work identity.
    return digest(re.sub(r"\W+", "", unicodedata.normalize("NFKC", title).casefold()).encode())


def allocate(rows: list[dict], *, seed: int, test: int, development: int, pilot: int) -> list[dict]:
    venues = sorted({r["venue_id"] for r in rows if r["status"] == "included"})
    if not venues or pilot % len(venues):
        raise ValueError("pilot size must balance exactly across venues")
    groups = defaultdict(set)
    for row in rows:
        if row["status"] == "included":
            groups[row["venue_id"]].add(title_group(row["title"]))
    roles, pilot_groups = {}, set()
    per_venue = pilot // len(venues)
    if per_venue < development:
        raise ValueError("pilot must have room for the development subset")
    for venue in venues:
        ordered = sorted(groups[venue], key=lambda group: digest(f"{seed}|{venue}|{group}".encode()))
        if len(ordered) < test + per_venue:
            raise ValueError(f"insufficient distinct leakage groups for {venue}")
        for index, group in enumerate(ordered):
            role = "test" if index < test else "development" if index < test + development else "pool"
            if group in roles and roles[group] != role:
                raise ValueError("cross-venue duplicate title needs manual split reconciliation")
            roles[group] = role
            if test <= index < test + per_venue:
                pilot_groups.add(group)
    result = [{"paper_id": r["paper_id"], "venue_id": r["venue_id"],
        "leakage_group": title_group(r["title"]), "split": roles[title_group(r["title"])],
        "is_pilot": title_group(r["title"]) in pilot_groups}
        for r in rows if r["status"] == "included"]
    if any(r["is_pilot"] and r["split"] == "test" for r in result):
        raise ValueError("held-out group overlaps pilot")
    # Multiple versions are reserved as a group, but never silently alter the requested paper counts.
    for venue in venues:
        selected = [r for r in result if r["venue_id"] == venue]
        if sum(r["split"] == "test" for r in selected) != test or sum(r["is_pilot"] for r in selected) != per_venue:
            raise ValueError("duplicate versions alter split sizes; reconcile before freezing")
    return sorted(result, key=lambda row: row["paper_id"])


def freeze_splits(manifest: Path, quality: Path, corpus: Path, output: Path) -> dict:
    config, corpus_config = read_config(quality), read_config(corpus)
    if corpus_config.get("legacy_membership"):
        from scientific_network.collect.extended import freeze_extended
        return freeze_extended(manifest, quality, corpus, output)
    held_out = config["held_out"]
    rows = allocate(read_jsonl(manifest), seed=held_out["random_seed"],
        test=held_out["test_papers_per_venue"], development=held_out["development_papers_per_venue"],
        pilot=corpus_config["pilot"]["papers"])
    write_table(output / "membership.parquet", rows)
    summary = {"stage": "split", "seed": held_out["random_seed"],
        "manifest_sha256": digest(manifest.read_bytes()),
        "quality_sha256": digest(quality.read_bytes()), "corpus_config_sha256": digest(corpus.read_bytes()),
        "membership_sha256": digest((output / "membership.jsonl").read_bytes()),
        "by_venue_split": dict(Counter(f"{r['venue_id']}:{r['split']}" for r in rows)),
        "pilot_by_venue": dict(Counter(r["venue_id"] for r in rows if r["is_pilot"])),
        "held_out_pilot_overlap": 0, "annotation_status": "reserved_unannotated"}
    write_json(output / "summary.json", summary)
    return summary
