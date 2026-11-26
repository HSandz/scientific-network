export interface TrendYearPoint {
  year: number;
  papers: number;
  share: number;
  yoy?: number | null;
}

export interface TrendRow {
  kind: "Topic" | "Method" | "Task" | "Dataset";
  id: string;
  name: string;
  class: string;
  total_papers: number;
  base_window_papers: number;
  recent_window_papers: number;
  base_share: number;
  recent_share: number;
  recent_over_base_share: number;
  slope_of_share: number;
  slope_p_value: number;
  cagr_of_share_2021_2025: number;
  yearly: TrendYearPoint[];
  period_yearly?: TrendYearPoint[];
  period_papers?: number;
  period_delta_pp?: number;
  display_aliases?: string[];
}

export interface MetricDefinition {
  name: string;
  definition: string;
  denominator: string;
  network: string;
  graph_version: string;
}

export interface TrendsResponse {
  kind: "Topic" | "Method" | "Task" | "Dataset";
  venue: string;
  venue_note?: string | null;
  period: string;
  classification_note: string;
  caveats: string[];
  classes: Record<string, number>;
  total_matching: number;
  leaderboards: {
    rising: TrendRow[];
    emerging: TrendRow[];
    declining: TrendRow[];
  };
  heatmap: Array<{
    id: string;
    name: string;
    class: string;
    years: TrendYearPoint[];
  }>;
  items: TrendRow[];
  metric_definitions: Record<string, MetricDefinition>;
}

export interface SubjectListItem {
  id: string;
  name: string;
  kind: "Topic" | "Method" | "Task" | "Dataset";
  class: string;
  total_papers: number;
  recent_share: number;
  cagr: number;
  has_ppr: boolean;
  display_aliases: string[];
  /** Yearly share of papers, 2021 to 2025, as fractions. */
  shares: number[];
}

export interface SubjectDetailResponse {
  id: string;
  name: string;
  kind: string;
  trend?: TrendRow | null;
  classification_note: string;
  display_aliases: string[];
  /** Organizations with at least min_org_papers on the subject, ranked by specialisation. */
  leading_groups: Array<{ id: string; name: string; specialisation: number; subject_papers: number; total_papers: number }>;
  min_org_papers: number;
  /** Subjects sharing two or more papers, per kind; null without a live graph. */
  co_mentions: Record<"Method" | "Task" | "Dataset", Array<{ id: string; name: string; co_papers: number }>> | null;
  researcher_evidence: { min_papers: number; max_papers: number; ranked: Array<{ id: string; name: string; subject_papers: number }> } | null;
  description: {
    text: string;
    source_kind?: string | null;
    label: string;
    wikipedia_url?: string | null;
    wikipedia_revision_id?: number | string | null;
    attribution?: string | null;
    license?: string | null;
  } | null;
  ppr_primary_rank_by: string;
  ppr_source?: "precomputed" | "on_demand" | "rca_fallback" | null;
  ppr_method_note?: string | null;
  filter_notes: Record<string, string>;
  top_organizations: Array<{
    id: string;
    name: string;
    ppr_score?: number;
    score?: number;
    global_pagerank?: number;
    lift?: number;
    rca?: number;
    subject_papers?: number;
    total_papers?: number;
  }>;
  top_researchers: Array<{
    id: string;
    name: string;
    ppr_score?: number;
    global_pagerank?: number;
    lift?: number;
    rca?: number;
    subject_papers?: number;
    total_papers?: number;
  }>;
  related_methods: Array<{ id: string; name: string; score?: number; co_papers?: number }>;
  related_tasks: Array<{ id: string; name: string; score?: number; co_papers?: number }>;
  related_datasets: Array<{ id: string; name: string; score?: number; co_papers?: number }>;
  communities: Array<{
    community_id: string;
    source: string;
    level: number;
    title: string;
    summary: string;
    key_findings: Array<{ claim: string; paper_ids: string[] }>;
    rating?: number;
    ai_generated_label: string;
  }>;
  most_cited_papers: Array<{
    paper_id: string;
    title: string;
    year: number;
    venue?: string;
    in_corpus_citations: number;
  }>;
  summary?: {
    text: string;
    findings: Array<{ claim: string; paper_ids: string[] }>;
    source_community_id?: string | null;
    label: string;
    source_kind?: string;
    wikipedia_url?: string | null;
    wikipedia_revision_id?: number | string | null;
    attribution?: string | null;
  } | null;
  metric_definitions: Record<string, MetricDefinition>;
}

export interface GroupsResponse {
  summary: Record<string, unknown>;
  government_exclusion_note: string;
  sectors: Array<{ name: string; count: number }>;
  countries: Array<{ code: string; count: number }>;
  total_organizations: number;
  organizations: Array<{
    id: string;
    name: string;
    papers: number;
    researchers: number;
    sector: string;
    notable: boolean;
    country_code?: string | null;
    wikidata_qid?: string | null;
    wikipedia_url?: string | null;
    parents?: string[];
  }>;
  org_anchored_communities: Array<{
    community: string;
    members: number;
    size_tier: "large" | "standard";
    organization_id: string;
    organization_name: string;
    top_topic: string;
    display_name: string;
    share: number;
    notable_organization: boolean;
  }>;
  rollup: Array<{
    parent: string;
    parent_name: string;
    child_organizations: number;
    papers: number;
    parent_is_v4_organization: boolean;
    notable: boolean;
  }>;
  matrix: {
    organizations: string[];
    topics: string[];
    cells: Array<{
      organization_id: string;
      organization_name: string;
      subject_id: string;
      subject_name: string;
      papers: number;
      share: number;
      rca: number;
    }>;
  };
  metric_definitions: Record<string, MetricDefinition>;
}

