"""Pilot pipeline, offline checks and explicit contracts for pending stages."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

from pydantic import ValidationError
import yaml

from scientific_network import __version__
from scientific_network.contracts import GraphArtifact
from scientific_network.evaluation.precision import precision_interval
from scientific_network.graph.schema import RELATIONSHIPS
from scientific_network.graph.validate import graph_counts, validate_graph
from scientific_network.pipeline import STAGES, IMPLEMENTED_STAGES
from scientific_network.collect.storage import SourceError


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Evidence-backed AI research network pilot")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("schema", help="print the ten relationship contracts as JSON")
    reconcile = commands.add_parser("reconcile-rosters", help="offline leakage triage; no work merges or split allocation")
    reconcile.add_argument("--input", type=Path, required=True)
    reconcile.add_argument("--previous-manifest", type=Path, required=True)
    reconcile.add_argument("--previous-membership", type=Path, required=True)
    reconcile.add_argument("--output", type=Path, required=True)
    freeze = commands.add_parser("freeze-diagnostics", help="freeze prospective five-year layout/year diagnostics")
    freeze.add_argument("--input", type=Path, required=True)
    freeze.add_argument("--triage", type=Path, required=True)
    freeze.add_argument("--config", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
    diagnostic = commands.add_parser("acquire-diagnostics", help="bounded metadata for frozen five-year development IDs")
    diagnostic.add_argument("--input", type=Path, required=True)
    diagnostic.add_argument("--splits", type=Path, required=True)
    diagnostic.add_argument("--config", type=Path, required=True)
    diagnostic.add_argument("--output", type=Path, required=True)
    diagnostic.add_argument("--cache", type=Path, required=True)
    headers = commands.add_parser("extract-diagnostics", help="selective PDF/header source triage for frozen development IDs")
    for name in ("input", "manifest", "splits", "config", "output", "cache"):
        headers.add_argument("--"+name, type=Path, required=True)
    corroborate = commands.add_parser("corroborate-diagnostics", help="bounded public-ORCID development support; no graph import")
    for name in ("input", "manifest", "splits", "reviews", "config", "output", "cache"):
        corroborate.add_argument("--"+name, type=Path, required=True)
    release_acquire = commands.add_parser("release-acquire", help="D040 release Phase 2: match roster papers to OpenAlex works by derived DOI")
    release_acquire.add_argument("--config", type=Path, required=True, help="configs/release-v1.yaml")
    release_acquire.add_argument("--works", type=Path, help="override the works.jsonl path from the config")
    release_acquire.add_argument("--report", type=Path, help="override the acquisition.json path from the config")
    release_acquire.add_argument("--limit", type=int, help="trial run over the first N papers; writes no outputs")
    release_acquire.add_argument("--preflight-only", action="store_true", help="check the OpenAlex allowance and stop")
    release_graph = commands.add_parser("release-graph", help="D040 release Phase 3: build the release graph from the roster-matched OpenAlex works")
    release_graph.add_argument("--config", type=Path, required=True, help="configs/release-v1.yaml")
    release_graph.add_argument("--taxonomy", type=Path, default=Path("configs/topics.yaml"), help="taxonomy for the phrase-baseline topics")
    release_graph.add_argument("--works", type=Path, help="override works.jsonl from the config")
    release_graph.add_argument("--output-dir", type=Path, help="override the graph directory from the config (must be empty or absent)")
    release_graph.add_argument("--summary", type=Path, help="override the tracked graph-summary path from the config")
    topic_test = commands.add_parser("freeze-topic-test", help="freeze the D040 topic test IDs before classifier tuning")
    topic_test.add_argument("--roster", type=Path, default=Path("data/manifests/five-year-roster-v10/corpus_manifest.jsonl"))
    topic_test.add_argument("--membership", type=Path, default=Path("data/manifests/five-year-splits-v1/membership.jsonl"))
    topic_test.add_argument("--leakage", type=Path, default=Path("data/manifests/five-year-roster-v10/leakage-triage.jsonl"))
    topic_test.add_argument("--seed", type=int, required=True)
    topic_test.add_argument("--output", type=Path, required=True)
    topic_cal = commands.add_parser("calibrate-topic-embeddings", help="calibrate topic thresholds using non-test release papers only")
    topic_cal.add_argument("--config", type=Path, default=Path("configs/topics-release-v1.yaml"))
    topic_cal.add_argument("--works", type=Path, default=Path("data/interim/release-v1/works.jsonl"))
    topic_cal.add_argument("--roster", type=Path, default=Path("data/manifests/five-year-roster-v10/corpus_manifest.jsonl"))
    topic_cal.add_argument("--membership", type=Path, default=Path("data/manifests/five-year-splits-v1/membership.jsonl"))
    topic_cal.add_argument("--leakage", type=Path, default=Path("data/manifests/five-year-roster-v10/leakage-triage.jsonl"))
    topic_cal.add_argument("--topic-test", type=Path, default=Path("data/manifests/release-v1/topic-test.jsonl"))
    topic_cal.add_argument("--target-coverage", type=float, default=0.85)
    topic_cal.add_argument("--sample-seed", type=int, default=20261108)
    topic_cal.add_argument("--sample-size", type=int, default=30)
    topic_cal.add_argument("--output", type=Path, required=True)
    release_topics = commands.add_parser("release-topic-graph-v2", help="build and validate graph v2 with frozen embedding topics")
    release_topics.add_argument("--input", type=Path, default=Path("data/processed/release-graph-v1/graph.json"))
    release_topics.add_argument("--works", type=Path, default=Path("data/interim/release-v1/works.jsonl"))
    release_topics.add_argument("--taxonomy", type=Path, default=Path("configs/topics-release-v1.yaml"))
    release_topics.add_argument("--quality", type=Path, default=Path("configs/quality-release-v1.yaml"))
    release_topics.add_argument("--output-dir", type=Path, default=Path("data/processed/release-graph-v2"))
    release_topics.add_argument("--summary", type=Path, default=Path("reports/release-v1/graph-v2-summary.json"))
    correction = commands.add_parser("correct-release-taxonomy", help="correct frozen taxonomy metadata without model inference")
    correction.add_argument("--input", type=Path, required=True)
    correction.add_argument("--taxonomy", type=Path, required=True)
    correction.add_argument("--quality", type=Path, required=True)
    correction.add_argument("--source-summary", type=Path, required=True)
    correction.add_argument("--source-freeze", type=Path, required=True)
    correction.add_argument("--output-dir", type=Path, required=True)
    correction.add_argument("--summary", type=Path, required=True)
    identity_correction = commands.add_parser("correct-release-identity", help="correct global ORCID evidence without changing frozen predictions")
    for option in ("works", "input", "taxonomy", "quality", "source-summary", "source-freeze", "protocol", "output-dir", "summary", "freeze-output"):
        identity_correction.add_argument("--" + option, type=Path, required=True)
    topic_review = commands.add_parser("prepare-topic-review-sheet", help="prepare a prediction-blind sheet for frozen topic-test papers")
    topic_review.add_argument("--works", type=Path, default=Path("data/interim/release-v1/works.jsonl"))
    topic_review.add_argument("--topic-test", type=Path, default=Path("data/manifests/release-v1/topic-test.jsonl"))
    topic_review.add_argument("--taxonomy", type=Path, default=Path("configs/topics-release-v1.yaml"))
    topic_review.add_argument("--output", type=Path, default=Path("reports/release-v1/audit/topic-label-sheet.csv"))
    topic_packets = commands.add_parser("prepare-topic-review-packets", help="assign the frozen topic test to reviewers A/B and create prediction-blind sheets")
    topic_packets.add_argument("--master-sheet", type=Path, default=Path("reports/release-v1/audit/topic-label-sheet.csv"))
    topic_packets.add_argument("--topic-test", type=Path, default=Path("data/manifests/release-v1/topic-test.jsonl"))
    topic_packets.add_argument("--taxonomy", type=Path, default=Path("configs/topics-release-v1.yaml"))
    topic_packets.add_argument("--output-dir", type=Path, default=Path("reports/release-v1/audit"))
    topic_eval = commands.add_parser("score-topic-review", help="score frozen phrase and embedding topic predictions against completed A/B review packets")
    topic_eval.add_argument("--graph-v1", type=Path, default=Path("data/processed/release-graph-v1/graph.json"))
    topic_eval.add_argument("--graph-v2", "--embedding-graph", type=Path, default=Path("data/processed/release-graph-v2/graph.json"))
    topic_eval.add_argument("--topic-test", type=Path, default=Path("data/manifests/release-v1/topic-test.jsonl"))
    topic_eval.add_argument("--taxonomy", type=Path, default=Path("configs/topics-release-v1.yaml"))
    topic_eval.add_argument("--allocation", type=Path, default=Path("reports/release-v1/audit/topic-review-allocation.json"))
    topic_eval.add_argument("--master-sheet", type=Path, default=Path("reports/release-v1/audit/topic-label-sheet.csv"))
    topic_eval.add_argument("--reviewer-a", type=Path, required=True, help="completed reviewer A CSV export")
    topic_eval.add_argument("--reviewer-b", type=Path, required=True, help="completed reviewer B CSV export")
    topic_eval.add_argument("--freeze", type=Path, default=Path("reports/release-v1/freeze.json"))
    topic_eval.add_argument("--graph-v2-summary", "--embedding-summary", type=Path, default=Path("reports/release-v1/graph-v2-summary.json"))
    topic_eval.add_argument("--output", type=Path, default=Path("reports/release-v1/topic-eval.json"))
    pregraph = commands.add_parser("prepare-pregraph", help="freeze diagnostic support tables and report unmet pregraph gates; no graph construction")
    pregraph.add_argument("--config", type=Path, required=True)
    pregraph.add_argument("--output", type=Path, required=True)
    validate = commands.add_parser("validate", help="check a graph artifact's structure, not semantic accuracy")
    validate.add_argument("--input", type=Path, required=True)
    validate.add_argument("--config", type=Path, default=Path("configs/quality.yaml"))
    validate.add_argument("--output", type=Path, help="optional JSON validation summary")
    validate.add_argument("--require-size", action="store_true", help="also fail on the configured size gates; does not certify a release")
    report = commands.add_parser("report", help="create a standalone HTML visualization from recorded artifacts")
    report.add_argument("--input", type=Path, required=True, help="versioned graph JSON")
    report.add_argument("--metrics", type=Path, required=True, help="matching collection metrics JSON")
    report.add_argument("--config", type=Path, default=Path("configs/quality.yaml"))
    report.add_argument("--scope-config", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    review = commands.add_parser("review", help="offline byline/identity/affiliation triage; no graph overrides")
    review.add_argument("--input", type=Path, required=True, help="original acquisition papers.json")
    review.add_argument("--headers", type=Path, required=True)
    review.add_argument("--graph", type=Path, required=True)
    review.add_argument("--queue", type=Path, required=True)
    review.add_argument("--manifest", type=Path, required=True)
    review.add_argument("--splits", type=Path, required=True)
    review.add_argument("--cache", type=Path, required=True)
    review.add_argument("--config", type=Path, required=True)
    review.add_argument("--output", type=Path, required=True)
    audit = commands.add_parser("audit-precision", help="compute an interval from supplied counts; does not perform an audit")
    audit.add_argument("--correct", type=int, required=True)
    audit.add_argument("--total", type=int, required=True)
    audit.add_argument("--confidence", type=float, default=0.95)
    audit_sample = commands.add_parser("freeze-audit-sample", help="prepare a hash-bound edge-review form (CSV, plus an HTML sheet for review_design split_with_overlap)")
    audit_sample.add_argument("--input", type=Path, required=True, help="frozen graph artifact")
    audit_sample.add_argument("--config", type=Path, default=Path("configs/quality.yaml"))
    audit_sample.add_argument("--readiness", type=Path, help="optional historical readiness receipt, verified against the graph when given (not required, D040)")
    audit_sample.add_argument("--output", type=Path, required=True, help="new CSV review form; the HTML sheet is written next to it")
    adjudication_form = commands.add_parser("prepare-edge-adjudications", help="prepare blank joint decisions for returned conflicts; final scoring validates frame and assignments")
    adjudication_form.add_argument("--reviews", type=Path, nargs="+", required=True)
    adjudication_form.add_argument("--output", type=Path, required=True)
    edge_audit = commands.add_parser("score-edge-audit", help="validate and score completed edge-audit review packets (double review, or split with overlap per the quality config); not component evaluation or release certification")
    edge_audit.add_argument("--input", type=Path, required=True, help="exact frozen graph artifact")
    edge_audit.add_argument("--reviews", type=Path, nargs="+", required=True, help="completed CSV exports, parsed separately; assignments follow double_review, split_with_overlap or single_reviewer")
    edge_audit.add_argument("--adjudications", type=Path, help="required only for reviewer disagreements")
    edge_audit.add_argument("--config", type=Path, default=Path("configs/quality.yaml"))
    edge_audit.add_argument("--readiness", type=Path, help="optional historical readiness receipt, verified against the graph when given (not required, D040)")
    edge_audit.add_argument("--allow-partial", action="store_true", help="explicitly score only returned completed reviews; report missingness and potential nonresponse bias")
    edge_audit.add_argument("--output", type=Path, required=True, help="new evaluation JSON")
    agent_review = commands.add_parser("score-agent-review", help="validate frozen agent provenance, receipts and source ledgers before AI-scoped edge/topic scoring")
    for option in ("evaluation-freeze", "completion-receipt", "protocol", "topic-ledger", "edge-ledger",
                   "graph", "quality", "graph-v1", "topic-test", "taxonomy", "allocation", "master-sheet",
                   "topic-reviewer-a", "topic-reviewer-b", "graph-freeze", "graph-summary", "edge-output", "topic-output"):
        agent_review.add_argument("--" + option, type=Path, required=True)
    agent_review.add_argument("--edge-reviews", type=Path, nargs="+", required=True)
    agent_review.add_argument("--adjudications", type=Path)
    agent_review.add_argument("--adjudication-ledger", type=Path)
    agent_review.add_argument("--allow-partial", action="store_true")
    agent_edges = commands.add_parser("score-agent-edge-review", help="validate a prospective edge-only agent review without attributing historical topic labels")
    for option in ("evaluation-freeze", "completion-receipt", "protocol", "edge-ledger", "graph", "quality", "graph-freeze", "graph-summary", "rubric", "edge-output"):
        agent_edges.add_argument("--" + option, type=Path, required=True)
    agent_edges.add_argument("--edge-packets", type=Path, nargs="+", required=True)
    agent_edges.add_argument("--edge-reviews", type=Path, nargs="+", required=True)
    agent_edges.add_argument("--adjudications", type=Path)
    agent_edges.add_argument("--adjudication-ledger", type=Path)
    agent_edges.add_argument("--adjudication-start-receipt", type=Path)
    agent_edges.add_argument("--allow-partial", action="store_true")
    split = commands.add_parser("split", help="freeze venue-balanced test/development/pilot membership")
    split.add_argument("--input", type=Path, required=True, help="corpus_manifest.jsonl")
    split.add_argument("--config", type=Path, default=Path("configs/quality.yaml"))
    split.add_argument("--corpus-config", type=Path, default=Path("configs/corpus.yaml"))
    split.add_argument("--output", type=Path, required=True)
    for name, spec in STAGES.items():
        prefix = "" if name in IMPLEMENTED_STAGES else "PLANNED: "
        stage = commands.add_parser(name, help=f"{prefix}{spec.inputs} → {spec.outputs}")
        stage.add_argument("--config", type=Path, default=Path(f"configs/{spec.config}.yaml"))
        if name == "evaluate":
            stage.add_argument("--frame", type=Path, required=True, help="frozen component evaluation frame")
            stage.add_argument("--predictions", type=Path, required=True, help="frozen model predictions")
            stage.add_argument("--gold", type=Path, required=True, help="two independent review packets and adjudications")
        else:
            stage.add_argument("--input", type=Path, required=name != "discover")
        stage.add_argument("--output", type=Path, required=True)
        if name in {"discover", "acquire", "extract", "resolve"}:
            stage.add_argument("--cache", type=Path, default=Path("data/raw/source-cache"))
        if name == "acquire":
            stage.add_argument("--splits", type=Path, required=True, help="frozen membership.jsonl")
            stage.add_argument("--previous", type=Path, help="reuse acquired records from matching frozen diagnostics; retry failures only")
        if name == "classify":
            stage.add_argument("--quality-config", type=Path, default=Path("configs/quality.yaml"))
            stage.add_argument("--cache", type=Path, default=Path("data/raw/source-cache"))
        if name == "resolve":
            stage.add_argument("--decisions", type=Path, help="input-bound source review; can withhold core records, never force an identity merge")
        if name == "analyze":
            stage.add_argument("--readiness", type=Path, help="optional historical readiness receipt, verified against the graph when given (not required, D040)")
            stage.add_argument("--quality-config", type=Path, default=Path("configs/quality.yaml"))
    return root


def validation_summary(args: argparse.Namespace) -> tuple[dict, int]:
    if args.output and args.output.resolve() in {args.input.resolve(), args.config.resolve()}:
        raise ValueError("output must differ from input and configuration")
    graph_bytes = args.input.read_bytes()
    config_bytes = args.config.read_bytes()
    graph = GraphArtifact.model_validate_json(graph_bytes)
    config = yaml.safe_load(config_bytes)
    if not isinstance(config, dict) or not isinstance(config.get("size"), dict):
        raise ValueError("quality configuration requires a size mapping")
    size = config["size"]
    for key in ("min_resolved_core_researchers", "min_unique_factual_edges", "required_relation_types"):
        if type(size.get(key)) is not int or size[key] < 1:
            raise ValueError(f"size.{key} must be a positive integer")
    max_labels = config.get("topics", {}).get("max_labels_per_paper", 3)
    if type(max_labels) is not int or max_labels < 1:
        raise ValueError("topics.max_labels_per_paper must be a positive integer")
    derived = config.get("derived", {})
    errors = validate_graph(graph, max_topic_labels=max_labels,
        researcher_min=derived.get("researcher_topic_min_distinct_papers", 2),
        organization_min=derived.get("organization_topic_min_distinct_papers", 3))
    counts = graph_counts(graph)
    size_checks = {
        "resolved_core_researchers": counts["resolved_core_researchers"] >= size["min_resolved_core_researchers"],
        "unique_core_factual_edges": counts["unique_core_factual_edges"] >= size["min_unique_factual_edges"],
        "all_relation_types_present": len(counts["edges_by_relation"]) == size["required_relation_types"],
    }
    failed = bool(errors) or (args.require_size and not all(size_checks.values()))
    summary = {
        "status": "failed" if failed else "passed",
        "validation_scope": "structural_only",
        "release_status": "ineligible_synthetic" if graph.is_synthetic else "not_assessed",
        "semantic_accuracy": "not_measured",
        "graph_version": graph.graph_version,
        "is_synthetic": graph.is_synthetic,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "input_sha256": sha256(graph_bytes).hexdigest(),
        "config_sha256": sha256(config_bytes).hexdigest(),
        "counts": counts,
        "size_targets": size,
        "size_checks": size_checks,
        "errors": errors,
        "limitations": [
            "Source correctness, actual raw-file hashes and NLP quality are not independently verified.",
            "Derived support/weights are recomputed when present; DBMS reconciliation requires the build stage.",
            "Independent global/per-type audits, recall and coverage are required before release.",
        ],
    }
    return summary, int(failed)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        corpus_path = args.corpus_config if args.command == "split" else getattr(args, "config", None)
        if args.command in {"split", "acquire", "extract", "resolve", "classify", "build"} and corpus_path:
            corpus = yaml.safe_load(corpus_path.read_text())
            if isinstance(corpus, dict) and str(corpus.get("workflow", "")).startswith("five_year_rosters_"):
                raise ValueError("five-year v1 supports official roster discovery only; reconcile cross-year leakage and implement/freeze a new sample contract before enrichment")
        if args.command == "schema":
            result = {relation: {
                "source": spec.source, "target": spec.target,
                "evidence_kind": spec.kind, "symmetric": spec.symmetric,
            } for relation, spec in RELATIONSHIPS.items()}
            exit_code = 0
        elif args.command == "validate":
            result, exit_code = validation_summary(args)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        elif args.command == "reconcile-rosters":
            from scientific_network.collect.reconcile import reconcile_rosters
            result = reconcile_rosters(args.input, args.previous_manifest, args.previous_membership, args.output)
            exit_code = 0
        elif args.command == "freeze-diagnostics":
            from scientific_network.collect.diagnostics import freeze_diagnostics
            result = freeze_diagnostics(args.input, args.triage, args.config, args.output)
            exit_code = 0
        elif args.command == "acquire-diagnostics":
            from scientific_network.collect.diagnostic_acquire import acquire_diagnostics
            result = acquire_diagnostics(args.input, args.splits, args.config, args.output, args.cache)
            exit_code = int(result['by_status'].get('failed', 0) > 0 or result['by_status'].get('review', 0) > 0)
        elif args.command == "extract-diagnostics":
            from scientific_network.preprocess.diagnostics import extract_diagnostics
            result = extract_diagnostics(args.input, args.manifest, args.splits, args.config, args.output, args.cache)
            exit_code = int(result['by_status'].get('review', 0) > 0)
        elif args.command == "corroborate-diagnostics":
            from scientific_network.resolve.diagnostics import corroborate_diagnostics
            result = corroborate_diagnostics(args.input, args.manifest, args.splits, args.reviews,
                args.config, args.output, args.cache)
            exit_code = int(result['review_queue_rows'] > 0 or result['collection_stopped'])
        elif args.command == "release-acquire":
            from scientific_network.collect.openalex_release import acquire as release_acquire
            result = release_acquire(args.config, works_path=args.works, report_path=args.report,
                                     limit=args.limit, preflight_only=args.preflight_only)
            exit_code = 0
        elif args.command == "release-graph":
            from scientific_network.resolve.release import build_release_graph
            release = yaml.safe_load(args.config.read_text())
            paths = release["paths"]
            result = build_release_graph(
                args.works or Path(paths["works"]), args.config, args.taxonomy, Path(release["configs"]["quality"]),
                args.output_dir or Path(paths["graph_v1_dir"]), args.summary or Path(paths["graph_summary"]))
            exit_code = 0
        elif args.command == "freeze-topic-test":
            from scientific_network.nlp.topic_test import freeze_topic_test
            result = freeze_topic_test(args.roster, args.membership, args.leakage, args.output, seed=args.seed)
            exit_code = 0
        elif args.command == "calibrate-topic-embeddings":
            from scientific_network.nlp.embeddings import (
                calibrate_topic_thresholds, load_development_documents, load_sentence_model,
            )
            if args.output.exists() or args.output.is_symlink():
                raise ValueError(f"refusing to overwrite calibration output: {args.output}")
            taxonomy = yaml.safe_load(args.config.read_text(encoding="utf-8"))
            if taxonomy.get("status") != "development_before_freeze":
                raise ValueError("topic calibration requires an unfrozen development taxonomy config")
            if any(value is not None for value in (taxonomy.get("model", {}).get("thresholds") or {}).values()):
                raise ValueError("topic calibration config already contains frozen thresholds")
            documents, split_report = load_development_documents(
                args.works, args.roster, args.membership, args.leakage, args.topic_test)
            model = load_sentence_model(taxonomy)
            result = {
                "split": split_report,
                "model": {key: taxonomy["model"].get(key) for key in ("name", "revision", "device", "batch_size")},
                "calibration": calibrate_topic_thresholds(
                    documents, taxonomy, model, target_coverage=args.target_coverage,
                    seed=args.sample_seed, sample_size=args.sample_size,
                    batch_size=taxonomy["model"].get("batch_size", 64)),
            }
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as handle:
                json.dump(result, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
            exit_code = 0
        elif args.command == "release-topic-graph-v2":
            from scientific_network.resolve.release_topics import build_release_graph_v2
            result = build_release_graph_v2(
                args.input, args.works, args.taxonomy, args.quality, args.output_dir, args.summary)
            exit_code = 0
        elif args.command == "correct-release-taxonomy":
            from scientific_network.resolve.release_taxonomy import correct_release_taxonomy
            result = correct_release_taxonomy(args.input, args.taxonomy, args.quality, args.source_summary,
                                             args.source_freeze, args.output_dir, args.summary)
            exit_code = 0
        elif args.command == "correct-release-identity":
            from scientific_network.resolve.release_identity import correct_release_identity
            result = correct_release_identity(args.works, args.input, args.taxonomy, args.quality,
                args.source_summary, args.source_freeze, args.protocol, args.output_dir, args.summary, args.freeze_output)
            exit_code = 0
        elif args.command == "prepare-topic-review-sheet":
            from scientific_network.evaluation.topic_review import prepare_topic_review_sheet
            result = prepare_topic_review_sheet(args.works, args.topic_test, args.taxonomy, args.output)
            exit_code = 0
        elif args.command == "prepare-topic-review-packets":
            from scientific_network.evaluation.topic_review import prepare_topic_review_packets
            result = prepare_topic_review_packets(args.master_sheet, args.topic_test, args.taxonomy, args.output_dir)
            exit_code = 0
        elif args.command == "score-topic-review":
            from scientific_network.evaluation.topic_eval import score_topic_review
            result = score_topic_review(
                args.graph_v1, args.graph_v2, args.topic_test, args.taxonomy,
                args.allocation, args.master_sheet, args.reviewer_a, args.reviewer_b,
                args.freeze, args.graph_v2_summary, args.output,
            )
            exit_code = 0
        elif args.command == "prepare-pregraph":
            from scientific_network.preprocess.pregraph import prepare_pregraph
            result = prepare_pregraph(args.config, args.output)
            exit_code = int(not result['full_pregraph_ready'])
        elif args.command == "report":
            from scientific_network.reporting.html import render_report
            result = render_report(args.input, args.metrics, args.config, args.scope_config, args.output)
            exit_code = 0
        elif args.command == "review":
            from scientific_network.resolve.review import review_evidence
            result = review_evidence(args.input, args.headers, args.graph, args.queue,
                args.manifest, args.splits, args.cache, args.output, args.config)
            exit_code = int(any(k.endswith(":needs_review") for k in result["accepted_technical_checks"]))
        elif args.command == "discover":
            from scientific_network.collect.discover import discover
            result = discover(args.config, args.output, args.cache)
            exit_code = int(result["review_required"] > 0 or result.get("incomplete_editions", 0) > 0)
        elif args.command == "split":
            from scientific_network.collect.splits import freeze_splits
            result = freeze_splits(args.input, args.config, args.corpus_config, args.output)
            exit_code = 0
        elif args.command == "acquire":
            from scientific_network.collect.acquire import acquire
            result = acquire(args.input, args.splits, args.output, args.cache, args.config, args.previous)
            exit_code = int(result["failed"] > 0)
        elif args.command == "extract":
            from scientific_network.preprocess.extract import extract
            result = extract(args.input, args.output, args.cache, args.config)
            exit_code = int(result["by_status"].get("parsed", 0) == 0)
        elif args.command == "resolve":
            from scientific_network.resolve.pilot import resolve
            result = resolve(args.input, args.output, args.cache, args.config, args.decisions)
            exit_code = 0
        elif args.command == "classify":
            from scientific_network.nlp.baseline import classify
            result = classify(args.input, args.config, args.quality_config, args.output, args.cache)
            exit_code = 0
        elif args.command == "build":
            from scientific_network.graph.load import build
            result = build(args.input, args.output, args.config)
            exit_code = 0
        elif args.command == "analyze":
            from scientific_network.analysis.analyze import analyze_graph
            result = analyze_graph(args.input, args.config, args.output, args.readiness, args.quality_config)
            exit_code = 0
        elif args.command == "evaluate":
            from scientific_network.evaluation.components import evaluate_components
            result, exit_code = evaluate_components(
                args.frame, args.predictions, args.gold, args.config, args.output
            )
        elif args.command == "audit-precision":
            result = precision_interval(args.correct, args.total, args.confidence)
            result["input_status"] = "user_supplied_counts_not_independently_verified"
            exit_code = 0
        elif args.command == "freeze-audit-sample":
            from scientific_network.evaluation.edge_audit import prepare_edge_audit_sample
            result = prepare_edge_audit_sample(args.input, args.config, args.output, args.readiness)
            exit_code = 0
        elif args.command == "prepare-edge-adjudications":
            from scientific_network.evaluation.edge_audit import prepare_edge_adjudications
            result = prepare_edge_adjudications(args.reviews, args.output)
            exit_code = 0
        elif args.command == "score-edge-audit":
            from scientific_network.evaluation.edge_audit import evaluate_edge_audit
            result, exit_code = evaluate_edge_audit(args.input, args.reviews, args.config,
                args.output, args.adjudications, args.readiness, allow_partial=args.allow_partial)
        elif args.command == "score-agent-review":
            from scientific_network.evaluation.agent_review import score_agent_review
            result, exit_code = score_agent_review(**{
                key: value for key, value in vars(args).items() if key != "command"
            })
        elif args.command == "score-agent-edge-review":
            from scientific_network.evaluation.agent_edge_review import score_agent_edge_review
            result, exit_code = score_agent_edge_review(**{
                key: value for key, value in vars(args).items() if key != "command"
            })
        else:
            spec = STAGES[args.command]
            print(json.dumps({
                "stage": args.command, "status": "not_implemented",
                "component": f"src/scientific_network/{spec.component}/",
                "expected_inputs": spec.inputs, "expected_outputs": spec.outputs,
                "next_step": spec.next_step, "output_written": False,
            }, indent=2), file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2))
        return exit_code
    except (OSError, ValueError, ValidationError, yaml.YAMLError, SourceError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
