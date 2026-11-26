import { GraphNode, NodeLabel, RelationType, ViewMode } from "../types/explorer";

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
      ground: "#16202b",
      surface: "#1f2b38",
      raised: "#253342",
      active: "#2c3b4b",
      border: "#2f3e4e",
      rule: "#2f3e4e",
      control: "#5b5b5b",
      text: "#e5eaf0",
      muted: "#a9b5c2",
      faint: "#9f9f9f",
      accent: "#7fa6cc",
      positive: "#3fc07a",
      warning: "#e5a93b",
      negative: "#e5566f",
      chart1: "#cecece",
      chart2: "#9f9f9f",
      chart3: "#7fa6cc",
      chart4: "#3fc07a",
      chartGrid: "#2f3e4e",
      chartAxis: "#a9b5c2",
      chartPrimarySeries: "#7fa6cc",
      chartInkSeries: "#cecece",
      chartSecondarySeries: "#9f9f9f",
      heatmapScale: ["#16202b", "#243d54", "#2e5d8a", "#7fa6cc"],
      contextEdge: "#626a73",
      dimmedEdge: "#26333f",
      focusedEdge: "#7fa6cc",
      dimmedNode: "#2f3c49",
      labelPillBg: "rgba(22, 32, 43, 0.88)",
      labelInk: "#e5eaf0",
      hoverBg: "#1f2b38",
      hoverStroke: "#5b5b5b",
      hoverInk: "#e5eaf0",
      focusRing: "#7fa6cc",
    };
  }
  return {
    ground: "#f4f6f8",
    surface: "#ffffff",
    raised: "#eef1f4",
    active: "#e2e7ec",
    border: "#d5dce3",
    rule: "#d5dce3",
    control: "#c7c5be",
    text: "#1c2733",
    muted: "#526070",
    faint: "#64635e",
    accent: "#1d5fbf",
    positive: "#247b50",
    warning: "#92400e",
    negative: "#c4242a",
    chart1: "#141414",
    chart2: "#767570",
    chart3: "#1d5fbf",
    chart4: "#247b50",
    chartGrid: "#e2e7ec",
    chartAxis: "#526070",
    chartPrimarySeries: "#1d5fbf",
    chartInkSeries: "#141414",
    chartSecondarySeries: "#767570",
    heatmapScale: ["#eef1f4", "#b8cde6", "#3d73b5", "#1d5fbf"],
    contextEdge: "#8f969e",
    dimmedEdge: "#dde2e8",
    focusedEdge: "#1d5fbf",
    dimmedNode: "#d2d9e0",
    labelPillBg: "rgba(244, 246, 248, 0.88)",
    labelInk: "#1c2733",
    hoverBg: "#ffffff",
    hoverStroke: "#c7c5be",
    hoverInk: "#1c2733",
    focusRing: "#1c2733",
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

export function truncateCanvasLabel(label: string, maxChars = 36): string {
  if (!label) return "";
  const clean = label.trim();
  if (clean.length <= maxChars) return clean;
  return `${clean.slice(0, maxChars - 1).trimEnd()}…`;
}
