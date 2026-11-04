"""Additive roster discovery and prospectively frozen supplemental diagnostics."""

from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

from scientific_network.collect.storage import (SourceCache, SourceError, digest, read_config,
    read_jsonl, write_json, write_table)
from scientific_network.collect.splits import title_group


def discover_extended(config_path: Path, output: Path, cache_path: Path) -> dict:
    from scientific_network.collect.discover import parse_index
    config = read_config(config_path)
    legacy = Path(config["legacy_manifest"])
    if digest(legacy.read_bytes()) != config["legacy_manifest_sha256"]:
        raise ValueError("legacy manifest differs from protected configuration")
    write_json(output / "inputs.json", {"config_sha256": digest(config_path.read_bytes())})

    def edition_task(edition):
        name = edition["venue_id"].split(":")[1]
        destination = output / "editions" / name
        if (destination / "summary.json").exists():
            summary = json.loads((destination / "summary.json").read_text())
            return read_jsonl(destination / "roster.jsonl"), summary
        records, sources = [], []
        if edition.get("legacy"):
            records = [r for r in read_jsonl(legacy) if r["venue_id"] == edition["venue_id"]]
        elif edition.get("adapter"):
            try:
                with SourceCache(cache_path, timeout=config["retrieval"]["timeout_seconds"],
                                 attempts=config["retrieval"]["max_attempts"]) as cache:
                    if edition.get("edition_verification"):
                        from bs4 import BeautifulSoup
                        verification = edition["edition_verification"]
                        body, source = cache.get(verification["url"])
                        text = BeautifulSoup(body, "html.parser").get_text(" ", strip=True)
                        if digest(body) != verification["sha256"] or verification["required_text"] not in text:
                            raise ValueError("official edition/year mapping changed; review required")
                        sources.append(source)
                    for page in edition.get("pages", [edition["official_index"]]):
                        subedition = {**edition, **(page if isinstance(page, dict) else {"official_index": page})}
                        body, source = cache.get(subedition["official_index"], params=subedition.get("params"))
                        records.extend(parse_index(body, subedition, source))
                        sources.append(source)
                status = "collected" if all(r["status"] != "review" for r in records) else "needs_review"
                if len({r["paper_id"] for r in records}) != len(records):
                    raise ValueError("duplicate official IDs across roster pages")
            except (SourceError, ValueError) as exc:
                # Partial pages remain visible but cannot feed the frozen sample.
                status = "blocked"
                summary = {"venue_id": edition["venue_id"], "year": edition["year"],
                    "status": status, "reason": str(exc), "records": len(records), "sources": sources}
                write_table(destination / "roster.parquet", records)
                write_json(destination / "summary.json", summary)
                print(f"discover: {name}: blocked: {exc}", flush=True)
                return records, summary
        else:
            status = edition.get("edition_status", "unresolved_source")
        if edition.get("legacy"):
            status = "legacy_preserved"
        summary = {"venue_id": edition["venue_id"], "year": edition["year"], "status": status,
            "reason": edition.get("reason", "official_roster_parsed"), "records": len(records),
            "by_status": dict(Counter(r["status"] for r in records)), "sources": sources}
        write_table(destination / "roster.parquet", records)
        write_json(destination / "summary.json", summary)
        print(f"discover: {name}: {status}: {len(records)} records", flush=True)
        return records, summary

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(edition_task, config["editions"]))
    rows = sorted([r for records, _ in results for r in records], key=lambda r: r["paper_id"])
    ledger = [summary for _, summary in results]
    write_table(output / "edition-ledger.parquet", ledger)
    write_table(output / "corpus_manifest.parquet", rows)
    summary = {"stage": "discover", "parser_version": "extended-official-roster-v1",
        "config_sha256": digest(config_path.read_bytes()), "roster_records": len(rows),
        "by_venue_status": dict(Counter(f"{r['venue_id']}:{r['status']}" for r in rows)),
        "edition_statuses": dict(Counter(r["status"] for r in ledger)),
        "incomplete_editions": sum(r["status"] not in {"collected", "legacy_preserved", "no_2023_edition"} for r in ledger),
        "manifest_sha256": digest((output / "corpus_manifest.jsonl").read_bytes()),
        "review_required": sum(r["status"] == "review" for r in rows)}
    write_json(output / "summary.json", summary)
    return summary


