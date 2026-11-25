// Method-Task connections through shared papers (read-only; neo4j-enriched, bolt 7690).
// The extracted APPLIED_TO edges are sparse (frozen rule), so the application answers "which tasks does this method address" from
// papers that both USES_METHOD the method and ADDRESSES_TASK the task. Evidence = the shared papers.
// Parameters: $entity_id (a Method id, e.g. 'method:Q...'), $min_papers (default 1 when absent), $limit.
MATCH (m:Method {id: $entity_id})<-[:USES_METHOD]-(p:Paper)-[:ADDRESSES_TASK]->(t:Task)
WITH m, t, collect(DISTINCT p) AS papers
WHERE size(papers) >= coalesce($min_papers, 1)
RETURN t.id AS partner_id, t.name AS partner, size(papers) AS shared_papers,
       [p IN papers | p.year] AS years,
       [p IN papers | p.id] AS paper_ids
ORDER BY shared_papers DESC, partner LIMIT coalesce($limit, 50);
// Task -> Methods (the same relationship read from the task side)
MATCH (t:Task {id: $entity_id})<-[:ADDRESSES_TASK]-(p:Paper)-[:USES_METHOD]->(m:Method)
WITH t, m, collect(DISTINCT p) AS papers
WHERE size(papers) >= coalesce($min_papers, 1)
RETURN m.id AS partner_id, m.name AS partner, size(papers) AS shared_papers, [p IN papers | p.year] AS years, [p IN papers | p.id] AS paper_ids
ORDER BY shared_papers DESC, partner LIMIT coalesce($limit, 50);