export interface GroupDetailResponse {
  /** Position among all organizations by paper count (ties share a position). */
  paper_rank: number | null;
  ranked_organizations: number;
  profile: Record<string, unknown>;
  description?: {
    description: string;
    provenance_label?: string;
    source_kind?: string;
    wikipedia_url?: string | null;
    wikipedia_revision_id?: number | string | null;
    attribution?: string | null;
  } | null;
  specializations: Array<{
    subject: string;
    subject_name: string;
    kind: string;
    group_papers_in_subject: number;
    share_of_group: number;
    rca: number;
    first_active_year?: number | null;
    growth_late_minus_early: number;
  }>;
  partners: Array<{
    id: string;
    name: string;
    sector?: string;
    country_code?: string;
    papers: number;
    weight?: number;
  }>;
  child_units: Array<{ id: string; name: string; sector?: string }>;
  org_anchored_communities: Array<Record<string, unknown>>;
  top_papers: Array<{ paper_id: string; title: string; year: number; venue?: string }>;
}

export interface CommunityNodeItem {
  community_id: string;
  source: string;
  level: number;
  size: number;
  size_tier: string;
  title: string;
  summary: string;
  key_findings: Array<{ claim: string; paper_ids: string[] }>;
  centrality_rating?: number | null;
  centrality_rationale?: string | null;
  dominant_topics: Array<unknown>;
  papers_by_year?: Record<string, number>;
  /** Research communities only. */
  paper_count?: number;
  /** Research community detail only; null without a live graph. */
  top_people?: Array<{ id: string; name: string; papers: number }> | null;
  top_papers?: Array<{ id: string; title: string; year?: number; in_corpus_citations?: number }>;
  top_orgs?: Array<{ id: string; name: string; papers?: number }>;
  label_method?: string;
  label_task?: string;
  label_organization?: string;
  hubs?: string[];
  brokers?: string[];
  brokers_betweenness?: string[];
  rising_researchers?: Array<{ id: string; name: string; recent_papers: number; base_papers: number; share_ratio: number }>;
  ai_generated_label?: string | null;
}

export interface CommunitiesResponse {
  source: string;
  counts_by_source: Record<string, number>;
  n2_resolution_note: string;
  supernodes: CommunityNodeItem[];
  edges: Array<{ source: string; target: string; weight: number; shared: string[] }>;
  rising_researchers: Array<{
    id: string;
    name: string;
    recent_papers: number;
    base_papers: number;
    share_ratio: number;
    new_entrant: boolean;
    community: string;
  }>;
}

export interface AskCitation {
  paper_id: string;
  step?: number | null;
  sentence: string;
}

export interface AskResultPapers {
  step: number;
  tool?: string;
  role?: string;
  paper_ids: string[];
}

export interface AskCitationsEvent {
  paper_ids?: string[];
  citations?: AskCitation[];
  result_papers?: AskResultPapers[];
  evidence_labelling?: string | null;
}

export interface AskResult {
  question?: string;
  mode: string;
  answer: string;
  plan: Array<{ tool: string; args: Record<string, unknown>; purpose?: string }>;
  steps: Array<{
    tool: string;
    args?: Record<string, unknown>;
    rows: Array<Record<string, unknown>>;
    evidence_ids?: string[];
    error?: string;
  }>;
  subgraph: {
    nodes: Array<{ id: string; label?: string; name?: string; hop?: number }>;
    edges: Array<{ source: string; target: string; relation?: string; support_count?: number; hop?: number }>;
  };
  /** Papers that directly back a specific sentence (paper row or abstract excerpt). */
  citations: AskCitation[];
  /** Example papers behind each step's count or list; not evidence for a sentence. */
  result_papers?: AskResultPapers[];
  paper_ids?: string[];
  evidence_labelling?: string;
  faithfulness: { passed: boolean; errors: string[] };
  linked: Record<string, unknown>;
  ambiguous: Array<{ slot: string; query: string; candidates: Array<{ id: string; name: string; label: string }> }>;
  ai_generated_label?: string;
  from_cache?: boolean;
  cached_demo_id?: string;
}

export interface AskDemoItem {
  demo_id: string;
  mode: string;
  title: string;
  question: string;
  cached: boolean;
  latency_seconds?: number | null;
  result?: AskResult | null;
}

export interface PulseStripRow {
  id: string;
  name: string;
  kind: "Method" | "Task" | "Dataset" | "Topic";
  class: string;
  t: number;
  total_papers: number;
  papers: number[];
  share: number[];
  slope_p_value: number;
  display_aliases: string[];
}

export interface PulseResponse {
  graph_version: string;
  years: number[];
  year_totals: Record<string, number | null>;
  strip: PulseStripRow[];
  leaders: Array<{
    id: string;
    name: string;
    kind: string;
    class: string;
    organizations: Array<{ id: string; name: string; specialisation: number; subject_papers: number; total_papers: number }>;
  }>;
  smallworld: {
    holds: boolean;
    L: number | null;
    C: number | null;
    sigma_rewired: number | null;
    sigma_random: number | null;
    lcc_share_of_nodes: number | null;
  };
  thresholds: { min_subject_papers: number; min_org_papers: number };
  classification_note: string;
  caveats: string[];
  selection_rule: string;
}
