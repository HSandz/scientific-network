"""``research-network enrich <stage>`` subcommands for the D042 enrichment track."""

import argparse
from pathlib import Path

PLANNED = {
    "fetch-sources": "Phase 1 (E1): Wikidata/Wikipedia acquisition",
    "extract-entities": "Phase 2 (E2): mention detection, verification, linking",
    "extract-relations": "Phase 3 (E3): relation extraction",
    "build-graph": "Phase 4: v5-enriched build",
    "audit-sample": "Phase 5 (E4): frozen audit sample",
}


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
    for name, text in PLANNED.items():
        stages.add_parser(name, help=f"planned, not implemented: {text}")


def run_enrich(args) -> tuple[dict, int]:
    if args.enrich_command == "freeze-splits":
        from scientific_network.enrich.splits import freeze_enrichment_splits
        return freeze_enrichment_splits(
            args.works, args.membership, args.output, seed=args.seed, n_dev=args.development,
            n_test=args.test, audit_ledgers=args.audit_ledger, topic_test_path=args.topic_test), 0
    if args.enrich_command == "freeze-benchmark":
        from scientific_network.enrich.benchmark import freeze_benchmark
        return freeze_benchmark(args.output), 0
    return {"stage": f"enrich {args.enrich_command}", "status": "not_implemented",
            "note": PLANNED[args.enrich_command], "output_written": False}, 2
