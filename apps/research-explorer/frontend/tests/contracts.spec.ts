import { test, expect } from "@playwright/test";
import { effectiveSlice } from "../src/lib/effectiveGraph";
import {
  bridgeRanks,
  ccdfPoints,
  componentHistogram,
  sectorCells,
  topicCells,
} from "../src/lib/analytics";
import { lanePath, parallelGroups } from "../src/lib/edgeLanes";
import { makeViewSpec, shareSpec, validateSpec } from "../src/lib/viewSpec";
import { csv, exportGraph } from "../src/lib/exportGraph";
import type { GraphEdge, GraphNode } from "../src/types/explorer";
const node = (id: string) =>
  ({
    id,
    name: id,
    label: "Paper",
    score: 1,
    x: 0,
    y: 0,
    group: "Paper",
    properties: {},
    displayed_degree: 0,
    displayed_strength: 0,
  }) as GraphNode;
const edge = (
  id: string,
  relation: string,
  source = "paper:a",
  target = "paper:b",
  support = 1,
) =>
  ({
    edge_id: id,
    relation,
    source,
    target,
    support_count: support,
    fractional_weight: 0.99,
    evidence_kind: "observed",
    directed: true,
    symmetric: false,
    evidence_ids: [],
    graph_version: "invented-fixture",
    method_version: "test-only",
    validation_status: "accepted",
    properties: {},
  }) as GraphEdge;
const filters = {
  limit: 100,
  communityId: "",
  sector: "",
  crossSectorOnly: false,
  countryCode: "",
  yearMin: 2021,
  yearMax: 2025,
  venue: "",
  topicId: "",
  minSupport: 1,
  minWeight: 0,
  includeIsolates: false,
  includeTopics: false,
  preset: "custom",
  nodeLabels: ["Researcher", "Paper", "Topic", "Organization", "Venue"],
  relations: ["AUTHORED", "CITES", "HAS_TOPIC", "COAUTHORED_WITH"],
} as any;

test("effective edges preserve semantic IDs, predicate-specific support, degree and neighbor parity", () => {
  const nodes = [node("paper:a"), node("paper:b"), node("paper:c")];
  const edges = [
    edge("edge:a", "CITES"),
    edge("edge:b", "CITES", "paper:b", "paper:a"),
    edge("edge:c", "HAS_TOPIC"),
    edge("edge:d", "COAUTHORED_WITH"),
  ];
  const view = effectiveSlice(nodes, edges, "strong");
  expect(view.edges.map((e) => e.edge_id)).toEqual([
    "edge:a",
    "edge:b",
    "edge:c",
  ]);
  expect(view.nodes[0].displayed_degree).toBe(3);
  expect(view.nodes[0].displayed_neighbor_count).toBe(1);
  expect(view.nodes[0].displayed_strength).toBe(0);
  expect(
    effectiveSlice(nodes, [edge("edge:weak", "COAUTHORED_WITH")], "strong")
      .edges,
  ).toEqual([]);
  expect(effectiveSlice(nodes, [], "connected").nodes).toEqual([]);
  const groups = parallelGroups(edges);
  expect(groups[0].map((e) => e.edge_id)).toEqual([
    "edge:a",
    "edge:b",
    "edge:c",
    "edge:d",
  ]);
  expect(lanePath({ x: 0, y: 0 }, { x: 100, y: 0 }, 0, 2).y).toBe(-12);
  expect(lanePath({ x: 0, y: 0 }, { x: 100, y: 0 }, 1, 2).y).toBe(12);
});

test("view schema validates, clamps, includes all filters, and discloses transient expansion", () => {
  const state: any = {
    viewMode: "heterogeneous",
    workspaceTab: "graph",
    filters: {
      ...filters,
      venue: "venue:aaai",
      countryCode: "",
      topicId: "topic:graph-ml",
      yearMin: 2022,
      yearMax: 2024,
      minSupport: 3,
      minWeight: 0.4,
      limit: 150,
    },
    layoutMode: "circular",
    edgeFilterMode: "strong",
    selectedNodeId: "paper:a",
    selectedEdgeId: null,
    graphViewScope: { kind: "overview", title: "Overview" },
    extraNodes: [],
    extraEdges: [],
  };
  const spec = makeViewSpec(state);
  expect(validateSpec(JSON.parse(JSON.stringify(spec)), filters)).toMatchObject(
    JSON.parse(JSON.stringify(spec)),
  );
  const hidden = validateSpec({ ...spec, filters: { ...spec.filters, countryCode: "VN", communityId: "community:00001" } }, filters)!;
  expect(hidden.filters.countryCode).toBe("");
  expect(hidden.filters.communityId).toBe("");
  expect(hidden.notice).toContain("Unsupported hidden filters");
  const invalid = validateSpec(
    {
      ...spec,
      filters: { ...filters, limit: 10000, yearMin: NaN, minWeight: -1 },
      selectedNodeId: "../bad",
    },
    filters,
  )!;
  expect(invalid.filters.limit).toBe(250);
  expect(invalid.filters.yearMin).toBe(2021);
  expect(invalid.selectedNodeId).toBeNull();
  state.extraNodes = [node("paper:c")];
  const expanded = makeViewSpec(state);
  expect(expanded.shareable).toBe(false);
  expect(shareSpec(expanded).scope.kind).toBe("overview");
  expect(shareSpec(expanded).notice).toContain("cannot be reconstructed");
  const path = validateSpec(
    {
      ...spec,
      scope: {
        kind: "path",
        pathData: {
          sourceId: "paper:a",
          targetId: "paper:b",
          mode: "citation_directed",
          maxHops: 99,
        },
      },
    },
    filters,
  )!;
  expect(path.scope.pathData?.mode).toBe("citation_directed");
  expect(path.scope.pathData?.maxHops).toBe(4);
});

