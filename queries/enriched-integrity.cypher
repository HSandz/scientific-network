// v5-enriched integrity checks. Every query must return 0 rows or 0.
// 1. enrichment edges without evidence IDs or with a status other than accepted
MATCH ()-[r:USES_METHOD|ADDRESSES_TASK|USES_DATASET|APPLIED_TO|EVALUATED_ON|PART_OF|RELATED_TO]->()
WHERE r.evidence_ids IS NULL OR size(r.evidence_ids) = 0 OR r.validation_status <> 'accepted' RETURN count(r) AS edges_without_evidence;
// 2. entity nodes below the 3-paper node threshold
MATCH (n) WHERE (n:Method OR n:Task OR n:Dataset) AND n.paper_count < 3 RETURN count(n) AS nodes_below_threshold;
// 3. paper_count equals the number of distinct incoming paper edges
MATCH (n) WHERE n:Method OR n:Task OR n:Dataset
OPTIONAL MATCH (p:Paper)-[r:USES_METHOD|ADDRESSES_TASK|USES_DATASET]->(n)
WITH n, count(DISTINCT p) AS papers WHERE papers <> n.paper_count RETURN count(n) AS paper_count_mismatches;
// 4. APPLIED_TO and EVALUATED_ON need two supporting papers, RELATED_TO three
MATCH ()-[r:APPLIED_TO|EVALUATED_ON]->() WHERE r.support_count < 2 RETURN count(r) AS thin_relation_edges;
MATCH ()-[r:RELATED_TO]->() WHERE r.support_count < 3 RETURN count(r) AS thin_related_edges;
// 5. parent-only organizations must be non-core and carry their source
MATCH (o:Organization) WHERE o.source = 'wikidata_parent' AND (o.is_core <> false OR o.wikidata_qid IS NULL) RETURN count(o) AS bad_parent_nodes;
// 6. no enrichment edge touches a non-core paper
MATCH (p:Paper)-[:USES_METHOD|ADDRESSES_TASK|USES_DATASET]->() WHERE p.is_core <> true RETURN count(p) AS non_core_papers_with_entities;
