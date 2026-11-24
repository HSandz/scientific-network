"""Small-language-model steps of the entity and relation pipeline (specification §4.2–4.3).

Two prompts, both run at temperature 0 with schema-constrained JSON through
``scientific_network.rag.llm.LLMClient``:

* ``extract`` (SLM only): the model lists Method/Task/Dataset mentions and the two
  relations straight from the title and abstract.
* ``verify`` (encoder + SLM): the model keeps, drops or retypes the encoder's candidate
  spans and returns the relations it supports, possibly adding relations the encoder missed.

Every span the model returns must occur verbatim in the text; spans that do not are dropped
and kept with the reason ``not_in_text``. Dropped encoder spans keep the model's reason.
"""

import re

from scientific_network.enrich.textutil import normalize
from scientific_network.rag.llm import InvalidJSONError, LLMClient

EXTRACT_VERSION = "enrich-slm-extract-v2"
VERIFY_VERSION = "enrich-slm-verify-v4-pointwise"
TYPES = ["Method", "Task", "Dataset"]
RELATIONS = ["APPLIED_TO", "EVALUATED_ON"]

DEFINITIONS = """Entity types:
- Method: a model, algorithm, architecture or technique that the paper proposes, uses or directly compares against. Named systems ("GraphMix", "PPO") and established generic techniques ("transformer", "graph neural network", "contrastive learning") both count. Not a method: bare generic words ("model", "approach", "framework", "method", "algorithm", "network"), metrics, datasets, or the paper's own results.
- Task: a recognisable research problem the paper addresses ("image segmentation", "link prediction"). Not a task: whole fields ("machine learning", "deep learning"), vague goals ("improve performance"), application domains without a named problem.
- Dataset: a named dataset, benchmark, corpus or standard environment suite used for training or evaluation ("ImageNet", "MuJoCo"). Not a dataset: generic phrases ("real-world datasets", "public benchmarks").

Relations (between entities you list, supported by the text):
- APPLIED_TO: Method -> Task, the method is applied to or proposed for the task.
- EVALUATED_ON: Method or Task -> Dataset, evaluated or benchmarked on the dataset.

Copy each entity exactly as written in the text. List each entity once, using its fullest form."""

EXTRACT_RULES = """Extra rules:
- Never list the paper's own title as an entity, and never list a generic phrase such as "real-world datasets", "benchmark datasets", "synthetic data", "various benchmarks" or an application domain as a Dataset.
- A Dataset must carry a proper name (ImageNet, Cora, MNIST) or be a named benchmark or environment suite.
- Named systems, including the paper's own proposed method and its acronym, are Methods. Established technique names are valid Methods even when the paper did not invent them.
- Concepts, formalisms and application domains ("Markov decision processes", "physics", "E-commerce") are not Tasks."""

VERIFY_RULES = """Extra rules:
- Established technique names such as "graph neural network", "attention mechanism", "knowledge distillation" or "contrastive learning" ARE valid Methods. Do not drop a candidate because it is not new, not named, or not proposed by the paper.
- Keep a candidate whenever it fits one type definition. Drop it only if it is (a) a generic word or phrase with no specific content, (b) a metric, number, application domain or field of study, (c) the paper's own title, or (d) a duplicate of another candidate (then keep the fuller form and drop the other with the reason "duplicate").
- If the type is wrong but another type fits, retype it instead of dropping it."""

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "entities": {"type": "array", "items": {"type": "object", "properties": {
            "text": {"type": "string"}, "type": {"type": "string", "enum": TYPES}}, "required": ["text", "type"]}},
        "relations": {"type": "array", "items": {"type": "object", "properties": {
            "head": {"type": "string"}, "relation": {"type": "string", "enum": RELATIONS},
            "tail": {"type": "string"}}, "required": ["head", "relation", "tail"]}},
    },
    "required": ["entities", "relations"],
}

def extract_messages(text: str) -> tuple[str, str]:
    system = ("You extract research entities and relations from the title and abstract of a computer-science "
              "paper. Answer only with JSON.\n\n" + DEFINITIONS + "\n\n" + EXTRACT_RULES)
    return system, f"Title and abstract:\n{text}"


def in_text(text: str, surface: str) -> bool:
    return " ".join(surface.lower().split()) in " ".join(text.lower().split())


