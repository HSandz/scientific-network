"""Text helpers shared by extraction, normalization and scoring (specification §4.2 step 3)."""

import re

_ARTICLES = {"a", "an", "the"}
_TOKEN = re.compile(r"[a-z0-9]+")
_ACRONYM = re.compile(r"([A-Za-z][A-Za-z0-9/\-' ]{3,90}?)\s*\(\s*([A-Za-z][A-Za-z0-9\-]{1,11}s?)\s*\)")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


def paper_text(title: str, abstract: str) -> str:
    """The extraction input: title, a newline, then the abstract."""
    return f"{title.strip()}\n{(abstract or '').strip()}".strip()


def _stem(token: str) -> str:
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def normalize(surface: str) -> str:
    tokens = [_stem(t) for t in _TOKEN.findall(surface.lower()) if t not in _ARTICLES]
    return " ".join(tokens)


def token_set(surface: str) -> frozenset[str]:
    return frozenset(normalize(surface).split())


def jaccard(a: str, b: str) -> float:
    left, right = token_set(a), token_set(b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def acronym_map(text: str) -> dict[str, str]:
    """Map acronyms defined as ``Long Form (ABBR)`` in the same text to their long form (normalized key)."""
    mapping: dict[str, str] = {}
    for match in _ACRONYM.finditer(text):
        long_form, abbr = match.group(1).strip(), match.group(2)
        letters = [c for c in abbr.rstrip("s") if c.isalnum()]
        if len(letters) < 2:
            continue
        words = re.split(r"[\s\-/]+", long_form)
        lowered = [c.lower() for c in letters]
        for take in range(max(1, len(letters) - 1), min(len(letters) + 3, len(words)) + 1):
            tail = words[-take:]
            initials = [w[0].lower() for w in tail if w]
            if not initials or initials[0] != lowered[0]:
                continue
            pos, hits = 0, 0
            for ch in lowered:
                if ch in initials[pos:]:
                    pos = initials.index(ch, pos) + 1
                    hits += 1
            if hits >= max(2, len(lowered) - 1):
                mapping[abbr.lower().rstrip("s")] = " ".join(tail)
                mapping[abbr.lower()] = " ".join(tail)
                break
    return mapping


def expand(surface: str, acronyms: dict[str, str]) -> str:
    key = surface.strip().lower()
    return acronyms.get(key, surface)


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Character spans of sentences; the title line is its own sentence."""
    spans: list[tuple[int, int]] = []
    offset = 0
    for block in text.split("\n"):
        if block.strip():
            start = 0
            for piece in _SENTENCE_END.split(block):
                begin = block.index(piece, start)
                spans.append((offset + begin, offset + begin + len(piece)))
                start = begin + len(piece)
        offset += len(block) + 1
    return spans


def sentence_index(spans: list[tuple[int, int]], position: int) -> int:
    for index, (start, end) in enumerate(spans):
        if start <= position < end:
            return index
    return -1
