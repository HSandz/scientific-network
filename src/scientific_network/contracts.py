"""Small JSON interchange contract; future stage tables are listed in the data dictionary."""

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, model_validator

Identifier = Annotated[str, Field(min_length=1)]


class NodeLabel(StrEnum):
    RESEARCHER = "Researcher"
    ORGANIZATION = "Organization"
    PAPER = "Paper"
    TOPIC = "Topic"
    VENUE = "Venue"


class Relation(StrEnum):
    AUTHORED = "AUTHORED"
    AFFILIATED_WITH = "AFFILIATED_WITH"
    PUBLISHED_IN = "PUBLISHED_IN"
    CITES = "CITES"
    HAS_TOPIC = "HAS_TOPIC"
    SUBTOPIC_OF = "SUBTOPIC_OF"
    COAUTHORED_WITH = "COAUTHORED_WITH"
    COLLABORATED_WITH = "COLLABORATED_WITH"
    RESEARCHES_TOPIC = "RESEARCHES_TOPIC"
    CONTRIBUTES_TO_TOPIC = "CONTRIBUTES_TO_TOPIC"


class EvidenceKind(StrEnum):
    OBSERVED = "observed"
    INFERRED_TOPIC = "inferred_topic"
    CURATED_TAXONOMY = "curated_taxonomy"
    DERIVED = "derived"


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Node(Record):
    id: Identifier
    label: NodeLabel
    name: Identifier
    properties: dict[str, Any] = Field(default_factory=dict)


class EvidenceRecord(Record):
    id: Identifier
    kind: EvidenceKind
    source_url: HttpUrl | None = None
    retrieved_at: AwareDatetime | None = None
    raw_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")] | None = None
    source_locator: Identifier | None = None
    excerpt: str | None = None
    support_edge_ids: list[Identifier] = Field(default_factory=list)
    support_paper_ids: list[Identifier] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_provenance(self):
        if self.kind == EvidenceKind.DERIVED:
            if not self.support_edge_ids or not self.support_paper_ids:
                raise ValueError("derived evidence requires input edges and supporting papers")
        elif any(value is None for value in (
            self.source_url, self.retrieved_at, self.raw_sha256, self.source_locator
        )):
            raise ValueError("source evidence requires URL, retrieval time, hash, and locator")
        if self.kind == EvidenceKind.INFERRED_TOPIC and not self.excerpt:
            raise ValueError("topic evidence requires supporting text")
        return self


class Edge(Record):
    edge_id: Identifier
    relation: Relation
    source_id: Identifier
    target_id: Identifier
    evidence_kind: EvidenceKind
    evidence_ids: list[Identifier] = Field(min_length=1)
    method_version: Identifier
    graph_version: Identifier
    validation_status: Literal["accepted"]
    properties: dict[str, Any] = Field(default_factory=dict)


class AffiliationObservation(Record):
    """An aligned observation, never a paper-level Cartesian product."""

    id: Identifier
    researcher_id: Identifier
    paper_id: Identifier
    organization_id: Identifier
    evidence_ids: list[Identifier] = Field(min_length=1)


class GraphArtifact(Record):
    schema_version: Literal["0.1.0"] = "0.1.0"
    graph_version: Identifier
    is_synthetic: bool
    nodes: list[Node]
    edges: list[Edge]
    evidence: list[EvidenceRecord]
    affiliation_observations: list[AffiliationObservation] = Field(default_factory=list)