def slm_extract(client: LLMClient, text: str, *, max_tokens: int = 1500) -> dict:
    system, user = extract_messages(text)
    try:
        result = client.complete(prompt_version=EXTRACT_VERSION, system=system, user=user,
                                 schema=EXTRACT_SCHEMA, schema_name="extraction", max_tokens=max_tokens)
    except InvalidJSONError as exc:
        return {"valid": False, "error": str(exc), "entities": [], "relations": [], "dropped": [],
                "prompt_tokens": 0, "completion_tokens": 0, "cache_hit": False}
    parsed = result.parsed
    entities, dropped, seen = [], [], set()
    for item in parsed["entities"]:
        key = (item["type"], normalize(item["text"]))
        if not item["text"].strip() or key in seen:
            continue
        seen.add(key)
        if in_text(text, item["text"]):
            entities.append({"type": item["type"], "text": item["text"].strip()})
        else:
            dropped.append({"type": item["type"], "text": item["text"], "reason": "not_in_text"})
    names = {normalize(e["text"]): e for e in entities}
    relations = [r for r in parsed["relations"] if normalize(r["head"]) in names and normalize(r["tail"]) in names]
    relations = [r for r in relations if _endpoint_ok(r, names)]
    return {"valid": True, "entities": entities, "relations": relations, "dropped": dropped,
            "prompt_tokens": result.prompt_tokens, "completion_tokens": result.completion_tokens,
            "cache_hit": result.cache_hit}


def _endpoint_ok(relation: dict, names: dict) -> bool:
    head = names[normalize(relation["head"])]["type"]
    tail = names[normalize(relation["tail"])]["type"]
    if relation["relation"] == "APPLIED_TO":
        return head == "Method" and tail == "Task"
    return head in ("Method", "Task") and tail == "Dataset"


POINTWISE_SYSTEM = (
    "You check one candidate phrase at a time. The candidate was proposed by an automatic tagger for the title and "
    "abstract of a computer-science paper. Reply with exactly one letter and nothing else:\n"
    "K = keep: it is a valid entity of the proposed type\n"
    "M = valid, but it is a Method\nT = valid, but it is a Task\nD = valid, but it is a Dataset\n"
    "X = drop: it is not a valid entity of any type (generic phrase, metric, application domain, field, the paper's own "
    "title, or a part of a longer entity)\n\n" + DEFINITIONS + "\n\n" + VERIFY_RULES)
LETTER_TYPE = {"M": "Method", "T": "Task", "D": "Dataset"}
RELATION_SYSTEM = (
    "You check one proposed relation at a time for the title and abstract of a computer-science paper. Reply with exactly "
    "one letter and nothing else: K = the text supports the relation, X = it does not.\n"
    "APPLIED_TO: a Method is applied to, or proposed for, a Task. EVALUATED_ON: a Method or Task is evaluated or "
    "benchmarked on a Dataset. The relation must be stated or clearly implied by the text, not just the two phrases "
    "appearing in the same paper.")


def _letter(content: str) -> str:
    stripped = content.strip().upper()
    return stripped[0] if stripped and stripped[0] in "KMTDX" else "?"


_DECISION = re.compile(r"(\d+)\s*[:=.)\-]?\s*([KMTDX])\b", re.IGNORECASE)


def parse_decisions(content: str) -> dict[int, str]:
    """Parse ``1:K 2:X 3:M`` style output into {id: letter}; the first decision for an id wins."""
    out: dict[int, str] = {}
    for number, letter in _DECISION.findall(content.upper()):
        out.setdefault(int(number), letter)
    return out


def slm_verify(client: LLMClient, text: str, candidates: list[dict], relations: list[dict], *, workers: int = 1) -> dict:
    """Pointwise verification: one single-letter decision per candidate entity and per candidate relation.

    ``candidates``: [{id, text, type}] from the encoder; ``relations``: [{head, relation, tail}]. The shared
    prefix (system prompt and paper text) is identical across calls, so the server reuses its cached prefix.
    """
    entities, dropped, tokens = [], [], [0, 0]
    for candidate in candidates:
        user = (f"Title and abstract:\n{text}\n\nCandidate phrase: \"{candidate['text']}\"\n"
                f"Proposed type: {candidate['type']}\nAnswer (K, M, T, D or X):")
        result = client.complete(prompt_version=VERIFY_VERSION, system=POINTWISE_SYSTEM, user=user, max_tokens=3)
        tokens[0] += result.prompt_tokens
        tokens[1] += result.completion_tokens
        letter = _letter(result.content)
        if letter == "K":
            entities.append({"id": candidate["id"], "type": candidate["type"], "text": candidate["text"], "retyped_from": None})
        elif letter in LETTER_TYPE:
            final = LETTER_TYPE[letter]
            entities.append({"id": candidate["id"], "type": final, "text": candidate["text"],
                             "retyped_from": candidate["type"] if final != candidate["type"] else None})
        else:
            dropped.append({**candidate, "reason": "slm_drop" if letter == "X" else "no_decision"})
    names = {normalize(e["text"]): e for e in entities}
    final_relations = []
    for rel in relations:
        head, tail = names.get(normalize(rel["head"])), names.get(normalize(rel["tail"]))
        if head is None or tail is None or not _endpoint_ok(rel, names):
            continue
        user = (f"Title and abstract:\n{text}\n\nProposed relation: \"{rel['head']}\" ({head['type']}) --{rel['relation']}--> "
                f"\"{rel['tail']}\" ({tail['type']})\nAnswer (K or X):")
        result = client.complete(prompt_version=VERIFY_VERSION + "-relation", system=RELATION_SYSTEM, user=user, max_tokens=3)
        tokens[0] += result.prompt_tokens
        tokens[1] += result.completion_tokens
        if _letter(result.content) == "K":
            final_relations.append({k: rel[k] for k in ("head", "relation", "tail")})
    return {"valid": True, "entities": entities, "relations": final_relations, "dropped": dropped,
            "prompt_tokens": tokens[0], "completion_tokens": tokens[1], "cache_hit": False}


