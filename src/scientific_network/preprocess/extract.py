"""Selective pilot PDF/header acquisition with explicit parse/alignment outcomes."""

from collections import Counter
from datetime import datetime, timezone
import json
import os
import time
from statistics import median
from pathlib import Path
import xml.etree.ElementTree as ET

from dotenv import load_dotenv
import httpx

from scientific_network.collect.storage import SourceCache, SourceError, digest, read_config, write_bytes, write_json
from scientific_network.preprocess.tei import parse_header

METHOD = "grobid-0.8.2-crf-xml-header-v2"


def request_header(client: httpx.Client, url: str, endpoint: str, pdf: bytes) -> bytes:
    response = client.post(url + "/api/" + endpoint,
        headers={"Accept": "application/xml"},
        files={"input": ("paper.pdf", pdf, "application/pdf")},
        data={"consolidateHeader": "0", "includeRawAffiliations": "1"})
    if response.status_code != 200:
        raise SourceError(f"GROBID HTTP {response.status_code}")
    root = ET.fromstring(response.content)
    if root.tag != "{http://www.tei-c.org/ns/1.0}TEI":
        raise ValueError("GROBID response is not a TEI document")
    return response.content


def extract(input_path: Path, output: Path, cache_path: Path, config_path: Path) -> dict:
    load_dotenv(override=False)
    url = os.environ.get("GROBID_URL", "http://localhost:8070").rstrip("/")
    config = read_config(config_path)
    if config["pdf"]["consolidate_header"] != 0:
        raise ValueError("this pilot extractor requires disabled external consolidation")
    write_json(output / "inputs.json", {"papers_sha256": digest(input_path.read_bytes()),
        "config_sha256": digest(config_path.read_bytes()),
        "method_version": METHOD, "consolidateHeader": 0})
    records = []
    with SourceCache(cache_path) as cache, httpx.Client(timeout=180) as grobid:
        for index, original in enumerate(json.loads(input_path.read_text()), 1):
            if original["status"] != "acquired":
                records.append(original)
                continue
            record_path = output / "records" / f"{digest(original['paper_id'].encode())}.json"
            if record_path.exists():
                records.append(json.loads(record_path.read_text()))
                continue
            record = dict(original)
            started = time.monotonic()
            try:
                pdf_url = original["official"]["pdf_url"]
                if not pdf_url:
                    raise ValueError("official PDF URL missing")
                pdf, pdf_source = cache.get(pdf_url)
                if not pdf.startswith(b"%PDF"):
                    raise ValueError("PDF endpoint returned non-PDF content")
                # Download evidence remains available even if the parser is down.
                record.update(pdf_source=pdf_source, pdf_size_bytes=len(pdf))
                key = digest(f"{METHOD}|{pdf_source['sha256']}|consolidate=0".encode())
                metadata_path = cache_path / "requests" / f"{key}.json"
                if metadata_path.exists():
                    tei_source = json.loads(metadata_path.read_text())
                    tei = (cache_path / "objects" / tei_source["sha256"]).read_bytes()
                    if digest(tei) != tei_source["sha256"]:
                        raise ValueError("TEI cache hash mismatch")
                else:
                    tei = request_header(grobid, url, config["pdf"]["header_endpoint"], pdf)
                    tei_source = {"url": pdf_url, "sha256": digest(tei),
                        "retrieved_at": datetime.now(timezone.utc).isoformat(), "pdf_sha256": pdf_source["sha256"],
                        "method_version": METHOD, "consolidateHeader": 0}
                    write_bytes(cache_path / "objects" / tei_source["sha256"], tei)
                    write_json(metadata_path, tei_source)
                record.update(pdf_source=pdf_source, tei_source=tei_source,
                    header_authors=parse_header(tei), extraction_status="parsed", pdf_size_bytes=len(pdf))
            except (SourceError, ValueError, ET.ParseError, httpx.HTTPError) as exc:
                # HTTP exceptions can contain local request details; retain only their type.
                reason = type(exc).__name__ if isinstance(exc, httpx.HTTPError) else str(exc)
                record.update(extraction_status="review", extraction_reason=reason, header_authors=[])
            record["extraction_seconds"] = round(time.monotonic() - started, 3)
            write_json(record_path, record)
            records.append(record)
            if index % 10 == 0:
                print(f"extract: {index}/{len(json.loads(input_path.read_text()))} headers", flush=True)
    write_json(output / "papers.json", records)
    summary = {"stage": "extract", "input_sha256": digest(input_path.read_bytes()),
        "config_sha256": digest(config_path.read_bytes()), "method_version": METHOD,
        "by_status": dict(Counter(r.get("extraction_status", "acquisition_failed") for r in records)),
        "pdf_bytes": sum(r.get("pdf_size_bytes", 0) for r in records),
        "median_pdf_bytes": median([r["pdf_size_bytes"] for r in records if "pdf_size_bytes" in r]) if any("pdf_size_bytes" in r for r in records) else None,
        "sum_record_elapsed_seconds": round(sum(r.get("extraction_seconds", 0) for r in records), 3),
        "papers_with_header_affiliations": sum(any(a["affiliations"] for a in r.get("header_authors", [])) for r in records),
        "external_consolidation": False, "independent_mapping_audit": "not_performed"}
    write_json(output / "summary.json", summary)
    return summary
