// Enrichment v2 integrity checks (graph enriched-827be09bc987 on neo4j-enriched, bolt 7690). Every query must return 0.
// Replaces the thin-edge and evidence checks of queries/enriched-integrity.cypher, which do not know MEMBER_OF or support_rule.
// 1. enrichment edges without evidence IDs or with a status other than accepted
MATCH ()-[r:USES_METHOD|ADDRESSES_TASK|USES_DATASET|APPLIED_TO|EVALUATED_ON|PART_OF|MEMBER_OF|RELATED_TO]->()
WHERE r.evidence_ids IS NULL OR size(r.evidence_ids) = 0 OR r.validation_status <> 'accepted' RETURN count(r) AS edges_without_evidence;
// 2. entity nodes below the 3-paper node threshold
MATCH (n) WHERE (n:Method OR n:Task OR n:Dataset) AND n.paper_count < 3 RETURN count(n) AS nodes_below_threshold;
// 3. paper_count equals the number of distinct incoming paper edges
MATCH (n) WHERE n:Method OR n:Task OR n:Dataset
OPTIONAL MATCH (p:Paper)-[r:USES_METHOD|ADDRESSES_TASK|USES_DATASET]->(n)
WITH n, count(DISTINCT p) AS papers WHERE papers <> n.paper_count RETURN count(n) AS paper_count_mismatches;
// 4. every APPLIED_TO and EVALUATED_ON edge names the rule that admitted it, and the rule matches its support
MATCH ()-[r:APPLIED_TO|EVALUATED_ON]->()
WHERE r.support_rule IS NULL OR NOT r.support_rule IN ['two_or_more_papers', 'single_paper_same_sentence']
   OR (r.support_rule = 'two_or_more_papers' AND r.support_count < 2)
   OR (r.support_rule = 'single_paper_same_sentence' AND r.support_count <> 1)
RETURN count(r) AS relation_edges_with_bad_support_rule;
// 5. single-paper edges exist only for the relation adopted for them (EVALUATED_ON)
MATCH ()-[r:APPLIED_TO]->() WHERE r.support_rule = 'single_paper_same_sentence' RETURN count(r) AS single_paper_applied_to;
MATCH ()-[r:RELATED_TO]->() WHERE r.support_count < 3 RETURN count(r) AS thin_related_edges;
// 6. parent-only organizations must be non-core and carry their source
MATCH (o:Organization) WHERE o.source = 'wikidata_parent' AND (o.is_core <> false OR o.wikidata_qid IS NULL) RETURN count(o) AS bad_parent_nodes;
// 7. no enrichment edge touches a non-core paper
MATCH (p:Paper)-[:USES_METHOD|ADDRESSES_TASK|USES_DATASET]->() WHERE p.is_core <> true RETURN count(p) AS non_core_papers_with_entities;
// 8. MEMBER_OF only between organizations, never reflexive, and every one has a PART_OF edge for the same pair (it is additional)
MATCH (a)-[r:MEMBER_OF]->(b) WHERE NOT (a:Organization AND b:Organization) OR a = b RETURN count(r) AS bad_member_of;
MATCH (a:Organization)-[r:MEMBER_OF]->(b:Organization) WHERE NOT (a)-[:PART_OF]->(b) RETURN count(r) AS member_of_without_part_of_pair;
