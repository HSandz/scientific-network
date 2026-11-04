// Set Browser parameter edge_id to an actual accepted edge ID before running.
// Resolve the returned IDs in the versioned evidence ledger; support arrays may
// instead be partition references once the production storage contract is frozen.
MATCH (s)-[r {edge_id: $edge_id}]->(t)
RETURN s.id AS source_id, s.name AS source_name, type(r) AS predicate,
       t.id AS target_id, t.name AS target_name,
       r.evidence_kind AS evidence_kind, r.evidence_ids AS evidence_ids,
       r.graph_version AS graph_version, r.method_version AS method_version,
       r.support_count AS distinct_support_papers,
       r.fractional_weight AS fractional_weight;
