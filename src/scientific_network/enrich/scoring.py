"""Score extracted entities and relations against the frozen development reference labels.

Matching rule (fixed in docs/final-exam/enrichment-labeling-guideline-v1.md before any model
ran on development papers): same type, normalized token-set Jaccard >= 0.5, one-to-one,
greedy by similarity (lenient, primary); identical normalized strings (strict). Acronyms
defined in the paper text are expanded on both sides.
"""

from collections import defaultdict

from scientific_network.enrich.textutil import acronym_map, expand, jaccard, normalize

TYPES = ("Method", "Task", "Dataset")


def _prepare(items: list[tuple[str, str]], acronyms: dict[str, str]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    out = []
    for kind, surface in items:
        key = (kind, normalize(expand(surface, acronyms)))
        if key[1] and key not in seen:
            seen.add(key)
            out.append((kind, expand(surface, acronyms)))
    return out


def _greedy(pred: list[str], ref: list[str], threshold: float, strict: bool) -> int:
    pairs = []
    for i, p in enumerate(pred):
        for j, r in enumerate(ref):
            score = 1.0 if (strict and normalize(p) == normalize(r)) else (0.0 if strict else jaccard(p, r))
            if score >= (1.0 if strict else threshold) and score > 0:
                pairs.append((score, i, j))
    pairs.sort(key=lambda x: (-x[0], x[1], x[2]))
    used_p: set[int] = set()
    used_r: set[int] = set()
    matched = 0
    for _score, i, j in pairs:
        if i not in used_p and j not in used_r:
            used_p.add(i)
            used_r.add(j)
            matched += 1
    return matched


def prf(tp: int, n_pred: int, n_ref: int) -> dict:
    precision = tp / n_pred if n_pred else 0.0
    recall = tp / n_ref if n_ref else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "predicted": n_pred, "reference": n_ref, "precision": round(precision, 4),
            "recall": round(recall, 4), "f1": round(f1, 4)}


def score_entities(predictions: dict[str, list[tuple[str, str]]], labels: list[dict], texts: dict[str, str],
                   *, strict: bool = False) -> dict:
    """``predictions``: paper_id -> [(type, surface)]. Returns per-type and micro P/R/F1."""
    totals = defaultdict(lambda: [0, 0, 0])
    for label in labels:
        pid = label["paper_id"]
        acr = acronym_map(texts[pid])
        ref_items = ([("Method", s) for s in label["methods"]] + [("Task", s) for s in label["tasks"]]
                     + [("Dataset", s) for s in label["datasets"]])
        ref = _prepare(ref_items, acr)
        pred = _prepare(predictions.get(pid, []), acr)
        for kind in TYPES:
            r = [s for k, s in ref if k == kind]
            p = [s for k, s in pred if k == kind]
            tp = _greedy(p, r, 0.5, strict)
            for key in (kind, "micro"):
                totals[key][0] += tp
                totals[key][1] += len(p)
                totals[key][2] += len(r)
    result = {kind: prf(*totals[kind]) for kind in TYPES}
    result["micro"] = prf(*totals["micro"])
    result["macro_f1"] = round(sum(result[k]["f1"] for k in TYPES) / len(TYPES), 4)
    return result


def score_relations(predictions: dict[str, list[tuple[str, str, str]]], labels: list[dict], texts: dict[str, str],
                    *, strict: bool = False) -> dict:
    """``predictions``: paper_id -> [(head, RELATION, tail)]."""
    totals = defaultdict(lambda: [0, 0, 0])
    for label in labels:
        pid = label["paper_id"]
        acr = acronym_map(texts[pid])
        ref = list({(expand(r["head"], acr), r["relation"], expand(r["tail"], acr)) for r in label["relations"]})
        pred = list({(expand(h, acr), rel, expand(t, acr)) for h, rel, t in predictions.get(pid, [])})
        for rel in ("APPLIED_TO", "EVALUATED_ON"):
            r = [x for x in ref if x[1] == rel]
            p = [x for x in pred if x[1] == rel]
            pairs = []
            for i, a in enumerate(p):
                for j, b in enumerate(r):
                    if strict:
                        ok = normalize(a[0]) == normalize(b[0]) and normalize(a[2]) == normalize(b[2])
                        score = 1.0 if ok else 0.0
                    else:
                        hs, ts = jaccard(a[0], b[0]), jaccard(a[2], b[2])
                        score = min(hs, ts) if hs >= 0.5 and ts >= 0.5 else 0.0
                    if score > 0:
                        pairs.append((score, i, j))
            pairs.sort(key=lambda x: (-x[0], x[1], x[2]))
            used_p: set[int] = set()
            used_r: set[int] = set()
            tp = 0
            for _s, i, j in pairs:
                if i not in used_p and j not in used_r:
                    used_p.add(i)
                    used_r.add(j)
                    tp += 1
            for key in (rel, "micro"):
                totals[key][0] += tp
                totals[key][1] += len(p)
                totals[key][2] += len(r)
    return {key: prf(*value) for key, value in totals.items()}
