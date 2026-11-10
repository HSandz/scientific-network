export type NodeLabel = "Researcher" | "Paper" | "Organization" | "Topic" | "Venue";

export type RelationType =
  | "AUTHORED"
  | "AFFILIATED_WITH"
  | "PUBLISHED_IN"
  | "CITES"
  | "HAS_TOPIC"
  | "SUBTOPIC_OF"
  | "COAUTHORED_WITH"
  | "COLLABORATED_WITH"
  | "RESEARCHES_TOPIC"
  | "CONTRIBUTES_TO_TOPIC";

export type EvidenceKind = "observed" | "inferred_topic" | "curated_taxonomy" | "derived";

export type ViewMode = "researchers" | "organizations" | "citations" | "heterogeneous";

export type WorkspaceTab = "graph" | "table" | "analytics";

export type LayoutMode = "seeded" | "circular" | "concentric";

export type EdgeFilterMode = "all" | "strong" | "connected";

export type GraphViewScopeKind = "overview" | "ego" | "path";

export interface GraphViewScope {
  kind: GraphViewScopeKind;
  title: string;
  description?: string;
  centerId?: string | null;
  transient?: boolean;
  neighborParams?: Record<string, unknown>;
  pathData?: {
    sourceId: string;
    targetId: string;
    sourceName?: string;
    targetName?: string;
    mode?: string;
    maxHops?: number;
    hopCount: number;
    steps: string[];
  } | null;
  priorState?: {
    viewMode: ViewMode;
    selectedNodeId: string | null;
    cameraState?: { x: number; y: number; ratio: number } | null;
    extraNodes: GraphNode[];
    extraEdges: GraphEdge[];
    graphViewScope: {
      kind: GraphViewScopeKind;
      title: string;
      description?: string;
      centerId?: string | null;
    };
  } | null;
}

export interface FullProjectionMetrics {
  projection?: string | null;
  degree_strength?: number | null;
  betweenness?: number | null;
  pagerank?: number | null;
  in_degree?: number | null;
  out_degree?: number | null;
  community_id?: string | null;
  community_size?: number | null;
  community_rank?: number | null;
}

export interface GraphNode {
  id: string;
  label: NodeLabel;
  name: string;
  group: string;
  score: number;
  displayed_neighbor_count?: number;
  displayed_degree: number;
  displayed_strength: number;
  x: number;
  y: number;
  year?: number | null;
  sector?: string | null;
  country_code?: string | null;
  venue?: string | null;
  url?: string | null;
  properties: Record<string, unknown>;
  full_metrics?: FullProjectionMetrics | null;
}

export interface GraphEdge {
  edge_id: string;
  relation: RelationType;
  source: string;
  target: string;
  source_name?: string | null;
  target_name?: string | null;
  source_label?: string | null;
  target_label?: string | null;
  directed: boolean;
  symmetric: boolean;
  evidence_kind: EvidenceKind;
  evidence_ids: string[];
  support_count: number;
  fractional_weight?: number | null;
  method_version: string;
  graph_version: string;
  validation_status: string;
  properties: Record<string, unknown>;
}

export interface HealthResponse {
  status: "ok" | "degraded" | "error";
  neo4j_connected: boolean;
  neo4j_endpoint: string;
  expected_graph_version: string;
  observed_graph_versions: string[];
  database_verified: boolean;
  total_nodes: number;
  total_edges: number;
  warnings: string[];
  artifacts: Record<string, boolean>;
}

export interface QualityContract {
  edge_precision?: number;
  edge_precision_ai_assessed?: number;
  edge_precision_correct?: number;
  edge_precision_total?: number;
  edge_precision_incorrect?: number;
  edge_precision_unverifiable?: number;
  edge_precision_wilson_lower?: number;
  edge_precision_wilson_upper?: number;
  edge_precision_wilson_95?: [number, number];
  edge_precision_target?: number;
  edge_precision_wilson_target?: number;
  edge_precision_status?: string;
  macro_per_type_precision?: number;
  overlap_reviewed?: number;
  overlap_agreed?: number;
  overlap_agreement_rate?: number;
  cohens_kappa?: number;
  affiliation_coverage?: number;
  affiliation_positions_resolved?: number;
  affiliation_positions_eligible?: number;
  affiliation_positions_all_official?: number;
  affiliation_positions_accepted?: number;
  affiliation_conditional_coverage?: number;
  affiliation_papers_with_edge?: number;
  affiliation_papers_eligible?: number;
  affiliation_target?: number;
  affiliation_coverage_target?: number;
  affiliation_status?: string;
  affiliation_coverage_status?: string;
  abstract_coverage?: number;
  abstract_papers_resolved?: number;
  abstract_papers_eligible?: number;
  abstract_coverage_target?: number;
  abstract_coverage_status?: string;
  openalex_work_match_rate?: number;
  topic_coverage?: number;
  topic_papers_labeled?: number;
  topic_papers_eligible?: number;
  topic_papers_abstained?: number;
  topic_coverage_target?: number;
  topic_coverage_status?: string;
  topic_precision?: number;
  topic_precision_true_positive?: number;
  topic_precision_predicted_labels?: number;
  topic_embedding_precision?: number;
  topic_precision_target?: number;
  topic_precision_status?: string;
  topic_micro_f1?: number;
  topic_embedding_micro_f1?: number;
  topic_phrase_baseline_f1?: number;
  topic_phrase_baseline_precision?: number;
  topic_test_paper_count?: number;
  topic_eval_status?: string;
  evaluation_kind?: string;
  human_validation_performed?: boolean;
  reviewer_independence_established?: boolean;
  verified_course_accuracy_established?: boolean;
  verified_course_accuracy?: string;
  numeric_gate_scope?: string;
}