def allocate_extended(rows: list[dict], previous: list[dict], *, seed: int,
                      diagnostic_per_venue: int, eligible_venues: set[str]) -> list[dict]:
    old = {r["paper_id"]: r for r in previous}
    included = {r["paper_id"]: r for r in rows if r["status"] == "included"}
    if not old.keys() <= included.keys():
        raise ValueError("legacy membership missing from expanded roster")
    groups = defaultdict(list)
    for r in included.values():
        groups[title_group(r["title"])].append(r)
    result = [dict(r) for r in previous]
    by_venue = defaultdict(list)
    for group, records in groups.items():
        newcomers = [r for r in records if r["paper_id"] not in old]
        if not newcomers:
            continue
        # Do not silently deduplicate works or introduce newly exposed test records.
        # All additional versions of an existing title, even a pool title, are withheld.
        if len(records) > 1 or any(r["paper_id"] in old for r in records):
            role = "test" if any(old.get(r["paper_id"], {}).get("split") == "test" for r in records) else "review"
            for r in newcomers:
                result.append(dict(paper_id=r["paper_id"], venue_id=r["venue_id"],
                    leakage_group=group, split=role, is_pilot=False))
        elif records[0]["venue_id"] not in eligible_venues:
            r = records[0]
            result.append(dict(paper_id=r["paper_id"], venue_id=r["venue_id"],
                leakage_group=group, split="review", is_pilot=False))
        else:
            by_venue[records[0]["venue_id"]].append((group, records[0]))
    for venue, entries in sorted(by_venue.items()):
        ordered = sorted(entries, key=lambda pair: digest(f"{seed}|{venue}|{pair[0]}".encode()))
        count = len(ordered)
        # Prospective small-edition rule, without changing release accuracy gates.
        test = 60 if count >= 100 else max(1, count // 5)
        development = 30 if count >= 100 else max(diagnostic_per_venue, count // 10)
        if count < test + development or development < diagnostic_per_venue:
            raise ValueError(f"insufficient independent groups for {venue}; explicit allocation review needed")
        for index, (group, row) in enumerate(ordered):
            result.append(dict(paper_id=row["paper_id"], venue_id=venue, leakage_group=group,
                split="test" if index < test else "development" if index < test + development else "pool",
                is_pilot=test <= index < test + diagnostic_per_venue))
    result.sort(key=lambda r: r["paper_id"])
    if len({r["paper_id"] for r in result}) != len(included):
        raise ValueError("incomplete or duplicate split membership")
    for r in result:
        if r["paper_id"] in old and r != old[r["paper_id"]]:
            raise ValueError("legacy split assignment changed")
    test_groups = {r["leakage_group"] for r in result if r["split"] == "test"}
    if any(r["is_pilot"] and r["leakage_group"] in test_groups for r in result):
        raise ValueError("held-out leakage group overlaps diagnostic sample")
    return result


def freeze_extended(manifest: Path, quality: Path, corpus: Path, output: Path) -> dict:
    config = read_config(corpus)
    previous = Path(config["legacy_membership"])
    if digest(previous.read_bytes()) != config["legacy_membership_sha256"]:
        raise ValueError("legacy membership changed")
    discovered = json.loads((manifest.parent / "summary.json").read_text())
    if discovered["config_sha256"] != digest(corpus.read_bytes()) or discovered["manifest_sha256"] != digest(manifest.read_bytes()):
        raise ValueError("manifest or configuration changed since discovery")
    ledger = read_jsonl(manifest.parent / "edition-ledger.jsonl")
    eligible = {r["venue_id"] for r in ledger if r["status"] in {"collected", "legacy_preserved"}}
    seed = read_config(quality)["held_out"]["random_seed"]
    rows = allocate_extended(read_jsonl(manifest), read_jsonl(previous), seed=seed,
        diagnostic_per_venue=config["pilot"]["new_papers_per_venue"], eligible_venues=eligible)
    write_table(output / "membership.parquet", rows)
    summary = {"stage": "split", "method_version": "legacy-preserving-supplemental-v1", "seed": seed,
        "manifest_sha256": digest(manifest.read_bytes()), "quality_sha256": digest(quality.read_bytes()),
        "corpus_config_sha256": digest(corpus.read_bytes()),
        "previous_membership_sha256": digest(previous.read_bytes()),
        "membership_sha256": digest((output / "membership.jsonl").read_bytes()),
        "edition_ledger_sha256": digest((manifest.parent / "edition-ledger.jsonl").read_bytes()),
        "by_venue_split": dict(Counter(f"{r['venue_id']}:{r['split']}" for r in rows)),
        "pilot_by_venue": dict(Counter(r["venue_id"] for r in rows if r["is_pilot"])),
        "held_out_pilot_overlap": 0, "legacy_assignments_preserved": len(read_jsonl(previous)),
        "annotation_status": "reserved_unannotated"}
    write_json(output / "summary.json", summary)
    return summary
