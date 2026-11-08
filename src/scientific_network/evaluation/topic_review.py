"""Prepare a prediction-blind topic annotation sheet for the frozen D040 sample."""

from __future__ import annotations

import csv
import hashlib
import html
import json
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
    with csv_path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

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
            ) + f'</div><label>Labeler <input class="labeler" type="text"></label>'
            f'<label>Notes <textarea class="notes" rows="2"></textarea></label></article>'
        )
    safe_catalog = catalog_json.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    safe_rows = json.dumps(
        [{k: row[k] for k in ("paper_id", "venue_id", "year", "title", "abstract")} for row in rows],
        ensure_ascii=False,
    ).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\\u2028", "\\\\u2028").replace("\\u2029", "\\\\u2029")
    page = f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blind topic review sheet</title>
<style>
body{{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#17212b}}
.paper{{border:1px solid #cbd5df;border-radius:10px;padding:1rem;margin:1rem 0 2rem}}
.meta{{color:#526273;font-size:.9rem}}.abstract{{white-space:pre-wrap}}.topics{{columns:2;gap:2rem}}
.topics li{{break-inside:avoid;margin:.4rem 0 1rem}}code{{color:#4b5968}}label{{display:block;margin:.6rem 0}}
.labels{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}}select,input,textarea{{font:inherit;width:100%;box-sizing:border-box;padding:.45rem}}
button{{position:sticky;top:.5rem;padding:.7rem 1rem;background:#153d5b;color:white;border:0;border-radius:6px}}
@media(max-width:700px){{.topics{{columns:1}}.labels{{grid-template-columns:1fr}}}}
</style>
<h1>Blind topic review</h1><p>Choose up to three leaf topics for each paper. Classifier predictions are not shown. Save the completed CSV for evaluation.</p>
<button id="download">Download completed CSV</button>{''.join(rendered_papers)}
<script>
const baseRows={safe_rows};
const fields={json.dumps(FIELDS)};
function csvCell(v){{const s=String(v??"");return '"'+s.replaceAll('"','""')+'"';}}
document.getElementById('download').addEventListener('click',()=>{{
 const rows=[fields.map(csvCell).join(',')];
 document.querySelectorAll('.paper').forEach((card,i)=>{{
   const labels=[...new Set([...card.querySelectorAll('select.label')].map(x=>x.value).filter(Boolean))];
   const row={{...baseRows[i],topic_catalog:JSON.stringify({safe_catalog}),label_1:labels[0]||'',label_2:labels[1]||'',label_3:labels[2]||'',labeler:card.querySelector('.labeler').value,notes:card.querySelector('.notes').value}};
   rows.push(fields.map(key=>csvCell(row[key])).join(','));
 }});
 const blob=new Blob(['\\ufeff'+rows.join('\\r\\n')],{{type:'text/csv;charset=utf-8'}});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='topic-label-sheet-completed.csv';a.click();URL.revokeObjectURL(a.href);
}});
</script></html>'''
    with html_path.open("x", encoding="utf-8") as handle:
        handle.write(page)

    return {
        "status": "ready_for_human_labels", "paper_count": len(rows),
        "leaf_topic_count": len(catalog), "predictions_included": False,
        "works_sha256": _sha256(works_path), "topic_test_sha256": test_hash,
        "taxonomy_sha256": _sha256(taxonomy_path), "csv": str(csv_path),
        "html": str(html_path),
    }
