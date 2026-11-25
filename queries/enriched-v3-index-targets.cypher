// Enrichment v3: PART_OF targets that are an index, list or ranking (the v1 bug). On the v3 graph this returns 0 rows.
MATCH (a:Organization)-[:PART_OF]->(b:Organization)
WHERE b.name IN ['S&P 500', 'Dow Jones Industrial Average', 'Forbes Global 2000']
RETURN b.name AS parent, count(a) AS children ORDER BY children DESC;
