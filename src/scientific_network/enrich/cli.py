"""``research-network enrich <stage>`` subcommands for the D042 enrichment track."""

import argparse
from pathlib import Path

PLANNED: dict[str, str] = {}


def add_enrich_parser(commands) -> None:
    enrich = commands.add_parser("enrich", help="D042 enrichment track (splits, benchmark, sources, entities, relations)")
    stages = enrich.add_subparsers(dest="enrich_command", required=True)
    splits = stages.add_parser("freeze-splits", help="freeze the 100 development / 200 test enrichment papers")
    splits.add_argument("--works", type=Path, required=True)
    splits.add_argument("--membership", type=Path, required=True, help="five-year-splits-v1 membership.jsonl")
    splits.add_argument("--output", type=Path, required=True)
    splits.add_argument("--seed", type=int, required=True)
    splits.add_argument("--development", type=int, default=100)
    splits.add_argument("--test", type=int, default=200)
    splits.add_argument("--audit-ledger", type=Path, action="append", default=[])
    splits.add_argument("--topic-test", type=Path)
    bench = stages.add_parser("freeze-benchmark", help="hash-freeze the QA benchmark question text")
    bench.add_argument("--output", type=Path, required=True)
    slm = stages.add_parser("run-slm", help="run the SLM extract or verify step over a JSONL of {id, text} (development experiments)")
    slm.add_argument("--mode", choices=["extract", "verify", "verify-batch", "verify-pairs", "verify-gen", "verify-text"], required=True)
    slm.add_argument("--llm-config", type=Path, required=True)
    slm.add_argument("--texts", type=Path, required=True)
    slm.add_argument("--encoder-output", type=Path)
    slm.add_argument("--entity-threshold", type=float, default=0.3)
    slm.add_argument("--relation-threshold", type=float, default=0.3)
    slm.add_argument("--workers", type=int, default=2)
    slm.add_argument("--call-log", type=Path)
    slm.add_argument("--output", type=Path, required=True)
    score = stages.add_parser("score-dev", help="score a run on the frozen development reference labels")
    score.add_argument("--labels", type=Path, required=True)
    score.add_argument("--texts", type=Path, required=True)
    score.add_argument("--slm-output", type=Path)
    score.add_argument("--encoder-output", type=Path)
    score.add_argument("--entity-threshold", type=float, default=0.5)
    score.add_argument("--relation-threshold", type=float, default=0.5)
    score.add_argument("--tune", action="store_true", help="grid-search encoder thresholds on the development papers")
    fetch = stages.add_parser("fetch-sources", help="Phase 1 (E1): fetch Wikidata organization facts and linked Wikipedia pages")
    fetch.add_argument("--graph", type=Path, required=True, help="frozen v4 graph.json (read only)")
    fetch.add_argument("--works", type=Path, required=True)
    fetch.add_argument("--raw-dir", type=Path, default=Path("data/raw/enrichment-v1"))
    fetch.add_argument("--manifest", type=Path, default=Path("data/raw/enrichment-v1/fetch-manifest.jsonl"))
    fetch.add_argument("--output-dir", type=Path, default=Path("data/interim/enrichment-v1"))
    fetch.add_argument("--report", type=Path, default=Path("reports/enrichment-v1/sources.json"))
    fetch.add_argument("--min-interval", type=float, default=1.0)
    ent = stages.add_parser("extract-entities", help="Phase 2 (E2): verified mentions, surface-form merging, node threshold")
    ent.add_argument("--texts", type=Path, required=True)
    ent.add_argument("--encoder-output", type=Path, required=True)
    ent.add_argument("--slm-output", type=Path, required=True)
    ent.add_argument("--config", type=Path, required=True)
    ent.add_argument("--output-dir", type=Path, required=True)
    ent.add_argument("--report", type=Path, default=Path("reports/enrichment-v1/entities.json"))
    ent.add_argument("--merge-threshold", type=float, required=True)
    ent.add_argument("--min-papers", type=int, default=3)
    ent.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    link = stages.add_parser("link-entities", help="Phase 2 (E2 step 4): link entity nodes to Wikipedia pages and Wikidata QIDs")
    link.add_argument("--e2-dir", type=Path, required=True)
    link.add_argument("--texts", type=Path, required=True)
    link.add_argument("--output-dir", type=Path, required=True)
    link.add_argument("--raw-dir", type=Path, default=Path("data/raw/enrichment-v1"))
    link.add_argument("--manifest", type=Path, default=Path("data/raw/enrichment-v1/fetch-manifest.jsonl"))
    link.add_argument("--threshold", type=float, required=True)
    link.add_argument("--min-interval", type=float, default=1.2)
    link.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    link.add_argument("--report", type=Path, default=Path("reports/enrichment-v1/linking.json"))
    build = stages.add_parser("build-graph", help="Phases 3-4: relations, enrichment layer and the v5-enriched graph")
    build.add_argument("--e2-dir", type=Path, required=True)
    build.add_argument("--link-dir", type=Path, required=True)
    build.add_argument("--texts", type=Path, required=True)
    build.add_argument("--base-graph", type=Path, required=True, help="frozen v4 graph.json (read only)")
    build.add_argument("--config", type=Path, required=True)
    build.add_argument("--org-wikidata", type=Path, default=Path("data/interim/enrichment-v1/org-wikidata.json"))
    build.add_argument("--org-wikipedia", type=Path, default=Path("data/interim/enrichment-v1/org-wikipedia.json"))
    build.add_argument("--manifest", type=Path, default=Path("data/raw/enrichment-v1/fetch-manifest.jsonl"))
    build.add_argument("--quality-config", type=Path, default=Path("configs/quality-release-v1.yaml"),
                       help="v4 release quality config for the frozen structural validator")
    build.add_argument("--org-facts", type=Path, help="enrichment v2: Wikidata facts (P31, qualifiers, reverse statements) from the v2 fetch")
    build.add_argument("--v2-manifest", type=Path, help="enrichment v2: fetch manifest of the v2 raw store")
    build.add_argument("--output-dir", type=Path, required=True)
    load = stages.add_parser("load-graph", help="Phase 4: import v5-enriched into neo4j-enriched (bolt port 7690 only)")
    load.add_argument("--graph", type=Path, required=True)
    load.add_argument("--report", type=Path, required=True)
    audit = stages.add_parser("audit-sample", help="Phase 5 (E4): freeze the audit sample and write evaluator packets (before any judgement)")
    audit.add_argument("--graph", type=Path, required=True)
    audit.add_argument("--mentions", type=Path, required=True)
    audit.add_argument("--texts", type=Path, required=True)
    audit.add_argument("--test", type=Path, default=Path("data/manifests/enrichment-splits-v1/test.jsonl"))
    audit.add_argument("--link-dir", type=Path, required=True)
    audit.add_argument("--slm-only", type=Path, help="extract-mode SLM output on the test papers (ablation variant)")
    audit.add_argument("--output-dir", type=Path, required=True)
    audit.add_argument("--seed", type=int, required=True)
    audit.add_argument("--rules", type=Path, default=Path("configs/enrichment-v1-audit.json"))
    scorea = stages.add_parser("score-audit", help="Phase 5 (E4): score the answered packets with Wilson intervals and Cohen's kappa")
    scorea.add_argument("--audit-dir", type=Path, required=True)
    scorea.add_argument("--graph", type=Path, required=True)
    scorea.add_argument("--mentions", type=Path, required=True)
    scorea.add_argument("--texts", type=Path, required=True)
    scorea.add_argument("--test", type=Path, default=Path("data/manifests/enrichment-splits-v1/test.jsonl"))
    scorea.add_argument("--slm-only", type=Path)
    scorea.add_argument("--output", type=Path, required=True)
    scorea.add_argument("--run-info", type=Path, help="JSON with the actual evaluator models, run IDs and isolation notes")
    adj = stages.add_parser("audit-adjudicate", help="Phase 5 (E4): write packets for channel C from the A/B disagreements")
    adj.add_argument("--audit-dir", type=Path, required=True)
    cooc = stages.add_parser("cooccurrence", help="Read-only shared-paper connections: distribution report, or partners of one entity")
    cooc.add_argument("--graph", type=Path, required=True)
    cooc.add_argument("--output", type=Path, help="write the distribution report here (when no --entity is given)")
    cooc.add_argument("--entity", help="entity id, e.g. method:Q...; prints its partners of --partner-type")
    cooc.add_argument("--partner-type", choices=["Method", "Task", "Dataset"])
    cooc.add_argument("--min-papers", type=int, default=1)
    gl = stages.add_parser("guard-links", help="Enrichment v3: re-apply the link threshold and the narrower-page guard to cached candidate scores (offline)")
    gl.add_argument("--link-dir", type=Path, required=True)
    gl.add_argument("--config", type=Path, required=True)
    gl.add_argument("--output-dir", type=Path, required=True)
    gl.add_argument("--report", type=Path, required=True)
    ad = stages.add_parser("applied-to-dev-sample", help="Enrichment v3: draw and freeze the fresh APPLIED_TO development sample and packet")
    ad.add_argument("--candidates-graph", type=Path, required=True)
    ad.add_argument("--texts", type=Path, required=True)
    ad.add_argument("--packet-dir", type=Path, required=True)
    ad.add_argument("--report-dir", type=Path, required=True)
    a2 = stages.add_parser("audit-v2-sample", help="Enrichment v2 E4 audit: freeze the fresh samples and packets for the changed axes (before any judgement)")
    a2.add_argument("--graph", type=Path, required=True)
    a2.add_argument("--texts", type=Path, required=True)
    a2.add_argument("--v1-graph", type=Path, required=True)
    a2.add_argument("--v1-sample", type=Path, required=True)
    a2.add_argument("--dev-labels", type=Path, action="append", required=True)
    a2.add_argument("--config", type=Path, required=True)
    a2.add_argument("--output-dir", type=Path, required=True)
    tc = stages.add_parser("type-conflicts", help="list entity keys that carry more than one type (no typing change)")
    tc.add_argument("--graph", type=Path, required=True)
    tc.add_argument("--output", type=Path, required=True)
    pv2 = stages.add_parser("audit-partof-v2", help="Build PART_OF packet v2 (same 50 frozen items, Wikidata statement shown) and its receipt")
    pv2.add_argument("--audit-dir", type=Path, required=True)
    pv2.add_argument("--graph", type=Path, required=True)
    pv2.add_argument("--org-wikidata", type=Path, required=True)
    pv2.add_argument("--fetch-manifest", type=Path, required=True)
    pv2.add_argument("--raw-dir", type=Path, required=True)
    pv2.add_argument("--receipt", type=Path, required=True)
    pv2.add_argument("--packets-copy", type=Path, help="also copy the packets here (tracked location)")
    for name, text in PLANNED.items():
        stages.add_parser(name, help=f"planned, not implemented: {text}")


