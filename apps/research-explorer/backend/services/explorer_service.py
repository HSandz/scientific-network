"""Core service orchestrating Neo4j queries, precomputed analysis metrics, and evidence ledgers."""

from collections import Counter
import json
import math
from typing import Any

import networkx as nx

from ..config import (
    REPO_ROOT,
    EXPECTED_EDGES_BY_RELATION,
    EXPECTED_FACTUAL_EDGES,
    EXPECTED_GRAPH_SHA256,
    EXPECTED_GRAPH_VERSION,
    EXPECTED_NODES_BY_LABEL,
    EXPECTED_TOTAL_EDGES,
    EXPECTED_TOTAL_NODES,
)
from ..models.schemas import (
    CompareResponse,
    ConnectedEntityGroup,
    EdgeEvidenceResponse,
    EvidenceRecordItem,
    FullProjectionMetrics,
    GraphEdge,
    GraphNode,
    GraphSchemaResponse,
    GraphSummaryResponse,
    GraphViewResponse,
    HealthResponse,
    LabelSpecItem,
    NeighborhoodResponse,
    NodeDetailResponse,
    PathRequest,
    PathResponse,
    PredicateSpecItem,
    SearchResponse,
    SearchResultItem,
    TableEdgesResponse,
    TableNodesResponse,
)
from ..repositories.artifact_store import ArtifactStore
from ..repositories.neo4j_repo import Neo4jRepository, SYMMETRIC_RELATIONS


LAYOUT_SEED = 42

HETEROGENEOUS_PRESETS: list[dict[str, Any]] = [
    {
        "id": "topic_taxonomy_ecosystem",
        "title": "All 5 Labels & 10 Predicates Ecosystem",
        "description": "Balanced cross-slice containing Topics, Organizations, Researchers, Papers, and Venues across all 10 predicates.",
        "node_labels": ["Researcher", "Paper", "Organization", "Topic", "Venue"],
        "relations": [
            "AUTHORED",
            "AFFILIATED_WITH",
            "PUBLISHED_IN",
            "CITES",
            "HAS_TOPIC",
            "SUBTOPIC_OF",
            "COAUTHORED_WITH",
            "COLLABORATED_WITH",
            "RESEARCHES_TOPIC",
            "CONTRIBUTES_TO_TOPIC",
        ],
    },
    {
        "id": "researcher_paper_topic",
        "title": "Researcher → Paper → Topic & Venue",
        "description": "Traces authored core papers to their inferred leaf topics, parent topic hierarchy, and conference venues.",
        "node_labels": ["Researcher", "Paper", "Topic", "Venue"],
        "relations": ["AUTHORED", "HAS_TOPIC", "SUBTOPIC_OF", "PUBLISHED_IN"],
    },
    {
        "id": "academia_industry_topics",
        "title": "Academia–Industry Partnerships & Topics",
        "description": "Cross-sector organization collaborations (COLLABORATED_WITH) linked to topic contributions (CONTRIBUTES_TO_TOPIC).",
        "node_labels": ["Organization", "Topic"],
        "relations": ["COLLABORATED_WITH", "CONTRIBUTES_TO_TOPIC", "SUBTOPIC_OF"],
    },
    {
        "id": "researcher_organization",
        "title": "Researcher → Affiliation → Organization & Papers",
        "description": "Observed authorship-aligned organizational affiliations alongside authored papers and venues.",
        "node_labels": ["Researcher", "Organization", "Paper", "Venue"],
        "relations": ["AFFILIATED_WITH", "AUTHORED", "PUBLISHED_IN"],
    },
    {
        "id": "paper_venue_citation",
        "title": "Citation Chains, Topics & Venues",
        "description": "Directed in-scope paper citations (CITES) together with their conference venues and inferred topics.",
        "node_labels": ["Paper", "Venue", "Topic"],
        "relations": ["CITES", "PUBLISHED_IN", "HAS_TOPIC"],
    },
]

SCIENTIFIC_CAVEATS: list[str] = [
    "Release scope: AAAI/IJCAI 2021–2025 main-track core papers; excluded or unavailable papers limit coverage.",
    "Edge precision is AI-assessed. No independent human validation; reviewer independence and verified course accuracy are not established. Wilson intervals exclude evaluator error. Measurements and denominators are in the quality contract; unavailable measurements must not be inferred.",
    "Affiliations are authorship-specific observations, not current employment. Missing affiliations or sectors mean unknown, not no collaboration. Co-publication does not establish funding, contracts or employment.",
    "HAS_TOPIC is embedding-inferred; topic coverage is not accuracy. Historical topic evaluation is reused without retuning. The identity correction and embedding classifier are separate processing stages.",
    "Researcher identity uses compatible OpenAlex author IDs and global observed-ORCID conflict withholding; never normalized names alone.",
    "CITES points from citing to cited paper within this corpus. Counts are not global influence or exposure-adjusted impact.",
    "Layouts, radial rings and visual grouping do not measure geography, scientific similarity or hierarchy. Bounded graph slices are illustrative, not statistically representative.",
    "Centrality describes structural position in a particular projection, not researcher quality. Community IDs can change between graph versions.",
]


def _parse_json_prop(val: Any) -> Any:
    if isinstance(val, str) and val.startswith(("[", "{")):
        try:
            return json.loads(val)
        except Exception:
            return val
    return val


