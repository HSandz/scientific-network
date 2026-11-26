/**
 * Display rules for the Navigator. These change wording and what is shown, never the analysis:
 * momentum classes still come from analysis-final-exam-v2 (trend test p <= 0.10).
 */

/** Minimum evidence before a group is ranked as "leading" a subject. */
export const MIN_ORG_PAPERS = 3;
export const MIN_RESEARCHER_PAPERS = 5;

/**
 * A "stable" subject (no significant straight-line trend) whose share still moved a lot gets a
 * display-only label, so a 0.5% → 1.4% subject does not just read "Stable".
 * Applies when the 2025 share is at least GREW_RATIO times (or at most 1/GREW_RATIO of) the 2021
 * share and the change is at least MIN_CHANGE_POINTS percentage points.
 */
export const GREW_RATIO = 1.5;
export const MIN_CHANGE_POINTS = 0.3;

export type DisplayMomentum = "rising" | "emerging" | "stable" | "declining" | "grew-unsteady" | "fell-unsteady";

/** shares are fractions (0.014 = 1.4%). */
export function displayMomentum(cls: string | null | undefined, shares: number[]): DisplayMomentum {
  const c = (cls || "stable") as DisplayMomentum;
  if (c !== "stable" || shares.length < 2) return c;
  const a = shares[0] * 100;
  const b = shares[shares.length - 1] * 100;
  if (Math.abs(b - a) < MIN_CHANGE_POINTS) return "stable";
  if (a > 0 ? b / a >= GREW_RATIO : b > 0) return "grew-unsteady";
  if (b / a <= 1 / GREW_RATIO) return "fell-unsteady";
  return "stable";
}

export const MOMENTUM_WORD: Record<DisplayMomentum, string> = {
  rising: "Rising",
  emerging: "Emerging",
  stable: "Stable",
  declining: "Declining",
  "grew-unsteady": "Grew, not consistently",
  "fell-unsteady": "Fell, not consistently",
};

function pct(x: number): string {
  const v = x * 100;
  return v > 0 && v < 0.05 ? "<0.1%" : `${v.toFixed(1)}%`;
}

/** "Stable trend, share up from 0.5% to 1.4%" and friends. */
export function momentumSentence(cls: string | null | undefined, shares: number[]): string {
  const a = shares[0] ?? 0;
  const b = shares[shares.length - 1] ?? 0;
  const dir = b > a ? "up" : b < a ? "down" : "unchanged";
  const change = dir === "unchanged" ? `share ${pct(b)} in 2021 and 2025` : `share ${dir} from ${pct(a)} to ${pct(b)}`;
  switch (cls) {
    case "rising":
      return `Rising, ${change}`;
    case "emerging":
      return `Emerging, ${change}`;
    case "declining":
      return `Declining, ${change}`;
    default:
      return `Stable trend, ${change}`;
  }
}
