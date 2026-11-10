import { EvidenceKind, GraphNode, NodeLabel, RelationType, ViewMode } from "../types/explorer";

/**
 * Perceptually balanced scientific cartographic palette.
 * Avoids framework default 500 hexes and violet/purple hues so semantic
 * categories remain legible on both stone-light (#ffffff) and charcoal-dark (#171717) surfaces.
 */

export const LABEL_COLORS: Record<NodeLabel, string> = {
  Researcher: "#3b78bd",   // Cobalt slate
  Paper: "#c4792b",        // Ochre amber
  Organization: "#2a8c6a", // Mineral teal
  Topic: "#b55867",        // Terracotta rose
  Venue: "#7c8894",        // Graphite slate
};

export interface ThemeTokens {
  ground: string;
  surface: string;
  raised: string;
  active: string;
  border: string;
  rule: string;
  control: string;
  text: string;
  muted: string;
  faint: string;
  accent: string;
  positive: string;
  warning: string;
  negative: string;
  chart1: string;
  chart2: string;
  chart3: string;
  chart4: string;
  chartGrid: string;
  chartAxis: string;
  chartPrimarySeries: string;
  chartInkSeries: string;
  chartSecondarySeries: string;
  heatmapScale: string[];
  contextEdge: string;
  dimmedEdge: string;
  focusedEdge: string;
  dimmedNode: string;
  labelPillBg: string;
  labelInk: string;
  hoverBg: string;
  hoverStroke: string;
  hoverInk: string;
  focusRing: string;
}

export function getThemeTokens(darkMode: boolean): ThemeTokens {
  if (darkMode) {
    return {
      ground: "#1e1e1e",
      surface: "#252525",
      raised: "#2d2d2d",
      active: "#363636",
      border: "#373737",
      rule: "#323232",
      control: "#5b5b5b",
      text: "#cecece",
      muted: "#b0b0b0",
      faint: "#9f9f9f",
      accent: "#7fa6cc",
      positive: "#3fc07a",
      warning: "#e5a93b",
      negative: "#e5566f",
      chart1: "#cecece",
      chart2: "#9f9f9f",
      chart3: "#7fa6cc",
      chart4: "#3fc07a",
      chartGrid: "#323232",
      chartAxis: "#b0b0b0",
      chartPrimarySeries: "#7fa6cc",
      chartInkSeries: "#cecece",
      chartSecondarySeries: "#9f9f9f",
      heatmapScale: ["#1e1e1e", "#243d54", "#2e5d8a", "#7fa6cc"],
      contextEdge: "#626a73",
      dimmedEdge: "#2c3035",
      focusedEdge: "#7fa6cc",
      dimmedNode: "#323539",
      labelPillBg: "rgba(30, 30, 30, 0.88)",
      labelInk: "#cecece",
      hoverBg: "#252525",
      hoverStroke: "#5b5b5b",
      hoverInk: "#cecece",
      focusRing: "#7fa6cc",
    };
  }
  return {
    ground: "#f5f4f1",
    surface: "#ffffff",
    raised: "#ecebe7",
    active: "#e2e0da",
    border: "#dfddd7",
    rule: "#ecebe7",
    control: "#c7c5be",
    text: "#111111",
    muted: "#504f4c",
    faint: "#64635e",
    accent: "#1d5fbf",
    positive: "#247b50",
    warning: "#92400e",
    negative: "#c4242a",
    chart1: "#141414",
    chart2: "#767570",
    chart3: "#1d5fbf",
    chart4: "#247b50",
    chartGrid: "#e8e7e2",
    chartAxis: "#504f4c",
    chartPrimarySeries: "#1d5fbf",
    chartInkSeries: "#141414",
    chartSecondarySeries: "#767570",
    heatmapScale: ["#ecebe7", "#b8cde6", "#3d73b5", "#1d5fbf"],
    contextEdge: "#8f969e",
    dimmedEdge: "#dedcd6",
    focusedEdge: "#1d5fbf",
    dimmedNode: "#d5d3cd",
    labelPillBg: "rgba(245, 244, 241, 0.88)",
    labelInk: "#111111",
    hoverBg: "#ffffff",
    hoverStroke: "#c7c5be",
    hoverInk: "#111111",
    focusRing: "#111111",
  };
}

export const SECTOR_COLORS: Record<string, string> = {
  academia: "#2b6cb0",     // Cobalt slate
  industry: "#1f7a5c",     // Mineral teal
  government: "#b86b1b",   // Ochre amber
  nonprofit: "#a34857",    // Terracotta rose
  unknown: "#6e7681",      // Neutral slate
};

