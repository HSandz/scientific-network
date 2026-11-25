"""Hash-seed sensitivity of the qa-eval-v1 factual scorer (WORK-2026-11-26-001).

``UnifiedEntityResolver.resolve`` (qa_eval.py) accepts exact alias matches while
iterating a Python ``set`` of normalized answer spans. Set iteration order depends
on the per-process string hash seed (``PYTHONHASHSEED``), so the order of resolved
IDs, and therefore the top-k slice used for ``ranked_list`` answers, can change
between processes with identical inputs. This module measures that spread by
re-scoring EXISTING raw outputs in child processes with fixed hash seeds. It runs
no system and writes nothing into frozen result directories:

- ``k1``: re-scores reports/final-exam/k1-answer raw outputs (development only).
- ``qa-eval-v1``: copies the frozen test raw outputs into a scratch directory under
  an ignored run directory and re-scores them there; the frozen
  ``factual-scores.json`` is never touched.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
from typing import Any

import yaml


def _child_k1(config: Path) -> dict[str, Any]:
    from scientific_network.evaluation.k1_answer import load_config, score_all

    payload = score_all(load_config(config), write=False)
    return {
        k: {h: m["by_hop"][h]["mean_score"] for h in ("1", "2", "3", "factual_overall")}
        for k, m in payload["models"].items()
    }


def _child_qa(config: Path, scratch: Path) -> dict[str, Any]:
    from scientific_network.evaluation.qa_eval import score_factual_results

    cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
    payload = score_factual_results(cfg, out_dir=scratch)
    return {
        s: {h: v["by_hop"][h]["mean_score"] for h in ("1", "2", "3", "factual_overall")}
        for s, v in payload["systems"].items()
    }


def _summarize(per_seed: dict[str, dict[str, dict[str, float | None]]]) -> dict[str, Any]:
    keys = sorted({k for r in per_seed.values() for k in r})
    out: dict[str, Any] = {}
    for k in keys:
        out[k] = {}
        for h in ("1", "2", "3", "factual_overall"):
            vals = [r[k][h] for r in per_seed.values() if r.get(k, {}).get(h) is not None]
            if vals:
                out[k][h] = {"min": round(min(vals), 4), "mean": round(statistics.fmean(vals), 4),
                             "max": round(max(vals), 4), "n_seeds": len(vals)}
    return out


def run(target: str, seeds: list[int], *, config: Path, run_dir: Path, out: Path) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    per_seed: dict[str, Any] = {}
    for seed in seeds:
        env = {**os.environ, "PYTHONHASHSEED": str(seed)}
        cmd = [sys.executable, "-m", "scientific_network.evaluation.scorer_sensitivity", "child",
               "--target", target, "--config", str(config), "--run-dir", str(run_dir)]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        per_seed[str(seed)] = json.loads(res.stdout.strip().splitlines()[-1])
    payload = {
        "target": target,
        "reason": "UnifiedEntityResolver.resolve iterates a set of normalized spans; resolved-ID order (and the "
                  "ranked_list top-k slice) depends on PYTHONHASHSEED. Existing raw outputs re-scored only; no "
                  "system was run.",
        "seeds": seeds,
        "per_seed": per_seed,
        "summary": _summarize(per_seed),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--target", choices=("k1", "qa-eval-v1"), required=True)
    r.add_argument("--seeds", default="0-19")
    r.add_argument("--config", type=Path, required=True)
    r.add_argument("--run-dir", type=Path, required=True)
    r.add_argument("--out", type=Path, required=True)
    c = sub.add_parser("child")
    c.add_argument("--target", choices=("k1", "qa-eval-v1"), required=True)
    c.add_argument("--config", type=Path, required=True)
    c.add_argument("--run-dir", type=Path, required=True)
    args = ap.parse_args(argv)
    if args.cmd == "child":
        if args.target == "k1":
            res = _child_k1(args.config)
        else:
            cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
            frozen = Path("reports/final-exam/qa-eval-v1/raw-outputs.jsonl")
            scratch = args.run_dir / f"scratch-{os.environ.get('PYTHONHASHSEED', 'random')}"
            if scratch.resolve() == frozen.parent.resolve():
                raise RuntimeError("refusing to score into the frozen qa-eval-v1 directory")
            scratch.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(frozen, scratch / "raw-outputs.jsonl")
            del cfg
            res = _child_qa(args.config, scratch)
        print(json.dumps(res))
        return 0
    lo, _, hi = args.seeds.partition("-")
    seeds = list(range(int(lo), int(hi or lo) + 1))
    payload = run(args.target, seeds, config=args.config, run_dir=args.run_dir, out=args.out)
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
