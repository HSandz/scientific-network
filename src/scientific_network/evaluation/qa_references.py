"""Deterministic, parameterized Cypher reference answers for qa-benchmark-v1 (M3 Phase 1).

Computes exact reference answers against neo4j-enriched (port 7690) following each
question's ``relation_chain`` and ``judged`` type, applies
``missing_entity_rule: drop_and_report_never_replace``, records trend/community facts
from ``reports/final-exam/analysis-v2/`` for global questions, and writes
``references-v1.jsonl`` plus ``references-v1-receipt.json``.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import neo4j

from scientific_network.enrich.load5 import ENRICHED_BOLT_PORT

SLOT_TO_LABEL: dict[str, str] = {
    "method": "Method",
    "task": "Task",
    "dataset": "Dataset",
    "org": "Organization",
    "topic": "Topic",
}

CYPHER_TEMPLATES: dict[str, str] = {
    "T1a": (
        "MATCH (m:Method {id: $method_id})-[:APPLIED_TO]->(t:Task) "
        "RETURN DISTINCT t.id AS id, t.name AS name ORDER BY id"
    ),
    "T1b": (
        "MATCH (m:Method {id: $method_id})-[:EVALUATED_ON]->(d:Dataset) "
        "RETURN DISTINCT d.id AS id, d.name AS name ORDER BY id"
    ),
    "T1c": (
        "MATCH (p:Paper)-[:USES_METHOD]->(m:Method {id: $method_id}) "
        "RETURN count(DISTINCT p) AS count"
    ),
    "T1d": (
        "MATCH (p:Paper)-[:ADDRESSES_TASK]->(t:Task {id: $task_id}) "
        "RETURN count(DISTINCT p) AS count"
    ),
    "T1e": (
        "MATCH (o:Organization {id: $org_id})-[r:COLLABORATED_WITH]-(o2:Organization) "
        "RETURN o2.id AS id, o2.name AS name, toInteger(r.support_count) AS score "
        "ORDER BY score DESC, id ASC LIMIT 5"
    ),
    "T1f": (
        "MATCH (t:Task {id: $task_id})-[:EVALUATED_ON]->(d:Dataset) "
        "RETURN DISTINCT d.id AS id, d.name AS name ORDER BY id"
    ),
    "T1g": (
        "MATCH (p:Paper)-[:USES_DATASET]->(d:Dataset {id: $dataset_id}) "
        "RETURN min(toInteger(p.year)) AS min_year"
    ),
    "T1h": (
        "MATCH (m:Method {id: $method_id})-[:RELATED_TO]-(m2:Method) "
        "RETURN DISTINCT m2.id AS id, m2.name AS name ORDER BY id"
    ),
    "T2a": (
        "MATCH (m:Method {id: $method_id})<-[:USES_METHOD]-(p:Paper)-[:USES_DATASET]->(d:Dataset) "
        "RETURN DISTINCT d.id AS id, d.name AS name ORDER BY id"
    ),
    "T2b": (
        "MATCH (t:Task {id: $task_id})<-[:ADDRESSES_TASK]-(p:Paper)-[:HAS_TOPIC]->(tp:Topic) "
        "RETURN DISTINCT tp.id AS id, tp.name AS name ORDER BY id"
    ),
    "T2c": (
        "MATCH (d:Dataset {id: $dataset_id})<-[:EVALUATED_ON]-(t:Task)<-[:APPLIED_TO]-(m:Method) "
        "RETURN DISTINCT m.id AS id, m.name AS name ORDER BY id"
    ),
    "T2d": (
        "MATCH (o:Organization {id: $org_id})-[:COLLABORATED_WITH]-(d1:Organization) "
        "WITH o, collect(DISTINCT d1.id) AS direct_ids "
        "MATCH (o)-[:COLLABORATED_WITH]-()-[:COLLABORATED_WITH]-(d2:Organization) "
        "WHERE d2.id <> o.id AND NOT d2.id IN direct_ids "
        "RETURN DISTINCT d2.id AS id, d2.name AS name ORDER BY id"
    ),
    "T2e": (
        "MATCH (m:Method {id: $method_id})<-[:USES_METHOD]-(p:Paper)<-[:AUTHORED]-(r:Researcher) "
        "WITH r, count(DISTINCT p) AS score "
        "RETURN r.id AS id, r.name AS name, score ORDER BY score DESC, id ASC LIMIT 10"
    ),
    "T2f": (
        "MATCH (tp:Topic {id: $topic_id})<-[:HAS_TOPIC]-(p:Paper)-[:USES_DATASET]->(d:Dataset) "
        "WHERE toInteger(p.year) = $year "
        "RETURN DISTINCT d.id AS id, d.name AS name ORDER BY id"
    ),
    "T2g": (
        "MATCH (tp:Topic {id: $topic_id})<-[:HAS_TOPIC]-(p:Paper)-[:USES_METHOD]->(m:Method) "
        "WITH m, count(DISTINCT p) AS score "
        "RETURN m.id AS id, m.name AS name, score ORDER BY score DESC, id ASC LIMIT 5"
    ),
    "T2h": (
        "MATCH (m:Method {id: $method_id})<-[:USES_METHOD]-(p:Paper)-[:PUBLISHED_IN]->(v:Venue {id: $venue_id}) "
        "WHERE toInteger(p.year) = $year "
        "MATCH (p)-[:ADDRESSES_TASK]->(t:Task) "
        "RETURN DISTINCT t.id AS id, t.name AS name ORDER BY id"
    ),
    "T2i": (
        "MATCH (d:Dataset {id: $dataset_id})<-[:USES_DATASET]-(p:Paper)-[:HAS_TOPIC]->(tp:Topic) "
        "WITH tp, count(DISTINCT p) AS score "
        "RETURN tp.id AS id, tp.name AS name, score ORDER BY score DESC, id ASC LIMIT 3"
    ),
    "T3a": (
        "MATCH (m:Method {id: $method_id})<-[:USES_METHOD]-(p:Paper)<-[:AUTHORED]-(r:Researcher)-[:AFFILIATED_WITH]->(o:Organization) "
        "WITH o, count(DISTINCT p) AS score "
        "RETURN o.id AS id, o.name AS name, score ORDER BY score DESC, id ASC LIMIT 5"
    ),
    "T3b": (
        "MATCH (t:Task {id: $task_id})<-[:ADDRESSES_TASK]-(p:Paper)<-[:AUTHORED]-(r:Researcher)-[:AFFILIATED_WITH]->(o:Organization) "
        "WHERE toInteger(p.year) = $year "
        "WITH o, count(DISTINCT p) AS score "
        "RETURN o.id AS id, o.name AS name, score ORDER BY score DESC, id ASC LIMIT 5"
    ),
    "T3c": (
        "MATCH (o0:Organization {id: $org_id})-[:COLLABORATED_WITH]-(o:Organization)<-[:AFFILIATED_WITH]-(r:Researcher)-[:AUTHORED]->(p:Paper)-[:USES_METHOD]->(m:Method {id: $method_id}) "
        "RETURN DISTINCT o.id AS id, o.name AS name ORDER BY id"
    ),
    "T3d": (
        "MATCH (o:Organization {id: $org_id})<-[:AFFILIATED_WITH]-(r:Researcher)-[:AUTHORED]->(p:Paper)-[:USES_METHOD]->(m:Method {id: $method_id}) "
        "MATCH (p)-[:USES_DATASET]->(d:Dataset) "
        "RETURN DISTINCT d.id AS id, d.name AS name ORDER BY id"
    ),
    "T3e": (
        "MATCH (m:Method {id: $method_id})-[:APPLIED_TO]->(t:Task)<-[:ADDRESSES_TASK]-(p:Paper)-[:USES_DATASET]->(d:Dataset) "
        "RETURN DISTINCT d.id AS id, d.name AS name ORDER BY id"
    ),
}


def _sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _surface_variants(text: str) -> list[str]:
    base = text.strip().lower()
    variants = [base]
    if base.endswith("s") and not base.endswith(("ss", "us", "is")):
        variants.append(base[:-1])
    else:
        variants.append(base + "s")
    return variants


def resolve_slot_entity(session, label: str, text: str) -> dict[str, Any] | None:
    """Deterministically resolve a slot string to one node of ``label`` via exact name, key, or surfaces."""
    rows = session.execute_read(
        lambda tx: tx.run(
            f"MATCH (n:{label}) RETURN n.id AS id, n.name AS name, n.key AS key, n.surfaces AS surfaces, coalesce(n.paper_count, 0) AS paper_count"
        ).data()
    )
    return resolve_slot_from_rows(rows, text)


def resolve_slot_from_rows(rows: list[dict[str, Any]], text: str) -> dict[str, Any] | None:
    target = text.strip().lower()
    variants = set(_surface_variants(target))

    # 1. Exact case-insensitive name match
    exact = [r for r in rows if str(r.get("name") or "").strip().lower() == target]
    if exact:
        exact.sort(key=lambda r: (-int(r.get("paper_count") or 0), r["id"]))
        return {**exact[0], "match_kind": "exact_name"}

    # 2. Exact key match
    by_key = [r for r in rows if str(r.get("key") or "").strip().lower() in variants]
    if by_key:
        by_key.sort(key=lambda r: (-int(r.get("paper_count") or 0), r["id"]))
        return {**by_key[0], "match_kind": "normalized_key"}

    # 3. Surface-form match (plural/singular variants against surfaces map/list)
    by_surface = []
    for r in rows:
        raw_surf = r.get("surfaces")
        if isinstance(raw_surf, str) and raw_surf.startswith("{"):
            try:
                surf_map = json.loads(raw_surf)
            except json.JSONDecodeError:
                surf_map = {}
        elif isinstance(raw_surf, dict):
            surf_map = raw_surf
        else:
            surf_map = {}
        surf_keys = {str(k).strip().lower() for k in surf_map}
        if surf_keys & variants:
            by_surface.append(r)
    if by_surface:
        by_surface.sort(key=lambda r: (-int(r.get("paper_count") or 0), r["id"]))
        return {**by_surface[0], "match_kind": "surface_form"}
    return None


def _global_facts(question: dict[str, Any], analysis_dir: Path) -> dict[str, Any]:
    """Extract deterministic precomputed trend and community facts that ground a global benchmark question."""
    import csv

    tid = question["template_id"]
    slots = question.get("slots") or {}
    trends_summary = json.loads((analysis_dir / "trends" / "trends-summary.json").read_text(encoding="utf-8"))

    def _read_csv(rel: str) -> list[dict[str, str]]:
        with open(analysis_dir / rel, newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    facts: dict[str, Any] = {
        "reference_type": "trend_and_community_facts",
        "analysis_dir": str(analysis_dir),
        "classification_note": trends_summary.get("classification_note"),
        "caveats": trends_summary.get("caveats", []),
    }
    if tid in ("G1", "G13"):
        year = str(slots.get("year") or "2022")
        topics = _read_csv("trends/trends-topic.csv")
        methods = _read_csv("trends/trends-method.csv")
        facts["year"] = year
        facts["top_topics_by_share"] = [
            {"id": r["id"], "name": r["name"], "papers": int(r[f"papers_{year}"]), "share": float(r[f"share_{year}"])}
            for r in sorted(topics, key=lambda x: -int(x[f"papers_{year}"]))[:8]
        ]
        facts["top_methods_by_share"] = [
            {"id": r["id"], "name": r["name"], "papers": int(r[f"papers_{year}"]), "share": float(r[f"share_{year}"])}
            for r in sorted(methods, key=lambda x: -int(x[f"papers_{year}"]))[:10]
        ]
    elif tid in ("G2", "G3", "G4", "G8", "G14"):
        facts["examples"] = trends_summary.get("examples", {})
        facts["classes"] = trends_summary.get("classes", {})
    elif tid in ("G6", "G11", "G15"):
        n1_comms = _read_csv("communities/communities-N1.csv")
        n2_comms = _read_csv("communities/communities-N2.csv")
        facts["top_n1_communities"] = n1_comms[:10]
        facts["top_n2_communities"] = n2_comms[:10]
    else:
        facts["examples"] = trends_summary.get("examples", {})
        facts["group_interest_summary"] = trends_summary.get("group_interest", {})
    return facts


def compute_references(
    *,
    questions_path: Path,
    analysis_dir: Path,
    output_path: Path,
    receipt_path: Path,
    neo4j_uri: str | None = None,
    min_kept_test: int = 60,
    session_override=None,
) -> dict[str, Any]:
    """Run deterministic parameterized Cypher for all questions, freeze references-v1.jsonl and receipt."""
    load_dotenv(override=False)
    questions_bytes = questions_path.read_bytes()
    questions = [json.loads(line) for line in questions_bytes.decode("utf-8").splitlines() if line.strip()]

    def _run_with_session(session) -> tuple[str, list[dict[str, Any]]]:
        ver_rows = session.execute_read(
            lambda tx: tx.run("MATCH (m:Method) RETURN collect(DISTINCT m.graph_version) AS vs LIMIT 1").data()
        )
        graph_version = (ver_rows[0].get("vs") or ["unknown"])[0] if ver_rows else "unknown"

        # Cache per-label nodes once so slot lookup is deterministic and fast
        label_cache: dict[str, list[dict[str, Any]]] = {}
        for lab in set(SLOT_TO_LABEL.values()):
            label_cache[lab] = session.execute_read(
                lambda tx, _lab=lab: tx.run(
                    f"MATCH (n:{_lab}) RETURN n.id AS id, n.name AS name, n.key AS key, n.surfaces AS surfaces, coalesce(n.paper_count, 0) AS paper_count"
                ).data()
            )

        records: list[dict[str, Any]] = []
        for q in questions:
            qid = q["question_id"]
            tid = q["template_id"]
            split = q["split"]
            hops = str(q["hops"])
            slots = q.get("slots") or {}

            if hops == "global":
                records.append({
                    "question_id": qid,
                    "split": split,
                    "hops": hops,
                    "template_id": tid,
                    "intent": q["intent"],
                    "judged": q["judged"],
                    "answer_type": q["answer_type"],
                    "text": q["text"],
                    "status": "kept",
                    "drop_reason": None,
                    "resolved_slots": {},
                    "cypher_template_id": None,
                    "cypher_sha256": None,
                    "reference_answer": _global_facts(q, analysis_dir),
                })
                continue

            resolved_slots: dict[str, Any] = {}
            missing: list[dict[str, str]] = []
            for skey, sval in slots.items():
                if skey in SLOT_TO_LABEL:
                    lab = SLOT_TO_LABEL[skey]
                    hit = resolve_slot_from_rows(label_cache[lab], str(sval))
                    if hit is None:
                        missing.append({"slot": skey, "label": lab, "value": str(sval)})
                    else:
                        resolved_slots[skey] = {
                            "id": hit["id"],
                            "name": hit["name"],
                            "label": lab,
                            "match_kind": hit["match_kind"],
                        }
                elif skey == "venue":
                    resolved_slots["venue"] = {"id": f"venue:{str(sval).strip().lower()}", "name": str(sval)}
                elif skey == "year":
                    resolved_slots["year"] = int(sval)

            if missing:
                records.append({
                    "question_id": qid,
                    "split": split,
                    "hops": hops,
                    "template_id": tid,
                    "intent": q["intent"],
                    "judged": q["judged"],
                    "answer_type": q["answer_type"],
                    "text": q["text"],
                    "status": "dropped",
                    "drop_reason": f"missing_entity: {missing}",
                    "resolved_slots": resolved_slots,
                    "cypher_template_id": tid,
                    "cypher_sha256": _sha256_text(CYPHER_TEMPLATES[tid]),
                    "reference_answer": None,
                })
                continue

            cypher = CYPHER_TEMPLATES[tid]
            params: dict[str, Any] = {}
            for skey, val in resolved_slots.items():
                if skey == "year":
                    params["year"] = val
                else:
                    params[f"{skey}_id"] = val["id"]

            rows = session.execute_read(lambda tx, c=cypher, p=params: tx.run(c, **p).data())
            if q["answer_type"] == "number":
                val = int(rows[0]["count"]) if rows else 0
                is_empty = val <= 0
                ref_ans: Any = val
            elif q["answer_type"] == "year":
                val = rows[0]["min_year"] if rows else None
                is_empty = val is None
                ref_ans = int(val) if val is not None else None
            elif q["answer_type"] == "ranked_list":
                is_empty = len(rows) == 0
                ref_ans = [{"id": r["id"], "name": r["name"], "score": int(r["score"])} for r in rows]
            else:
                is_empty = len(rows) == 0
                ref_ans = [{"id": r["id"], "name": r["name"]} for r in rows]

            records.append({
                "question_id": qid,
                "split": split,
                "hops": hops,
                "template_id": tid,
                "intent": q["intent"],
                "judged": q["judged"],
                "answer_type": q["answer_type"],
                "text": q["text"],
                "status": "dropped" if is_empty else "kept",
                "drop_reason": "empty_reference_result" if is_empty else None,
                "resolved_slots": resolved_slots,
                "cypher_template_id": tid,
                "cypher_sha256": _sha256_text(cypher),
                "reference_answer": None if is_empty else ref_ans,
            })
        return graph_version, records

    if session_override is not None:
        graph_version, records = _run_with_session(session_override)
    else:
        uri = neo4j_uri or os.environ.get("EXPLORER_ENRICHED_NEO4J_URI") or f"bolt://127.0.0.1:{ENRICHED_BOLT_PORT}"
        user = os.environ.get("NEO4J_USERNAME", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "")
        if not password:
            raise RuntimeError("NEO4J_PASSWORD must be configured to compute QA references")
        with neo4j.GraphDatabase.driver(uri, auth=(user, password), connection_timeout=15) as driver:
            with driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j"), default_access_mode=neo4j.READ_ACCESS) as session:
                graph_version, records = _run_with_session(session)

    # Compute kept / dropped counts by split and hop class
    counts_by_split: dict[str, dict[str, dict[str, int]]] = {}
    dropped_list: list[dict[str, Any]] = []
    for rec in records:
        sp = rec["split"]
        hp = rec["hops"]
        st = rec["status"]
        counts_by_split.setdefault(sp, {}).setdefault(hp, {"kept": 0, "dropped": 0})
        counts_by_split[sp][hp][st] += 1
        if st == "dropped":
            dropped_list.append({
                "question_id": rec["question_id"],
                "split": sp,
                "hops": hp,
                "template_id": rec["template_id"],
                "drop_reason": rec["drop_reason"],
            })

    kept_test = sum(v["kept"] for v in counts_by_split.get("test", {}).values())
    kept_dev = sum(v["kept"] for v in counts_by_split.get("development", {}).values())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_text = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records)
    output_path.write_text(jsonl_text, encoding="utf-8")

    graph_summary_path = Path("reports/enrichment-v3/graph-summary.json")
    graph_sha256 = None
    if graph_summary_path.exists():
        gs = json.loads(graph_summary_path.read_text(encoding="utf-8"))
        graph_sha256 = gs.get("graph_sha256") or gs.get("sha256")

    receipt = {
        "benchmark_version": "qa-benchmark-v1",
        "reference_version": "references-v1",
        "graph_version": graph_version,
        "graph_sha256": graph_sha256,
        "questions_sha256": _sha256_text(questions_bytes.decode("utf-8")),
        "references_sha256": _sha256_text(jsonl_text),
        "query_hashes": {k: _sha256_text(v) for k, v in sorted(CYPHER_TEMPLATES.items())},
        "total_questions": len(records),
        "kept_test": kept_test,
        "dropped_test": sum(v["dropped"] for v in counts_by_split.get("test", {}).values()),
        "kept_development": kept_dev,
        "dropped_development": sum(v["dropped"] for v in counts_by_split.get("development", {}).values()),
        "min_kept_test_gate": min_kept_test,
        "gate_passed": kept_test >= min_kept_test,
        "counts_by_split_and_hops": counts_by_split,
        "dropped": dropped_list,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if kept_test < min_kept_test:
        raise RuntimeError(f"QA reference gate failed: kept_test={kept_test} < {min_kept_test}")
    return receipt
