"""Freeze the D040 topic test sample before classifier tuning."""

from collections import defaultdict
import hashlib
import json
from pathlib import Path


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {path}:{number}: {exc}") from exc
    return rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _rank(seed: int, group: str) -> str:
    return hashlib.sha256(f"{seed}\0{group}".encode("utf-8")).hexdigest()


def freeze_topic_test(
    roster_path: Path,
    membership_path: Path,
    leakage_path: Path,
    output_path: Path,
    *,
    seed: int,
    ijcai_size: int = 30,
    aaai_size: int = 20,
    ijcai_frame_size: int = 80,
) -> dict:
    """Select existing IJCAI tests and new AAAI tests, holding out each full candidate group.

    Sampling is deterministic SHA-256 rank ordering. Candidate groups that intersect an
    existing development or test group are excluded from the new AAAI sample, so known
    siblings cannot leak between classifier development and the blind topic test.
    """
    for value, name in ((seed, "seed"), (ijcai_size, "ijcai_size"), (aaai_size, "aaai_size"),
                        (ijcai_frame_size, "ijcai_frame_size")):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name} must be a nonnegative integer")
    if ijcai_size == 0 or aaai_size == 0:
        raise ValueError("both topic-test samples must be nonempty")
    if ijcai_size > ijcai_frame_size:
        raise ValueError("ijcai_size cannot exceed the frozen IJCAI test-frame size")
    if output_path.exists() or output_path.is_symlink():
        raise ValueError(f"refusing to overwrite existing topic-test manifest: {output_path}")

    roster_rows = _read_jsonl(roster_path)
    membership_rows = _read_jsonl(membership_path)
    leakage_rows = _read_jsonl(leakage_path)
    in_scope = {
        row["paper_id"]: row for row in roster_rows
        if row.get("status") == "included"
        and row.get("venue_id") in {"venue:aaai", "venue:ijcai"}
        and row.get("year") in {2021, 2022, 2023, 2024, 2025}
    }
    membership_by_id = {row["paper_id"]: row for row in membership_rows}
    ids_by_membership_group: dict[str, set[str]] = defaultdict(set)
    for row in membership_rows:
        ids_by_membership_group[row["leakage_group"]].add(row["paper_id"])
    leakage_by_id: dict[str, dict] = {}
    for row in leakage_rows:
        for paper_id in row.get("candidate_paper_ids", [row.get("paper_id")]):
            if paper_id:
                leakage_by_id[paper_id] = row

    def heldout_group(paper_id: str) -> tuple[str, set[str]]:
        ids = {paper_id}
        assignment = membership_by_id.get(paper_id)
        if assignment:
            ids.update(ids_by_membership_group[assignment["leakage_group"]])
        triage = leakage_by_id.get(paper_id)
        if triage:
            ids.update(triage.get("candidate_paper_ids") or [paper_id])
        group = (assignment or {}).get("leakage_group") or (triage or {}).get("leakage_candidate_group") or paper_id
        return group, ids

    ijcai_candidates = []
    all_frozen_test_ids, development_ids = set(), set()
    for row in membership_rows:
        if row.get("split") == "test":
            all_frozen_test_ids.add(row["paper_id"])
        elif row.get("split") == "development":
            development_ids.add(row["paper_id"])
        if row.get("split") == "test" and row.get("venue_id") == "venue:ijcai":
            paper_id = row["paper_id"]
            paper = in_scope.get(paper_id)
            if paper:
                ijcai_candidates.append((row, paper))
    if len(ijcai_candidates) < ijcai_size:
        raise ValueError(f"need {ijcai_size} in-scope IJCAI test papers; found {len(ijcai_candidates)}")
    if len(ijcai_candidates) != ijcai_frame_size:
        raise ValueError(f"expected {ijcai_frame_size} in-scope IJCAI test papers; found {len(ijcai_candidates)}")
    if len({row["leakage_group"] for row, _ in ijcai_candidates}) != len(ijcai_candidates):
        raise ValueError("frozen IJCAI test sample contains multiple papers from one leakage group")

    selected_ijcai = sorted(
        ijcai_candidates,
        key=lambda pair: (_rank(seed, pair[0]["leakage_group"]), pair[0]["paper_id"]),
    )[:ijcai_size]
    selected_ijcai_ids = {row["paper_id"] for row, _ in selected_ijcai}
    selected_ijcai_groups = {row["leakage_group"] for row, _ in selected_ijcai}

    aaai_groups: dict[str, set[str]] = defaultdict(set)
    for paper_id, paper in in_scope.items():
        if paper["venue_id"] == "venue:aaai":
            group, ids = heldout_group(paper_id)
            aaai_groups[group].update(ids)

    aaai_candidates = []
    for group, ids in aaai_groups.items():
        # Groups already assigned anywhere, or overlapping any frozen IJCAI test, cannot
        # be sampled as new AAAI tests. This preserves old development/test assignments.
        assignments = [membership_by_id[pid] for pid in ids if pid in membership_by_id]
        if any(item["split"] in {"development", "test"} for item in assignments):
            continue
        if ids & all_frozen_test_ids:
            continue
        if group in selected_ijcai_groups:
            continue
        aaai_ids = sorted(pid for pid in ids if in_scope.get(pid, {}).get("venue_id") == "venue:aaai")
        if not aaai_ids:
            continue
        # One test unit per group; all candidate versions remain in heldout_paper_ids.
        representative = aaai_ids[0]
        aaai_candidates.append((group, representative, ids))
    if len(aaai_candidates) < aaai_size:
        raise ValueError(f"need {aaai_size} leakage-safe AAAI test groups; found {len(aaai_candidates)}")
    selected_aaai = sorted(
        aaai_candidates,
        key=lambda item: (_rank(seed, item[0]), item[1]),
    )[:aaai_size]

    source_hashes = {
        "roster_sha256": _sha256(roster_path),
        "membership_sha256": _sha256(membership_path),
        "leakage_sha256": _sha256(leakage_path),
    }
    source_files = {
        "roster": str(roster_path), "membership": str(membership_path), "leakage": str(leakage_path),
    }
    output_rows = []
    for membership, paper in selected_ijcai:
        _, heldout_ids = heldout_group(paper["paper_id"])
        if heldout_ids & development_ids:
            raise ValueError(f"IJCAI test group intersects development: {paper['paper_id']}")
        output_rows.append({
            "paper_id": paper["paper_id"], "venue_id": paper["venue_id"], "year": paper["year"],
            "role": "topic_test", "sample_source": "frozen_ijcai_test_membership",
            "source_split": membership["split"], "source_leakage_group": membership["leakage_group"],
            "selection_rank_sha256": _rank(seed, membership["leakage_group"]),
            "heldout_paper_ids": sorted(heldout_ids), "seed": seed, "source_files": source_files, **source_hashes,
        })
    for group, paper_id, heldout_ids in selected_aaai:
        if heldout_ids & development_ids:
            raise ValueError(f"AAAI test group intersects development: {paper_id}")
        paper = in_scope[paper_id]
        output_rows.append({
            "paper_id": paper_id, "venue_id": paper["venue_id"], "year": paper["year"],
            "role": "topic_test", "sample_source": "new_aaai_roster_reservation",
            "source_split": "newly_reserved", "source_leakage_group": group,
            "selection_rank_sha256": _rank(seed, group),
            "heldout_paper_ids": sorted(heldout_ids), "seed": seed, "source_files": source_files, **source_hashes,
        })
    output_rows.sort(key=lambda row: (row["venue_id"], row["year"], row["paper_id"]))
    if len({row["paper_id"] for row in output_rows}) != ijcai_size + aaai_size:
        raise ValueError("topic-test paper IDs are not unique")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in output_rows)
    with output_path.open("x", encoding="utf-8") as handle:
        handle.write(payload)
    return {
        "status": "frozen", "seed": seed, "sampled_ijcai": len(selected_ijcai),
        "sampled_aaai": len(selected_aaai), "test_papers": len(output_rows),
        "input_sha256": source_hashes, "output_sha256": _sha256(output_path),
        "output": str(output_path),
    }
