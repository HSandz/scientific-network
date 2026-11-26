import { communityTitle, orgName, subjectName } from "./names";
import type { CommunityNodeItem } from "../types/navigator";

const lower = (s: string) => s.replace(/^[A-Z](?=[a-z])/, (c) => c.toLowerCase());

/** The cluster's most characteristic terms as a phrase, for example "Computer vision, image classification". */
export function topTerms(c: Pick<CommunityNodeItem, "dominant_topics" | "source">, n = 3): string {
  const names = ((c.dominant_topics || []) as Array<any>)
    .map((t) => (typeof t === "object" ? subjectName(String(t.name || ""), t.label) : c.source === "N2" ? orgName(String(t)) : subjectName(String(t), "Topic")))
    .filter(Boolean)
    .slice(0, n);
  return names.map((x, i) => (i ? lower(x) : x)).join(", ");
}

/** The full readable name: the generated title without internal ids, else the top terms. */
export function clusterTitle(c: CommunityNodeItem): string {
  const generated = c.ai_generated_label ? communityTitle(c.title) : "";
  return generated || topTerms(c, 3) || "Unnamed cluster";
}

/** A short name for the map: long generated sentences give way to the top two terms. */
export function clusterLabel(c: CommunityNodeItem): string {
  const full = clusterTitle(c);
  return full.length <= 44 ? full : topTerms(c, 2) || full;
}

/**
 * Display-only momentum for a research cluster: its share of all papers in 2024–2025 against
 * 2021–2022. A doubling or halving reaches the end of the colour scale.
 */
export function clusterMomentum(
  byYear: Record<string, number> | undefined,
  totals: Record<string, number | null | undefined>,
): { t: number; ratio: number; words: string } | null {
  if (!byYear) return null;
  const share = (years: string[]) => {
    const total = years.reduce((a, y) => a + Number(totals[y] || 0), 0);
    return total ? years.reduce((a, y) => a + Number(byYear[y] || 0), 0) / total : 0;
  };
  const base = share(["2021", "2022"]);
  const recent = share(["2024", "2025"]);
  if (!base || !recent) return null;
  const ratio = recent / base;
  const pctChange = Math.round((ratio - 1) * 100);
  const words = Math.abs(pctChange) < 5 ? "share about the same" : `share ${pctChange > 0 ? "up" : "down"} ${Math.abs(pctChange)}%`;
  return { t: Math.max(-1, Math.min(1, Math.log2(ratio))), ratio, words };
}
