// Separate projection inputs. These queries do not run GDS algorithms.
MATCH (a:Researcher)-[r:COAUTHORED_WITH]->(b:Researcher)
RETURN a.id AS source, b.id AS target, r.support_count AS shared_papers,
       r.fractional_weight AS fractional_weight;

MATCH (a:Organization)-[r:COLLABORATED_WITH]->(b:Organization)
RETURN a.id AS source, b.id AS target, r.support_count AS shared_papers,
       r.fractional_weight AS fractional_weight;

MATCH (citing:Paper)-[r:CITES]->(cited:Paper)
WHERE citing.is_core = true AND cited.is_core = true
RETURN citing.id AS source, cited.id AS target, r.edge_id AS edge_id;

// Isolates require a separate complete node list for each projection.
MATCH (r:Researcher)-[:AUTHORED]->(p:Paper)
WHERE p.is_core = true AND r.resolution_status = 'resolved'
RETURN DISTINCT r.id AS researcher_id;
