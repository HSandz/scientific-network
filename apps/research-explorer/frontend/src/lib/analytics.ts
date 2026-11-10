// Presentation transforms only: no retuning, new community detection or fabricated cells.
export interface TopicRow {
  year: number;
  venue_id: string;
  venue: string;
  topic_id: string;
  topic: string;
  paper_count: number;
  fractional_paper_count: number;
  labeled_paper_count: number;
  all_core_paper_count: number;
  topic_label_coverage: number;
  share_of_fractional_topic_mass: number;
}
export function topicCells(
  rows: TopicRow[],
  venue: string,
  yearMin: number,
  yearMax: number,
  topic: string,
) {
  return rows.filter(
    (r) =>
      (!venue || r.venue_id === venue) &&
      r.year >= yearMin &&
      r.year <= yearMax &&
      (!topic || r.topic_id === topic),
  );
}
export function componentHistogram(sizes: number[]) {
  const counts = new Map<number, number>();
  for (const size of sizes) counts.set(size, (counts.get(size) || 0) + 1);
  return [...counts].sort((a, b) => a[0] - b[0]);
}
export function sectorCells(
  rows: {
    row_sector: string;
    column_sector: string;
    pair_paper_support_count: number;
  }[],
) {
  const sectors = [
    ...new Set([
      ...rows.flatMap((r) => [r.row_sector, r.column_sector]),
      "unknown",
    ]),
  ].sort();
  return {
    sectors,
    max: Math.max(0, ...rows.map((r) => r.pair_paper_support_count)),
    cells: rows.map((r) => [
      sectors.indexOf(r.column_sector),
      sectors.indexOf(r.row_sector),
      r.pair_paper_support_count,
    ]),
  };
}
export function ccdfPoints(
  rows: { degree: number; researcher_count_at_least: number }[],
) {
  return rows.map((r) => [r.degree, r.researcher_count_at_least]);
}
export function bridgeRanks(
  base: { node_id: string; score: number }[],
  strict: { node_id: string; score: number }[],
) {
  const ids = [
    ...new Set([
      ...base.map((x) => x.node_id),
      ...strict.map((x) => x.node_id),
    ]),
  ];
  return ids.map((id) => ({
    id,
    base: base.findIndex((x) => x.node_id === id) + 1 || null,
    strict: strict.findIndex((x) => x.node_id === id) + 1 || null,
  }));
}

/** First/last selected endpoints must both exist. No interpolation or implicit zero. */
export function topicChanges(rows: TopicRow[], firstYear: number, lastYear: number) {
  return [...new Set(rows.map(r => r.topic_id))].flatMap(id => {
    const first = rows.find(r => r.topic_id === id && r.year === firstYear);
    const last = rows.find(r => r.topic_id === id && r.year === lastYear);
    return first && last ? [{ first, last, delta: 100 * (last.share_of_fractional_topic_mass - first.share_of_fractional_topic_mass) }] : [];
  }).sort((a,b) => b.delta - a.delta || a.first.topic_id.localeCompare(b.first.topic_id));
}
export interface CitationCohort {
  venue_id: string; year: number; paper_denominator: number; zero_in_degree_count: number;
  distribution: { in_degree: number; paper_count: number }[];
}
export function cohortCdf(cohort: CitationCohort): [number, number][] {
  if (cohort.paper_denominator <= 0) return [];
  let cumulative = 0;
  return [...cohort.distribution].sort((a,b) => a.in_degree-b.in_degree).map(row => {
    cumulative += row.paper_count;
    return [row.in_degree, 100 * cumulative / cohort.paper_denominator];
  });
}
