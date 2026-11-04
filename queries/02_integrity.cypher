// Each query should return no rows on a structurally accepted graph.
MATCH (s)-[r]->(t)
WHERE s = t
RETURN s.id AS self_loop_node, type(r) AS relation;

MATCH (s)-[r]->(t)
WITH type(r) AS relation, s.id AS source_id, t.id AS target_id, count(*) AS copies
WHERE copies > 1
RETURN relation, source_id, target_id, copies;

MATCH (s)-[r]->(t)
WHERE type(r) IN ['COAUTHORED_WITH', 'COLLABORATED_WITH'] AND s.id >= t.id
RETURN r.edge_id AS incorrectly_oriented_edge;

MATCH ()-[r]->()
WHERE r.edge_id IS NULL OR r.method_version IS NULL OR r.graph_version IS NULL
   OR r.evidence_kind IS NULL OR r.evidence_ids IS NULL OR size(r.evidence_ids) = 0
   OR r.validation_status IS NULL OR r.validation_status <> 'accepted'
RETURN r.edge_id AS missing_or_invalid_provenance, type(r) AS relation;

WITH {
  AUTHORED: ['Researcher', 'Paper'],
  AFFILIATED_WITH: ['Researcher', 'Organization'],
  PUBLISHED_IN: ['Paper', 'Venue'],
  CITES: ['Paper', 'Paper'],
  HAS_TOPIC: ['Paper', 'Topic'],
  SUBTOPIC_OF: ['Topic', 'Topic'],
  COAUTHORED_WITH: ['Researcher', 'Researcher'],
  COLLABORATED_WITH: ['Organization', 'Organization'],
  RESEARCHES_TOPIC: ['Researcher', 'Topic'],
  CONTRIBUTES_TO_TOPIC: ['Organization', 'Topic']
} AS endpoint_schema
MATCH (s)-[r]->(t)
WITH s, r, t, endpoint_schema[type(r)] AS expected
WHERE expected IS NULL OR NOT (expected[0] IN labels(s)) OR NOT (expected[1] IN labels(t))
RETURN r.edge_id AS invalid_endpoint_edge, type(r) AS relation;

MATCH (p:Paper)
WHERE p.is_core = true
OPTIONAL MATCH (p)-[:PUBLISHED_IN]->(v:Venue)
WITH p, count(v) AS venue_count
WHERE venue_count <> 1
RETURN p.id AS paper_with_invalid_primary_venue, venue_count;

// JSON validation checks evidence references, affiliation triples and exact derived
// support/weights. The loader reconciles counts. These queries do not establish
// raw-source correctness or independent semantic accuracy.
