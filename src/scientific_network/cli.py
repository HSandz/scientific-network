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
    split = commands.add_parser("split", help="freeze venue-balanced test/development/pilot membership")
    split.add_argument("--input", type=Path, required=True, help="corpus_manifest.jsonl")
    split.add_argument("--config", type=Path, default=Path("configs/quality.yaml"))
    split.add_argument("--corpus-config", type=Path, default=Path("configs/corpus.yaml"))
    split.add_argument("--output", type=Path, required=True)
    for name, spec in STAGES.items():
        prefix = "" if name in IMPLEMENTED_STAGES else "PLANNED: "
        stage = commands.add_parser(name, help=f"{prefix}{spec.inputs} → {spec.outputs}")
        stage.add_argument("--config", type=Path, default=Path(f"configs/{spec.config}.yaml"))
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
        elif args.command == "audit-precision":
            result = precision_interval(args.correct, args.total, args.confidence)
            result["input_status"] = "user_supplied_counts_not_independently_verified"
            exit_code = 0
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