test("export JSON and both CSVs represent the effective slice with provenance", () => {
  const nodes = [node("paper:a"), node("paper:b")],
    edges = [edge("edge:a", "CITES"), edge("edge:b", "COAUTHORED_WITH")];
  const slice = effectiveSlice(nodes, edges, "strong");
  const spec = validateSpec(
    { version: 2, filters, scope: { kind: "overview" } },
    filters,
  )!;
  const exported = exportGraph(slice.nodes, slice.edges, spec);
  expect(exported.edge_count).toBe(1);
  expect(exported.edges[0].edge_id).toBe("edge:a");
  expect(exported.graph_version).toBeNull();
  expect(exported.quality).toBeNull();
  expect(
    csv(exported.edges as any, [
      "edge_id",
      "source",
      "target",
      "relation",
      "directed",
    ]),
  ).toBe(
    '"edge_id","source","target","relation","directed"\r\n"edge:a","paper:a","paper:b","CITES","true"',
  );
  expect(csv(exported.nodes as any, ["id"])).toContain(
    '"paper:a"\r\n"paper:b"',
  );
});

test("analytic transforms retain unknowns, numerical CCDF tail, missing ranks and true denominators", () => {
  expect(componentHistogram([8, 2, 1, 1])).toEqual([
    [1, 2],
    [2, 1],
    [8, 1],
  ]);
  const m = sectorCells([
    {
      row_sector: "unknown",
      column_sector: "industry",
      pair_paper_support_count: 17,
    },
  ]);
  expect(m.sectors).toContain("unknown");
  expect(m.max).toBe(17);
  expect(
    ccdfPoints([
      { degree: 0, researcher_count_at_least: 10 },
      { degree: 90, researcher_count_at_least: 1 },
    ]),
  ).toEqual([
    [0, 10],
    [90, 1],
  ]);
  expect(
    bridgeRanks([{ node_id: "a", score: 2 }], [{ node_id: "b", score: 1 }]),
  ).toEqual([
    { id: "a", base: 1, strict: null },
    { id: "b", base: null, strict: 1 },
  ]);
  const rows: any = [
    {
      venue_id: "venue:aaai",
      year: 2022,
      topic_id: "topic:x",
      paper_count: 8,
      labeled_paper_count: 10,
      all_core_paper_count: 20,
      share_of_fractional_topic_mass: 0.4,
    },
    {
      venue_id: "venue:ijcai",
      year: 2022,
      topic_id: "topic:x",
      labeled_paper_count: 30,
    },
  ];
  expect(topicCells(rows, "venue:aaai", 2022, 2022, "topic:x")).toEqual([
    rows[0],
  ]);
});

test("zoom policy uses inverse ratio, hysteresis and bounded viewport budgets", async () => {
  const {zoomBand,labelBudget} = await import('../src/lib/labelPolicy');
  expect(zoomBand(1,'overview')).toBe('overview');
  expect(zoomBand(.65,'overview')).toBe('medium');
  expect(zoomBand(.72,'medium')).toBe('medium');
  expect(zoomBand(.8,'medium')).toBe('overview');
  expect(zoomBand(.3,'medium')).toBe('close');
  expect(zoomBand(.1,'close')).toBe('detail');
  expect(labelBudget('overview',1440,900)).toBe(0);
  expect(labelBudget('medium',390,500)).toBeLessThan(labelBudget('medium',1440,900));
  expect(labelBudget('detail',10000,10000)).toBe(48);
});

test("temporal transforms require observed endpoints and keep citation cohort denominators", async () => {
  const {topicChanges,cohortCdf} = await import('../src/lib/analytics');
  const row = (year:number,share:number) => ({year,topic_id:'invented:topic',topic:'Invented topic',share_of_fractional_topic_mass:share}) as any;
  expect(topicChanges([row(2022,.4),row(2025,.6)],2021,2025)).toEqual([]);
  expect(topicChanges([row(2021,.4),row(2025,.3)],2021,2025)[0].delta).toBeCloseTo(-10);
  expect(cohortCdf({venue_id:'invented',year:2021,paper_denominator:10,zero_in_degree_count:6,distribution:[{in_degree:2,paper_count:4},{in_degree:0,paper_count:6}]})).toEqual([[0,60],[2,100]]);
  expect(cohortCdf({venue_id:'invented',year:2021,paper_denominator:0,zero_in_degree_count:0,distribution:[]})).toEqual([]);
});
