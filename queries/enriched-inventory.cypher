// v5-enriched inventory (run against neo4j-enriched, bolt 7690). Counts per label and relation, by layer.
MATCH (n) WITH labels(n)[0] AS label, n.graph_version AS graph_version, count(*) AS nodes
RETURN label, graph_version, nodes ORDER BY label, graph_version;
MATCH ()-[r]->() WITH type(r) AS relation, r.graph_version AS graph_version, r.evidence_kind AS evidence_kind, count(*) AS edges
RETURN relation, graph_version, evidence_kind, edges ORDER BY relation, graph_version;
