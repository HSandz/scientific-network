/** Sigma camera ratio is inverse zoom. Hysteresis prevents threshold flicker. */
export type ZoomBand = "overview" | "medium" | "close" | "detail";
export function zoomBand(ratio: number, previous: ZoomBand): ZoomBand {
  const thresholds = [0.72, 0.38, 0.18];
  const bands: ZoomBand[] = ["overview", "medium", "close", "detail"];
  let index = bands.indexOf(previous);
  while (index < 3 && ratio < thresholds[index] * 0.94) index++;
  while (index > 0 && ratio > thresholds[index - 1] * 1.06) index--;
  return bands[index];
}
export function labelBudget(
  band: ZoomBand,
  width: number,
  height: number,
): number {
  if (band === "overview") return 0;
  const limits = { medium: 6, close: 24, detail: 48 };
  const area = band === "medium" ? 65000 : band === "close" ? 26000 : 16000;
  return Math.max(
    1,
    Math.min(limits[band], Math.floor((width * height) / area)),
  );
}
