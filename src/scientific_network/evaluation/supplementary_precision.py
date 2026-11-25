"""Supplementary, post-hoc, AI-assessed literature-supported precision (WORK-2026-11-26-001).

The qa-eval-v1 factual score measures agreement with the graph's edges, not truth: an answer item
that is correct and supported by the literature but is not an edge of the graph scores 0. This
check asks isolated AI evaluators whether each listed answer item is a correct answer supported by
the AAAI/IJCAI 2021-2025 papers shown with it. It uses the EXISTING frozen raw outputs of
qa-eval-v1 only: no system is run.

Subcommands:
  sample     extract listed items from S2/S4 answers to hop-1/hop-2 list questions, sample with a
             seed, write the tracked manifest (no abstracts) and the ignored judging packet
  judge      run evaluator A (fresh Claude), B (fresh codex exec) on every item and C (fresh codex
             exec, separate session) on A/B disagreements; archive raw outputs immediately
  aggregate  adjudicate, compute precision with Wilson intervals, append to qa-eval-v1 results
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import re
import subprocess
import time
from typing import Any

import yaml

from scientific_network.evaluation.edge_audit import cohens_kappa
from scientific_network.evaluation.precision import precision_interval
from scientific_network.evaluation.qa_eval import load_works_metadata

PAPER_ID_RE = re.compile(r"paper:(?:aaai|ijcai):\d{4}:[A-Za-z0-9_.-]*[A-Za-z0-9_-]")
_BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+(.*)$")
_STOP = frozenset("a an and the of for in on to with by from via using based task tasks method methods "
                  "dataset datasets model models learning".split())
VERDICTS = ("yes", "no", "unclear")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s.lower()).split())


def _clean_item(raw: str) -> str:
    t = PAPER_ID_RE.sub(" ", raw)
    t = re.sub(r"\[[^\]]*\]", " ", t).replace("**", "").replace("__", "")
    t = t.split(":", 1)[0]
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t)
    t = re.sub(r"\s*[—–-]\s+.*$", "", t)
    return " ".join(t.split()).strip(" .,;:")


def extract_items(answer: str) -> list[dict[str, Any]]:
    """Listed answer items with the paper IDs cited on the same line.

    Bullet or numbered lines give one item each (their head before any colon). An answer without
    bullets gives the comma/and-separated tail of its first sentence that introduces a list with a
    colon. The same rule is applied to every system.
    """
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line in answer.splitlines():
        m = _BULLET_RE.match(line)
        if not m:
            continue
        text = _clean_item(m.group(1))
        key = _norm(text)
        if len(key) < 2 or key in seen:
            continue
        seen.add(key)
        items.append({"item_text": text, "cited_paper_ids": list(dict.fromkeys(PAPER_ID_RE.findall(line)))})
    if items:
        return items
    for raw_sent in re.split(r"(?<=[.!?])\s+|\n+", answer):
        sent = re.sub(r"\[[^\]]*\]", " ", PAPER_ID_RE.sub(" ", raw_sent))  # IDs contain colons
        if ":" not in sent:
            continue
        tail = sent.split(":", 1)[1]
        if tail.strip().startswith(('"', "'", "“", "‘")):
            continue  # a quotation, not a list
        parts = [p for p in re.split(r",|;|\band\b", tail) if p.strip() and not re.search(r"[\"“”]", p)]
        if len(parts) < 2:
            continue
        for part in parts:
            text = _clean_item(part)
            key = _norm(text)
            if len(key) < 2 or len(text) > 80 or key in seen:
                continue
            seen.add(key)
            items.append({"item_text": text, "cited_paper_ids": list(dict.fromkeys(PAPER_ID_RE.findall(part)))})
        break
    return items


def _content_tokens(text: str) -> list[str]:
    return [w for w in _norm(text).split() if len(w) >= 3 and w not in _STOP]


def select_evidence(item: dict[str, Any], shown: list[str], meta: dict[str, dict[str, Any]], k: int = 3) -> tuple[list[str], str]:
    """Papers shown to the evaluator for one item (identical rule for every system)."""
    if item["cited_paper_ids"]:
        return item["cited_paper_ids"][:k], "cited_on_item_line"
    toks = _content_tokens(item["item_text"])
    if toks:
        hits = []
        for pid in shown:
            m = meta.get(pid)
            if not m:
                continue
            blob = f" {_norm(m.get('title', '') + ' ' + m.get('abstract', ''))} "
            if all(f" {t}" in blob for t in toks):
                hits.append(pid)
        if hits:
            return hits[:k], "shown_paper_mentions_item"
    if shown:
        return shown[:k], "first_shown_papers_no_mention"
    return [], "no_paper_shown"


def sample_items(cfg: dict[str, Any]) -> dict[str, Any]:
    raw_path = Path(cfg["inputs"]["raw_outputs"])
    if _sha256_file(raw_path) != cfg["inputs"]["raw_outputs_sha256"]:
        raise ValueError("frozen raw outputs hash mismatch")
    refs = {json.loads(l)["question_id"]: json.loads(l) for l in Path(cfg["inputs"]["references"]).read_text(encoding="utf-8").splitlines() if l.strip()}
    rows = [json.loads(l) for l in raw_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    systems = cfg["sample"]["systems"]
    hops = {str(h) for h in cfg["sample"]["hops"]}
    types = set(cfg["sample"]["answer_types"])
    sel = [r for r in rows if r["system"] in systems and str(r["hops"]) in hops and r["answer_type"] in types]

    all_pids = {p for r in sel for p in (r.get("paper_ids") or [])}
    all_pids |= {p for r in sel for p in PAPER_ID_RE.findall(r.get("answer") or "")}
    meta = load_works_metadata(Path(cfg["inputs"]["works_jsonl"]), all_pids)

    rng = random.Random(int(cfg["sample"]["seed"]))
    per_system: dict[str, list[dict[str, Any]]] = {}
    pool_sizes: dict[str, int] = {}
    for sysname in systems:
        by_q: dict[str, list[dict[str, Any]]] = {}
        for r in sorted((x for x in sel if x["system"] == sysname), key=lambda x: x["question_id"]):
            shown = list(dict.fromkeys((r.get("paper_ids") or []) + PAPER_ID_RE.findall(r.get("answer") or "")))
            for pos, it in enumerate(extract_items(r.get("answer") or "")):
                ev, rule = select_evidence(it, shown, meta)
                by_q.setdefault(r["question_id"], []).append({
                    "system": sysname,
                    "question_id": r["question_id"],
                    "hops": str(r["hops"]),
                    "answer_type": r["answer_type"],
                    "question_text": refs[r["question_id"]]["text"],
                    "item_position": pos,
                    "item_text": it["item_text"],
                    "cited_paper_ids": it["cited_paper_ids"],
                    "evidence_paper_ids": ev,
                    "evidence_rule": rule,
                })
        pool_sizes[sysname] = sum(len(v) for v in by_q.values())
        qids = sorted(by_q)
        rng.shuffle(qids)
        for q in qids:
            rng.shuffle(by_q[q])
        picked: list[dict[str, Any]] = []
        cap = int(cfg["sample"]["max_items_per_system"])
        while len(picked) < cap and any(by_q[q] for q in qids):
            for q in qids:
                if by_q[q] and len(picked) < cap:
                    picked.append(by_q[q].pop(0))
        per_system[sysname] = picked

    items = [x for s in systems for x in per_system[s]]
    rng.shuffle(items)
    for i, it in enumerate(items, start=1):
        it["item_id"] = f"sp-{i:03d}"
    manifest = {
        "protocol_version": cfg["protocol_version"],
        "post_hoc": True,
        "ai_assessed": True,
        "raw_outputs_sha256": cfg["inputs"]["raw_outputs_sha256"],
        "seed": cfg["sample"]["seed"],
        "pool_sizes": pool_sizes,
        "sampled_per_system": {s: len(per_system[s]) for s in systems},
        "evidence_rule_counts": {
            s: {rule: sum(1 for x in per_system[s] if x["evidence_rule"] == rule)
                for rule in ("cited_on_item_line", "shown_paper_mentions_item", "first_shown_papers_no_mention", "no_paper_shown")}
            for s in systems
        },
        "evaluator_question": cfg["judging"]["question"],
        "items": [{k: v for k, v in it.items()} for it in items],
    }
    out = Path(cfg["outputs"]["manifest"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    packet = []
    for it in items:
        packet.append({
            "item_id": it["item_id"],
            "question": it["question_text"],
            "answer_item": it["item_text"],
            "papers_shown": [
                {"paper_id": p, "title": meta.get(p, {}).get("title", ""), "year": meta.get(p, {}).get("year"),
                 "abstract": meta.get(p, {}).get("abstract", "")}
                for p in it["evidence_paper_ids"]
            ],
        })
    pk = Path(cfg["outputs"]["packet"])
    pk.parent.mkdir(parents=True, exist_ok=True)
    pk.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in packet) + "\n", encoding="utf-8")
    return {"manifest": str(out), "manifest_sha256": _sha256_file(out), "pool_sizes": pool_sizes,
            "sampled": manifest["sampled_per_system"], "evidence_rules": manifest["evidence_rule_counts"]}


# ---------------------------------------------------------------------------
# Judging
# ---------------------------------------------------------------------------


def _prompt(items: list[dict[str, Any]], question: str) -> str:
    return (
        "You are an independent scientific evaluator. Each item below gives a research question about "
        "papers from the AAAI and IJCAI conferences, 2021-2025, one item from an answer list, and the "
        "paper(s) shown with that item (title and abstract).\n"
        f"For each item answer: {question}\n"
        "Verdicts:\n"
        "- yes: the item is a correct answer to the question and the shown paper(s) support it.\n"
        "- no: the item is not a correct answer to the question, or the shown paper(s) do not support it "
        "(unrelated, contradict it, or no paper is shown).\n"
        "- unclear: the title and abstract are not enough to decide.\n"
        "Judge each item independently. Use only the text shown; do not use outside knowledge to supply "
        "missing evidence. Do not use tools or files.\n"
        "Return ONLY a JSON array, no markdown fences or prose, one object per item:\n"
        '[{"item_id": "...", "verdict": "yes"|"no"|"unclear", "rationale": "one short sentence"}]\n\n'
        "Items:\n" + json.dumps(items, ensure_ascii=False, indent=1)
    )


def _extract_array(text: str) -> list[dict[str, Any]]:
    raw = text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        val = json.loads(raw)
        if isinstance(val, list):
            return val
    except json.JSONDecodeError:
        pass
    m = re.search(r"\[.*\]", raw, flags=re.S)
    if not m:
        raise ValueError(f"no JSON array in response: {raw[:200]}")
    return json.loads(m.group(0))


def _run_cli(channel: str, prompt: str, workdir: Path, tag: str, cli: dict[str, str]) -> tuple[str, dict[str, Any]]:
    workdir.mkdir(parents=True, exist_ok=True)
    log = workdir / f"{tag}.log"
    if channel == "A":
        proc = subprocess.run([cli["claude"], "-p", "--output-format", "json"], input=prompt, text=True,
                              capture_output=True, cwd=workdir, timeout=900)
        log.write_text(proc.stdout + "\n--- STDERR ---\n" + proc.stderr, encoding="utf-8")
        if proc.returncode != 0:
            raise RuntimeError(f"claude exited {proc.returncode}")
        payload = json.loads(proc.stdout)
        if payload.get("is_error"):
            raise RuntimeError("claude returned an error")
        return str(payload.get("result") or ""), {"session_id": payload.get("session_id"),
                                                   "models": sorted((payload.get("modelUsage") or {}).keys())}
    msg = workdir / f"{tag}.last.txt"
    proc = subprocess.run([cli["codex"], "exec", "--skip-git-repo-check", "--json", "-o", str(msg.resolve()), "-"],
                          input=prompt, text=True, capture_output=True, cwd=workdir, timeout=900)
    log.write_text(proc.stdout + "\n--- STDERR ---\n" + proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"codex exited {proc.returncode}")
    thread = None
    for line in proc.stdout.splitlines():
        if line.strip().startswith("{"):
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "thread.started":
                thread = ev.get("thread_id")
    text = msg.read_text(encoding="utf-8") if msg.exists() else ""
    return text, {"session_id": thread, "models": [cli.get("codex_model_label", "codex")]}


def _judge_batch(channel: str, batch: list[dict[str, Any]], *, question: str, workdir: Path, tag: str,
                 cli: dict[str, str]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    ids = [x["item_id"] for x in batch]
    last = ""
    for attempt in range(3):
        try:
            text, meta = _run_cli(channel, _prompt(batch, question), workdir, f"{tag}.a{attempt}", cli)
            got: dict[str, dict[str, Any]] = {}
            for obj in _extract_array(text):
                iid = str(obj.get("item_id") or "").strip()
                v = str(obj.get("verdict") or "").strip().lower()
                if iid in ids and v in VERDICTS:
                    got[iid] = {"verdict": v, "rationale": str(obj.get("rationale") or "")[:400]}
            missing = [i for i in ids if i not in got]
            if not missing:
                return got, {**meta, "attempts": attempt + 1}
            last = f"missing {missing[:5]}"
        except Exception as exc:  # noqa: BLE001 - retried and reported
            last = str(exc)
        time.sleep(2)
    raise RuntimeError(f"{channel} {tag} failed: {last}")


def run_judging(cfg: dict[str, Any]) -> dict[str, Any]:
    packet = [json.loads(l) for l in Path(cfg["outputs"]["packet"]).read_text(encoding="utf-8").splitlines() if l.strip()]
    manifest = json.loads(Path(cfg["outputs"]["manifest"]).read_text(encoding="utf-8"))
    if [x["item_id"] for x in packet] != [x["item_id"] for x in manifest["items"]]:
        raise ValueError("packet and manifest disagree")
    q = cfg["judging"]["question"]
    bs = int(cfg["judging"]["batch_size"])
    root = Path(cfg["judging"]["workdir"])
    cli = cfg["judging"]["cli"]
    archive = Path(cfg["outputs"]["run_dir"]) / "judging"
    archive.mkdir(parents=True, exist_ok=True)
    batches = [packet[i:i + bs] for i in range(0, len(packet), bs)]

    def channel_run(ch: str, items_batches: list[list[dict[str, Any]]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        verdicts: dict[str, Any] = {}
        metas: list[dict[str, Any]] = []
        for bi, b in enumerate(items_batches):
            got, meta = _judge_batch(ch, b, question=q, workdir=root / f"{ch}-b{bi:02d}", tag=f"{ch}-b{bi:02d}", cli=cli)
            verdicts.update(got)
            metas.append({"batch": bi, "items": [x["item_id"] for x in b], **meta})
            (archive / f"verdicts-{ch}.json").write_text(json.dumps({"verdicts": verdicts, "calls": metas}, indent=2) + "\n", encoding="utf-8")
        return verdicts, metas

    with ThreadPoolExecutor(max_workers=2) as ex:
        fa = ex.submit(channel_run, "A", batches)
        fb = ex.submit(channel_run, "B", batches)
        va, ma = fa.result()
        vb, mb = fb.result()
    disputed = [x for x in packet if va[x["item_id"]]["verdict"] != vb[x["item_id"]]["verdict"]]
    vc: dict[str, Any] = {}
    mc: list[dict[str, Any]] = []
    if disputed:
        vc, mc = channel_run("C", [disputed[i:i + bs] for i in range(0, len(disputed), bs)])
    evidence = {
        "protocol_version": cfg["protocol_version"],
        "ai_assessed": True,
        "post_hoc": True,
        "manifest_sha256": _sha256_file(Path(cfg["outputs"]["manifest"])),
        "judged_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "evaluators": cfg["judging"]["evaluators"],
        "calls": {"A": ma, "B": mb, "C": mc},
        "verdicts": {"A": va, "B": vb, "C": vc},
    }
    out = Path(cfg["outputs"]["evaluator_evidence"])
    out.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"items": len(packet), "disputed": len(disputed), "evidence": str(out)}


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _rate(k: int, n: int) -> dict[str, Any]:
    if not n:
        return {"yes": 0, "total": 0, "rate": None, "wilson_95_ci": None}
    ci = precision_interval(k, n)
    return {"yes": k, "total": n, "rate": round(k / n, 4),
            "wilson_95_ci": [round(ci["wilson_lower"], 4), round(ci["wilson_upper"], 4)]}


def aggregate(cfg: dict[str, Any]) -> dict[str, Any]:
    manifest = json.loads(Path(cfg["outputs"]["manifest"]).read_text(encoding="utf-8"))
    ev = json.loads(Path(cfg["outputs"]["evaluator_evidence"]).read_text(encoding="utf-8"))
    va, vb, vc = ev["verdicts"]["A"], ev["verdicts"]["B"], ev["verdicts"]["C"]
    resolved = []
    for it in manifest["items"]:
        iid = it["item_id"]
        a, b = va[iid]["verdict"], vb[iid]["verdict"]
        final = a if a == b else vc[iid]["verdict"]
        resolved.append({**it, "verdict_a": a, "verdict_b": b, "verdict_c": vc.get(iid, {}).get("verdict"), "final": final})
    by_system: dict[str, Any] = {}
    for s in cfg["sample"]["systems"]:
        sub = [x for x in resolved if x["system"] == s]
        entry = {
            "literature_supported_precision": _rate(sum(1 for x in sub if x["final"] == "yes"), len(sub)),
            "excluding_unclear": _rate(sum(1 for x in sub if x["final"] == "yes"), sum(1 for x in sub if x["final"] != "unclear")),
            "verdicts": {v: sum(1 for x in sub if x["final"] == v) for v in VERDICTS},
            "by_hop": {},
            "by_evidence_rule": {},
        }
        for h in sorted({x["hops"] for x in sub}):
            hs = [x for x in sub if x["hops"] == h]
            entry["by_hop"][h] = _rate(sum(1 for x in hs if x["final"] == "yes"), len(hs))
        for rule in sorted({x["evidence_rule"] for x in sub}):
            rs = [x for x in sub if x["evidence_rule"] == rule]
            entry["by_evidence_rule"][rule] = _rate(sum(1 for x in rs if x["final"] == "yes"), len(rs))
        by_system[s] = entry
    kappa = cohens_kappa([(x["verdict_a"], x["verdict_b"]) for x in resolved])
    result = {
        "protocol_version": cfg["protocol_version"],
        "label": "Supplementary, post-hoc, AI-assessed literature-supported precision",
        "added": "2026-11-26",
        "reason": cfg["reason"],
        "ai_assessed": True,
        "post_hoc": True,
        "does_not_replace": "the frozen graph-agreement factual scores in this file",
        "manifest": cfg["outputs"]["manifest"],
        "manifest_sha256": ev["manifest_sha256"],
        "evaluator_evidence": cfg["outputs"]["evaluator_evidence"],
        "evaluators": cfg["judging"]["evaluators"],
        "question": cfg["judging"]["question"],
        "cohens_kappa_ab": round(kappa, 4) if kappa is not None else None,
        "disagreements_adjudicated_by_c": sum(1 for x in resolved if x["verdict_a"] != x["verdict_b"]),
        "by_system": by_system,
    }
    Path(cfg["outputs"]["result"]).write_text(json.dumps({**result, "items": resolved}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Supplementary literature-supported precision (post hoc, AI-assessed).")
    ap.add_argument("cmd", choices=("sample", "judge", "aggregate"))
    ap.add_argument("--config", type=Path, default=Path("configs/supplementary-precision-v1.yaml"))
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    fn = {"sample": sample_items, "judge": run_judging, "aggregate": aggregate}[args.cmd]
    print(json.dumps(fn(cfg), indent=2, ensure_ascii=False)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
