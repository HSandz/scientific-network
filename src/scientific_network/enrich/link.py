"""E2 step 4: link entities to Wikipedia pages and Wikidata QIDs (specification §4.2).

Candidates come from the Wikipedia search API (top results for the normalized name). Each candidate
is scored by the cosine similarity between an entity context (name plus titles of up to three
supporting papers) and the page lead, embedded with all-MiniLM-L6-v2. The best candidate above a
threshold chosen on development data is accepted; otherwise the entity stays unlinked.
All candidates and scores are written, so thresholds can be applied without refetching.
"""

import json
import re
import subprocess
from pathlib import Path

import numpy as np

from scientific_network.enrich.k1 import write_jsonl
from scientific_network.enrich.sources import WIKIPEDIA_API, Fetcher, fetch_wikipedia
from scientific_network.enrich.textutil import normalize

_PAREN = re.compile(r"\s*\([^)]*\)")


def title_overlap(name: str, title: str) -> float:
    """Token-set Jaccard between the entity name and the page title without its parenthetical."""
    left, right = set(normalize(name).split()), set(normalize(_PAREN.sub("", title)).split())
    return len(left & right) / len(left | right) if left and right else 0.0


def search_titles(fetcher: Fetcher, name: str, *, limit: int = 5) -> list[str]:
    payload, _row = fetcher.get("wikipedia_search", WIKIPEDIA_API,
                                {"action": "query", "format": "json", "formatversion": "2", "list": "search",
                                 "srsearch": name, "srnamespace": "0", "srlimit": str(limit), "srprop": ""})
    return [hit["title"] for hit in payload["query"]["search"]]


def entity_context(node: dict, titles: list[str]) -> str:
    return f"{node['name']}. " + " ".join(titles[:3])


def embed(rows: list[dict], workdir: Path, name: str, device: str) -> dict[str, np.ndarray]:
    write_jsonl(workdir / f"{name}.jsonl", rows)
    subprocess.run(["uv", "run", "--project", "ops/extract", "python", "ops/extract/embed.py", "--input",
                    str(workdir / f"{name}.jsonl"), "--output", str(workdir / name), "--device", device], check=True)
    matrix = np.load(workdir / f"{name}.npy")
    return {row["id"]: matrix[i] for i, row in enumerate(rows)}


def link_entities(nodes: list[dict], support_titles: dict[str, list[str]], fetcher: Fetcher, workdir: Path, *,
                  device: str = "cuda", limit: int = 5) -> list[dict]:
    """Return one record per node with every scored candidate (best first)."""
    candidates = {n["id"]: search_titles(fetcher, n["name"], limit=limit) for n in nodes}
    pages = fetch_wikipedia_leads(fetcher, sorted({t for ts in candidates.values() for t in ts}))
    context_rows = [{"id": n["id"], "text": entity_context(n, support_titles.get(n["id"], []))} for n in nodes]
    lead_rows = [{"id": title, "text": page["lead"][:1200]} for title, page in sorted(pages.items()) if page["lead"]]
    context_vec = embed(context_rows, workdir, "link-contexts", device)
    lead_vec = embed(lead_rows, workdir, "link-leads", device)
    out = []
    for node in nodes:
        scored = []
        for title in candidates[node["id"]]:
            page = pages.get(title)
            if page is None or title not in lead_vec:
                continue
            scored.append({"title": page["title"], "url": page["url"], "wikibase_item": page["wikibase_item"],
                           "revision_id": page["revision_id"], "page_id": page["page_id"],
                           "score": round(float(context_vec[node["id"]] @ lead_vec[title]), 4),
                           "title_overlap": round(title_overlap(node["name"], page["title"]), 4),
                           "lead_sha256": page["lead_sha256"]})
        scored.sort(key=lambda c: (-c["score"], c["title"]))
        out.append({"id": node["id"], "type": node["type"], "name": node["name"], "candidates": scored})
    return out


def fetch_wikipedia_leads(fetcher: Fetcher, titles: list[str], *, batch: int = 20) -> dict[str, dict]:
    """Leads, page IDs, revision IDs and QIDs only (no wikitext)."""
    pages: dict[str, dict] = {}
    for start in range(0, len(titles), batch):
        chunk = titles[start:start + batch]
        payload, row = fetcher.get("wikipedia_lead", WIKIPEDIA_API,
                                   {"action": "query", "format": "json", "formatversion": "2", "redirects": "1",
                                    "titles": "|".join(chunk), "prop": "extracts|revisions|pageprops", "exintro": "1",
                                    "explaintext": "1", "exlimit": "max", "rvprop": "ids|timestamp", "rvslots": "main"})
        renamed = {e["from"]: e["to"] for e in payload["query"].get("redirects", []) + payload["query"].get("normalized", [])}
        for page in payload["query"]["pages"]:
            if page.get("missing") or "pageid" not in page:
                continue
            revision = (page.get("revisions") or [{}])[0]
            record = {"title": page["title"], "page_id": page["pageid"], "revision_id": revision.get("revid"),
                      "wikibase_item": (page.get("pageprops") or {}).get("wikibase_item"), "lead": page.get("extract", ""),
                      "url": "https://en.wikipedia.org/wiki/" + page["title"].replace(" ", "_"), "lead_sha256": row["sha256"]}
            pages[page["title"]] = record
            for original, target in renamed.items():
                if target == page["title"] or renamed.get(target) == page["title"]:
                    pages[original] = record
    return pages


def apply_threshold(links: list[dict], *, threshold: float, min_title_overlap: float) -> list[dict]:
    """Accept the best candidate when its score and title overlap pass; otherwise leave the entity unlinked."""
    out = []
    for link in links:
        best = next((c for c in link["candidates"] if c["wikibase_item"]), None)
        accepted = best is not None and best["score"] >= threshold and best["title_overlap"] >= min_title_overlap
        out.append({"id": link["id"], "linked": accepted, "wikibase_item": best["wikibase_item"] if accepted else None,
                    "wikipedia_title": best["title"] if accepted else None, "wikipedia_url": best["url"] if accepted else None,
                    "revision_id": best["revision_id"] if accepted else None, "link_score": best["score"] if best else None})
    return out
