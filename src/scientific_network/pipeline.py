"""Implementation contracts for pending stages; never simulate successful work."""

from dataclasses import dataclass

IMPLEMENTED_STAGES = {"discover", "acquire", "extract", "resolve", "classify", "build", "analyze", "evaluate"}


@dataclass(frozen=True)
class StageSpec:
    component: str
    config: str
    inputs: str
    outputs: str
    next_step: str


STAGES = {
    "discover": StageSpec("collect", "corpus", "official proceedings indexes", "corpus manifest and exclusions", "Implement and test official NeurIPS/PMLR roster adapters; preserve track metadata."),
    "acquire": StageSpec("collect", "corpus", "frozen corpus manifest", "immutable raw responses and retrieval ledger", "Implement content-hashed caching, bounded retries, and source-specific quota handling."),
    "extract": StageSpec("preprocess", "corpus", "raw metadata and selected PDFs/TEI", "paper, author, affiliation and reference mentions", "Pilot GROBID markers and retain exact source locators; keep raw fields."),
    "resolve": StageSpec("resolve", "corpus", "mentions, crosswalks and reviewed identity evidence", "canonical tables, affiliation triples and review history", "Implement reversible identity decisions; never merge on name alone."),
    "classify": StageSpec("nlp", "topics", "titles, abstracts, development labels and frozen taxonomy", "supported topic decisions, abstentions and method metadata", "Implement phrase baseline; calibrate on development data before held-out evaluation."),
    "build": StageSpec("graph", "quality", "structurally and semantically accepted canonical tables", "idempotent Neo4j graph and reproducible edge exports", "Implement R1–R6 loading and exact R7–R10 derivation; reconcile counts on repeated imports."),
    "analyze": StageSpec("analysis", "analysis", "validated graph and a frozen named-projection config; real graphs also record the quality size gates", "per-projection metrics and seeded community tables; business findings remain separate", "Implement frozen evidence-sensitivity comparisons, citation-age/coverage analysis, figures, and source-supported business findings."),
    "evaluate": StageSpec("evaluation", "quality", "frozen frame, predictions, two independent labels and adjudications", "component precision/recall/F1 and core-frame coverage; edge-audit results remain separate", "Obtain and verify real independent labels on the reserved test frame, then complete P07 coverage and final edge-audit requirements."),
}
