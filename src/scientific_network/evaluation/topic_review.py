"""Prepare a prediction-blind topic annotation sheet for the frozen D040 sample."""

from __future__ import annotations

import csv
import hashlib
import html
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml


FIELDS = [
    "paper_id", "venue_id", "year", "title", "abstract", "topic_catalog",
    "label_1", "label_2", "label_3", "labeler", "notes",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid JSONL at {path}:{number}: {exc}") from exc


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_html_sheet(
    rows: list[dict[str, Any]],
    catalog: list[dict[str, str]],
    html_path: Path,
    *,
    assigned_labeler: str | None = None,
    download_name: str = "topic-label-sheet-completed.csv",
) -> None:
    rendered_papers = []
    for index, row in enumerate(rows):
        options = "".join(
            f'<option value="{html.escape(leaf["id"], quote=True)}">'
            f'{html.escape(leaf["name"])}</option>' for leaf in catalog
        )
        topic_list = "".join(
            f'<li><strong>{html.escape(leaf["name"])}</strong> '
            f'<code>{html.escape(leaf["id"])}</code><br>'
            f'{html.escape(leaf["definition"])}</li>' for leaf in catalog
        )
        labeler_control = (
            f'<p class="assigned">Assigned reviewer: <strong>{html.escape(assigned_labeler)}</strong></p>'
            if assigned_labeler is not None
            else '<label>Labeler <input class="labeler" type="text"></label>'
        )
        rendered_papers.append(
            f'<article class="paper" data-index="{index}"><h2>{index + 1}. '
            f'{html.escape(str(row["title"]))}</h2><p class="meta">'
            f'{html.escape(str(row["venue_id"]))} · {html.escape(str(row["year"]))} · '
            f'{html.escape(row["paper_id"])}</p><details><summary>16 topic definitions</summary>'
            f'<ol class="topics">{topic_list}</ol></details>'
            f'<p class="abstract">{html.escape(str(row["abstract"])) or "Abstract unavailable."}</p>'
            f'<div class="labels">' + "".join(
                f'<label>Label {slot}<select class="label"><option value="">Unassigned</option>{options}</select></label>'
                for slot in range(1, 4)
            ) + f'</div>{labeler_control}'
            f'<label>Notes <textarea class="notes" rows="2"></textarea></label></article>'
        )
    catalog_json = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))
    safe_catalog = catalog_json.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    safe_rows = json.dumps(
        [{k: row[k] for k in ("paper_id", "venue_id", "year", "title", "abstract")} for row in rows],
        ensure_ascii=False,
    ).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\\u2028", "\\\\u2028").replace("\\u2029", "\\\\u2029")
    labeler_expression = (
        json.dumps(assigned_labeler) if assigned_labeler is not None
        else "card.querySelector('.labeler').value"
    )
    page_title = (
        "Blind topic review sheet" if assigned_labeler is None
        else f"Blind topic review sheet — reviewer {html.escape(assigned_labeler)}"
    )
    page = f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{page_title}</title>