BATCH_SYSTEM = (
    "You check candidate phrases proposed by an automatic tagger for the title and abstract of a computer-science "
    "paper. For every candidate give one letter:\n"
    "K = keep: a valid entity of the proposed type\n"
    "M = valid, but it is a Method\nT = valid, but it is a Task\nD = valid, but it is a Dataset\n"
    "X = drop: not a valid entity of any type (generic phrase, metric, application domain, field, the paper's own "
    "title, or a part of a longer entity)\n"
    "Answer with one decision per candidate in the form 1:K 2:X 3:M, separated by spaces, and nothing else.\n\n"
    + DEFINITIONS + "\n\n" + VERIFY_RULES)
BATCH_RELATION_SYSTEM = (
    "You check relations proposed between entities of a computer-science paper. For every numbered relation answer "
    "K if the title and abstract support it or X if they do not. APPLIED_TO: a Method is applied to, or proposed for, a "
    "Task. EVALUATED_ON: a Method or Task is evaluated or benchmarked on a Dataset. The text must state or clearly imply "
    "the relation; two phrases appearing in the same paper is not enough. Answer in the form 1:K 2:X, separated by "
    "spaces, and nothing else.")
BATCH_VERSION = "enrich-slm-verify-v5-batch"


def pair_candidates(entities: list[dict], hints: list[dict], *, cap: int = 14) -> list[dict]:
    """Type-valid (head, relation, tail) pairs among kept entities; encoder hints rank first, then all other valid pairs."""
    names = {normalize(e["text"]): e for e in entities}
    hinted = {(normalize(r["head"]), r["relation"], normalize(r["tail"])) for r in hints}
    pairs = []
    for head in entities:
        for tail in entities:
            if head is tail:
                continue
            if head["type"] == "Method" and tail["type"] == "Task":
                relation = "APPLIED_TO"
            elif head["type"] in ("Method", "Task") and tail["type"] == "Dataset":
                relation = "EVALUATED_ON"
            else:
                continue
            key = (normalize(head["text"]), relation, normalize(tail["text"]))
            pairs.append((key not in hinted, head["id"], tail["id"],
                          {"head": head["text"], "relation": relation, "tail": tail["text"]}))
    pairs.sort(key=lambda x: x[:3])
    del names
    return [p[3] for p in pairs[:cap]]


