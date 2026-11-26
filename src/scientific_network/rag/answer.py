"""Grounded answer synthesis, faithfulness verifier, and streaming orchestrator (spec §6.3 & §6.5)."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Callable, Iterator

import numpy as np

from scientific_network.rag.executor import iter_execute_plan
from scientific_network.rag.llm import LLMClient, LLMError
from scientific_network.rag.planner import build_plan, link_entities, parse_question, route_mode
from scientific_network.rag.retrieval import global_search, local_search
from scientific_network.rag.sqlite_vectors import SQLiteVectorStore
from scientific_network.rag.tools import RAGToolset

_NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_:])-?\d+(?:\.\d+)?%?")
_PAPER_ID_RE = re.compile(r"paper:(?:aaai|ijcai):\d{4}:[A-Za-z0-9_.-]*[A-Za-z0-9_-]")
_ENTITY_ID_RE = re.compile(r"\b(?:method|task|dataset|organization|researcher|topic|venue|research|N1|N2):[A-Za-z0-9_:-]+")
_BRACKET_RE = re.compile(r"\[([^\[\]\n]+)\]")
_ENTITY_PREFIX_RE = re.compile(
    r"\b(?:paper|method|task|dataset|organization|researcher|topic|venue|research|N1|N2):",
    re.I,
)
_PLACEHOLDER_WORDS = frozenset({"...", "…", "id", "paper", "papers", "citation", "citations", "tbd", "todo", "xxx"})

_CAP_SPAN_RE = re.compile(
    r"\b[A-Z][A-Za-z0-9'’-]*(?:[ \t]+(?:(?:of|for|and|in|on|the|at|to|from|by|with|de|di|&)[ \t]+)*[A-Z][A-Za-z0-9'’-]*)+"
    r"(?:[ \t]*\([A-Z][A-Za-z0-9 \t.-]{1,24}\))?"
)
_LIST_BOLD_HEAD_RE = re.compile(r"(?m)^\s*(?:[-*]|\d+\.)\s+\*\*([^*:\n]{2,110}?)\*\*")
_LIST_COLON_HEAD_RE = re.compile(r"(?m)^\s*(?:[-*]|\d+\.)\s+([^:\n]{2,90}?):")

_ACRONYM_MAP: dict[str, tuple[str, ...]] = {
    "llm": ("large language model", "large language models"),
    "llms": ("large language model", "large language models"),
    "gnn": ("graph neural network", "graph neural networks"),
    "gnns": ("graph neural network", "graph neural networks"),
    "cnn": ("convolutional neural network", "convolutional neural networks"),
    "cnns": ("convolutional neural network", "convolutional neural networks"),
    "nlp": ("natural language processing",),
    "rl": ("reinforcement learning",),
    "vlm": ("vision language model", "vision-language model"),
    "vlms": ("vision language model", "vision-language model"),
    "rag": ("retrieval augmented generation",),
    "qa": ("question answering",),
    "kg": ("knowledge graph", "knowledge graphs"),
    "ai": ("artificial intelligence",),
}

# Explicit generic prose/heading/metric words that never name an external domain entity.
_GENERIC_ENTITY_WORDS: frozenset[str] = frozenset({
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of", "on", "or",
    "over", "per", "the", "to", "under", "vs", "with", "within", "across", "after",
    "before", "between", "during", "since", "not", "no", "none", "only", "based",
    "aaai", "ijcai", "ai", "summary", "key", "finding", "findings", "total", "paper",
    "papers", "share", "shares", "delta", "growth", "rate", "minimum", "threshold",
    "note", "notes", "step", "steps", "top", "ranked", "rank", "organization",
    "organizations", "researcher", "researchers", "method", "methods", "task", "tasks",
    "dataset", "datasets", "topic", "topics", "community", "communities", "graph",
    "graphs", "network", "networks", "corpus", "analysis", "result", "results",
    "evidence", "overview", "direction", "directions", "research", "main", "major",
    "retrieved", "trace", "table", "below", "above", "cutoff", "year", "years",
    "post", "pre", "increase", "increased", "decrease", "decreased", "rising",
    "emerging", "declining", "stable", "collaborator", "collaborators",
    "collaboration", "collaborations", "co", "occurrence", "occurring", "centrality",
    "pagerank", "lift", "rca", "leiden", "graphrag", "local", "global", "search",
    "report", "reports", "cited", "citations", "citation", "count", "counts",
    "example", "examples", "qualified", "excluded", "stopped", "matching", "records",
    "found", "could", "compose", "faithful", "answer", "inspect", "model", "models",
    "data", "metric", "metrics", "score", "scores", "period", "level", "category",
    "categories", "overall", "additional", "primary", "secondary", "other", "all",
    "high", "highest", "low", "lowest", "fastest", "growing", "most", "leading",
    "known", "unknown", "shown", "row", "rows", "item", "items", "value", "values",
    "percentage", "percent", "pp", "cagr", "slope", "ppr", "support", "supporting",
    "supported", "hub", "hubs", "broker", "brokers", "entity", "entities", "group",
    "groups", "cluster", "clusters", "venue", "venues", "title", "name", "names",
    "id", "ids", "both", "each", "more", "than", "fewer", "further", "however",
    "therefore", "including", "especially", "notably", "while", "these", "those",
    "this", "that", "there", "here", "one", "two", "three", "four", "five", "six",
    "seven", "eight", "nine", "ten", "first", "second", "third",
    "evaluated", "tested", "trained", "applied", "conducted", "reported", "using",
})


def _norm_text(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s.lower()).split())


def _collect_trace_strings(obj: Any, out: list[str]) -> None:
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, list):
        for item in obj:
            _collect_trace_strings(item, out)
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_trace_strings(v, out)


def _extract_allowed_numbers(obj: Any) -> set[float]:
    nums: set[float] = set()
    if isinstance(obj, bool):
        return nums
    if isinstance(obj, (int, float)):
        v = float(obj)
        nums.update({v, round(v, 1), round(v, 2), round(v, 3), round(v * 100.0, 1), round(v * 100.0, 2)})
        return nums
    if isinstance(obj, str):
        cleaned = _PAPER_ID_RE.sub(" ", obj)
        cleaned = _ENTITY_ID_RE.sub(" ", cleaned)
        for m in _NUMBER_RE.findall(cleaned):
            try:
                nums.add(float(m.rstrip("%")))
            except ValueError:
                continue
        return nums
    if isinstance(obj, list):
        for item in obj:
            nums |= _extract_allowed_numbers(item)
    elif isinstance(obj, dict):
        for v in obj.values():
            nums |= _extract_allowed_numbers(v)
    return nums


def _extract_answer_numbers(text: str) -> list[float]:
    cleaned = _PAPER_ID_RE.sub(" ", text)
    cleaned = _ENTITY_ID_RE.sub(" ", cleaned)
    # Ignore markdown ordered list prefixes ("1. "), hyphenated tokens (GPT-4, CIFAR-100, Qwen3.5-4B), 2D/3D, L0/L1, N1-N4
    cleaned = re.sub(r"(?m)^\s*\d+\.\s+", " ", cleaned)
    cleaned = re.sub(r"\b[A-Za-z][A-Za-z0-9.]*-\d+\b|\b\d+[Dd]\b|\bL[01](?::\d+)?\b|\bN[1-4]\b", " ", cleaned)
    out = []
    for m in _NUMBER_RE.findall(cleaned):
        try:
            out.append(float(m.rstrip("%")))
        except ValueError:
            continue
    return out


def _extract_candidate_entities(answer: str) -> list[str]:
    text_no_ids = _PAPER_ID_RE.sub(" ", answer)
    text_no_ids = _ENTITY_ID_RE.sub(" ", text_no_ids)
    candidates: list[str] = []
    seen: set[str] = set()

    def _add(raw: str) -> None:
        cleaned = raw.replace("**", "").strip(" \t\r\n.,;:!?\"'()[]")
        cleaned = re.sub(r"\s*\([^()]*\d[^()]*\)\s*$", "", cleaned).strip()
        # A list head cut at a colon inside a parenthetical ("X (lift: 3.2)" -> "X (lift") names X;
        # drop the unclosed parenthetical fragment (2026-11-26).
        cleaned = re.sub(r"\s*\([^()]*$", "", cleaned).strip()
        if len(cleaned) < 2 or not re.search(r"[A-Za-z]", cleaned):
            return
        key = _norm_text(cleaned)
        if key and key not in seen:
            seen.add(key)
            candidates.append(cleaned)

    for m in _LIST_BOLD_HEAD_RE.finditer(text_no_ids):
        _add(m.group(1))
    for m in _LIST_COLON_HEAD_RE.finditer(text_no_ids):
        _add(m.group(1))
    plain = text_no_ids.replace("**", "")
    for m in _CAP_SPAN_RE.finditer(plain):
        _add(m.group(0))
    return candidates


def _entity_in_trace(cand: str, allowed_norm_blob: str, allowed_norms: list[str]) -> bool:
    norm = _norm_text(cand)
    if not norm:
        return True
    words = norm.split()
    if all(w in _GENERIC_ENTITY_WORDS or w.isdigit() for w in words):
        return True

    variants = {norm}
    if norm.endswith("s") and len(norm) > 3:
        variants.add(norm[:-1])
    else:
        variants.add(norm + "s")
    for v in list(variants):
        if v.startswith("the ") and len(v) > 5:
            variants.add(v[4:])

    for v in variants:
        if f" {v} " in allowed_norm_blob:
            return True
        if len(v) >= 5 and any(v in s for s in allowed_norms):
            return True

    for w in words:
        for exp in _ACRONYM_MAP.get(w, ()):
            if exp in allowed_norm_blob:
                other_words = [ow for ow in words if ow != w]
                if all(ow in _GENERIC_ENTITY_WORDS or f" {ow} " in allowed_norm_blob for ow in other_words):
                    return True

    trimmed_words = list(words)
    while len(trimmed_words) > 1 and trimmed_words[0] in _GENERIC_ENTITY_WORDS:
        trimmed_words.pop(0)
        sub = " ".join(trimmed_words)
        if f" {sub} " in allowed_norm_blob or (len(sub) >= 5 and any(sub in s for s in allowed_norms)):
            return True

    for candidate_str in (cand, " ".join(trimmed_words)):
        if re.search(r"\s+(?:and|&)\s+", candidate_str, flags=re.I):
            parts = [p.strip() for p in re.split(r"\s+(?:and|&)\s+", candidate_str, flags=re.I) if p.strip()]
            if len(parts) >= 2:
                meaningful = [p for p in parts if not all(w in _GENERIC_ENTITY_WORDS or w.isdigit() for w in _norm_text(p).split())]
                if meaningful and all(len(p) >= 2 and _entity_in_trace(p, allowed_norm_blob, allowed_norms) for p in parts):
                    return True
    return False


def verify_answer_faithfulness(answer: str, trace_payload: Any, question: str) -> list[str]:
    """Verify answer faithfulness against the retrieved trace and question (spec §6.3).

    Rules enforced:
    1. **Numbers**: Every numeric value in ``answer`` (excluding numbers embedded inside valid
       paper/entity IDs, markdown ordered-list prefixes ``1. ``, and model/network tokens such as
       ``GPT-4``, ``CIFAR-100``, ``3D``, ``L0``/``L1``, ``N1``–``N4``) must match a number in
       ``trace_payload`` or ``question`` within ``max(0.01, 0.005 * abs(a))`` (also accepting
       percentage forms ``value * 100`` rounded to 1–2 decimals).
    2. **Bracketed and paper citations**:
       - Placeholder or truncated citations inside brackets (containing ``...``, ``…``, ``TBD``,
         ``TODO``, bare ``paper:``, or generic words like ``[citation]``/``[paper]``) are rejected.
       - Every bracketed or unbracketed ``paper:...`` / entity ID token must match the full ID
         pattern and appear verbatim in ``trace_payload`` (or ``question``).
    3. **Named entities**: Capitalized multi-word spans and list-item heads in ``answer`` are
       normalized and matched against strings in ``trace_payload`` and ``question`` (including
       singular/plural variants and explicit AI acronym expansions such as ``LLM`` ↔ ``large
       language model``). An explicit documented allowlist covers generic prose/metric/heading
       words (e.g. ``Key Findings``, ``Minimum Threshold``, ``AAAI``, ``IJCAI``) and contains no
       institution, researcher, method, task, or dataset names. Any unmatched entity is rejected.
    """
    errors: list[str] = []

    allowed_nums = _extract_allowed_numbers(trace_payload) | _extract_allowed_numbers(question)
    for val in _extract_answer_numbers(answer):
        if any(abs(val - a) <= max(0.01, 0.005 * abs(a)) for a in allowed_nums):
            continue
        errors.append(f"number {val:g} not in trace")

    trace_text = json.dumps(trace_payload, ensure_ascii=False)
    allowed_id_blob = trace_text + "\n" + question

    for bm in _BRACKET_RE.finditer(answer):
        inner = bm.group(1).strip()
        low = inner.lower()
        if "..." in inner or "…" in inner or low in _PLACEHOLDER_WORDS:
            errors.append(f"placeholder or truncated citation [{inner}]")
            continue
        if _ENTITY_PREFIX_RE.search(inner):
            tokens = [t.strip() for t in re.split(r"[,;]+", inner) if t.strip()]
            for tok in tokens:
                if _PAPER_ID_RE.fullmatch(tok):
                    if tok not in trace_text:
                        errors.append(f"cited paper {tok} not in trace")
                elif _ENTITY_ID_RE.fullmatch(tok):
                    if tok not in allowed_id_blob:
                        errors.append(f"cited entity {tok} not in trace")
                else:
                    errors.append(f"malformed or truncated citation token [{tok}]")

    for pid in sorted(set(_PAPER_ID_RE.findall(answer))):
        if pid not in trace_text:
            msg = f"cited paper {pid} not in trace"
            if msg not in errors:
                errors.append(msg)

    raw_strings: list[str] = [question]
    _collect_trace_strings(trace_payload, raw_strings)
    allowed_norms = [_norm_text(s) for s in raw_strings if isinstance(s, str) and s.strip()]
    allowed_norm_blob = " " + "  ".join(allowed_norms) + " "
    for cand in _extract_candidate_entities(answer):
        if not _entity_in_trace(cand, allowed_norm_blob, allowed_norms):
            errors.append(f"entity {cand!r} not in trace")

    return errors


_ANSWER_SYS = (
    "Answer the user question concisely using ONLY the retrieved graph trace below.\n"
    "Rules:\n"
    "- Every number you state MUST appear verbatim in the trace.\n"
    "- Mention ONLY organizations, researchers, methods, tasks, datasets, and topics present in the trace or question; NEVER invent entities.\n"
    "- Copy complete paper IDs verbatim from the trace's `paper_ids` field in brackets, e.g. [paper:aaai:2024:29823]. "
    "NEVER write placeholder or truncated citations such as [paper:...], [...], or ellipses inside brackets; if an item has no paper ID in the trace, omit the bracketed citation.\n"
    "- For share-growth questions, report BOTH paper counts (k of n papers) and shares, plus the minimum-paper threshold stated in the step note.\n"
    "- When a step shows top K of N deterministically ranked rows, state 'showing top K of N' cleanly; NEVER say the trace was truncated.\n"
    "- If the trace stopped on an empty step, clearly state that no matching records were found rather than guessing."
)


# rag-answer-v4 / rag-local-answer-v3 (2026-11-26, WORK-2026-11-26-001): separate citations from
# "papers in this result". Aggregate claims point to the trace step; a paper ID is cited only for a
# sentence about that specific paper. The qa-eval-v1 benchmark ran rag-answer-v3 / rag-local-answer-v2.
_ANSWER_SYS_V4 = (
    "Answer the user question concisely using ONLY the retrieved graph trace below.\n"
    "Rules:\n"
    "- Every number you state MUST appear verbatim in the trace.\n"
    "- Mention ONLY organizations, researchers, methods, tasks, datasets, and topics present in the trace or question; NEVER invent entities.\n"
    "- Aggregate claims (counts, shares, growth, rankings, co-occurrence, or any list computed over many papers) point to the trace step that computed them, written as [step N] with N the step number in the trace. "
    "Put [step N] at the end of each such sentence and after the introduction of each ranked or listed group, e.g. 'The organizations ranked by lift are [step 1]:'. Write each listed item as '- Name: the row's counts and metric values in words', keeping every count the rules below ask for. "
    "NEVER attach paper IDs to aggregate claims: the papers listed with a step are example papers behind the count, not evidence for the sentence, and the interface lists them separately.\n"
    "- Cite a paper ID in brackets, copied verbatim (e.g. [paper:aaai:2024:29823]), ONLY when the sentence states something about that specific paper "
    "and the trace gives that paper as its own row or abstract excerpt. NEVER write placeholder or truncated citations such as [paper:...], [...], or ellipses inside brackets.\n"
    "- For share-growth questions, report BOTH paper counts (k of n papers) and shares, plus the minimum-paper threshold stated in the step note.\n"
    "- When a step shows top K of N deterministically ranked rows, state 'showing top K of N' cleanly; NEVER say the trace was truncated.\n"
    "- If the trace stopped on an empty step, clearly state that no matching records were found rather than guessing."
)

_ANSWER_SYSTEMS: dict[str, str] = {
    "rag-answer-v3": _ANSWER_SYS,
    "rag-local-answer-v2": _ANSWER_SYS,
    "rag-answer-v4": _ANSWER_SYS_V4,
    "rag-local-answer-v3": _ANSWER_SYS_V4,
}
CURRENT_ANSWER_PROMPT = "rag-answer-v4"
CURRENT_LOCAL_ANSWER_PROMPT = "rag-local-answer-v3"

_STEP_REF_RE = re.compile(r"\[\s*steps?\s+(\d+)(?:\s*(?:,|and|&|-|–)\s*(\d+))*\s*\]", re.I)
_STEP_NUM_RE = re.compile(r"\d+")


def _step_numbers(trace_payload: Any) -> set[int]:
    steps = trace_payload.get("steps") if isinstance(trace_payload, dict) else None
    out: set[int] = set()
    for idx, st in enumerate(steps or [], start=1):
        try:
            out.add(int(st.get("step", idx)))
        except (TypeError, ValueError):
            out.add(idx)
    return out or {1}


def check_step_references(answer: str, trace_payload: Any) -> list[str]:
    """Every [step N] reference must name a step that exists in the trace."""
    valid = _step_numbers(trace_payload)
    errors: list[str] = []
    for m in _STEP_REF_RE.finditer(answer):
        for num in _STEP_NUM_RE.findall(m.group(0)):
            if int(num) not in valid:
                errors.append(f"step reference {num} not in trace")
    return errors


def _direct_paper_ids_for_step(step: dict[str, Any]) -> set[str]:
    """Paper IDs that a step returns as their own rows (the step is *about* those papers)."""
    direct: set[str] = set()
    for row in step.get("rows") or []:
        if not isinstance(row, dict):
            continue
        for key in ("id", "paper_id"):
            val = row.get(key)
            if isinstance(val, str) and _PAPER_ID_RE.fullmatch(val):
                direct.add(val)
    return direct


_CHUNK_LINE_RE = re.compile(r"(?m)^- \[(paper:(?:aaai|ijcai):\d{4}:[A-Za-z0-9_.-]*[A-Za-z0-9_-])\]")


def chunk_paper_ids(context: str) -> set[str]:
    """Paper IDs whose abstract sentence was packed into a local-search context."""
    return set(_CHUNK_LINE_RE.findall(context or ""))


def _sentence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    for m in re.finditer(r"(?<=[.!?])\s+|\n+", text):
        spans.append((start, m.start()))
        start = m.end()
    spans.append((start, len(text)))
    return [(a, b) for a, b in spans if text[a:b].strip()]


def label_answer_evidence(
    answer: str,
    steps: list[dict[str, Any]],
    *,
    extra_direct: dict[int, set[str]] | None = None,
) -> dict[str, Any]:
    """Separate citations from papers in the result (2026-11-26 product change).

    - ``citations``: a paper ID written next to a sentence, where the trace returns that paper as its
      own row (``papers`` tool) or as an abstract excerpt (local search). Only these are shown as
      citations.
    - ``result_papers``: per step, the example papers behind a count or list.
    - Inline paper IDs attached to aggregate claims are moved out of the sentence: the bracket is
      rewritten to the ``[step N]`` that produced the papers, and the papers stay listed under
      ``result_papers``.
    """
    direct_by_step: dict[int, set[str]] = {}
    step_of_pid: dict[str, int] = {}
    result_papers: list[dict[str, Any]] = []
    for idx, st in enumerate(steps or [], start=1):
        try:
            sno = int(st.get("step", idx))
        except (TypeError, ValueError):
            sno = idx
        direct = _direct_paper_ids_for_step(st) | set((extra_direct or {}).get(sno, set()))
        direct_by_step[sno] = direct
        pids = list(dict.fromkeys(st.get("paper_ids") or []))
        for row in st.get("rows") or []:
            if isinstance(row, dict):
                for pid in row.get("paper_ids") or []:
                    if isinstance(pid, str) and pid not in pids:
                        pids.append(pid)
        for pid in pids + sorted(direct):
            step_of_pid.setdefault(pid, sno)
        if pids:
            result_papers.append({
                "step": sno,
                "tool": st.get("tool"),
                "role": "papers_in_result",
                "paper_ids": pids,
            })
    all_direct = {pid for d in direct_by_step.values() for pid in d}

    moved: list[dict[str, Any]] = []

    def _rewrite(m: re.Match[str]) -> str:
        inner = m.group(1)
        tokens = [t.strip() for t in re.split(r"[,;]+", inner) if t.strip()]
        if not tokens or not any(_PAPER_ID_RE.fullmatch(t) for t in tokens):
            return m.group(0)
        keep: list[str] = []
        step_refs: list[int] = []
        for tok in tokens:
            if _PAPER_ID_RE.fullmatch(tok) and tok not in all_direct:
                sno = step_of_pid.get(tok)
                moved.append({"paper_id": tok, "step": sno})
                if sno is not None and sno not in step_refs:
                    step_refs.append(sno)
            else:
                keep.append(tok)
        parts: list[str] = []
        if keep:
            parts.append(f"[{', '.join(keep)}]")
        if step_refs:
            parts.append(f"[step {', '.join(str(n) for n in sorted(step_refs))}]")
        return " ".join(parts)

    rewritten = _BRACKET_RE.sub(_rewrite, answer)
    # Collapse repeated identical step references produced by adjacent brackets.
    rewritten = re.sub(r"(\[step [0-9, ]+\])(?:\s*\1)+", r"\1", rewritten)
    rewritten = re.sub(r"[ \t]+([.,;:])", r"\1", rewritten)
    rewritten = re.sub(r"[ \t]{2,}", " ", rewritten)

    citations: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for a, b in _sentence_spans(rewritten):
        sentence = rewritten[a:b].strip()
        for pid in _PAPER_ID_RE.findall(sentence):
            if pid in all_direct and (pid, a) not in seen:
                seen.add((pid, a))
                citations.append({"paper_id": pid, "step": step_of_pid.get(pid), "sentence": sentence})
    return {
        "answer": rewritten,
        "citations": citations,
        "result_papers": result_papers,
        "moved_inline_paper_ids": moved,
        "labelling_version": "evidence-labels-v1",
    }


_NOISY_ROW_KEYS = frozenset({
    "edge_id",
    "source_id",
    "target_id",
    "center_id",
    "evidence_ids",
    "support_paper_ids",
    "fractional_weight",
    "evidence_kind",
})


def _strip_noisy_row_keys(row: Any) -> Any:
    if isinstance(row, dict):
        return {k: v for k, v in row.items() if k not in _NOISY_ROW_KEYS}
    return row


def _compact_trace_for_prompt(
    trace_payload: Any,
    *,
    max_rows: int = 15,
    max_chars: int = 10500,
) -> Any:
    """Keep deterministically ranked top rows per step intact within prompt budget.

    Strips verbose internal edge metadata keys and, when multi-step JSON still exceeds
    ``max_chars``, trims earlier intermediate steps before reducing the final step so
    the LLM always receives valid JSON with the final step prioritized.
    """
    if not isinstance(trace_payload, dict) or "steps" not in trace_payload:
        return trace_payload
    raw_steps = list(trace_payload.get("steps") or [])
    n_steps = len(raw_steps)

    def _build(
        early_rows: int,
        early_pids: int,
        final_rows: int,
        final_pids: int,
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for idx, st in enumerate(raw_steps):
            rows = [_strip_noisy_row_keys(r) for r in (st.get("rows") or [])]
            total_n = int(st.get("row_count", len(rows)))
            is_last = idx == n_steps - 1
            row_cap = final_rows if is_last else min(max_rows, early_rows)
            pid_cap = final_pids if is_last else early_pids
            shown_rows = rows[:row_cap]
            out.append({
                "step": st.get("step"),
                "tool": st.get("tool"),
                "total_row_count": total_n,
                "shown_row_count": len(shown_rows),
                "ranking_note": (
                    f"Showing top {len(shown_rows)} of {total_n} deterministically ranked rows."
                    if total_n > len(shown_rows)
                    else f"All {len(shown_rows)} rows shown."
                ),
                "note": st.get("note", ""),
                "rows": shown_rows,
                "paper_ids": list(st.get("paper_ids") or [])[:pid_cap],
            })
        return out

    compacted = _build(max_rows, 25, max_rows, 25)
    if len(json.dumps({"steps": compacted}, ensure_ascii=False, separators=(",", ":"))) <= max_chars:
        return {"steps": compacted}

    for early_rows, early_pids in ((5, 5), (2, 3), (0, 2)):
        compacted = _build(early_rows, early_pids, max_rows, 25)
        if len(json.dumps({"steps": compacted}, ensure_ascii=False, separators=(",", ":"))) <= max_chars:
            return {"steps": compacted}

    for final_rows in range(max_rows - 1, -1, -1):
        compacted = _build(0, 2, final_rows, min(15, 25))
        if len(json.dumps({"steps": compacted}, ensure_ascii=False, separators=(",", ":"))) <= max_chars:
            return {"steps": compacted}
    return {"steps": _build(0, 0, 0, 5)}


def compose_grounded_answer(
    question: str,
    trace_payload: Any,
    llm: LLMClient,
    *,
    prompt_version: str = "rag-answer-v3",
    max_rows_in_prompt: int = 15,
) -> dict[str, Any]:
    """Compose an answer from the trace with automatic faithfulness check + 1 retry."""
    prompt_trace = _compact_trace_for_prompt(trace_payload, max_rows=max_rows_in_prompt)
    trace_json = json.dumps(prompt_trace, ensure_ascii=False, separators=(",", ":"))

    last_errs: list[str] = []
    for attempt in (0, 1):
        pv = prompt_version if attempt == 0 else f"{prompt_version}-retry"
        user_msg = f"Question: {question}\n\nTrace:\n{trace_json}"
        if attempt == 1:
            user_msg += (
                f"\n\nYour previous answer failed faithfulness checks ({'; '.join(last_errs)}). "
                "Rewrite using ONLY exact numbers, entity names, and verbatim paper IDs present in the trace (no [paper:...] placeholders)."
            )
        try:
            system = _ANSWER_SYSTEMS.get(prompt_version, _ANSWER_SYS)
            res = llm.complete(prompt_version=pv, system=system, user=user_msg, max_tokens=700)
            ans = res.content.strip()
        except LLMError as exc:
            last_errs = [str(exc)]
            continue
        errs = verify_answer_faithfulness(ans, trace_payload, question)
        if _ANSWER_SYSTEMS.get(prompt_version) is _ANSWER_SYS_V4:
            errs += check_step_references(ans, prompt_trace)
        if not errs:
            return {
                "answer": ans,
                "faithfulness_passed": True,
                "faithfulness_errors": [],
                "attempts": attempt + 1,
                "ai_generated_label": "AI-generated from graph data",
            }
        last_errs = errs

    return {
        "answer": "Could not compose a faithful answer from the retrieved graph trace; inspect the step tables below.",
        "faithfulness_passed": False,
        "faithfulness_errors": last_errs,
        "attempts": 2,
        "ai_generated_label": "AI-generated from graph data",
    }


def _label_fields(labels: dict[str, Any]) -> dict[str, Any]:
    return {
        "citations": labels["citations"],
        "result_papers": labels["result_papers"],
        "moved_inline_paper_ids": labels["moved_inline_paper_ids"],
        "evidence_labelling": labels["labelling_version"],
    }


def _citations_event(paper_ids: list[str], labels: dict[str, Any]) -> dict[str, Any]:
    """SSE payload: ``paper_ids`` (all papers touched, kept for older clients), direct citations and
    the per-step papers in the result."""
    return {
        "paper_ids": list(paper_ids or []),
        "citations": labels["citations"],
        "result_papers": labels["result_papers"],
        "evidence_labelling": labels["labelling_version"],
    }


def _emit_answer_tokens(answer_text: str) -> Iterator[dict[str, Any]]:
    words = answer_text.split(" ")
    for i in range(0, len(words), 6):
        chunk = (" " if i > 0 else "") + " ".join(words[i:i + 6])
        yield {"event": "token", "data": {"text": chunk}}


def run_ask(
    question: str,
    *,
    toolset: RAGToolset,
    llm: LLMClient,
    mode: str = "auto",
    resolved_overrides: dict[str, str] | None = None,
    vector_store: SQLiteVectorStore | None = None,
    embed_fn: Callable[[str], np.ndarray] | None = None,
    reports_path: Path = Path("reports/final-exam/rag-v1/community-reports.json"),
) -> dict[str, Any]:
    """Run parse -> link -> route -> plan/retrieve -> execute -> grounded answer."""
    final_result: dict[str, Any] = {}
    for ev in stream_ask(
        question,
        toolset=toolset,
        llm=llm,
        mode=mode,
        resolved_overrides=resolved_overrides,
        vector_store=vector_store,
        embed_fn=embed_fn,
        reports_path=reports_path,
    ):
        if ev.get("event") == "done":
            final_result = ev["data"]
    return final_result


def stream_ask(
    question: str,
    *,
    toolset: RAGToolset,
    llm: LLMClient,
    mode: str = "auto",
    resolved_overrides: dict[str, str] | None = None,
    vector_store: SQLiteVectorStore | None = None,
    embed_fn: Callable[[str], np.ndarray] | None = None,
    reports_path: Path = Path("reports/final-exam/rag-v1/community-reports.json"),
    answer_prompt_version: str = CURRENT_ANSWER_PROMPT,
    local_answer_prompt_version: str = CURRENT_LOCAL_ANSWER_PROMPT,
) -> Iterator[dict[str, Any]]:
    """Stream SSE-friendly stage events progressively as work happens.

    Sequence: ``stage(parsing)`` -> ``parsed`` (with linked entities) ->
    [``disambiguate`` + ``done`` if ambiguous] ->
    ``stage(planning)`` -> ``plan`` -> per-step ``step`` + ``subgraph`` ->
    ``stage(synthesizing)`` -> ``token`` chunks -> ``citations`` -> ``done``.
    """
    yield {"event": "stage", "data": {"stage": "parsing", "mode": mode}}
    parsed = parse_question(question, llm)
    link_res = link_entities(parsed, toolset, resolved_overrides=resolved_overrides, question=question)
    yield {
        "event": "parsed",
        "data": {"parsed": parsed, "linked": link_res["linked"]},
    }

    if link_res["needs_disambiguation"]:
        res = {
            "status": "needs_disambiguation",
            "question": question,
            "parsed": parsed,
            "linked": link_res["linked"],
            "disambiguation": link_res["disambiguation"],
            "answer": "Multiple researchers match that name; please select the intended researcher.",
            "faithfulness_passed": True,
            "faithfulness_errors": [],
            "steps": [],
            "subgraph_nodes": [],
            "subgraph_edges": [],
            "paper_ids": [],
            "ai_generated_label": "AI-generated from graph data",
        }
        yield {"event": "disambiguate", "data": res}
        yield {"event": "done", "data": res}
        return

    chosen_mode = route_mode(question, mode, parsed, link_res["linked"])

    if chosen_mode == "global":
        yield {"event": "stage", "data": {"stage": "global_map_reduce", "mode": "global"}}
        g_res = global_search(question, llm=llm, reports_path=reports_path, vector_store=vector_store, embed_fn=embed_fn)
        step = {
            "step": 1,
            "tool": "community_report",
            "purpose": "global map-reduce",
            "empty": False,
            "row_count": len(g_res["points"]),
            "rows": g_res["points"],
            "source_kind": "global_search",
            "note": f"Synthesized over {len(g_res['reports_used'])} community reports.",
            "paper_ids": g_res["paper_ids"],
            "evidence_ids": [],
        }
        labels = label_answer_evidence(g_res["answer"], [step])
        errs = verify_answer_faithfulness(labels["answer"], g_res["points"], question)
        yield {"event": "step", "data": step}
        yield {"event": "subgraph", "data": {"nodes": [], "edges": []}}
        yield from _emit_answer_tokens(labels["answer"])
        yield {"event": "citations", "data": _citations_event(g_res["paper_ids"], labels)}
        yield {
            "event": "done",
            "data": {
                "status": "ok",
                "question": question,
                "mode": "global",
                "parsed": parsed,
                "linked": link_res["linked"],
                "plan": [],
                "steps": [step],
                "stopped_reason": None,
                "answer": labels["answer"],
                "faithfulness_passed": len(errs) == 0,
                "faithfulness_errors": errs,
                "subgraph_nodes": [],
                "subgraph_edges": [],
                "paper_ids": g_res["paper_ids"],
                **_label_fields(labels),
                "ai_generated_label": "AI-generated from graph data",
            },
        }
        return

    if chosen_mode == "local" and vector_store is not None and embed_fn is not None:
        yield {"event": "stage", "data": {"stage": "local_retrieve", "mode": "local"}}
        l_res = local_search(question, toolset=toolset, vector_store=vector_store, embed_fn=embed_fn)
        step = {
            "step": 1,
            "tool": "local_search",
            "purpose": "entity-centric neighborhood + chunks",
            "empty": False,
            "row_count": len(l_res["paper_ids"]),
            "rows": [{"section": s} for s in l_res["sections_used"]],
            "source_kind": "local_search",
            "note": f"Packed {len(l_res['sections_used'])} context sections.",
            "paper_ids": l_res["paper_ids"],
            "evidence_ids": [],
        }
        yield {"event": "step", "data": step}
        yield {"event": "subgraph", "data": {"nodes": l_res["subgraph_nodes"], "edges": l_res["subgraph_edges"]}}
        yield {"event": "stage", "data": {"stage": "synthesizing", "mode": "local"}}
        composed = compose_grounded_answer(question, l_res, llm, prompt_version=local_answer_prompt_version)
        labels = label_answer_evidence(
            composed["answer"], [step], extra_direct={1: chunk_paper_ids(l_res.get("context", ""))}
        )
        yield from _emit_answer_tokens(labels["answer"])
        yield {"event": "citations", "data": _citations_event(l_res["paper_ids"], labels)}
        yield {
            "event": "done",
            "data": {
                "status": "ok",
                "question": question,
                "mode": "local",
                "parsed": parsed,
                "linked": link_res["linked"],
                "plan": [],
                "steps": [step],
                "stopped_reason": None,
                "answer": labels["answer"],
                "faithfulness_passed": composed["faithfulness_passed"],
                "faithfulness_errors": composed["faithfulness_errors"],
                "subgraph_nodes": l_res["subgraph_nodes"],
                "subgraph_edges": l_res["subgraph_edges"],
                "paper_ids": l_res["paper_ids"],
                **_label_fields(labels),
                "ai_generated_label": "AI-generated from graph data",
            },
        }
        return

    yield {"event": "stage", "data": {"stage": "planning", "mode": chosen_mode}}
    plan = build_plan(question, parsed, link_res["linked"], llm)
    yield {"event": "plan", "data": {"mode": chosen_mode, "plan": plan, "linked": link_res["linked"]}}

    exec_res: dict[str, Any] = {
        "steps": [],
        "stopped_reason": None,
        "stopped_at_step": None,
        "subgraph_nodes": [],
        "subgraph_edges": [],
        "paper_ids": [],
        "evidence_ids": [],
    }
    for inc in iter_execute_plan(plan, toolset, linked=link_res["linked"]):
        exec_res = {k: v for k, v in inc.items() if k != "step"}
        yield {"event": "step", "data": inc["step"]}
        yield {"event": "subgraph", "data": {"nodes": inc["subgraph_nodes"], "edges": inc["subgraph_edges"]}}

    if exec_res["stopped_reason"] == "empty_step":
        step_no = exec_res["stopped_at_step"]
        st = exec_res["steps"][-1]
        answer_text = (
            f"Stopped at step {step_no} (`{st['tool']}`): no matching records were found in the graph "
            f"({st['note']})."
        )
        composed = {
            "answer": answer_text,
            "faithfulness_passed": True,
            "faithfulness_errors": [],
            "ai_generated_label": "AI-generated from graph data",
        }
    else:
        yield {"event": "stage", "data": {"stage": "synthesizing", "mode": chosen_mode}}
        composed = compose_grounded_answer(
            question,
            {"steps": [{k: s[k] for k in ("step", "tool", "row_count", "rows", "note", "paper_ids")} for s in exec_res["steps"]]},
            llm,
            prompt_version=answer_prompt_version,
        )

    labels = label_answer_evidence(composed["answer"], exec_res["steps"])
    yield from _emit_answer_tokens(labels["answer"])
    yield {"event": "citations", "data": _citations_event(exec_res["paper_ids"], labels)}
    yield {
        "event": "done",
        "data": {
            "status": "ok",
            "question": question,
            "mode": chosen_mode,
            "parsed": parsed,
            "linked": link_res["linked"],
            "plan": plan,
            "steps": exec_res["steps"],
            "stopped_reason": exec_res["stopped_reason"],
            "stopped_at_step": exec_res["stopped_at_step"],
            "answer": labels["answer"],
            "faithfulness_passed": composed["faithfulness_passed"],
            "faithfulness_errors": composed["faithfulness_errors"],
            "subgraph_nodes": exec_res["subgraph_nodes"],
            "subgraph_edges": exec_res["subgraph_edges"],
            "paper_ids": exec_res["paper_ids"],
            **_label_fields(labels),
            "ai_generated_label": composed["ai_generated_label"],
        },
    }
