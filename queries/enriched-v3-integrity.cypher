// Enrichment v3 integrity checks (graph enriched-cb371912e308 on neo4j-enriched, bolt 7690). Every query must return 0.
// v3 differs from v2/integrity: single-paper APPLIED_TO is allowed, and a pair carries exactly one of PART_OF and MEMBER_OF.
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
// 5. RELATED_TO keeps its three-paper threshold (APPLIED_TO and EVALUATED_ON single-paper edges are allowed in v3 and checked in 4)
MATCH ()-[r:RELATED_TO]->() WHERE r.support_count < 3 RETURN count(r) AS thin_related_edges;
// 6. parent-only organizations must be non-core and carry their source
MATCH (o:Organization) WHERE o.source = 'wikidata_parent' AND (o.is_core <> false OR o.wikidata_qid IS NULL) RETURN count(o) AS bad_parent_nodes;
// 7. no enrichment edge touches a non-core paper
MATCH (p:Paper)-[:USES_METHOD|ADDRESSES_TASK|USES_DATASET]->() WHERE p.is_core <> true RETURN count(p) AS non_core_papers_with_entities;
// 8. MEMBER_OF only between organizations, never reflexive
MATCH (a)-[r:MEMBER_OF]->(b) WHERE NOT (a:Organization AND b:Organization) OR a = b RETURN count(r) AS bad_member_of;
// 9. exactly one of PART_OF and MEMBER_OF per organization pair
MATCH (a:Organization)-[:MEMBER_OF]->(b:Organization) WHERE (a)-[:PART_OF]->(b) RETURN count(*) AS pairs_with_both_predicates;
// 10. no PART_OF target is an index, list or ranking from the known v1 cases (the class check is in the build validator)
MATCH (a:Organization)-[:PART_OF]->(b:Organization) WHERE b.name IN ['S&P 500', 'Dow Jones Industrial Average', 'Forbes Global 2000'] RETURN count(a) AS index_targets;
// 11. every parent-only organization node is the target of a PART_OF or MEMBER_OF edge (no orphans after the rule dropped edges)
MATCH (o:Organization) WHERE o.source = 'wikidata_parent' AND NOT ()-[:PART_OF|MEMBER_OF]->(o) RETURN count(o) AS orphan_parent_nodes;