def _json_load(path):
    import json as _j
    return _j.loads(path.read_text()) if path else None


def run_enrich(args) -> tuple[dict, int]:
    if args.enrich_command == "freeze-splits":
        from scientific_network.enrich.splits import freeze_enrichment_splits
        return freeze_enrichment_splits(
            args.works, args.membership, args.output, seed=args.seed, n_dev=args.development,
            n_test=args.test, audit_ledgers=args.audit_ledger, topic_test_path=args.topic_test), 0
    if args.enrich_command == "freeze-benchmark":
        from scientific_network.enrich.benchmark import freeze_benchmark
        return freeze_benchmark(args.output), 0
    if args.enrich_command == "fetch-sources":
        from scientific_network.enrich.sources import acquire_organization_sources
        return acquire_organization_sources(args.graph, args.works, args.raw_dir, args.manifest, args.output_dir,
                                            args.report, min_interval=args.min_interval), 0
    if args.enrich_command == "extract-entities":
        from scientific_network.enrich.e2 import run_extract_entities
        return run_extract_entities(args.texts, args.encoder_output, args.slm_output, args.config, args.output_dir,
                                    args.report, merge_threshold=args.merge_threshold, min_papers=args.min_papers,
                                    device=args.device), 0
    if args.enrich_command == "link-entities":
        from scientific_network.enrich.e3 import run_link_entities
        report = run_link_entities(args.e2_dir, args.texts, args.raw_dir, args.manifest, args.output_dir, threshold=args.threshold,
                                   device=args.device, min_interval=args.min_interval)
        import json as _json
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(_json.dumps(report, indent=1, sort_keys=True) + "\n")
        return report, 0
    if args.enrich_command == "build-graph":
        import json as _json
        from scientific_network.enrich.e3 import run_build_enrichment
        summary = run_build_enrichment(args.e2_dir, args.link_dir, args.texts, args.org_wikidata, args.org_wikipedia, args.base_graph,
                                       args.manifest, args.output_dir, _json.loads(args.config.read_text()),
                                       quality_config=args.quality_config, org_facts_path=args.org_facts, v2_manifest=args.v2_manifest)
        return summary, 0 if summary["validation"]["status"] == "passed" else 1
    if args.enrich_command == "guard-links":
        import json as _json
        from scientific_network.enrich.e3 import run_guard_links
        cfg = _json.loads(args.config.read_text())
        link_cfg = cfg["linking"]
        report = run_guard_links(args.link_dir, args.output_dir, threshold=link_cfg["threshold"], reject_narrower_page=link_cfg["reject_narrower_page"])
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(_json.dumps(report, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
        return report, 0
    if args.enrich_command == "applied-to-dev-sample":
        from scientific_network.enrich.v3 import freeze_applied_to_dev
        return freeze_applied_to_dev(candidates_graph_path=args.candidates_graph, texts_path=args.texts, out_dir=args.packet_dir, report_dir=args.report_dir), 0
    if args.enrich_command == "audit-v2-sample":
        from scientific_network.enrich.audit_v2 import freeze_v2
        return freeze_v2(graph_path=args.graph, texts_path=args.texts, v1_graph_path=args.v1_graph, v1_sample_path=args.v1_sample,
                         dev_label_files=args.dev_labels, config_path=args.config, out_dir=args.output_dir), 0
    if args.enrich_command == "type-conflicts":
        import json as _json
        from scientific_network.enrich.quality import type_conflicts
        report = type_conflicts(_json.loads(args.graph.read_text(encoding="utf-8")))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(_json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return {k: v for k, v in report.items() if k != "conflicts"}, 0
    if args.enrich_command == "load-graph":
        from scientific_network.enrich.load5 import build as load_enriched
        return load_enriched(args.graph, args.report), 0
    if args.enrich_command == "audit-sample":
        from scientific_network.enrich.quality import freeze_audit
        return freeze_audit(graph_path=args.graph, mentions_path=args.mentions, texts_path=args.texts, test_path=args.test,
                            link_dir=args.link_dir, slm_only_path=args.slm_only, out_dir=args.output_dir, seed=args.seed,
                            rules_path=args.rules), 0
    if args.enrich_command == "score-audit":
        from scientific_network.enrich.quality import score_audit
        return score_audit(audit_dir=args.audit_dir, graph_path=args.graph, mentions_path=args.mentions, texts_path=args.texts,
                           test_path=args.test, slm_only_path=args.slm_only, output=args.output,
                           run_info=_json_load(args.run_info)), 0
    if args.enrich_command == "audit-partof-v2":
        import json as _json
        import shutil
        from hashlib import sha256 as _sha

        from scientific_network.enrich.part_of_v2 import build_packets, statement_index
        graph = _json.loads(args.graph.read_text(encoding="utf-8"))
        result = build_packets(args.audit_dir, graph, _json.loads(args.org_wikidata.read_text()), statement_index(args.fetch_manifest, args.raw_dir))
        if args.packets_copy:
            args.packets_copy.mkdir(parents=True, exist_ok=True)
            for info in result["packets"].values():
                shutil.copy(info["path"], args.packets_copy)
        v1 = _json.loads((args.audit_dir / "freeze-receipt.json").read_text())
        receipt = {"purpose": "PART_OF packet v2, written before any v2 judgement", "supersedes": "PART_OF packet v1 for the part_of axis only",
                   "v1_freeze_receipt": {"sample_sha256": v1["sample_sha256"], "items_sha256": v1["items_sha256"]},
                   "why": "v1 showed only organization names and descriptions; 14 of 50 items were judged unclear because the names alone do not show an "
                          "affiliation. That is a packet defect, not evidence about the data.",
                   "created_after_v1_results_were_seen": True,
                   "what_changed": "only the evidence shown (Wikidata property P749/P361, both QIDs and labels, the statement item URL, the raw-store response SHA-256 "
                                   "and retrieval time); the same 50 items, no sample change, no other axis changed; the question wording is unchanged except that it "
                                   "names the cited statement and lets general knowledge decide",
                   "note_on_graph_evidence_hash": "the PART_OF evidence records in the graph carry one aggregate hash of all SPARQL responses; the packets show the "
                                                  "per-statement raw response hash instead, found by re-reading the raw store",
                   **result}
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(_json.dumps(receipt, indent=1, ensure_ascii=False) + "\n")
        return receipt, 0
    if args.enrich_command == "cooccurrence":
        import json as _json

        from scientific_network.enrich.cooccurrence import CooccurrenceIndex, distribution
        graph = _json.loads(args.graph.read_text(encoding="utf-8"))
        index = CooccurrenceIndex.from_graph(graph)
        if args.entity:
            if not args.partner_type:
                raise SystemExit("--partner-type is required with --entity")
            return {"entity": args.entity, "partners": index.partners(args.entity, args.partner_type, args.min_papers)}, 0
        report = {**distribution(index), "graph_version": graph["graph_version"]}
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(_json.dumps(report, indent=1, ensure_ascii=False) + "\n")
        return report, 0
    if args.enrich_command == "audit-adjudicate":
        from scientific_network.enrich.quality import write_adjudication_packet
        return write_adjudication_packet(args.audit_dir), 0
    if args.enrich_command == "run-slm":
        from scientific_network.enrich.k1 import client_from_config, read_jsonl, run_slm
        client = client_from_config(args.llm_config, log_path=args.call_log)
        return run_slm(args.mode, client, read_jsonl(args.texts), args.output, encoder_path=args.encoder_output,
                       entity_threshold=args.entity_threshold, relation_threshold=args.relation_threshold,
                       workers=args.workers), 0
    if args.enrich_command == "score-dev":
        from scientific_network.enrich.k1 import (predictions_from_encoder, predictions_from_slm, read_jsonl,
                                                  score_predictions, tune_encoder)
        labels = read_jsonl(args.labels)
        texts = {r["id"]: r["text"] for r in read_jsonl(args.texts)}
        out = {}
        if args.encoder_output and (args.tune or not args.slm_output):
            encoded = read_jsonl(args.encoder_output)
            if args.tune:
                out["tuning"] = tune_encoder(encoded, labels, texts)
            else:
                ents, rels = predictions_from_encoder(encoded, texts, entity_threshold=args.entity_threshold,
                                                      relation_threshold=args.relation_threshold)
                out["encoder_only"] = score_predictions(ents, rels, labels, texts)
        if args.slm_output:
            ents, rels = predictions_from_slm(read_jsonl(args.slm_output))
            out["slm"] = score_predictions(ents, rels, labels, texts)
        return out, 0
    return {"stage": f"enrich {args.enrich_command}", "status": "not_implemented",
            "note": PLANNED[args.enrich_command], "output_written": False}, 2