def slm_verify_batch(client: LLMClient, text: str, candidates: list[dict], relations: list[dict], *,
                     enumerate_pairs: bool = False) -> dict:
    """Two calls per paper: letter decisions for all candidate entities, then for the relations among kept ones."""
    if not candidates:
        return {"valid": True, "entities": [], "relations": [], "dropped": [], "prompt_tokens": 0,
                "completion_tokens": 0, "cache_hit": False}
    lines = [f"{c['id']}. \"{c['text']}\" (proposed type: {c['type']})" for c in candidates]
    user = f"Title and abstract:\n{text}\n\nCandidates:\n" + "\n".join(lines) + "\n\nDecisions:"
    result = client.complete(prompt_version=BATCH_VERSION, system=BATCH_SYSTEM, user=user,
                             max_tokens=6 * len(candidates) + 8)
    tokens = [result.prompt_tokens, result.completion_tokens]
    decisions = parse_decisions(result.content)
    entities, dropped = [], []
    for candidate in candidates:
        letter = decisions.get(candidate["id"], "?")
        if letter == "K":
            entities.append({"id": candidate["id"], "type": candidate["type"], "text": candidate["text"], "retyped_from": None})
        elif letter in LETTER_TYPE:
            final = LETTER_TYPE[letter]
            entities.append({"id": candidate["id"], "type": final, "text": candidate["text"],
                             "retyped_from": candidate["type"] if final != candidate["type"] else None})
        else:
            dropped.append({**candidate, "reason": "slm_drop" if letter == "X" else "no_decision"})
    names = {normalize(e["text"]): e for e in entities}
    if enumerate_pairs:
        relations = pair_candidates(entities, relations)
    usable = [r for r in relations if normalize(r["head"]) in names and normalize(r["tail"]) in names and _endpoint_ok(r, names)]
    final_relations = []
    if usable:
        rel_lines = [f"{i}. \"{r['head']}\" ({names[normalize(r['head'])]['type']}) --{r['relation']}--> "
                     f"\"{r['tail']}\" ({names[normalize(r['tail'])]['type']})" for i, r in enumerate(usable, 1)]
        user = f"Title and abstract:\n{text}\n\nRelations:\n" + "\n".join(rel_lines) + "\n\nDecisions:"
        result = client.complete(prompt_version=BATCH_VERSION + "-relation", system=BATCH_RELATION_SYSTEM, user=user,
                                 max_tokens=6 * len(usable) + 8)
        tokens[0] += result.prompt_tokens
        tokens[1] += result.completion_tokens
        decided = parse_decisions(result.content)
        final_relations = [{k: r[k] for k in ("head", "relation", "tail")} for i, r in enumerate(usable, 1)
                           if decided.get(i) == "K"]
    return {"valid": True, "entities": entities, "relations": final_relations, "dropped": dropped,
            "prompt_tokens": tokens[0], "completion_tokens": tokens[1], "cache_hit": False}


RELATION_GEN_VERSION = "enrich-slm-relations-v1"
RELATION_GEN_SCHEMA = {
    "type": "object",
    "properties": {"relations": {"type": "array", "items": {"type": "object", "properties": {
        "head": {"type": "integer"}, "relation": {"type": "string", "enum": RELATIONS},
        "tail": {"type": "integer"}}, "required": ["head", "relation", "tail"]}}},
    "required": ["relations"],
}
RELATION_GEN_SYSTEM = (
    "You list the relations that the title and abstract of a computer-science paper state between the numbered "
    "entities given. Use only the entity numbers. Answer only with JSON.\n"
    "APPLIED_TO: a Method (head) is applied to, or proposed for, a Task (tail).\n"
    "EVALUATED_ON: a Method or Task (head) is evaluated or benchmarked on a Dataset (tail).\n"
    "List a relation only if the text supports it; list every supported one. Hints from an automatic tagger may be "
    "wrong or incomplete.")


def slm_relations(client: LLMClient, text: str, entities: list[dict], hints: list[dict], *, max_tokens: int = 400) -> tuple[list[dict], int, int]:
    heads = [e for e in entities if e["type"] in ("Method", "Task")]
    tails = [e for e in entities if e["type"] in ("Task", "Dataset")]
    if not heads or not tails:
        return [], 0, 0
    by_id = {e["id"]: e for e in entities}
    lines = [f"{e['id']}. {e['text']} ({e['type']})" for e in entities]
    hint_lines = [f"{r['head']} --{r['relation']}--> {r['tail']}" for r in hints] or ["(none)"]
    user = (f"Title and abstract:\n{text}\n\nEntities:\n" + "\n".join(lines) + "\n\nTagger hints:\n"
            + "\n".join(hint_lines))
    try:
        result = client.complete(prompt_version=RELATION_GEN_VERSION, system=RELATION_GEN_SYSTEM, user=user,
                                 schema=RELATION_GEN_SCHEMA, schema_name="relations", max_tokens=max_tokens)
    except InvalidJSONError:
        return [], 0, 0
    out, seen = [], set()
    for rel in result.parsed["relations"]:
        head, tail = by_id.get(rel["head"]), by_id.get(rel["tail"])
        if head is None or tail is None:
            continue
        item = {"head": head["text"], "relation": rel["relation"], "tail": tail["text"]}
        key = (head["id"], rel["relation"], tail["id"])
        names = {normalize(head["text"]): head, normalize(tail["text"]): tail}
        if key not in seen and _endpoint_ok(item, names):
            seen.add(key)
            out.append(item)
    return out, result.prompt_tokens, result.completion_tokens
