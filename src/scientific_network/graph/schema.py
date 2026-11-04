"""The plan's ten predicates, including storage direction and evidence class."""

from dataclasses import dataclass
from hashlib import sha256
import json

from scientific_network.contracts import EvidenceKind as K, NodeLabel as N, Relation as R


@dataclass(frozen=True)
class RelationshipSpec:
    source: N
    target: N
    kind: K
    symmetric: bool = False


RELATIONSHIPS = {
    R.AUTHORED: RelationshipSpec(N.RESEARCHER, N.PAPER, K.OBSERVED),
    R.AFFILIATED_WITH: RelationshipSpec(N.RESEARCHER, N.ORGANIZATION, K.OBSERVED),
    R.PUBLISHED_IN: RelationshipSpec(N.PAPER, N.VENUE, K.OBSERVED),
    R.CITES: RelationshipSpec(N.PAPER, N.PAPER, K.OBSERVED),
    R.HAS_TOPIC: RelationshipSpec(N.PAPER, N.TOPIC, K.INFERRED_TOPIC),
    R.SUBTOPIC_OF: RelationshipSpec(N.TOPIC, N.TOPIC, K.CURATED_TAXONOMY),
    R.COAUTHORED_WITH: RelationshipSpec(N.RESEARCHER, N.RESEARCHER, K.DERIVED, True),
    R.COLLABORATED_WITH: RelationshipSpec(N.ORGANIZATION, N.ORGANIZATION, K.DERIVED, True),
    R.RESEARCHES_TOPIC: RelationshipSpec(N.RESEARCHER, N.TOPIC, K.DERIVED),
    R.CONTRIBUTES_TO_TOPIC: RelationshipSpec(N.ORGANIZATION, N.TOPIC, K.DERIVED),
}


def edge_id(relation: R, source_id: str, target_id: str) -> str:
    if RELATIONSHIPS[relation].symmetric:
        source_id, target_id = sorted((source_id, target_id))
    payload = json.dumps([relation, source_id, target_id], separators=(",", ":"))
    return "edge:" + sha256(payload.encode("utf-8")).hexdigest()
