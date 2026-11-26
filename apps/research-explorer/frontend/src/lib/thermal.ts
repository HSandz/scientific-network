/**
 * The thermal scale: the one bold colour device. It encodes momentum only
 * (cooling, stable, heating). Interpolation is in CIE Lab so mid-tones stay clean,
 * and colours are read from the live CSS variables so both themes work.
 */

type RGB = [number, number, number];

export function cssVar(name: string): string {
  if (typeof document === "undefined") return "#888888";
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "#888888";
}

export function parseColor(c: string): RGB {
  const s = c.trim();
  if (s.startsWith("#")) {
    const h = s.length === 4 ? s.slice(1).split("").map((x) => x + x).join("") : s.slice(1, 7);
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  const m = s.match(/rgba?\(\s*([\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)/i);
  if (m) return [Number(m[1]), Number(m[2]), Number(m[3])];
  return [136, 136, 136];
}

function toLinear(c: number) {
  const v = c / 255;
  return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
}
function fromLinear(v: number) {
  const c = v <= 0.0031308 ? 12.92 * v : 1.055 * v ** (1 / 2.4) - 0.055;
  return Math.max(0, Math.min(255, Math.round(c * 255)));
}
const Xn = 0.95047, Yn = 1, Zn = 1.08883;
function f(t: number) {
  return t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116;
}
function finv(t: number) {
  return t ** 3 > 0.008856 ? t ** 3 : (t - 16 / 116) / 7.787;
}
function rgbToLab([r, g, b]: RGB): RGB {
  const R = toLinear(r), G = toLinear(g), B = toLinear(b);
  const X = (R * 0.4124 + G * 0.3576 + B * 0.1805) / Xn;
  const Y = (R * 0.2126 + G * 0.7152 + B * 0.0722) / Yn;
  const Z = (R * 0.0193 + G * 0.1192 + B * 0.9505) / Zn;
  return [116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))];
}
function labToRgb([L, a, bb]: RGB): RGB {
  const fy = (L + 16) / 116, fx = fy + a / 500, fz = fy - bb / 200;
  const X = finv(fx) * Xn, Y = finv(fy) * Yn, Z = finv(fz) * Zn;
  const R = X * 3.2406 + Y * -1.5372 + Z * -0.4986;
  const G = X * -0.9689 + Y * 1.8758 + Z * 0.0415;
  const B = X * 0.0557 + Y * -0.204 + Z * 1.057;
  return [fromLinear(R), fromLinear(G), fromLinear(B)];
}
export function toHex([r, g, b]: RGB): string {
  return `#${[r, g, b].map((x) => x.toString(16).padStart(2, "0")).join("")}`;
}
export function mixLab(a: string, b: string, t: number): string {
  const la = rgbToLab(parseColor(a)), lb = rgbToLab(parseColor(b));
  const k = Math.max(0, Math.min(1, t));
  return toHex(labToRgb([la[0] + (lb[0] - la[0]) * k, la[1] + (lb[1] - la[1]) * k, la[2] + (lb[2] - la[2]) * k]));
}
export function withAlpha(c: string, alpha: number): string {
  const [r, g, b] = parseColor(c);
  return `rgb(${r} ${g} ${b} / ${alpha})`;
}

export interface ThermalPalette {
  cool: string;
  neutral: string;
  heat: string;
  paper: string;
  surface: string;
  dark: boolean;
}

export function readPalette(): ThermalPalette {
  return {
    cool: cssVar("--cool"),
    neutral: cssVar("--neutral"),
    heat: cssVar("--heat"),
    paper: cssVar("--paper"),
    surface: cssVar("--surface"),
    dark: typeof document !== "undefined" && document.documentElement.classList.contains("dark"),
  };
}

/** t in [-1, 1]: negative cools toward blue, positive heats toward amber. */
export function thermal(t: number, p: ThermalPalette = readPalette()): string {
  return t < 0 ? mixLab(p.neutral, p.cool, Math.min(1, -t)) : mixLab(p.neutral, p.heat, Math.min(1, t));
}

/** Row hue: mild trends start part-way from grey so momentum stays readable. */
export function rowHue(t: number, p: ThermalPalette = readPalette()): string {
  return Math.abs(t) < 0.2 ? p.neutral : thermal(Math.sign(t) * (0.5 + 0.5 * Math.abs(t)), p);
}

/**
 * A heat-strip cell: the row hue blended with the page by share (k in [0, 1]).
 * In dark mode the blend runs through a lifted, desaturated base so low-share heat
 * cells read as dim amber, not brown.
 */
export function cellColor(hue: string, k: number, p: ThermalPalette = readPalette()): string {
  if (!p.dark) return mixLab(p.paper, hue, k);
  const base = mixLab(p.surface, "#3A4757", 0.35);
  // ease-in so faint cells stay close to the surface, then reach full hue
  const eased = 0.12 + 0.88 * k ** 1.15;
  return mixLab(base, hue, eased);
}

export type MomentumClass = "rising" | "emerging" | "stable" | "declining" | string;

/** Signed momentum strength in [-1, 1] from the share slope, relative to the largest |slope| shown. */
export function momentumT(slope: number, maxAbsSlope: number, cls: MomentumClass): number {
  if (!maxAbsSlope) return 0;
  let t = Math.sqrt(Math.abs(slope) / maxAbsSlope) * (slope >= 0 ? 1 : -1);
  if (cls === "stable") t = Math.max(-0.18, Math.min(0.18, t));
  if (cls === "declining" && t > -0.25) t = -0.25;
  if ((cls === "rising" || cls === "emerging") && t < 0.25) t = 0.25;
  return t;
}

export function momentumInkVar(cls: MomentumClass): string {
  return cls === "declining" ? "var(--cool-ink)" : cls === "stable" ? "var(--muted)" : "var(--heat-ink)";
}

export function fmtPct(x: number, digits = 1): string {
  if (!Number.isFinite(x)) return "–";
  if (x > 0 && x < 0.05 * 10 ** (1 - digits)) return `<${(0.1 * 10 ** (1 - digits)).toFixed(digits)}%`;
  return `${x.toFixed(digits)}%`;
}