export interface GraphSummaryResponse {
  graph_version: string;
  graph_sha256: string;
  database_verified: boolean;
  warnings: string[];
  nodes_by_label: Record<string, number>;
  edges_by_relation: Record<string, number>;
  edges_by_evidence_kind: Record<string, number>;
  total_nodes: number;
  total_edges: number;
  unique_core_factual_edges: number;
  core_papers: number;
  resolved_core_researchers: number;
  quality: QualityContract;
  size_gates: Record<string, unknown>;
  scientific_caveats: string[];
}

export interface CommunityOption {
  community_id: string;
  rank: number;
  member_count: number;
  paper_count?: number;
  top_topics?: Array<{
    topic_id: string;
    topic: string;
    paper_count: number;
    share_of_fractional_topic_mass: number;
  }>;
  label: string;
}

export interface GraphViewResponse {
  view: string;
  title: string;
  description: string;
  relation: string;
  directed: boolean;
  full_node_count: number;
  full_edge_count: number;
  displayed_node_count: number;
  displayed_edge_count: number;
  score_name: string;
  color_meaning: string;
  metric_scope_note: string;
  scientific_caveat: string;
  layout_seed: number;
  applied_filters: Record<string, unknown>;
  available_communities: CommunityOption[];
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface SearchResultItem {
  id: string;
  label: NodeLabel;
  name: string;
  subtitle?: string | null;
  year?: number | null;
  sector?: string | null;
  country_code?: string | null;
  venue?: string | null;
  score: number;
  url?: string | null;
  properties: Record<string, unknown>;
  full_metrics?: FullProjectionMetrics | null;
}

export interface SearchResponse {
  query: string;
  total_matches: number;
  grouped_counts: Record<string, number>;
  results: SearchResultItem[];
}

export interface ConnectedEntityGroup {
  relation: RelationType;
  direction: "outgoing" | "incoming" | "undirected";
  evidence_kind: EvidenceKind;
  total_count: number;
  items: Array<{
    edge_id: string;
    neighbor_id: string;
    neighbor_name: string;
    neighbor_label: NodeLabel;
    year?: number | null;
    sector?: string | null;
    support_count: number;
    fractional_weight?: number | null;
    byline_position?: number | null;
    cosine_similarity?: number | null;
  }>;
}

export interface NodeDetailResponse {
  node: GraphNode;
  relation_counts: Record<string, number>;
  total_degree: number;
  connected_groups: ConnectedEntityGroup[];
  affiliation_observations: Array<Record<string, unknown>>;
  topic_portfolio: Array<{
    organization_id: string;
    organization: string;
    sector: string;
    topic_id: string;
    topic: string;
    supported_paper_count: number;
    fractional_topic_portfolio_share: number;
  }>;
  external_links: Array<{ label: string; url: string }>;
  scientific_notes: string[];
}

export interface NeighborhoodResponse {
  center_id: string;
  center_node: GraphNode;
  total_incident_edges: number;
  returned_neighbor_count: number;
  truncated: boolean;
  metric_scope_note: string;
  applied_filters: Record<string, unknown>;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface EvidenceRecordItem {
  id: string;
  kind: EvidenceKind;
  source_url?: string | null;
  retrieved_at?: string | null;
  raw_sha256?: string | null;
  source_locator?: string | null;
  excerpt?: string | null;
  support_edge_ids: string[];
  support_paper_ids: string[];
}

export interface EdgeEvidenceResponse {
  edge: GraphEdge;
  source_node: GraphNode;
  target_node: GraphNode;
  ledger_source: "artifact_ledger" | "neo4j_fallback";
  evidence_records: EvidenceRecordItem[];
  supporting_papers: Array<{
    paper_id: string;
    title: string;
    year?: number | null;
    venue?: string | null;
    doi?: string | null;
    official_url?: string | null;
    pdf_url?: string | null;
    openalex_id?: string | null;
  }>;
  supporting_base_edges: GraphEdge[];
  affiliation_observations: Array<{
    id: string;
    researcher_id: string;
    researcher_name?: string;
    paper_id: string;
    paper_title?: string;
    paper_year?: number;
    organization_id: string;
    organization_name?: string;
    evidence_ids: string[];
  }>;
  derivation_explanation: string;
  scientific_limitations: string[];
}

export interface PathResponse {
  source_id: string;
  target_id: string;
  mode: string;
  max_hops: number;
  found: boolean;
  hop_count: number;
  direction_note: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  step_descriptions: string[];
}

export interface CompareResponse {
  left_node: GraphNode;
  right_node: GraphNode;
  direct_edges: GraphEdge[];
  shared_neighbors: GraphNode[];
  shared_papers: Array<{
    paper_id: string;
    title: string;
    year?: number | null;
    venue?: string | null;
    doi?: string | null;
    official_url?: string | null;
  }>;
  left_topics: Array<{
    topic_id: string;
    topic: string;
    supported_paper_count: number;
    fractional_topic_portfolio_share: number;
  }>;
  right_topics: Array<{
    topic_id: string;
    topic: string;
    supported_paper_count: number;
    fractional_topic_portfolio_share: number;
  }>;
  comparison_notes: string[];
}

export interface TableNodesResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  sort_by: string;
  sort_order: string;
  items: GraphNode[];
}

export interface TableEdgesResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  sort_by: string;
  sort_order: string;
  items: GraphEdge[];
}
