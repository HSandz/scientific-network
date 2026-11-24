"""Freeze the enrichment development and test splits before any prompt or threshold work.

Selection is deterministic: within each venue-year stratum, eligible papers (those
with an abstract) are ordered by SHA-256 of ``seed NUL paper_id``; development papers
take the first ``n_dev`` ranks and test papers the next ``n_test``. The two splits
are therefore disjoint by construction. Per-stratum quotas are proportional to the
eligible stratum size with largest-remainder rounding, computed separately for the
development and the test split.
"""

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

METHOD_VERSION = "enrichment-splits-v1"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _rank(seed: int, paper_id: str) -> str:
    return hashlib.sha256(f"{seed}\0{paper_id}".encode("utf-8")).hexdigest()


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid JSONL at {path}:{number}: {exc}") from exc
    return rows


def allocate_quotas(sizes: dict[str, int], total: int) -> dict[str, int]:
    """Proportional allocation by largest remainder; ties break on stratum key."""
    population = sum(sizes.values())
    if total < 0 or total > population:
        raise ValueError("quota total must be between 0 and the eligible population")
    exact = {key: total * size / population for key, size in sizes.items()}
    quota = {key: int(value) for key, value in exact.items()}
    leftover = total - sum(quota.values())
    order = sorted(sizes, key=lambda key: (-(exact[key] - quota[key]), key))
    for key in order[:leftover]:
        quota[key] += 1
    for key, value in quota.items():
        if value > sizes[key]:
            raise ValueError(f"stratum {key} cannot supply {value} papers")
    return quota


def eligible_papers(works: list[dict]) -> list[dict]:
    """Papers with a non-empty abstract, as ``{paper_id, venue_id, year}`` rows."""
    rows = []
    for work in works:
        abstract = ((work.get("openalex") or {}).get("abstract") or "").strip()
        if abstract:
            rows.append({"paper_id": work["paper_id"], "venue_id": work["venue_id"], "year": work["year"]})
    if len({row["paper_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate paper_id among eligible works")
    return rows


def draw_splits(eligible: list[dict], *, seed: int, n_dev: int, n_test: int) -> dict[str, list[dict]]:
    if n_dev < 1 or n_test < 1:
        raise ValueError("both splits must be nonempty")
    strata: dict[str, list[dict]] = defaultdict(list)
    for row in eligible:
        strata[f"{row['venue_id']}|{row['year']}"].append(row)
    sizes = {key: len(rows) for key, rows in strata.items()}
    dev_quota = allocate_quotas(sizes, n_dev)
    test_quota = allocate_quotas(sizes, n_test)
    result: dict[str, list[dict]] = {"development": [], "test": []}
    for key in sorted(strata):
        ranked = sorted(strata[key], key=lambda row: (_rank(seed, row["paper_id"]), row["paper_id"]))
        need = dev_quota[key] + test_quota[key]
        if need > len(ranked):
            raise ValueError(f"stratum {key} has {len(ranked)} papers, needs {need}")
        for row in ranked[: dev_quota[key]]:
            result["development"].append({**row, "stratum": key})
        for row in ranked[dev_quota[key]:need]:
            result["test"].append({**row, "stratum": key})
    for rows in result.values():
        rows.sort(key=lambda row: row["paper_id"])
    return result


def _audit_paper_sets(ledger_paths: list[Path]) -> dict[str, set[str]]:
    sets: dict[str, set[str]] = {}
    for path in ledger_paths:
        ids = set()
        for row in _read_jsonl(path):
            for key in ("paper_id", "unit_id"):
                if isinstance(row.get(key), str) and row[key].startswith("paper:"):
                    ids.add(row[key])
        sets[str(path)] = ids
    return sets


def freeze_enrichment_splits(
    works_path: Path,
    membership_path: Path,
    output_dir: Path,
    *,
    seed: int,
    n_dev: int = 100,
    n_test: int = 200,
    audit_ledgers: list[Path] | None = None,
    topic_test_path: Path | None = None,
) -> dict:
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError(f"refusing to overwrite existing splits: {output_dir}")
    works = _read_jsonl(works_path)
    eligible = eligible_papers(works)
    drawn = draw_splits(eligible, seed=seed, n_dev=n_dev, n_test=n_test)
    dev_ids = {row["paper_id"] for row in drawn["development"]}
    test_ids = {row["paper_id"] for row in drawn["test"]}
    if dev_ids & test_ids:
        raise ValueError("development and test splits overlap")

    membership = {row["paper_id"]: row["split"] for row in _read_jsonl(membership_path)}
    overlap = {"five_year_splits_v1": {}, "audit_samples": {}, "topic_test": None}
    for name, ids in (("development", dev_ids), ("test", test_ids)):
        counts = Counter(membership.get(pid, "absent_from_five_year_splits_v1") for pid in ids)
        overlap["five_year_splits_v1"][name] = dict(sorted(counts.items()))
    for path, ids in _audit_paper_sets(audit_ledgers or []).items():
        overlap["audit_samples"][path] = {
            "sample_papers": len(ids),
            "in_development": len(ids & dev_ids),
            "in_test": len(ids & test_ids),
            "test_paper_ids": sorted(ids & test_ids),
        }
    if topic_test_path is not None:
        topic_ids = {row["paper_id"] for row in _read_jsonl(topic_test_path) if "paper_id" in row}
        overlap["topic_test"] = {
            "path": str(topic_test_path), "papers": len(topic_ids),
            "in_development": len(topic_ids & dev_ids), "in_test": len(topic_ids & test_ids),
        }

    output_dir.mkdir(parents=True)
    files = {}
    for name in ("development", "test"):
        path = output_dir / f"{name}.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for row in drawn[name]:
                handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        files[f"{name}.jsonl"] = _sha256_file(path)

    def stratum_counts(rows):
        return dict(sorted(Counter(row["stratum"] for row in rows).items()))

    receipt = {
        "method_version": METHOD_VERSION,
        "rule": ("Eligible papers have a non-empty OpenAlex abstract. Strata are venue|year. "
                 "Per-stratum quotas are proportional (largest remainder), separately for each split. "
                 "Within a stratum papers are ranked by sha256(seed NUL paper_id); development takes "
                 "the first ranks, test the next, so the splits are disjoint."),
        "seed": seed,
        "sizes": {"development": len(drawn["development"]), "test": len(drawn["test"])},
        "eligible_papers": len(eligible),
        "corpus_papers": len(works),
        "papers_without_abstract": len(works) - len(eligible),
        "stratum_population": dict(sorted(Counter(f"{r['venue_id']}|{r['year']}" for r in eligible).items())),
        "stratum_counts": {"development": stratum_counts(drawn["development"]), "test": stratum_counts(drawn["test"])},
        "inputs": {
            "works": {"path": str(works_path), "sha256": _sha256_file(works_path)},
            "five_year_splits_membership": {"path": str(membership_path), "sha256": _sha256_file(membership_path)},
        },
        "overlap": overlap,
        "file_sha256": files,
        "discipline": ("Every prompt, threshold, cosine cut-off and support minimum is tuned on the development "
                       "papers only. Test-paper extraction outputs are not opened until the E4 audit sample is frozen."),
    }
    with (output_dir / "receipt.json").open("w", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return receipt