export const YEAR_COLORS: Record<number, string> = {
  2021: "#5c768d",         // Cool slate
  2022: "#3b7a8c",         // Deep verdigris
  2023: "#287d67",         // Mineral green
  2024: "#8f7526",         // Warm brass
  2025: "#c2593f",         // Vermilion clay
};

export const COMMUNITY_PALETTE: string[] = [
  "#2b6cb0", // Cobalt slate
  "#1f7a5c", // Mineral teal
  "#b86b1b", // Ochre amber
  "#a34857", // Terracotta rose
  "#3b7a8c", // Deep verdigris
  "#7a6f28", // Olive brass
  "#4d6b53", // Sage pine
  "#9c5338", // Sienna clay
  "#3d5a80", // Deep marine
  "#287d67", // Sea mineral
  "#8a5a44", // Umber
  "#5c768d", // Steel blue
];

export const EVIDENCE_KIND_COLORS: Record<EvidenceKind, string> = {
  observed: "#1f7a5c",         // Mineral teal (factual R1-R4)
  inferred_topic: "#b86b1b",   // Ochre amber (embedding R5)
  curated_taxonomy: "#a34857", // Terracotta rose (taxonomy R6)
  derived: "#2b6cb0",          // Cobalt slate (derived R7-R10)
};

export const PREDICATE_COLORS: Record<RelationType, string> = {
  AUTHORED: "#1f7a5c",
  AFFILIATED_WITH: "#287d67",
  PUBLISHED_IN: "#5a6570",
  CITES: "#c2593f",
  HAS_TOPIC: "#b86b1b",
  SUBTOPIC_OF: "#a34857",
  COAUTHORED_WITH: "#2b6cb0",
  COLLABORATED_WITH: "#3b7a8c",
  RESEARCHES_TOPIC: "#7a6f28",
  CONTRIBUTES_TO_TOPIC: "#8a5a44",
};

export const PREDICATE_R_CODE: Record<RelationType, string> = {
  AUTHORED: "R1",
  AFFILIATED_WITH: "R2",
  PUBLISHED_IN: "R3",
  CITES: "R4",
  HAS_TOPIC: "R5",
  SUBTOPIC_OF: "R6",
  COAUTHORED_WITH: "R7",
  COLLABORATED_WITH: "R8",
  RESEARCHES_TOPIC: "R9",
  CONTRIBUTES_TO_TOPIC: "R10",
};

export function hashString(str: string): number {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return Math.abs(h);
}

export function getCommunityColor(communityId: string | null | undefined): string {
  if (!communityId || communityId === "unassigned") {
    return "#6e7681";
  }
  // Extract trailing digits if formatted like community:00000 for deterministic cycling
  const match = communityId.match(/(\d+)$/);
  if (match) {
    const idx = parseInt(match[1], 10);
    return COMMUNITY_PALETTE[idx % COMMUNITY_PALETTE.length];
  }
  const idx = hashString(communityId) % COMMUNITY_PALETTE.length;
  return COMMUNITY_PALETTE[idx];
}

export function getNodeColor(node: GraphNode, mode: ViewMode): string {
  if (mode === "researchers" && node.label === "Researcher") {
    return getCommunityColor(node.group);
  }
  if (mode === "organizations" && node.label === "Organization") {
    const sec = (node.sector || node.group || "unknown").toLowerCase();
    return SECTOR_COLORS[sec] || SECTOR_COLORS.unknown;
  }
  if (mode === "citations" && node.label === "Paper") {
    const yr = node.year || Number(node.group);
    return YEAR_COLORS[yr] || "#b86b1b";
  }
  return LABEL_COLORS[node.label] || "#6e7681";
}

export function getNodeRadius(node: GraphNode, mode: ViewMode): number {
  const baseScore = Math.max(0, node.score || node.displayed_degree || 1);
  if (mode === "citations") {
    return Math.min(20, Math.max(5.5, 5.5 + Math.sqrt(baseScore) * 2.0));
  }
  if (mode === "organizations") {
    return Math.min(22, Math.max(6, 6 + Math.log1p(baseScore) * 3.0));
  }
  if (mode === "researchers") {
    return Math.min(20, Math.max(5.5, 5.5 + Math.log1p(baseScore) * 3.0));
  }
  if (node.label === "Venue") return 14;
  if (node.label === "Topic") return node.properties.level === "parent" ? 13 : 9.5;
  if (node.label === "Organization") return 10;
  if (node.label === "Researcher") return 8;
  return 6.5;
}

export function truncateCanvasLabel(label: string, maxChars = 36): string {
  if (!label) return "";
  const clean = label.trim();
  if (clean.length <= maxChars) return clean;
  return `${clean.slice(0, maxChars - 1).trimEnd()}…`;
}