<style>
body{{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#17212b}}
.paper{{border:1px solid #cbd5df;border-radius:10px;padding:1rem;margin:1rem 0 2rem}}
.meta{{color:#526273;font-size:.9rem}}.abstract{{white-space:pre-wrap}}.topics{{columns:2;gap:2rem}}
.topics li{{break-inside:avoid;margin:.4rem 0 1rem}}code{{color:#4b5968}}label{{display:block;margin:.6rem 0}}
.labels{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}}select,input,textarea{{font:inherit;width:100%;box-sizing:border-box;padding:.45rem}}
button{{position:sticky;top:.5rem;padding:.7rem 1rem;background:#153d5b;color:white;border:0;border-radius:6px}}
@media(max-width:700px){{.topics{{columns:1}}.labels{{grid-template-columns:1fr}}}}
</style>
<h1>Blind topic review</h1><p>Choose up to three leaf topics for each paper. Classifier predictions are not shown. If none applies, leave labels blank and explain that in Notes. Save the completed CSV for evaluation.</p>
<button id="download">Download completed CSV</button>{''.join(rendered_papers)}
<script>
const baseRows={safe_rows};
const fields={json.dumps(FIELDS)};
function csvCell(v){{const s=String(v??"");return '"'+s.replaceAll('"','""')+'"';}}
document.getElementById('download').addEventListener('click',()=>{{
 const rows=[fields.map(csvCell).join(',')];
 let incomplete=false;
 document.querySelectorAll('.paper').forEach((card,i)=>{{
   const labels=[...new Set([...card.querySelectorAll('select.label')].map(x=>x.value).filter(Boolean))];
   const notes=card.querySelector('.notes').value;
   if(labels.length===0&&!notes.trim()){{incomplete=true;return;}}
   const row={{...baseRows[i],topic_catalog:JSON.stringify({safe_catalog}),label_1:labels[0]||'',label_2:labels[1]||'',label_3:labels[2]||'',labeler:{labeler_expression},notes}};
   rows.push(fields.map(key=>csvCell(row[key])).join(','));
 }});
 if(incomplete){{alert('Complete every paper. If no topic applies, record that decision in Notes.');return;}}
 const blob=new Blob(['\\ufeff'+rows.join('\\r\\n')],{{type:'text/csv;charset=utf-8'}});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download={json.dumps(download_name)};a.click();URL.revokeObjectURL(a.href);
}});
</script></html>'''
    with html_path.open("x", encoding="utf-8") as handle:
        handle.write(page)


def assign_topic_reviewers(
    papers: list[dict[str, Any]], *, seed: int, reviewer_ids: tuple[str, str] = ("A", "B")
) -> dict[str, Any]:
    """Allocate the frozen 20-AAAI/30-IJCAI set 30/30 with 10 shared.

    Stable SHA-256 ordering is used within venue strata. Four AAAI papers and six
    IJCAI papers are shared; the remaining papers are split evenly by venue.
    """
    if reviewer_ids != ("A", "B"):
        raise ValueError("D040 topic packets use reviewer IDs A and B")
    ids = [row.get("paper_id") for row in papers]
    if len(ids) != 50 or any(not paper_id for paper_id in ids) or len(set(ids)) != 50:
        raise ValueError("topic reviewer allocation requires 50 uniquely identified papers")
    counts = Counter(row.get("venue_id") for row in papers)
    expected = {"venue:aaai": 20, "venue:ijcai": 30}
    if dict(counts) != expected:
        raise ValueError(f"topic reviewer allocation requires the frozen venue counts {expected}")

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in papers:
        groups[row["venue_id"]].append(row)

    def rank(row: dict[str, Any], purpose: str) -> tuple[str, str]:
        value = f"d040-topic-review-allocation-v1\0{seed}\0{purpose}\0{row['paper_id']}"
        return hashlib.sha256(value.encode("utf-8")).hexdigest(), row["paper_id"]

    assignments = {reviewer: set() for reviewer in reviewer_ids}
    overlap: set[str] = set()
    for venue_id, overlap_size in (("venue:aaai", 4), ("venue:ijcai", 6)):
        ordered = sorted(groups[venue_id], key=lambda row: rank(row, "overlap"))
        selected = ordered[:overlap_size]
        overlap.update(row["paper_id"] for row in selected)
        for reviewer in reviewer_ids:
            assignments[reviewer].update(row["paper_id"] for row in selected)
        exclusive = sorted(ordered[overlap_size:], key=lambda row: rank(row, "exclusive"))
        half = len(exclusive) // 2
        if half * 2 != len(exclusive):
            raise ValueError(f"venue stratum cannot be split evenly: {venue_id}")
        assignments[reviewer_ids[0]].update(row["paper_id"] for row in exclusive[:half])
        assignments[reviewer_ids[1]].update(row["paper_id"] for row in exclusive[half:])

    if any(len(assigned) != 30 for assigned in assignments.values()):
        raise ValueError("topic reviewer allocation did not produce 30 papers per reviewer")
    if assignments["A"] | assignments["B"] != set(ids) or assignments["A"] & assignments["B"] != overlap:
        raise ValueError("topic reviewer allocation failed its coverage/overlap invariant")
    return {
        "reviewer_paper_ids": {reviewer: sorted(assigned) for reviewer, assigned in assignments.items()},
        "overlap_paper_ids": sorted(overlap),
        "venue_counts": {
            reviewer: dict(sorted(Counter(row["venue_id"] for row in papers if row["paper_id"] in assignments[reviewer]).items()))
            for reviewer in reviewer_ids
        },
        "seed": seed,
    }


def prepare_topic_review_sheet(
    works_path: Path,
    topic_test_path: Path,
    taxonomy_path: Path,
    csv_path: Path,
) -> dict[str, Any]:
    """Write blank CSV and HTML review sheets without exposing model predictions."""
    html_path = csv_path.with_suffix(".html")
    if any(path.exists() or path.is_symlink() for path in (csv_path, html_path)):
        raise ValueError("refusing to overwrite an existing topic review sheet")

    taxonomy = yaml.safe_load(taxonomy_path.read_text(encoding="utf-8"))
    if not isinstance(taxonomy, dict) or taxonomy.get("status") != "frozen":
        raise ValueError("topic review sheets require a frozen classifier configuration")
    calibration = taxonomy.get("calibration") or {}
    if calibration.get("works_sha256") != _sha256(works_path):
        raise ValueError("frozen classifier does not bind to the current works input")
    test_hash = _sha256(topic_test_path)
    if calibration.get("topic_test_sha256") != test_hash:
        raise ValueError("frozen classifier does not bind to the current topic test manifest")

    leaves = taxonomy.get("leaves") or []
    if len(leaves) != 16 or len({leaf.get("id") for leaf in leaves}) != 16:
        raise ValueError("topic review sheet requires 16 uniquely identified leaf topics")
    catalog = [{key: leaf[key] for key in ("id", "name", "definition")} for leaf in leaves]
    manifest_rows = list(_jsonl(topic_test_path))
    ids = [row.get("paper_id") for row in manifest_rows]
    if len(ids) != 50 or len(set(ids)) != 50 or any(not value for value in ids):
        raise ValueError("topic review sheet requires the frozen 50-paper test manifest")

    wanted = set(ids)
    papers: dict[str, dict[str, Any]] = {}
    for row in _jsonl(works_path):
        paper_id = row.get("paper_id")
        if paper_id not in wanted:
            continue
        if paper_id in papers:
            raise ValueError(f"duplicate works row for held-out paper: {paper_id}")
        # Deliberately project only source fields; predictions are never read or rendered.
        papers[paper_id] = {
            "paper_id": paper_id,
            "venue_id": row.get("venue_id", ""),
            "year": row.get("year", ""),
            "title": row.get("roster", {}).get("title", ""),
            "abstract": (row.get("openalex") or {}).get("abstract") or "",
        }
    if set(papers) != wanted:
        raise ValueError(f"works input is missing {len(wanted - set(papers))} topic-test papers")

    catalog_json = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))
    rows = [{**papers[paper_id], "topic_catalog": catalog_json,
             "label_1": "", "label_2": "", "label_3": "", "labeler": "", "notes": ""}
            for paper_id in ids]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(csv_path, rows)
    _write_html_sheet(rows, catalog, html_path)

    return {
        "status": "ready_for_human_labels", "paper_count": len(rows),
        "leaf_topic_count": len(catalog), "predictions_included": False,
        "works_sha256": _sha256(works_path), "topic_test_sha256": test_hash,
        "taxonomy_sha256": _sha256(taxonomy_path), "csv": str(csv_path),
        "html": str(html_path),
    }


def prepare_topic_review_packets(
    master_csv_path: Path,
    topic_test_path: Path,
    taxonomy_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Create deterministic, prediction-blind A/B packets from the frozen master sheet."""
    allocation_path = output_dir / "topic-review-allocation.json"
    packet_paths = {
        reviewer: {
            "csv": output_dir / f"topic-label-sheet-reviewer-{reviewer}.csv",
            "html": output_dir / f"topic-label-sheet-reviewer-{reviewer}.html",
        }
        for reviewer in ("A", "B")
    }
    targets = [allocation_path] + [path for paths in packet_paths.values() for path in paths.values()]
    if any(path.exists() or path.is_symlink() for path in targets):
        raise ValueError("refusing to overwrite an existing topic review packet or allocation manifest")

    taxonomy = yaml.safe_load(taxonomy_path.read_text(encoding="utf-8"))
    if not isinstance(taxonomy, dict) or taxonomy.get("status") != "frozen":
        raise ValueError("topic reviewer packets require a frozen classifier configuration")
    calibration = taxonomy.get("calibration") or {}
    test_hash = _sha256(topic_test_path)
    if calibration.get("topic_test_sha256") != test_hash:
        raise ValueError("frozen classifier does not bind to the current topic test manifest")
    catalog_rows = taxonomy.get("leaves") or []
    if len(catalog_rows) != 16 or len({row.get("id") for row in catalog_rows}) != 16:
        raise ValueError("topic reviewer packets require 16 uniquely identified leaf topics")
    catalog = [{key: leaf[key] for key in ("id", "name", "definition")} for leaf in catalog_rows]

    manifest_rows = list(_jsonl(topic_test_path))
    seeds = {row.get("seed") for row in manifest_rows}
    if len(manifest_rows) != 50 or len(seeds) != 1 or None in seeds:
        raise ValueError("topic reviewer packets require the frozen 50-paper test manifest and one seed")
    seed = int(next(iter(seeds)))
    with master_csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError("topic master sheet has an unexpected schema")
        master_rows = list(reader)
    ids = [row.get("paper_id") for row in master_rows]
    if len(ids) != 50 or len(set(ids)) != 50 or set(ids) != {row.get("paper_id") for row in manifest_rows}:
        raise ValueError("topic master sheet must exactly match the frozen 50-paper test frame")
    for row in master_rows:
        if any(row.get(field, "").strip() for field in ("label_1", "label_2", "label_3", "labeler", "notes")):
            raise ValueError("topic master sheet contains annotations; refusing to create replacement packets")
        try:
            row_catalog = json.loads(row["topic_catalog"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("topic master sheet contains an invalid topic catalog") from exc
        if row_catalog != catalog:
            raise ValueError("topic master sheet catalog differs from the frozen taxonomy")

    assignment = assign_topic_reviewers(master_rows, seed=seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    row_by_id = {row["paper_id"]: row for row in master_rows}
    for reviewer, paper_ids in assignment["reviewer_paper_ids"].items():
        rows = [{**row_by_id[paper_id], "labeler": reviewer} for paper_id in ids if paper_id in set(paper_ids)]
        _write_csv(packet_paths[reviewer]["csv"], rows)
        _write_html_sheet(
            rows, catalog, packet_paths[reviewer]["html"], assigned_labeler=reviewer,
            download_name=f"topic-label-sheet-reviewer-{reviewer}-completed.csv",
        )

    result = {
        "status": "ready_for_human_labels",
        "assignment_method_version": "d040-topic-review-allocation-v1",
        "seed": seed,
        "reviewers": ["A", "B"],
        "paper_count": 50,
        "assignments_per_reviewer": {reviewer: len(values) for reviewer, values in assignment["reviewer_paper_ids"].items()},
        "unique_papers_per_reviewer": {reviewer: len(values) for reviewer, values in assignment["reviewer_paper_ids"].items()},
        "total_assignment_rows": sum(len(values) for values in assignment["reviewer_paper_ids"].values()),
        "reviewer_paper_ids": assignment["reviewer_paper_ids"],
        "overlap_count": len(assignment["overlap_paper_ids"]),
        "overlap_paper_ids": assignment["overlap_paper_ids"],
        "venue_counts": assignment["venue_counts"],
        "predictions_included": False,
        "master_sheet": {"path": str(master_csv_path), "sha256": _sha256(master_csv_path)},
        "topic_test_manifest": {"path": str(topic_test_path), "sha256": test_hash},
        "taxonomy": {"path": str(taxonomy_path), "sha256": _sha256(taxonomy_path)},
        "reviewer_sheets": {},
    }
    for reviewer, paths in packet_paths.items():
        result["reviewer_sheets"][reviewer] = {
            key: {"path": str(path), "sha256": _sha256(path)} for key, path in paths.items()
        }
    with allocation_path.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    result["allocation_manifest"] = {
        "path": str(allocation_path), "sha256": _sha256(allocation_path),
    }
    return result
