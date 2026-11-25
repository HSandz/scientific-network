// Method-Dataset connections through shared papers; first query: entity is a Method, second: entity is a Dataset (read-only; neo4j-enriched, bolt 7690). Shared-paper counts from USES_METHOD and USES_DATASET only.
// Parameters: $entity_id, $min_papers (default 1), $limit.
MATCH (a:Method {id: $entity_id})<-[:USES_METHOD]-(p:Paper)-[:USES_DATASET]->(b:Dataset)
WITH a, b, collect(DISTINCT p) AS papers
WHERE size(papers) >= coalesce($min_papers, 1)
RETURN b.id AS partner_id, b.name AS partner, size(papers) AS shared_papers, [p IN papers | p.year] AS years, [p IN papers | p.id] AS paper_ids
ORDER BY shared_papers DESC, partner LIMIT coalesce($limit, 50);
MATCH (a:Dataset {id: $entity_id})<-[:USES_DATASET]-(p:Paper)-[:USES_METHOD]->(b:Method)
WITH a, b, collect(DISTINCT p) AS papers
WHERE size(papers) >= coalesce($min_papers, 1)
RETURN b.id AS partner_id, b.name AS partner, size(papers) AS shared_papers, [p IN papers | p.year] AS years, [p IN papers | p.id] AS paper_ids
ORDER BY shared_papers DESC, partner LIMIT coalesce($limit, 50);