class ExplorerService:
    """High-level read-only exploration service."""

    def __init__(self, repo: Neo4jRepository, store: ArtifactStore) -> None:
        self.repo = repo
        self.store = store

    def get_health(self) -> HealthResponse:
        inv = self.repo.verify_inventory(use_cache=False)
        status = "ok" if inv["connected"] and inv["database_verified"] else ("degraded" if inv["connected"] else "error")
        return HealthResponse(
            status=status,
            neo4j_connected=inv["connected"],
            neo4j_endpoint=inv["endpoint"],
            expected_graph_version=EXPECTED_GRAPH_VERSION,
            observed_graph_versions=inv["observed_graph_versions"],
            database_verified=inv["database_verified"],
            total_nodes=inv["total_nodes"],
            total_edges=inv["total_edges"],
            warnings=inv["warnings"],
            artifacts={
                "summary_json": bool(self.store.summary_data),
                "analysis_json": bool(self.store.analysis_data),
                "network_views_json": bool(self.store.network_views_data),
                "audit_results_json": bool(self.store.audit_results_data),
                "graph_ledger_available": self.store.ledger_available,
            },
        )

    def _build_quality_contract(self) -> dict[str, Any]:
        """Build the single canonical quality and provenance contract from release artifacts.
        
        When underlying artifacts or sections are absent, returns explicit unavailable
        states and None numeric fields rather than historical fallback defaults.
        """
        summary = self.store.summary_data or {}
        coverage = summary.get("coverage", {}) if isinstance(summary, dict) else {}
        audit = self.store.audit_results_data or {}
        qcfg = self.store.quality_config_data or {}
        topic_eval = self.store.topic_eval_data or {}
        topic_reuse = self.store.historical_topic_reuse_data or {}

        audit_cfg = qcfg.get("audit", {}) if isinstance(qcfg, dict) else {}
        cov_targets = qcfg.get("coverage_targets", {}) if isinstance(qcfg, dict) else {}
        comp_targets = qcfg.get("component_precision_targets", {}) if isinstance(qcfg, dict) else {}

        # 1. Edge precision from audit artifact
        global_audit = audit.get("global") or audit.get("global_sample") or {}
        has_audit = bool(all(key in global_audit for key in ("precision", "correct", "total", "wilson_95")) and isinstance(global_audit["wilson_95"], dict) and all(key in global_audit["wilson_95"] for key in ("wilson_lower", "wilson_upper")))

        edge_target = float(audit_cfg.get("min_precision", 0.95)) if audit_cfg else 0.95
        wilson_target = float(audit_cfg.get("wilson_lower_bound_must_exceed", 0.90)) if audit_cfg else 0.90

        if has_audit:
            edge_precision = float(global_audit.get("precision", 0.0))
            wilson_obj = global_audit.get("wilson_95", {})
            if isinstance(wilson_obj, dict):
                wilson_lower = float(wilson_obj.get("wilson_lower", 0.0))
                wilson_upper = float(wilson_obj.get("wilson_upper", 0.0))
            elif isinstance(wilson_obj, (list, tuple)) and len(wilson_obj) >= 2:
                wilson_lower = float(wilson_obj[0])
                wilson_upper = float(wilson_obj[1])
            else:
                wilson_lower = edge_precision
                wilson_upper = edge_precision

            edge_status = (
                "passed"
                if edge_precision >= edge_target and wilson_lower > wilson_target
                else "failed"
            )
            correct_val: int | None = int(global_audit.get("correct", 0))
            total_val: int | None = int(global_audit.get("total", global_audit.get("n", 0)))
            incorrect_val: int | None = int(global_audit.get("incorrect", 0))
            unverifiable_val: int | None = int(global_audit.get("unverifiable", 0))
            wilson_lower_val: float | None = wilson_lower
            wilson_upper_val: float | None = wilson_upper
            wilson_pair_val: list[float] | None = [wilson_lower, wilson_upper]
            edge_precision_val: float | None = edge_precision
        else:
            edge_precision_val = None
            correct_val = None
            total_val = None
            incorrect_val = None
            unverifiable_val = None
            wilson_lower_val = None
            wilson_upper_val = None
            wilson_pair_val = None
            edge_status = "unavailable"

        agreement = audit.get("agreement", {}) if isinstance(audit, dict) else {}
        has_agreement = bool(agreement)
        overlap_reviewed_val: int | None = int(agreement.get("edges_reviewed_by_both", 0)) if has_agreement else None
        overlap_agreed_val: int | None = int(agreement.get("agreed", 0)) if has_agreement else None
        overlap_rate_val: float | None = float(agreement.get("percent", 0.0)) if has_agreement else None
        kappa_val: float | None = float(agreement.get("cohens_kappa", 0.0)) if has_agreement else None
        macro_prec_val: float | None = float(audit.get("macro_per_type_precision", 0.0)) if has_audit and "macro_per_type_precision" in audit else None

        # 2. Coverage metrics from summary artifact
        has_coverage = bool(all(key in coverage for key in ("accepted_authorships_with_institution", "author_positions", "papers_with_abstract", "eligible_papers", "papers_topic_labeled", "papers_topic_abstained")))

        aff_target = float(cov_targets.get("author_paper_affiliation_resolution", 0.80)) if cov_targets else 0.80
        abs_target = float(cov_targets.get("abstracts", 0.95)) if cov_targets else 0.95
        top_cov_target = float(cov_targets.get("topics_on_eligible_papers", 0.80)) if cov_targets else 0.80

        if has_coverage:
            aff_resolved_val: int | None = int(coverage.get("accepted_authorships_with_institution", 0))
            aff_eligible_val: int | None = int(coverage.get("author_positions", 0))
            if "author_paper_affiliation_coverage" in coverage:
                aff_cov_val: float | None = float(coverage["author_paper_affiliation_coverage"])
            elif aff_eligible_val and aff_eligible_val > 0:
                aff_cov_val = (aff_resolved_val or 0) / aff_eligible_val
            else:
                aff_cov_val = 0.0
            aff_status = "passed" if aff_cov_val >= aff_target else "failed"

            abs_resolved_val: int | None = int(coverage.get("papers_with_abstract", 0))
            abs_eligible_val: int | None = int(coverage.get("eligible_papers", 0))
            if "abstract_coverage" in coverage:
                abs_cov_val: float | None = float(coverage["abstract_coverage"])
            elif abs_eligible_val and abs_eligible_val > 0:
                abs_cov_val = (abs_resolved_val or 0) / abs_eligible_val
            else:
                abs_cov_val = 0.0
            abs_status = "passed" if abs_cov_val >= abs_target else "failed"

            top_labeled_val: int | None = int(coverage.get("papers_topic_labeled", 0))
            top_eligible_val: int | None = int(coverage.get("eligible_papers", abs_eligible_val or 0))
            top_abstained_val: int | None = int(coverage.get("papers_topic_abstained", 0))
            if "topic_coverage" in coverage:
                top_cov_val: float | None = float(coverage["topic_coverage"])
            elif top_eligible_val and top_eligible_val > 0:
                top_cov_val = (top_labeled_val or 0) / top_eligible_val
            else:
                top_cov_val = 0.0
            top_cov_status = "passed" if top_cov_val >= top_cov_target else "failed"

            aff_all_official_val: int | None = int(coverage["all_official_authorships"]) if "all_official_authorships" in coverage else None
            aff_accepted_val: int | None = int(coverage["accepted_authorships"]) if "accepted_authorships" in coverage else None
            aff_cond_cov_val: float | None = (
                (aff_resolved_val or 0) / aff_accepted_val
                if aff_accepted_val and aff_accepted_val > 0
                else None
            )
            aff_papers_with_edge_val: int | None = int(coverage["papers_with_accepted_affiliation_edge"]) if "papers_with_accepted_affiliation_edge" in coverage else None
            match_rate_val: float | None = (
                (abs_resolved_val or 0) / max(1, abs_eligible_val or 1)
                if abs_eligible_val
                else None
            )
        else:
            aff_resolved_val = None
            aff_eligible_val = None
            aff_cov_val = None
            aff_status = "unavailable"
            abs_resolved_val = None
            abs_eligible_val = None
            abs_cov_val = None
            abs_status = "unavailable"
            top_labeled_val = None
            top_eligible_val = None
            top_abstained_val = None
            top_cov_val = None
            top_cov_status = "unavailable"
            aff_all_official_val = None
            aff_accepted_val = None
            aff_cond_cov_val = None
            aff_papers_with_edge_val = None
            match_rate_val = None

        # 3. Topic evaluation
        emb_micro = (
            topic_eval.get("models", {})
            .get("embedding_classifier", {})
            .get("paper_normalized_review_metrics", {})
            .get("micro", {})
            if isinstance(topic_eval, dict)
            else {}
        )
        phr_micro = (
            topic_eval.get("models", {})
            .get("phrase_baseline", {})
            .get("paper_normalized_review_metrics", {})
            .get("micro", {})
            if isinstance(topic_eval, dict)
            else {}
        )
        has_topic_eval = bool(emb_micro and "precision" in emb_micro)

        top_prec_target = float(comp_targets.get("topic_labels", 0.95)) if comp_targets else 0.95

        if has_topic_eval:
            top_prec_val: float | None = float(emb_micro["precision"])
            top_prec_status = "passed" if top_prec_val >= top_prec_target else "failed"
            top_f1_val: float | None = float(
                emb_micro.get(
                    "f1",
                    topic_reuse.get("historical_micro_f1", {}).get("embedding_classifier", 0.0),
                )
            )
            phr_f1_val: float | None = float(
                phr_micro.get(
                    "f1",
                    topic_reuse.get("historical_micro_f1", {}).get("phrase_baseline", 0.0),
                )
            )
            phr_prec_val: float | None = float(phr_micro.get("precision", 0.0))
            topic_test_count_val: int | None = int(topic_eval.get("topic_test_paper_count", 50))
            topic_eval_status_val: str = str(
                topic_reuse.get(
                    "status",
                    "historical_reference_reuse_supported_by_exact_prediction_equality",
                )
            )
        else:
            top_prec_val = None
            top_prec_status = "unavailable"
            top_f1_val = None
            phr_f1_val = None
            phr_prec_val = None
            topic_test_count_val = None
            topic_eval_status_val = "unavailable"

        eval_kind_str = str(audit.get("evaluation_kind", "ai_agent_review")) if has_audit else "unavailable"
        course_acc_str = str(audit.get("verified_course_accuracy", "not_established")) if has_audit else "not_established"
        gate_scope_str = str(audit.get("numeric_gate_scope", "ai_assessed_only")) if has_audit else "unavailable"

        return {
            # Canonical keys
            "edge_precision": edge_precision_val,
            "edge_precision_ai_assessed": edge_precision_val,
            "edge_precision_correct": correct_val,
            "edge_precision_total": total_val,
            "edge_precision_incorrect": incorrect_val,
            "edge_precision_unverifiable": unverifiable_val,
            "edge_precision_wilson_lower": wilson_lower_val,
            "edge_precision_wilson_upper": wilson_upper_val,
            "edge_precision_wilson_95": wilson_pair_val,
            "edge_precision_target": edge_target,
            "edge_precision_wilson_target": wilson_target,
            "edge_precision_status": edge_status,
            "macro_per_type_precision": macro_prec_val,
            "overlap_reviewed": overlap_reviewed_val,
            "overlap_agreed": overlap_agreed_val,
            "overlap_agreement_rate": overlap_rate_val,
            "cohens_kappa": kappa_val,
            "affiliation_coverage": aff_cov_val,
            "affiliation_positions_resolved": aff_resolved_val,
            "affiliation_positions_eligible": aff_eligible_val,
            "affiliation_positions_all_official": aff_all_official_val,
            "affiliation_positions_accepted": aff_accepted_val,
            "affiliation_conditional_coverage": aff_cond_cov_val,
            "affiliation_papers_with_edge": aff_papers_with_edge_val,
            "affiliation_papers_eligible": abs_eligible_val,
            "affiliation_target": aff_target,
            "affiliation_coverage_target": aff_target,
            "affiliation_status": aff_status,
            "affiliation_coverage_status": aff_status,
            "abstract_coverage": abs_cov_val,
            "abstract_papers_resolved": abs_resolved_val,
            "abstract_papers_eligible": abs_eligible_val,
            "abstract_coverage_target": abs_target,
            "abstract_coverage_status": abs_status,
            "openalex_work_match_rate": match_rate_val,
            "topic_coverage": top_cov_val,
            "topic_papers_labeled": top_labeled_val,
            "topic_papers_eligible": top_eligible_val,
            "topic_papers_abstained": top_abstained_val,
            "topic_coverage_target": top_cov_target,
            "topic_coverage_status": top_cov_status,
            "topic_precision": top_prec_val,
            "topic_precision_true_positive": emb_micro.get("true_positive"),
            "topic_precision_predicted_labels": (emb_micro["true_positive"] + emb_micro["false_positive"]) if "true_positive" in emb_micro and "false_positive" in emb_micro else None,
            "topic_precision_denominator_note": "Paper-normalized weighted label judgments; inverse reviewer count per paper, not independent human gold",
            "topic_embedding_precision": top_prec_val,
            "topic_precision_target": top_prec_target,
            "topic_precision_status": top_prec_status,
            "topic_micro_f1": top_f1_val,
            "topic_embedding_micro_f1": top_f1_val,
            "topic_phrase_baseline_f1": phr_f1_val,
            "topic_phrase_baseline_precision": phr_prec_val,
            "topic_test_paper_count": topic_test_count_val,
            "topic_eval_status": topic_eval_status_val,
            "evaluation_kind": eval_kind_str,
            "human_validation_performed": False,
            "reviewer_independence_established": False,
            "verified_course_accuracy_established": False,
            "verified_course_accuracy": course_acc_str,
            "numeric_gate_scope": gate_scope_str,
        }

    def get_summary(self) -> GraphSummaryResponse:
        inv = self.repo.verify_inventory(use_cache=True)
        summary = self.store.summary_data
        counts = summary.get("counts", {})

        if not summary or not counts or not summary.get("graph_sha256") or not summary.get("graph_version"):
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Release summary artifact unavailable")
        nodes_by_label = inv["nodes_by_label"] or counts["nodes_by_label"]
        edges_by_relation = inv["edges_by_relation"] or counts["edges_by_relation"]
        edges_by_kind = counts["edges_by_evidence_kind"]
        quality_summary = self._build_quality_contract()

        return GraphSummaryResponse(
            graph_version=summary["graph_version"],
            graph_sha256=summary["graph_sha256"],
            database_verified=inv["database_verified"],
            warnings=inv["warnings"],
            nodes_by_label=nodes_by_label,
            edges_by_relation=edges_by_relation,
            edges_by_evidence_kind=edges_by_kind,
            total_nodes=sum(nodes_by_label.values()),
            total_edges=sum(edges_by_relation.values()),
            unique_core_factual_edges=counts["unique_core_factual_edges"],
            core_papers=counts["core_papers"],
            resolved_core_researchers=counts["resolved_core_researchers"],
            quality=quality_summary,
            size_gates=summary.get("size_gates", {}),
            scientific_caveats=SCIENTIFIC_CAVEATS + ([f"Frozen topic model: {summary['model']['name']}; revision {summary['model'].get('revision', 'unavailable')}; tau {summary.get('thresholds', {}).get('tau', 'unavailable')}. See frozen summary for calibration provenance."] if summary.get("model", {}).get("name") else []),
        )

    def get_schema(self) -> GraphSchemaResponse:
        inv = self.repo.verify_inventory(use_cache=True)
        n_counts = inv["nodes_by_label"] or self.store.summary_data.get("counts", {}).get("nodes_by_label")
        e_counts = inv["edges_by_relation"] or self.store.summary_data.get("counts", {}).get("edges_by_relation")
        if not n_counts or not e_counts:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Graph schema inventory unavailable")

        labels = [
            LabelSpecItem(
                label="Researcher",
                description="Resolved person keyed by compatible OpenAlex author ID on matched works (ORCID conflict-checked).",
                id_prefix="researcher:openalex:A...",
                key_properties=["name", "resolution_status", "identity_method", "openalex_id", "orcid"],
                count=n_counts["Researcher"],
            ),
            LabelSpecItem(
                label="Paper",
                description="Main-track AAAI or IJCAI proceedings paper (2021–2025) from roster v10.",
                id_prefix="paper:{venue}:{year}:{id}",
                key_properties=["name", "year", "official_url", "pdf_url", "doi", "openalex_id", "track", "is_core", "official_author_count"],
                count=n_counts["Paper"],
            ),
            LabelSpecItem(
                label="Organization",
                description="Institution or corporate entity with an OpenAlex institution ID on accepted authorships.",
                id_prefix="organization:I...",
                key_properties=["name", "sector", "country_code", "ror", "openalex_id"],
                count=n_counts["Organization"],
            ),
            LabelSpecItem(
                label="Topic",
                description="Frozen vocabulary concept (4 parent topics and 16 leaf topics).",
                id_prefix="topic:{slug}",
                key_properties=["name", "level", "parent_id", "definition", "synonyms", "taxonomy_version"],
                count=n_counts["Topic"],
            ),
            LabelSpecItem(
                label="Venue",
                description="Conference series (AAAI and IJCAI).",
                id_prefix="venue:{slug}",
                key_properties=["name"],
                count=n_counts["Venue"],
            ),
        ]

        predicates = [
            PredicateSpecItem(
                id="R1",
                predicate="AUTHORED",
                source_label="Researcher",
                target_label="Paper",
                evidence_kind="observed",
                symmetric=False,
                directed=True,
                description="Resolved researcher on the official paper byline at a compatible position.",
                weight_rule="Unit observation; stores byline_position and roster_name.",
                count=e_counts["AUTHORED"],
            ),
            PredicateSpecItem(
                id="R2",
                predicate="AFFILIATED_WITH",
                source_label="Researcher",
                target_label="Organization",
                evidence_kind="observed",
                symmetric=False,
                directed=True,
                description="Aggregated over aligned author–paper–organization observations (not employment duration).",
                weight_rule="Stores support_paper_count and raw_affiliation_strings.",
                count=e_counts["AFFILIATED_WITH"],
            ),
            PredicateSpecItem(
                id="R3",
                predicate="PUBLISHED_IN",
                source_label="Paper",
                target_label="Venue",
                evidence_kind="observed",
                symmetric=False,
                directed=True,
                description="Official main-track conference proceedings publication.",
                weight_rule="Exactly one primary venue per core paper; stores edition year.",
                count=e_counts["PUBLISHED_IN"],
            ),
            PredicateSpecItem(
                id="R4",
                predicate="CITES",
                source_label="Paper",
                target_label="Paper",
                evidence_kind="observed",
                symmetric=False,
                directed=True,
                description="Explicit within-corpus reference from citing paper to cited in-scope paper.",
                weight_rule="Directed unit edge (citing → cited).",
                count=e_counts["CITES"],
            ),
            PredicateSpecItem(
                id="R5",
                predicate="HAS_TOPIC",
                source_label="Paper",
                target_label="Topic",
                evidence_kind="inferred_topic",
                symmetric=False,
                directed=True,
                description="1–3 leaf topics assigned by the frozen sentence-embedding classifier (or abstained).",
                weight_rule="Stores cosine_similarity, threshold_tau, margin_delta, and supporting sentence excerpt.",
                count=e_counts["HAS_TOPIC"],
            ),
            PredicateSpecItem(
                id="R6",
                predicate="SUBTOPIC_OF",
                source_label="Topic",
                target_label="Topic",
                evidence_kind="curated_taxonomy",
                symmetric=False,
                directed=True,
                description="Curated hierarchy connecting each of the 16 leaf topics to its parent topic.",
                weight_rule="Curated taxonomy link (leaf → parent).",
                count=e_counts["SUBTOPIC_OF"],
            ),
            PredicateSpecItem(
                id="R7",
                predicate="COAUTHORED_WITH",
                source_label="Researcher",
                target_label="Researcher",
                evidence_kind="derived",
                symmetric=True,
                directed=False,
                description="Derived collaboration between distinct resolved researchers sharing ≥1 accepted core paper.",
                weight_rule="Each shared paper with k official authors contributes 1/(k-1) to fractional_weight; stores support_count.",
                count=e_counts["COAUTHORED_WITH"],
            ),
            PredicateSpecItem(
                id="R8",
                predicate="COLLABORATED_WITH",
                source_label="Organization",
                target_label="Organization",
                evidence_kind="derived",
                symmetric=True,
                directed=False,
                description="Derived collaboration between two organizations supported by ≥2 distinct authors on the same core paper.",
                weight_rule="A sole dual-affiliated author creates no edge. Contributes 1/q per supported org pair on a paper.",
                count=e_counts["COLLABORATED_WITH"],
            ),
            PredicateSpecItem(
                id="R9",
                predicate="RESEARCHES_TOPIC",
                source_label="Researcher",
                target_label="Topic",
                evidence_kind="derived",
                symmetric=False,
                directed=True,
                description="Derived researcher topic profile requiring ≥2 distinct accepted core papers with that leaf topic.",
                weight_rule="Thresholded at support_count ≥ 2 distinct core papers.",
                count=e_counts["RESEARCHES_TOPIC"],
            ),
            PredicateSpecItem(
                id="R10",
                predicate="CONTRIBUTES_TO_TOPIC",
                source_label="Organization",
                target_label="Topic",
                evidence_kind="derived",
                symmetric=False,
                directed=True,
                description="Derived organization topic profile requiring ≥3 distinct accepted core papers with aligned author affiliation and topic.",
                weight_rule="Thresholded at support_count ≥ 3 distinct core papers.",
                count=e_counts["CONTRIBUTES_TO_TOPIC"],
            ),
        ]

        return GraphSchemaResponse(
            graph_version=EXPECTED_GRAPH_VERSION,
            labels=labels,
            predicates=predicates,
            heterogeneous_presets=HETEROGENEOUS_PRESETS,
            evidence_classes={
                "observed": "Factual claims (R1–R4) directly backed by matched official roster and OpenAlex authorship/reference records; inventory reported separately.",
                "inferred_topic": "Text-inferred topic assignments (R5) from title/abstract embeddings with sentence excerpts; inventory reported separately.",
                "curated_taxonomy": "Frozen 16-leaf → 4-parent topic hierarchy (R6, 16 edges).",
                "derived": "Materialized social and topic-profile edges (R7–R10) deterministically derived from accepted core-paper support; inventory reported separately.",
            },
        )

    def _build_graph_node(
        self,
        raw: dict[str, Any],
        *,
        venue_map: dict[str, str] | None = None,
        pos: tuple[float, float] = (0.0, 0.0),
        deg: int = 0,
        strength: float = 0.0,
    ) -> GraphNode:
        nid = raw["id"]
        label = raw.get("_label") or raw.get("label") or "Researcher"
        name = raw.get("name", nid)
        metrics_dict = self.store.get_node_metrics(nid)
        full_metrics = FullProjectionMetrics(**metrics_dict) if metrics_dict else None

        clean_props = {
            k: _parse_json_prop(v)
            for k, v in raw.items()
            if k not in {"id", "name", "_label", "label", "_match_rank", "project", "graph_version"}
        }
        year = clean_props.get("year")
        sector = clean_props.get("sector")
        country_code = clean_props.get("country_code")
        venue = (venue_map or {}).get(nid) or clean_props.get("venue")

        if label == "Researcher":
            group = str(full_metrics.community_id if full_metrics and full_metrics.community_id else "unassigned")
            url = f"https://openalex.org/{clean_props.get('openalex_id') or nid.rsplit(':', 1)[-1]}"
        elif label == "Organization":
            group = str(sector or "unknown")
            url = clean_props.get("ror") or f"https://openalex.org/{clean_props.get('openalex_id') or nid.rsplit(':', 1)[-1]}"
        elif label == "Paper":
            group = str(year or "unknown")
            url = clean_props.get("official_url")
        elif label == "Topic":
            group = str(clean_props.get("level") or "topic")
            url = None
        else:
            group = nid
            url = None

        score = float(full_metrics.degree_strength) if full_metrics and full_metrics.degree_strength is not None else float(deg)

        return GraphNode(
            id=nid,
            label=label,
            name=name,
            group=group,
            score=round(score, 6),
            displayed_degree=deg,
            displayed_strength=round(strength, 6),
            x=round(float(pos[0]), 6),
            y=round(float(pos[1]), 6),
            year=int(year) if isinstance(year, int) else None,
            sector=sector,
            country_code=country_code,
            venue=venue,
            url=url,
            properties=clean_props,
            full_metrics=full_metrics,
        )

    def _compute_layout_and_finalize(
        self,
        raw_nodes: list[dict[str, Any]],
        raw_edges: list[dict[str, Any]],
        *,
        precomputed_positions: dict[str, tuple[float, float]] | None = None,
        center_id: str | None = None,
        preserve_exact_positions: bool = False,
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        if not raw_nodes and not raw_edges:
            return [], []

        paper_ids = [n["id"] for n in raw_nodes if (n.get("_label") or n.get("label")) == "Paper"]
        venue_map = self.repo.get_paper_venues(paper_ids) if paper_ids else {}

        deg_counter: Counter[str] = Counter()
        str_counter: dict[str, float] = Counter()
        for e in raw_edges:
            s, t = e["source"], e["target"]
            w = float(e.get("fractional_weight") or e.get("support_count") or 1.0)
            deg_counter[s] += 1
            deg_counter[t] += 1
            str_counter[s] += w
            str_counter[t] += w

        positions: dict[str, tuple[float, float]] = {}
        if preserve_exact_positions and precomputed_positions:
            positions.update(precomputed_positions)

        missing_ids = sorted(n["id"] for n in raw_nodes if n["id"] not in positions)
        if missing_ids:
            g = nx.Graph()
            dig = nx.DiGraph()
            for n in sorted(raw_nodes, key=lambda item: item["id"]):
                g.add_node(n["id"])
                dig.add_node(n["id"])
            for e in sorted(raw_edges, key=lambda item: item["edge_id"]):
                u, v = e["source"], e["target"]
                if u in g and v in g and u != v:
                    w = float(e.get("fractional_weight") or e.get("support_count") or 1.0)
                    g.add_edge(u, v, weight=1.0 + 0.15 * math.log1p(max(0.05, w)))
                    dig.add_edge(u, v)

            def relax_box(
                pos_map: dict[str, Any],
                min_dist: float,
                xmin: float,
                xmax: float,
                ymin: float,
                ymax: float,
                iters: int = 85,
            ) -> None:
                ids = sorted(pos_map.keys())
                if len(ids) <= 1:
                    if ids:
                        positions[ids[0]] = ((xmin + xmax) / 2.0, (ymin + ymax) / 2.0)
                    return
                xs = [float(pos_map[k][0]) for k in ids]
                ys = [float(pos_map[k][1]) for k in ids]
                span_x = (max(xs) - min(xs)) or 1.0
                span_y = (max(ys) - min(ys)) or 1.0
                pad_x = 0.07 * (xmax - xmin)
                pad_y = 0.07 * (ymax - ymin)
                bx0, bx1 = xmin + pad_x, xmax - pad_x
                by0, by1 = ymin + pad_y, ymax - pad_y
                pts: dict[str, list[float]] = {}
                for k in ids:
                    nx_val = bx0 + ((float(pos_map[k][0]) - min(xs)) / span_x) * (bx1 - bx0)
                    ny_val = by0 + ((float(pos_map[k][1]) - min(ys)) / span_y) * (by1 - by0)
                    pts[k] = [nx_val, ny_val]
                for _ in range(iters):
                    moved = False
                    for i in range(len(ids)):
                        u = ids[i]
                        for j in range(i + 1, len(ids)):
                            v = ids[j]
                            dx = pts[v][0] - pts[u][0]
                            dy = pts[v][1] - pts[u][1]
                            d = math.hypot(dx, dy)
                            if d < min_dist:
                                if d < 1e-6:
                                    ang = (i * 2.399963229728653 + j) % (2.0 * math.pi)
                                    dx, dy, d = math.cos(ang) * 1e-3, math.sin(ang) * 1e-3, 1e-3
                                push = 0.52 * (min_dist - d)
                                pts[u][0] -= (dx / d) * push
                                pts[u][1] -= (dy / d) * push
                                pts[v][0] += (dx / d) * push
                                pts[v][1] += (dy / d) * push
                                moved = True
                    for k in ids:
                        pts[k][0] = max(xmin, min(xmax, pts[k][0]))
                        pts[k][1] = max(ymin, min(ymax, pts[k][1]))
                    if not moved:
                        break
                for k in ids:
                    positions[k] = (pts[k][0], pts[k][1])

            if len(g) == 1:
                only_id = next(iter(g.nodes))
                positions[only_id] = (0.0, 0.0)
            elif center_id and center_id in g and len(g) <= 260:
                # Radial + spring hybrid for ego neighborhoods so the center node is anchored at (0, 0)
                pos_init: dict[str, tuple[float, float]] = {center_id: (0.0, 0.0)}
                others = [nid for nid in sorted(g.nodes) if nid != center_id]
                for idx, nid in enumerate(others):
                    angle = (2.0 * math.pi * idx) / max(1, len(others))
                    radius = 0.58 if g.has_edge(center_id, nid) else 0.86
                    pos_init[nid] = (radius * math.cos(angle), radius * math.sin(angle))
                computed = nx.spring_layout(
                    g,
                    pos=pos_init,
                    fixed=[center_id],
                    seed=LAYOUT_SEED,
                    iterations=65,
                    weight="weight",
                    scale=0.88,
                )
                min_d = min(0.18, 0.55 * math.sqrt(3.0 / max(1, len(g))))
                relax_box(computed, min_d, -0.88, 0.88, -0.88, 0.88, iters=70)
                positions[center_id] = (0.0, 0.0)
            else:
                # Component-aware deterministic layout:
                # 1. Separate connected components (len >= 2) from slice-level isolates (len == 1)
                #    so isolates never form a misleading outer ring or crush connected clusters.
                comps = sorted(
                    nx.connected_components(g),
                    key=lambda c: (-len(c), sorted(c)[0]),
                )
                connected_comps = [sorted(c) for c in comps if len(c) >= 2]
                isolates = sorted([next(iter(c)) for c in comps if len(c) == 1])

                has_isolates = len(isolates) > 0 and len(connected_comps) > 0
                main_ymin = -0.44 if has_isolates else -0.88
                main_ymax = 0.88

                large_comps = [c for c in connected_comps if len(c) >= 4]
                small_comps = [c for c in connected_comps if len(c) < 4]

                if len(connected_comps) == 1 and not isolates:
                    c = connected_comps[0]
                    sub = g.subgraph(c)
                    iters = 90 if len(c) <= 150 else 55
                    raw_p = nx.spring_layout(
                        sub,
                        seed=LAYOUT_SEED,
                        k=2.2 / math.sqrt(max(len(c), 1)),
                        iterations=iters,
                        weight="weight",
                    )
                    area = 1.76 * 1.76
                    min_d = min(0.22, 0.62 * math.sqrt(area / max(1, len(c))))
                    relax_box(raw_p, min_d, -0.88, 0.88, -0.88, 0.88, iters=90)
                else:
                    upper_ymin = 0.04 if small_comps else main_ymin
                    if large_comps:
                        total_large = sum(math.sqrt(len(c)) for c in large_comps)
                        cur_x = -0.88
                        for idx, c in enumerate(large_comps):
                            share = math.sqrt(len(c)) / max(1e-6, total_large)
                            w_box = 1.76 * share
                            x0 = cur_x + (0.035 if idx > 0 else 0.0)
                            x1 = cur_x + w_box - (0.035 if idx < len(large_comps) - 1 else 0.0)
                            cur_x += w_box
                            sub = g.subgraph(c)
                            raw_p = nx.spring_layout(
                                sub,
                                seed=LAYOUT_SEED + idx,
                                k=2.2 / math.sqrt(max(len(c), 1)),
                                iterations=85,
                                weight="weight",
                            )
                            area = max(0.1, (x1 - x0) * (main_ymax - upper_ymin))
                            min_d = min(0.20, 0.58 * math.sqrt(area / max(1, len(c))))
                            relax_box(raw_p, min_d, x0, x1, upper_ymin, main_ymax, iters=90)

                    if small_comps:
                        band_y0 = main_ymin
                        band_y1 = -0.04 if large_comps else main_ymax
                        cols = max(1, min(5, int(math.ceil(math.sqrt(len(small_comps) * 1.5)))))
                        rows = int(math.ceil(len(small_comps) / cols))
                        cell_w = 1.76 / cols
                        cell_h = (band_y1 - band_y0) / max(1, rows)
                        for idx, c in enumerate(small_comps):
                            r_idx = idx // cols
                            c_idx = idx % cols
                            cx = -0.88 + (c_idx + 0.5) * cell_w
                            cy = band_y1 - (r_idx + 0.5) * cell_h
                            span = min(0.11, cell_w * 0.28)
                            if len(c) == 2:
                                u, v = c[0], c[1]
                                if dig.has_edge(v, u) and not dig.has_edge(u, v):
                                    u, v = v, u
                                positions[u] = (cx - span, cy)
                                positions[v] = (cx + span, cy)
                            else:
                                for k_i, nid in enumerate(c):
                                    ang = (2.0 * math.pi * k_i) / len(c)
                                    positions[nid] = (
                                        cx + span * math.cos(ang),
                                        cy + span * 0.75 * math.sin(ang),
                                    )

                    if isolates:
                        iso_y0, iso_y1 = (-0.90, -0.56) if connected_comps else (-0.84, 0.84)
                        cols = max(6, min(15, int(math.ceil(math.sqrt(len(isolates) * 3.5)))))
                        rows = int(math.ceil(len(isolates) / cols))
                        for idx, nid in enumerate(isolates):
                            r_idx = idx // cols
                            c_idx = idx % cols
                            x = -0.88 + (1.76 * (c_idx + 0.5) / cols)
                            y = iso_y1 - ((iso_y1 - iso_y0) * (r_idx + 0.5) / max(1, rows))
                            positions[nid] = (x, y)

        nodes = [
            self._build_graph_node(
                raw,
                venue_map=venue_map,
                pos=positions.get(raw["id"], (0.0, 0.0)),
                deg=deg_counter[raw["id"]],
                strength=str_counter[raw["id"]],
            )
            for raw in raw_nodes
        ]
        nodes.sort(key=lambda item: (-item.score, item.id))

        edges = [
            GraphEdge(
                edge_id=e["edge_id"],
                relation=e["relation"],
                source=e["source"],
                target=e["target"],
                source_name=e.get("source_name"),
                target_name=e.get("target_name"),
                source_label=e.get("source_label"),
                target_label=e.get("target_label"),
                directed=e.get("directed", e["relation"] not in SYMMETRIC_RELATIONS),
                symmetric=e.get("symmetric", e["relation"] in SYMMETRIC_RELATIONS),
                evidence_kind=e.get("evidence_kind", "observed"),
                evidence_ids=e.get("evidence_ids", []),
                support_count=int(e.get("support_count", 1)),
                fractional_weight=e.get("fractional_weight"),
                method_version=e.get("method_version", ""),
                graph_version=e.get("graph_version", EXPECTED_GRAPH_VERSION),
                validation_status=e.get("validation_status", "accepted"),
                properties={k: _parse_json_prop(v) for k, v in e.get("properties", {}).items()},
            )
            for e in raw_edges
        ]
        return nodes, edges

    def search(
        self,
        query: str,
        *,
        labels: list[str] | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        venue: str | None = None,
        sector: str | None = None,
        limit: int = 30,
    ) -> SearchResponse:
        grouped_counts, raw_items = self.repo.search_nodes(
            query,
            labels=labels,
            year_min=year_min,
            year_max=year_max,
            venue=venue,
            sector=sector,
            limit=limit,
        )
        paper_ids = [r["id"] for r in raw_items if r.get("_label") == "Paper"]
        venue_map = self.repo.get_paper_venues(paper_ids) if paper_ids else {}

        results: list[SearchResultItem] = []
        for raw in raw_items:
            gnode = self._build_graph_node(raw, venue_map=venue_map)
            subtitle_parts = [gnode.label.value]
            if gnode.year:
                subtitle_parts.append(str(gnode.year))
            if gnode.venue:
                subtitle_parts.append(gnode.venue.replace("venue:", "").upper())
            if gnode.sector:
                subtitle_parts.append(gnode.sector)
            if gnode.country_code:
                subtitle_parts.append(gnode.country_code)
            if gnode.properties.get("orcid"):
                subtitle_parts.append(f"ORCID {gnode.properties['orcid']}")
            results.append(
                SearchResultItem(
                    id=gnode.id,
                    label=gnode.label,
                    name=gnode.name,
                    subtitle=" · ".join(subtitle_parts),
                    year=gnode.year,
                    sector=gnode.sector,
                    country_code=gnode.country_code,
                    venue=gnode.venue,
                    score=gnode.score,
                    url=gnode.url,
                    properties=gnode.properties,
                    full_metrics=gnode.full_metrics,
                )
            )

        # Sort by match rank first, then full-projection score descending
        rank_by_id = {r["id"]: int(r.get("_match_rank", 2)) for r in raw_items}
        results.sort(key=lambda item: (rank_by_id.get(item.id, 2), -item.score, item.name))

        return SearchResponse(
            query=query,
            total_matches=sum(grouped_counts.values()),
            grouped_counts=grouped_counts,
            results=results,
        )

    def get_view(
        self,
        view: str,
        *,
        limit: int | None = None,
        community_id: str | None = None,
        sector: str | None = None,
        cross_sector_only: bool = False,
        country_code: str | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        venue: str | None = None,
        topic_id: str | None = None,
        min_support: int = 1,
        min_weight: float = 0.0,
        include_isolates: bool = False,
        include_topics: bool = False,
        preset: str = "topic_taxonomy_ecosystem",
        relations: list[str] | None = None,
        node_labels: list[str] | None = None,
    ) -> GraphViewResponse:
        """Load one of the four primary exploration modes with server-side filters."""
        applied_filters = {
            "limit": limit,
            "community_id": community_id,
            "sector": sector,
            "cross_sector_only": cross_sector_only,
            "country_code": country_code,
            "year_min": year_min,
            "year_max": year_max,
            "venue": venue,
            "topic_id": topic_id,
            "min_support": min_support,
            "min_weight": min_weight,
            "include_isolates": include_isolates,
            "include_topics": include_topics,
            "preset": preset if view == "heterogeneous" else None,
        }

        if view == "researchers":
            node_limit = min(max(10, limit or 100), 250)
            default_unfiltered = (
                node_limit == 100
                and not community_id
                and min_support <= 1
                and min_weight <= 0.0
                and not include_isolates
                and "researchers" in self.store.network_views_data.get("views", {})
            )
            precomputed_pos: dict[str, tuple[float, float]] = {}
            if default_unfiltered:
                v_payload = self.store.network_views_data["views"]["researchers"]
                target_ids = [n["id"] for n in v_payload["nodes"]]
                precomputed_pos = {n["id"]: (float(n["x"]), float(n["y"])) for n in v_payload["nodes"]}
            elif community_id and community_id in self.store.researcher_communities:
                comm_members = self.store.researcher_communities[community_id]
                # Order community members by their full-projection degree_strength
                comm_sorted = sorted(
                    comm_members,
                    key=lambda nid: (
                        -float((self.store.get_node_metrics(nid) or {}).get("degree_strength", 0.0)),
                        nid,
                    ),
                )
                target_ids = comm_sorted[:node_limit]
            else:
                target_ids = self.store.get_top_node_ids("researcher_collaboration", "degree_strength", node_limit)

            nodes_by_id = self.repo.get_nodes_by_ids(target_ids)
            edges_raw = self.repo.get_induced_edges(
                list(nodes_by_id.keys()),
                relations=["COAUTHORED_WITH"],
                min_support=min_support,
                min_weight=min_weight,
                limit=1500,
            )
            if not include_isolates and (min_support > 1 or min_weight > 0.0):
                connected_ids = {e["source"] for e in edges_raw} | {e["target"] for e in edges_raw}
                raw_nodes = [n for nid, n in nodes_by_id.items() if nid in connected_ids]
            else:
                raw_nodes = list(nodes_by_id.values())

            nodes, edges = self._compute_layout_and_finalize(
                raw_nodes, edges_raw, precomputed_positions=precomputed_pos
            )
            return GraphViewResponse(
                view="researchers",
                title="Mode A — Researcher Collaboration Network",
                description="Derived COAUTHORED_WITH projection over resolved researchers sharing accepted core papers.",
                relation="COAUTHORED_WITH",
                directed=False,
                full_node_count=EXPECTED_NODES_BY_LABEL["Researcher"],
                full_edge_count=EXPECTED_EDGES_BY_RELATION["COAUTHORED_WITH"],
                displayed_node_count=len(nodes),
                displayed_edge_count=len(edges),
                score_name="Full-projection fractional collaboration strength",
                color_meaning="Louvain community membership (seed 17, resolution 0.8; palette repeats)",
                metric_scope_note="Node score, betweenness, PageRank, and community ID come from the full 32,189-researcher projection. Displayed degree counts only edges visible in the current canvas.",
                scientific_caveat="Each core paper with k official authors contributes 1/(k-1) to each resolved pair. Community colors use a repeating palette and do not prove identical community IDs.",
                layout_seed=LAYOUT_SEED,
                applied_filters=applied_filters,
                available_communities=self.store.get_available_communities("researchers", limit=25),
                nodes=nodes,
                edges=edges,
            )

        if view == "organizations":
            node_limit = min(max(10, limit or 60), 200)
            default_unfiltered = (
                node_limit == 60
                and not community_id
                and not sector
                and not cross_sector_only
                and not country_code
                and min_support <= 1
                and min_weight <= 0.0
                and not include_topics
                and "organizations" in self.store.network_views_data.get("views", {})
            )
            precomputed_pos = {}
            if default_unfiltered:
                v_payload = self.store.network_views_data["views"]["organizations"]
                target_ids = [n["id"] for n in v_payload["nodes"]]
                precomputed_pos = {n["id"]: (float(n["x"]), float(n["y"])) for n in v_payload["nodes"]}
                nodes_by_id = self.repo.get_nodes_by_ids(target_ids)
                raw_nodes = list(nodes_by_id.values())
                edges_raw = self.repo.get_induced_edges(
                    target_ids,
                    relations=["COLLABORATED_WITH"],
                    min_support=min_support,
                    min_weight=min_weight,
                    limit=1500,
                )
            elif community_id and community_id in self.store.organization_communities:
                comm_members = self.store.organization_communities[community_id][:node_limit]
                nodes_by_id = self.repo.get_nodes_by_ids(comm_members)
                raw_nodes = list(nodes_by_id.values())
                edges_raw = self.repo.get_induced_edges(
                    comm_members,
                    relations=["COLLABORATED_WITH"],
                    min_support=min_support,
                    min_weight=min_weight,
                    limit=1500,
                )
            else:
                raw_nodes, edges_raw = self.repo.get_organization_collaboration_subgraph(
                    sector=sector,
                    cross_sector_only=cross_sector_only,
                    country_code=country_code,
                    min_support=min_support,
                    min_weight=min_weight,
                    include_topics=include_topics,
                    limit=node_limit,
                )

            nodes, edges = self._compute_layout_and_finalize(
                raw_nodes, edges_raw, precomputed_positions=precomputed_pos
            )
            return GraphViewResponse(
                view="organizations",
                title="Mode B — Organization Collaboration Network",
                description="Derived COLLABORATED_WITH partnerships supported by distinct coauthors affiliated with distinct institutions.",
                relation="COLLABORATED_WITH",
                directed=False,
                full_node_count=EXPECTED_NODES_BY_LABEL["Organization"],
                full_edge_count=EXPECTED_EDGES_BY_RELATION["COLLABORATED_WITH"],
                displayed_node_count=len(nodes),
                displayed_edge_count=len(edges),
                score_name="Full-projection fractional collaboration strength",
                color_meaning="Organization sector (academia, industry, government, nonprofit, unknown)",
                metric_scope_note="Node score and rankings reflect the full 2,047-organization projection. Displayed degree reflects only currently visible links.",
                scientific_caveat="Affiliations reflect paper-specific authorship observations (73.71% coverage; fails 80% target), not current employment. A sole dual-affiliated author never creates an organization collaboration edge.",
                layout_seed=LAYOUT_SEED,
                applied_filters=applied_filters,
                available_communities=self.store.get_available_communities("organizations", limit=20),
                nodes=nodes,
                edges=edges,
            )

        if view == "citations":
            node_limit = min(max(10, limit or 80), 200)
            default_unfiltered = (
                node_limit == 80
                and year_min is None
                and year_max is None
                and not venue
                and not topic_id
                and "citations" in self.store.network_views_data.get("views", {})
            )
            precomputed_pos = {}
            if default_unfiltered:
                v_payload = self.store.network_views_data["views"]["citations"]
                target_ids = [n["id"] for n in v_payload["nodes"]]
                precomputed_pos = {n["id"]: (float(n["x"]), float(n["y"])) for n in v_payload["nodes"]}
                nodes_by_id = self.repo.get_nodes_by_ids(target_ids)
                raw_nodes = list(nodes_by_id.values())
                edges_raw = self.repo.get_induced_edges(
                    target_ids,
                    relations=["CITES"],
                    limit=1500,
                )
            else:
                raw_nodes, edges_raw = self.repo.get_citation_subgraph(
                    year_min=year_min,
                    year_max=year_max,
                    venue=venue,
                    topic_id=topic_id,
                    limit=node_limit,
                )

            nodes, edges = self._compute_layout_and_finalize(
                raw_nodes, edges_raw, precomputed_positions=precomputed_pos
            )
            return GraphViewResponse(
                view="citations",
                title="Mode C — Within-Corpus Citation Network",
                description="Directed CITES relationships (citing paper → cited paper) inside the AAAI/IJCAI 2021–2025 release corpus.",
                relation="CITES",
                directed=True,
                full_node_count=EXPECTED_NODES_BY_LABEL["Paper"],
                full_edge_count=EXPECTED_EDGES_BY_RELATION["CITES"],
                displayed_node_count=len(nodes),
                displayed_edge_count=len(edges),
                score_name="Within-corpus citation PageRank / degree",
                color_meaning="Publication edition year (2021–2025)",
                metric_scope_note="Citation scores reflect the full 13,617-paper / 7,308-edge in-scope citation projection without exposure-time normalization.",
                scientific_caveat="Arrows point from citing paper to cited paper. Counts measure references strictly inside this AAAI/IJCAI 2021–2025 corpus and must not be confused with global citation impact.",
                layout_seed=LAYOUT_SEED,
                applied_filters=applied_filters,
                available_communities=[],
                nodes=nodes,
                edges=edges,
            )

        # Mode D: Heterogeneous knowledge graph
        node_limit = min(max(20, limit or 120), 250)
        raw_nodes, edges_raw = self.repo.get_heterogeneous_subgraph(
            preset=preset,
            relations=relations,
            node_labels=node_labels,
            year_min=year_min,
            year_max=year_max,
            venue=venue,
            sector=sector,
            topic_id=topic_id,
            limit=node_limit,
        )
        nodes, edges = self._compute_layout_and_finalize(raw_nodes, edges_raw)
        return GraphViewResponse(
            view="heterogeneous",
            title="Mode D — Heterogeneous Knowledge Graph",
            description="Multi-entity exploration across Researchers, Papers, Organizations, Topics, and Venues.",
            relation="MULTI_RELATION",
            directed=True,
            full_node_count=EXPECTED_TOTAL_NODES,
            full_edge_count=EXPECTED_TOTAL_EDGES,
            displayed_node_count=len(nodes),
            displayed_edge_count=len(edges),
            score_name="Entity projection strength / degree",
            color_meaning="Entity label (Researcher, Paper, Organization, Topic, Venue)",
            metric_scope_note="Combines observed (R1–R4), inferred-topic (R5), curated-taxonomy (R6), and derived (R7–R10) relationships in a bounded subgraph.",
            scientific_caveat="Keep observed facts, inferred embedding topics, curated taxonomy, and derived social/profile edges distinct when interpreting multi-hop paths.",
            layout_seed=LAYOUT_SEED,
            applied_filters=applied_filters,
            available_communities=[],
            nodes=nodes,
            edges=edges,
        )

    def get_node_detail(self, node_id: str) -> NodeDetailResponse | None:
        raw_node = self.repo.get_node_by_id(node_id)
        if raw_node is None:
            return None

        label = raw_node.get("_label") or "Researcher"
        venue_map = self.repo.get_paper_venues([node_id]) if label == "Paper" else {}
        rel_counts = self.repo.get_node_relation_counts(node_id)
        total_deg = sum(rel_counts.values())

        gnode = self._build_graph_node(raw_node, venue_map=venue_map, deg=total_deg)
        raw_groups = self.repo.get_node_connected_groups(node_id, per_group_limit=15)
        connected_groups = [
            ConnectedEntityGroup(
                relation=g["relation"],
                direction=g["direction"],
                evidence_kind=g.get("evidence_kind") or "observed",
                total_count=int(g["total_count"]),
                items=g["items"],
            )
            for g in raw_groups
        ]

        # External links
        external_links: list[dict[str, str]] = []
        props = gnode.properties
        if props.get("official_url"):
            external_links.append({"label": "Official Proceedings Page", "url": str(props["official_url"])})
        if props.get("pdf_url"):
            external_links.append({"label": "Official PDF", "url": str(props["pdf_url"])})
        if props.get("doi"):
            doi_str = str(props["doi"])
            doi_url = doi_str if doi_str.startswith("http") else f"https://doi.org/{doi_str}"
            external_links.append({"label": f"DOI ({doi_str})", "url": doi_url})
        if props.get("openalex_id"):
            oa_id = str(props["openalex_id"])
            oa_url = oa_id if oa_id.startswith("http") else f"https://openalex.org/{oa_id}"
            external_links.append({"label": f"OpenAlex ({oa_id})", "url": oa_url})
        elif label in {"Researcher", "Organization"}:
            suffix = node_id.rsplit(":", 1)[-1]
            external_links.append({"label": f"OpenAlex ({suffix})", "url": f"https://openalex.org/{suffix}"})
        if props.get("orcid"):
            orcid_str = str(props["orcid"])
            orcid_url = orcid_str if orcid_str.startswith("http") else f"https://orcid.org/{orcid_str}"
            external_links.append({"label": f"ORCID ({orcid_str})", "url": orcid_url})
        if props.get("ror"):
            external_links.append({"label": "ROR Registry", "url": str(props["ror"])})

        # Topic portfolio for Organization or Researcher
        topic_portfolio: list[dict[str, Any]] = []
        if label == "Organization":
            topic_portfolio = self.store.org_topic_profiles.get(node_id, [])[:15]

        # Affiliation observations if ledger is loaded
        aff_obs: list[dict[str, Any]] = []
        if self.store.ensure_ledger_loaded():
            if label == "Researcher":
                aff_obs = self.store.affiliations_by_researcher.get(node_id, [])[:20]
            elif label == "Paper":
                aff_obs = self.store.affiliations_by_paper.get(node_id, [])[:20]
            elif label == "Organization":
                aff_obs = self.store.affiliations_by_org.get(node_id, [])[:20]

        notes: list[str] = []
        if label == "Researcher":
            notes.append(
                "Identity is scoped to OpenAlex author ID on DOI-matched works with compatible byline names and no conflicting observed ORCIDs."
            )
            notes.append(
                "Full-projection centrality metrics are computed over all 32,189 resolved researchers (COAUTHORED_WITH)."
            )
        elif label == "Organization":
            notes.append(
                "Affiliations represent paper-specific authorship observations, never current employment or blanket paper-level institution lists."
            )
        elif label == "Paper":
            if props.get("unresolved_author_reason"):
                notes.append(f"Unresolved authorship note: {props['unresolved_author_reason']}")
            notes.append(
                "Citation counts and PageRank measure strictly within-corpus AAAI/IJCAI 2021–2025 references."
            )
        elif label == "Topic":
            notes.append(
                "Topic assignments (HAS_TOPIC) are inferred from title/abstract embeddings (tau=0.2709, delta=0.02) and are provisional."
            )

        return NodeDetailResponse(
            node=gnode,
            relation_counts=rel_counts,
            total_degree=total_deg,
            connected_groups=connected_groups,
            affiliation_observations=aff_obs,
            topic_portfolio=topic_portfolio,
            external_links=external_links,
            scientific_notes=notes,
        )

    def get_neighbors(
        self,
        node_id: str,
        *,
        relations: list[str] | None = None,
        node_labels: list[str] | None = None,
        direction: str = "both",
        year_min: int | None = None,
        year_max: int | None = None,
        venue: str | None = None,
        sector: str | None = None,
        min_support: int = 1,
        min_weight: float = 0.0,
        limit: int = 60,
        include_induced_edges: bool = True,
    ) -> NeighborhoodResponse | None:
        raw_center = self.repo.get_node_by_id(node_id)
        if raw_center is None:
            return None

        total_incident, neighbor_nodes_raw, edges_raw = self.repo.get_neighborhood(
            node_id,
            relations=relations,
            node_labels=node_labels,
            direction=direction,
            year_min=year_min,
            year_max=year_max,
            venue=venue,
            sector=sector,
            min_support=min_support,
            min_weight=min_weight,
            limit=limit,
            include_induced_edges=include_induced_edges,
        )

        # Scope collaboration support through immutable evidence, never current profiles.
        narrowed = bool(venue or (year_min is not None and year_min > 2021) or (year_max is not None and year_max < 2025))
        if narrowed:
            if not self.store.ensure_ledger_loaded():
                from fastapi import HTTPException
                raise HTTPException(status_code=503, detail="Paper-specific neighborhood filter evidence unavailable")
            support_by_edge = {}
            paper_ids = set()
            for edge in edges_raw:
                support = set()
                if edge["relation"] == "AFFILIATED_WITH":
                    support.update(a["paper_id"] for a in self.store.affiliations_by_researcher_org.get((edge["source"], edge["target"]), []))
                for eid in edge.get("evidence_ids", []):
                    support.update(self.store.evidence_by_id.get(eid, {}).get("support_paper_ids", []))
                support.update(i for i in (edge["source"], edge["target"]) if i.startswith("paper:"))
                support_by_edge[edge["edge_id"]] = support
                paper_ids.update(support)
            if len(paper_ids) > 5000:
                from fastapi import HTTPException
                raise HTTPException(status_code=503, detail="Paper filter exceeds bounded evidence lookup; use a smaller neighborhood")
            paper_nodes = self.repo.get_nodes_by_ids(sorted(paper_ids))
            paper_venues = self.repo.get_paper_venues(sorted(paper_ids)) if venue else {}
            allowed = {pid for pid, paper in paper_nodes.items() if (year_min or 2021) <= paper.get("year", 0) <= (year_max or 2025) and (not venue or paper_venues.get(pid) == venue)}
            edges_raw = [edge for edge in edges_raw if edge["relation"] == "SUBTOPIC_OF" or support_by_edge[edge["edge_id"]] & allowed]
            incident_ids = {endpoint for edge in edges_raw for endpoint in (edge["source"], edge["target"])}
            neighbor_nodes_raw = [n for n in neighbor_nodes_raw if n["id"] in incident_ids]

        all_raw_nodes = [raw_center, *[n for n in neighbor_nodes_raw if n["id"] != node_id]]
        nodes, edges = self._compute_layout_and_finalize(
            all_raw_nodes,
            edges_raw,
            center_id=node_id,
        )
        center_gnode = next((n for n in nodes if n.id == node_id), nodes[0])

        return NeighborhoodResponse(
            center_id=node_id,
            center_node=center_gnode,
            total_incident_edges=total_incident,
            returned_neighbor_count=max(0, len(nodes) - 1),
            truncated=total_incident > sum(1 for edge in edges_raw if node_id in (edge["source"], edge["target"])),
            metric_scope_note="Scores, support counts and fractional weights retain full-period frozen meanings. A narrowed year/venue requires at least one accepted supporting paper in that window. The incident-edge total is a prefilter upper bound when paper evidence filtering is active; returned graph metrics describe only returned edges.",
            applied_filters={
                "relations": relations,
                "node_labels": node_labels,
                "direction": direction,
                "year_min": year_min,
                "year_max": year_max,
                "venue": venue,
                "sector": sector,
                "min_support": min_support,
                "min_weight": min_weight,
                "limit": limit,
                "include_induced_edges": include_induced_edges,
            },
            nodes=nodes,
            edges=edges,
        )

    def get_edge_detail(self, edge_id: str) -> GraphEdge | None:
        bundle = self.repo.get_edge_by_id(edge_id)
        if bundle is None:
            return None
        e = bundle["edge"]
        return GraphEdge(
            edge_id=e["edge_id"],
            relation=e["relation"],
            source=e["source"],
            target=e["target"],
            source_name=e.get("source_name"),
            target_name=e.get("target_name"),
            source_label=e.get("source_label"),
            target_label=e.get("target_label"),
            directed=e["directed"],
            symmetric=e["symmetric"],
            evidence_kind=e["evidence_kind"],
            evidence_ids=e["evidence_ids"],
            support_count=e["support_count"],
            fractional_weight=e.get("fractional_weight"),
            method_version=e["method_version"],
            graph_version=e["graph_version"],
            validation_status=e["validation_status"],
            properties={k: _parse_json_prop(v) for k, v in e.get("properties", {}).items()},
        )

    def get_edge_evidence(self, edge_id: str) -> EdgeEvidenceResponse | None:
        bundle = self.repo.get_edge_by_id(edge_id)
        if bundle is None:
            return None

        e_raw = bundle["edge"]
        s_raw = bundle["source_node"]
        t_raw = bundle["target_node"]

        nodes, edges = self._compute_layout_and_finalize(
            [s_raw, t_raw],
            [e_raw],
            precomputed_positions={s_raw["id"]: (-0.5, 0.0), t_raw["id"]: (0.5, 0.0)},
        )
        edge_model = edges[0]
        source_node = next(n for n in nodes if n.id == s_raw["id"])
        target_node = next(n for n in nodes if n.id == t_raw["id"])

        has_ledger = self.store.ensure_ledger_loaded()
        evidence_records: list[EvidenceRecordItem] = []
        support_paper_ids: list[str] = []
        support_edge_ids: list[str] = []

        if has_ledger:
            for evid in edge_model.evidence_ids:
                ev = self.store.evidence_by_id.get(evid)
                if ev:
                    evidence_records.append(
                        EvidenceRecordItem(
                            id=ev["id"],
                            kind=ev["kind"],
                            source_url=str(ev["source_url"]) if ev.get("source_url") else None,
                            retrieved_at=str(ev["retrieved_at"]) if ev.get("retrieved_at") else None,
                            raw_sha256=ev.get("raw_sha256"),
                            source_locator=ev.get("source_locator"),
                            excerpt=ev.get("excerpt"),
                            support_edge_ids=list(ev.get("support_edge_ids", [])),
                            support_paper_ids=list(ev.get("support_paper_ids", [])),
                        )
                    )
                    support_paper_ids.extend(ev.get("support_paper_ids", []))
                    support_edge_ids.extend(ev.get("support_edge_ids", []))

        # Deduplicate preserving order
        support_paper_ids = list(dict.fromkeys(support_paper_ids))
        support_edge_ids = list(dict.fromkeys(support_edge_ids))

        # For observed edges where one endpoint is a Paper, include that paper in supporting_papers
        if s_raw.get("_label") == "Paper" and s_raw["id"] not in support_paper_ids:
            support_paper_ids.insert(0, s_raw["id"])
        if t_raw.get("_label") == "Paper" and t_raw["id"] not in support_paper_ids:
            support_paper_ids.append(t_raw["id"])

        # Affiliation observations for AFFILIATED_WITH or COLLABORATED_WITH
        affiliation_observations: list[dict[str, Any]] = []
        if has_ledger:
            if edge_model.relation == "AFFILIATED_WITH":
                obs_list = self.store.affiliations_by_researcher_org.get(
                    (edge_model.source, edge_model.target), []
                )
                for obs in obs_list[:25]:
                    affiliation_observations.append(dict(obs))
                    if obs["paper_id"] not in support_paper_ids:
                        support_paper_ids.append(obs["paper_id"])
            elif edge_model.relation == "COLLABORATED_WITH":
                for pid in support_paper_ids[:15]:
                    for obs in self.store.affiliations_by_paper.get(pid, []):
                        if obs["organization_id"] in {edge_model.source, edge_model.target}:
                            affiliation_observations.append(dict(obs))

        supporting_papers: list[dict[str, Any]] = []
        if support_paper_ids:
            paper_nodes = self.repo.get_nodes_by_ids(support_paper_ids[:25])
            venue_map = self.repo.get_paper_venues(list(paper_nodes.keys()))
            for pid in support_paper_ids[:25]:
                p = paper_nodes.get(pid)
                if p:
                    supporting_papers.append({
                        "paper_id": pid,
                        "title": p.get("name", pid),
                        "year": p.get("year"),
                        "venue": venue_map.get(pid),
                        "doi": p.get("doi"),
                        "official_url": p.get("official_url"),
                        "pdf_url": p.get("pdf_url"),
                        "openalex_id": p.get("openalex_id"),
                    })
        elif edge_model.evidence_kind == "derived":
            supporting_papers = self.repo.resolve_derived_supporting_papers_cypher(
                edge_model.relation.value,
                edge_model.source,
                edge_model.target,
                limit=20,
            )

        # Fallback evidence records if graph.json was absent
        if not evidence_records:
            for evid in edge_model.evidence_ids:
                fallback_url = source_node.url or target_node.url
                evidence_records.append(
                    EvidenceRecordItem(
                        id=evid,
                        kind=edge_model.evidence_kind,
                        source_url=fallback_url,
                        source_locator="Resolved via Neo4j edge provenance metadata (local graph.json ledger not loaded)",
                        support_paper_ids=[p["paper_id"] for p in supporting_papers],
                    )
                )

        supporting_base_edges: list[dict[str, Any]] = []
        if support_edge_ids:
            supporting_base_edges = self.repo.get_edges_by_ids(support_edge_ids[:25])

        # Enrich affiliation observations with researcher/paper/organization names
        if affiliation_observations:
            lookup_ids: set[str] = set()
            for obs in affiliation_observations:
                lookup_ids.update([obs["researcher_id"], obs["paper_id"], obs["organization_id"]])
            entity_Lookup = self.repo.get_nodes_by_ids(list(lookup_ids))
            for obs in affiliation_observations:
                obs["researcher_name"] = entity_Lookup.get(obs["researcher_id"], {}).get("name", obs["researcher_id"])
                obs["paper_title"] = entity_Lookup.get(obs["paper_id"], {}).get("name", obs["paper_id"])
                obs["paper_year"] = entity_Lookup.get(obs["paper_id"], {}).get("year")
                obs["organization_name"] = entity_Lookup.get(obs["organization_id"], {}).get("name", obs["organization_id"])

        derivation_explanation = self._explain_edge(edge_model)
        limitations = [
            "Edge validation_status='accepted' means structural and source-rule checks passed; AI-assessed sample precision is 96.5% (human accuracy not established).",
        ]
        if edge_model.relation == "HAS_TOPIC":
            limitations.append(
                "Inferred topic assignment from sentence-transformer cosine similarity against taxonomy definitions; not an author-supplied keyword."
            )
        elif edge_model.relation in {"AFFILIATED_WITH", "COLLABORATED_WITH", "CONTRIBUTES_TO_TOPIC"}:
            limitations.append(
                "Affiliation evidence comes from authorship-aligned OpenAlex institutions on matched papers (73.71% overall position coverage) and does not represent employment history."
            )
        elif edge_model.relation == "CITES":
            limitations.append(
                "Within-corpus citation between matched AAAI/IJCAI 2021–2025 works; references outside this corpus are excluded."
            )

        return EdgeEvidenceResponse(
            edge=edge_model,
            source_node=source_node,
            target_node=target_node,
            ledger_source="artifact_ledger" if has_ledger else "neo4j_fallback",
            evidence_records=evidence_records,
            supporting_papers=supporting_papers,
            supporting_base_edges=supporting_base_edges,
            affiliation_observations=affiliation_observations,
            derivation_explanation=derivation_explanation,
            scientific_limitations=limitations,
        )

    def _explain_edge(self, edge: GraphEdge) -> str:
        rel = edge.relation.value
        sc = edge.support_count
        fw = edge.fractional_weight
        if rel == "AUTHORED":
            pos = edge.properties.get("byline_position", "?")
            rname = edge.properties.get("roster_name", "")
            return f"Observed authorship at byline position {pos} (roster name: {rname!r}) matched to OpenAlex work and author ID."
        if rel == "AFFILIATED_WITH":
            raw_strs = edge.properties.get("raw_affiliation_strings", [])
            return f"Aggregated over {sc} accepted author–paper–organization triple(s). Raw affiliation strings: {raw_strs}."
        if rel == "PUBLISHED_IN":
            return f"Official proceedings inclusion in {edge.target} ({edge.properties.get('year', '')}) from roster v10."
        if rel == "CITES":
            return "Observed reference in OpenAlex referenced_works resolving to an in-scope matched AAAI/IJCAI paper."
        if rel == "HAS_TOPIC":
            cos = edge.properties.get("cosine_similarity")
            tau = edge.properties.get("threshold_tau")
            cos_str = f"{float(cos):.4f}" if isinstance(cos, (int, float)) else str(cos)
            tau_str = f"{float(tau):.4f}" if isinstance(tau, (int, float)) else str(tau)
            return f"Inferred leaf topic via sentence-embedding cosine similarity ({cos_str} ≥ τ={tau_str})."
        if rel == "SUBTOPIC_OF":
            return "Curated taxonomy hierarchy mapping leaf topic to parent category."
        if rel == "COAUTHORED_WITH":
            fw_str = f"{fw:.4f}" if isinstance(fw, (int, float)) else "N/A"
            return f"Derived from {sc} shared core paper(s); summed fractional collaboration weight = {fw_str} (each paper with k official authors contributes 1/(k-1))."
        if rel == "COLLABORATED_WITH":
            fw_str = f"{fw:.4f}" if isinstance(fw, (int, float)) else "N/A"
            return f"Derived from {sc} shared core paper(s) with distinct authors affiliated with each organization; fractional weight = {fw_str}."
        if rel == "RESEARCHES_TOPIC":
            return f"Derived researcher topic profile backed by {sc} distinct authored core papers labeled with this topic (minimum threshold: 2)."
        if rel == "CONTRIBUTES_TO_TOPIC":
            return f"Derived organization topic profile backed by {sc} distinct core papers with aligned author affiliation and topic label (minimum threshold: 3)."
        return "Accepted relationship in release graph v4."

    def get_analytics_overview(self) -> dict[str, Any]:
        """Return precomputed full-graph analytics from reports/release-v4/analysis.json."""
        analysis = self.store.analysis_data
        if not analysis or not analysis.get("release_metrics"):
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Frozen analytics artifact unavailable")
        rm = analysis.get("release_metrics", {})
        projections = analysis.get("projections", {})
        robustness = analysis.get("robustness", {})

        derived = analysis.get("explorer_derived")
        derived_path = REPO_ROOT / "reports/explorer-analysis-release-v1/derived.json"
        if derived is None and derived_path.is_file():
            derived = json.loads(derived_path.read_bytes())
        if derived and derived.get("graph_sha256") != analysis.get("input_sha256"):
            derived = None  # Never serve an extension for another graph.

        proj_summaries = {}
        for name, p in projections.items():
            proj_summaries[name] = {
                "node_count": p.get("node_count"),
                "edge_count": p.get("edge_count"),
                "directed": p.get("directed"),
                "density": p.get("density"),
                "isolate_count": p.get("isolate_count"),
                "degree_mean": p.get("degree_mean"),
                "degree_max": p.get("degree_max"),
                "top_degree_strength": p.get("top_degree_strength", [])[:15],
                "top_betweenness": p.get("top_betweenness", [])[:20],
                "component_sizes": p.get("weak_or_undirected_component_sizes", []),
                "top_pagerank": p.get("top_pagerank", [])[:15],
            }

        return {
            "graph_version": analysis.get("graph_version"),
            "provenance": {"analysis_input_sha256": analysis.get("input_sha256"), "analysis_config_sha256": analysis.get("analysis_config_sha256"), "quality_config_sha256": analysis.get("quality_config_sha256"), "run_at": analysis.get("run_at")},
            "analysis_method_version": analysis.get("analysis_method_version"),
            "evidence_scope": rm.get("evidence_scope", ""),
            "quality": self._build_quality_contract(),
            "explorer_derived": derived,
            "projections": proj_summaries,
            "annual_counts": rm.get("annual_counts", {}),
            "researcher_degree_ccdf": rm.get("researcher_degree_ccdf", {}),
            "researcher_component_sizes": {
                "projection": rm.get("researcher_component_sizes", {}).get("projection"),
                "component_count": rm.get("researcher_component_sizes", {}).get("component_count"),
                "top_sizes": rm.get("researcher_component_sizes", {}).get("sizes_descending", [])[:25],
            },
            "sector_mixing": rm.get("sector_mixing", {}),
            "country_pair_collaborations": {
                "counting_rule": rm.get("country_pair_collaborations", {}).get("counting_rule"),
                "rows": rm.get("country_pair_collaborations", {}).get("rows", [])[:25],
            },
            "topic_shares_by_year_venue": rm.get("topic_shares_by_year_venue", {}),
            "cited_papers": rm.get("cited_papers", {}),
            "bridge_researchers": rm.get("bridge_researchers", {}),
            "academia_industry_pairs": rm.get("academia_industry_topic_pair_candidates", [])[:25],
            "organization_topic_candidates": rm.get("organization_topic_comparison_candidates", [])[:25],
            "robustness": {
                "strict_evidence_filter_status": robustness.get("strict_evidence_filter_status"),
                "sensitivity_comparison": robustness.get("sensitivity_comparison"),
                "per_projection": robustness.get("per_projection", {}),
                "strict_evidence_filter_sha256": robustness.get("strict_evidence_filter_sha256"),
                "strict_projections": {name: {key: p.get(key) for key in ("node_count", "edge_count", "isolate_count", "weak_or_undirected_component_sizes", "top_betweenness")} for name, p in analysis.get("strict_projections", {}).items() if name in ("researcher_collaboration", "organization_collaboration")},
            },
            "limitations": analysis.get("limitations", SCIENTIFIC_CAVEATS),
        }

    def find_path(self, req: PathRequest) -> PathResponse:
        if req.source_id == req.target_id:
            raw_node = self.repo.get_node_by_id(req.source_id)
            nodes, _ = self._compute_layout_and_finalize([raw_node] if raw_node else [], [])
            return PathResponse(
                source_id=req.source_id,
                target_id=req.target_id,
                mode=req.mode,
                max_hops=req.max_hops,
                found=bool(nodes),
                hop_count=0,
                direction_note="Source and target are the same entity.",
                nodes=nodes,
                edges=[],
                step_descriptions=["Source and target are identical."],
            )

        raw_nodes, raw_edges = self.repo.find_shortest_path(
            req.source_id,
            req.target_id,
            mode=req.mode,
            max_hops=req.max_hops,
        )
        if not raw_nodes:
            return PathResponse(
                source_id=req.source_id,
                target_id=req.target_id,
                mode=req.mode,
                max_hops=req.max_hops,
                found=False,
                hop_count=0,
                direction_note=self._path_direction_note(req.mode),
                nodes=[],
                edges=[],
                step_descriptions=[],
            )

        # Position path nodes linearly from left to right for clear visual inspection
        pos_map: dict[str, tuple[float, float]] = {}
        n_count = len(raw_nodes)
        for idx, rn in enumerate(raw_nodes):
            x = -0.8 + (1.6 * idx / max(1, n_count - 1))
            y = 0.12 * (1 if idx % 2 == 1 else -1) if 0 < idx < n_count - 1 else 0.0
            pos_map[rn["id"]] = (x, y)

        nodes, edges = self._compute_layout_and_finalize(
            raw_nodes, raw_edges, precomputed_positions=pos_map, preserve_exact_positions=True
        )
        # Preserve path order for nodes
        order_index = {rn["id"]: i for i, rn in enumerate(raw_nodes)}
        nodes.sort(key=lambda item: order_index.get(item.id, 999))

        steps: list[str] = []
        for edge in edges:
            arrow = "↔" if edge.symmetric else "→"
            steps.append(
                f"{edge.source_name or edge.source} —[{edge.relation.value} ({edge.evidence_kind.value})]{arrow} {edge.target_name or edge.target}"
            )

        return PathResponse(
            source_id=req.source_id,
            target_id=req.target_id,
            mode=req.mode,
            max_hops=req.max_hops,
            found=True,
            hop_count=len(edges),
            direction_note=self._path_direction_note(req.mode),
            nodes=nodes,
            edges=edges,
            step_descriptions=steps,
        )

    def _path_direction_note(self, mode: str) -> str:
        if mode == "citation_directed":
            return "Directed citation path: every step follows CITES from citing paper to cited paper."
        if mode == "citation_undirected":
            return "Undirected citation chain: traverses CITES links in either direction; this alone does not establish co-citation or bibliographic coupling."
        if mode == "collaboration":
            return "Undirected collaboration path across COAUTHORED_WITH, COLLABORATED_WITH, AUTHORED, and AFFILIATED_WITH."
        return "Heterogeneous knowledge graph path across accepted release relationships."

    def compare_nodes(self, left_id: str, right_id: str) -> CompareResponse | None:
        left_raw = self.repo.get_node_by_id(left_id)
        right_raw = self.repo.get_node_by_id(right_id)
        if not left_raw or not right_raw:
            return None

        comp = self.repo.compare_entities(left_id, right_id)
        left_node = self._build_graph_node(left_raw)
        right_node = self._build_graph_node(right_raw)
        _, direct_edges = self._compute_layout_and_finalize([left_raw, right_raw], comp["direct_edges"])
        shared_neighbors = [self._build_graph_node(sn) for sn in comp["shared_neighbors"]]

        if left_node.label == "Organization" and right_node.label == "Organization":
            support = set()
            if not self.store.ensure_ledger_loaded():
                from fastapi import HTTPException
                raise HTTPException(status_code=503, detail="Organization co-publication evidence unavailable")
            if self.store.ensure_ledger_loaded():
                for edge in direct_edges:
                    if edge.relation == "COLLABORATED_WITH":
                        for eid in edge.evidence_ids:
                            support.update(self.store.evidence_by_id.get(eid, {}).get("support_paper_ids", []))
            paper_nodes = self.repo.get_nodes_by_ids(sorted(support)[:100])
            comp["shared_papers"] = [{"paper_id": pid, "title": raw.get("name", pid), "year": raw.get("year"), "official_url": raw.get("official_url"), "doi": raw.get("doi")} for pid, raw in paper_nodes.items()]

        left_topics = self.store.org_topic_profiles.get(left_id, [])[:10]
        right_topics = self.store.org_topic_profiles.get(right_id, [])[:10]

        notes = [
            "Shared papers and collaboration weights are computed strictly from accepted core-paper support in release v4.",
            "Topic portfolios use fractional allocation across accepted inferred leaf labels. Organization shared papers resolve accepted R8 evidence only (up to 100); shared-neighbor results are bounded to 30 and are not complete unique-neighbor counts.",
        ]
        return CompareResponse(
            left_node=left_node,
            right_node=right_node,
            direct_edges=direct_edges,
            shared_neighbors=shared_neighbors,
            shared_papers=comp["shared_papers"],
            left_topics=left_topics,
            right_topics=right_topics,
            comparison_notes=notes,
        )

    def get_table_nodes(
        self,
        *,
        label: str | None = None,
        query: str = "",
        year_min: int | None = None,
        year_max: int | None = None,
        sector: str | None = None,
        venue: str | None = None,
        sort_by: str = "score",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 25,
    ) -> TableNodesResponse:
        safe_size = min(max(1, int(page_size)), 100)
        safe_page = max(1, int(page))

        # When sorting by full-projection `score` on a single projection label with no text filter,
        # use the precomputed full-projection score ordering for true global top-N pagination!
        proj_for_label = {
            "Researcher": "researcher_collaboration",
            "Organization": "organization_collaboration",
            "Paper": "core_citations",
            "Topic": "paper_topics",
        }.get(label or "")

        if sort_by == "score" and proj_for_label and not query.strip() and year_min is None and year_max is None and not sector and not venue:
            proj_data = self.store.analysis_data.get("projections", {}).get(proj_for_label, {})
            scores_map = proj_data.get("centrality_scores", {}).get("degree_strength", {})
            if scores_map:
                reverse = sort_order.lower() != "asc"
                sorted_ids = [
                    nid
                    for nid, _ in sorted(
                        scores_map.items(),
                        key=lambda item: (float(item[1]), item[0]),
                        reverse=reverse,
                    )
                    if nid.startswith(f"{label.lower()}:")
                ]
                total = len(sorted_ids)
                start = (safe_page - 1) * safe_size
                page_ids = sorted_ids[start : start + safe_size]
                nodes_by_id = self.repo.get_nodes_by_ids(page_ids)
                venue_map = self.repo.get_paper_venues(page_ids) if label == "Paper" else {}
                deg_lookup = getattr(self.repo, "get_nodes_degree_counts", lambda _ids: {})(page_ids)
                items = [
                    self._build_graph_node(
                        nodes_by_id[nid],
                        venue_map=venue_map,
                        deg=int(deg_lookup.get(nid, 0)),
                    )
                    for nid in page_ids
                    if nid in nodes_by_id
                ]
                total_pages = max(1, math.ceil(total / safe_size))
                return TableNodesResponse(
                    total=total,
                    page=safe_page,
                    page_size=safe_size,
                    total_pages=total_pages,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    items=items,
                )

        total, raw_items = self.repo.query_table_nodes(
            label=label,
            query=query,
            year_min=year_min,
            year_max=year_max,
            sector=sector,
            venue=venue,
            sort_by=sort_by,
            sort_order=sort_order,
            page=safe_page,
            page_size=safe_size,
        )
        paper_ids = [r["id"] for r in raw_items if r.get("_label") == "Paper"]
        venue_map = self.repo.get_paper_venues(paper_ids) if paper_ids else {}
        row_ids = [r["id"] for r in raw_items if "id" in r]
        deg_lookup = getattr(self.repo, "get_nodes_degree_counts", lambda _ids: {})(row_ids)
        items = [
            self._build_graph_node(
                r,
                venue_map=venue_map,
                deg=int(deg_lookup.get(r["id"], 0)),
            )
            for r in raw_items
        ]
        if sort_by == "score":
            items.sort(key=lambda item: item.score, reverse=(sort_order.lower() != "asc"))

        total_pages = max(1, math.ceil(total / safe_size))
        return TableNodesResponse(
            total=total,
            page=safe_page,
            page_size=safe_size,
            total_pages=total_pages,
            sort_by=sort_by,
            sort_order=sort_order,
            items=items,
        )

    def get_table_edges(
        self,
        *,
        relation: str | None = None,
        evidence_kind: str | None = None,
        query: str = "",
        min_support: int = 1,
        min_weight: float = 0.0,
        sort_by: str = "support_count",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 25,
    ) -> TableEdgesResponse:
        safe_size = min(max(1, int(page_size)), 100)
        safe_page = max(1, int(page))
        total, raw_edges = self.repo.query_table_edges(
            relation=relation,
            evidence_kind=evidence_kind,
            query=query,
            min_support=min_support,
            min_weight=min_weight,
            sort_by=sort_by,
            sort_order=sort_order,
            page=safe_page,
            page_size=safe_size,
        )
        _, edges = self._compute_layout_and_finalize([], raw_edges)
        total_pages = max(1, math.ceil(total / safe_size))
        return TableEdgesResponse(
            total=total,
            page=safe_page,
            page_size=safe_size,
            total_pages=total_pages,
            sort_by=sort_by,
            sort_order=sort_order,
            items=edges,
        )
