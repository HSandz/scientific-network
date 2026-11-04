// Counts are meaningful only after loading the selected graph version.
MATCH (n)
RETURN labels(n) AS labels, count(*) AS nodes
ORDER BY nodes DESC;

MATCH ()-[r]->()
RETURN type(r) AS relation, r.evidence_kind AS evidence_kind, count(*) AS edges
ORDER BY relation;

MATCH (r:Researcher)-[:AUTHORED]->(p:Paper)
WHERE p.is_core = true AND r.resolution_status = 'resolved'
RETURN count(DISTINCT r) AS resolved_core_researchers,
       count(DISTINCT p) AS core_papers_with_resolved_authorship;

// Counts alone cannot establish evidence correctness or independent precision.
