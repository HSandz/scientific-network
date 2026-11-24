"""Turn raw encoder output into de-duplicated, type-checked candidates for SLM verification.

The encoders repeat an entity once per mention (GLiNER-Relex also repeats relations) and
GLiNER-Relex can violate endpoint types, so candidates are merged by (type, normalized
surface) keeping the highest score, relations are filtered to valid endpoint types, and
low-scoring spans are cut by a threshold chosen on development papers.
"""

from scientific_network.enrich.textutil import acronym_map, expand, normalize

LABEL = {"method": "Method", "task": "Task", "dataset": "Dataset"}
RELATION = {"applied_to": "APPLIED_TO", "evaluated_on": "EVALUATED_ON", "task_evaluated_on": "EVALUATED_ON"}
GENERIC = {"model", "method", "approach", "framework", "algorithm", "network", "technique", "task", "dataset",
           "benchmark", "data", "system", "problem", "performance", "results"}


def merge_entities(record: dict, text: str, *, threshold: float, expand_acronyms: bool = True) -> list[dict]:
    acronyms = acronym_map(text) if expand_acronyms else {}
    merged: dict[tuple[str, str], dict] = {}
    for entity in record["entities"]:
        if entity["score"] < threshold or entity["label"] not in LABEL:
            continue
        surface = expand(entity["text"].strip(), acronyms)
        key = (LABEL[entity["label"]], normalize(surface))
        if not key[1] or key[1] in GENERIC:
            continue
        slot = merged.setdefault(key, {"type": key[0], "text": surface, "score": entity["score"], "mentions": []})
        slot["score"] = max(slot["score"], entity["score"])
        slot["mentions"].append({"start": entity["start"], "end": entity["end"], "surface": entity["text"],
                                 "score": entity["score"]})
    ordered = sorted(merged.values(), key=lambda e: (e["mentions"][0]["start"] if e["mentions"][0]["start"] >= 0 else 10**9, e["text"]))
    for index, entity in enumerate(ordered, 1):
        entity["id"] = index
    return ordered


def merge_relations(record: dict, entities: list[dict], text: str, *, threshold: float) -> list[dict]:
    acronyms = acronym_map(text)
    by_name = {normalize(e["text"]): e for e in entities}
    seen, out = set(), []
    for rel in record["relations"]:
        name = RELATION.get(rel["relation"])
        if name is None or rel["score"] < threshold:
            continue
        head = by_name.get(normalize(expand(rel["head"], acronyms)))
        tail = by_name.get(normalize(expand(rel["tail"], acronyms)))
        if head is None or tail is None:
            continue
        ok = (name == "APPLIED_TO" and head["type"] == "Method" and tail["type"] == "Task") or \
             (name == "EVALUATED_ON" and head["type"] in ("Method", "Task") and tail["type"] == "Dataset")
        key = (head["id"], name, tail["id"])
        if ok and key not in seen:
            seen.add(key)
            out.append({"head": head["text"], "relation": name, "tail": tail["text"], "score": rel["score"]})
    return out
