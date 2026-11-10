import { test, expect, Page } from "@playwright/test";
import fs from "node:fs/promises";
const storePath = "/src/stores/useExplorerStore.ts";
async function state(page: Page) {
  return page.evaluate(async (path) => {
    const s = (window as any).__explorerStore;
    const v = s.getState();
    return {
      mode: v.viewMode,
      filters: v.filters,
      scope: v.graphViewScope,
      extraNodes: v.extraNodes.map((n: any) => n.id).sort(),
      extraEdges: v.extraEdges.map((e: any) => e.edge_id).sort(),
    };
  }, storePath);
}
async function exportSlice(page: Page) {
  await page.getByTestId("open-export-menu").click();
  const wait = page.waitForEvent("download");
  await page.getByTestId("export-subgraph-json").click();
  const d = await wait;
  return JSON.parse(await fs.readFile((await d.path())!, "utf8"));
}
const ids = (v: any) => ({
  nodes: v.nodes.map((n: any) => n.id).sort(),
  edges: v.edges.map((e: any) => e.edge_id).sort(),
});
async function ready(page: Page) {
  await expect(page.getByTestId("sigma-canvas-container")).toHaveAttribute(
    "data-renderer-generation",
    "2",
    { timeout: 20000 },
  );
  await expect(page.getByTestId("displayed-counts")).toContainText(
    /Displayed: [1-9][\d,]* nodes/,
  );
}

test("filtered overview, persistent bookmark, Ego and directed Path reconstruct the effective edge IDs", async ({
  page,
}) => {
  test.setTimeout(90000);
  await page.goto("/?mode=researchers");
  await ready(page);
  await page.evaluate(async (p) => {
    const s = (window as any).__explorerStore;
    s.getState().updateFilters({ minSupport: 2, limit: 60 });
    s.getState().setEdgeFilterMode("strong");
    s.getState().saveCurrentView("Repeated evidence");
  }, storePath);
  await page.waitForResponse(
    (r) => r.url().includes("/views/researchers") && r.status() === 200,
  );
  await page.waitForTimeout(300);
  const before = await exportSlice(page);
  expect(before.edge_count).toBeGreaterThan(0);
  expect(before.view_spec.filters.minSupport).toBe(2);
  const url = await page.evaluate(
    async (p) => (window as any).__explorerStore.getState().buildShareUrl(),
    storePath,
  );
  await page.goto(url);
  await ready(page);
  const after = await exportSlice(page);
  expect(ids(after)).toEqual(ids(before));
  const saved = await page.evaluate(
    async (p) => (window as any).__explorerStore.getState().savedViews,
    storePath,
  );
  expect(saved.some((v: any) => v.name === "Repeated evidence")).toBe(true);
  await page.evaluate(
    async ({ p, id }) => {
      (window as any).__explorerStore.getState().selectNode(id);
    },
    { p: storePath, id: after.nodes[0].id },
  );
  await page.getByTestId("canvas-isolate-ego").click();
  await expect(page.getByTestId("canvas-scope-banner")).toContainText("Ego");
  const ego = await exportSlice(page);
  expect(ego.view_spec.shareable).toBe(true);
  const egoUrl = await page.evaluate(
    async (p) => (window as any).__explorerStore.getState().buildShareUrl(),
    storePath,
  );
  await page.goto(egoUrl);
  await expect(page.getByTestId("canvas-scope-banner")).toContainText("Ego");
  await expect
    .poll(async () => (await state(page)).extraEdges.length)
    .toBe(ego.edge_count);
  expect(ids(await exportSlice(page))).toEqual(ids(ego));
  await page.evaluate(async (p) => {
    const { explorerApi } = await import("/src/lib/api.ts");
    const s = (window as any).__explorerStore;
    const view = await explorerApi.getViewSubgraph("citations", {limit: 30});
    const a = view.edges.find((e: any) => e.relation === "CITES")!;
    s.getState().setViewMode("citations");
    const res = await explorerApi.findPath({
      source_id: a.source,
      target_id: a.target,
      mode: "citation_directed",
      max_hops: 4,
    });
    s.getState().enterPathView(res);
  }, storePath);
  const path = await exportSlice(page);
  expect(path.edge_count).toBeGreaterThan(0);
  expect(path.view_spec.scope.pathData.mode).toBe("citation_directed");
  expect(path.edges.every((e: any) => e.relation === "CITES" && e.directed)).toBe(true);
  const pathUrl = await page.evaluate(
    async (p) => (window as any).__explorerStore.getState().buildShareUrl(),
    storePath,
  );
  await page.goto(pathUrl);
  await expect
    .poll(async () => (await state(page)).extraEdges.length)
    .toBe(path.edge_count);
  expect(ids(await exportSlice(page))).toEqual(ids(path));
});

test("late expansion is discarded, 503 keeps prior graph, selection and theme preserve renderer/camera", async ({
  page,
}) => {
  await page.goto("/?mode=researchers");
  await ready(page);
  const original = await exportSlice(page);
  await page.getByRole("button", { name: "Zoom in", exact: true }).click();
  await page.waitForTimeout(350);
  const camera = await page
    .getByTestId("sigma-canvas-container")
    .getAttribute("data-camera");
  await page.evaluate(
    async ({ p, id }) =>
      (window as any).__explorerStore.getState().selectNode(id),
    { p: storePath, id: original.nodes[0].id },
  );
  await page.getByTestId("theme-toggle").click();
  await expect(page.getByTestId("sigma-canvas-container")).toHaveAttribute(
    "data-renderer-generation",
    "2",
  );
  expect(
    await page
      .getByTestId("sigma-canvas-container")
      .getAttribute("data-camera"),
  ).toBe(camera);
  await page.route("**/api/nodes/*/neighbors?**", async (route) => {
    await new Promise((r) => setTimeout(r, 800));
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: '{"detail":"Injected 503"}',
    });
  });
  await page.getByTestId("canvas-expand-hop").click();
  await expect(page.getByTestId("expansion-error-banner")).toContainText(
    "Injected 503",
  );
  expect(ids(await exportSlice(page))).toEqual(ids(original));
  await page.unroute("**/api/nodes/*/neighbors?**");
  let release!: () => void;
  const barrier = new Promise<void>((r) => (release = r));
  await page.route("**/api/nodes/*/neighbors?**", async (route) => {
    const response = await route.fetch();
    await barrier;
    await route.fulfill({ response });
  });
  await page.getByTestId("canvas-expand-hop").click();
  await page.waitForTimeout(200);
  await page.evaluate(
    async (p) =>
      (window as any).__explorerStore.getState().setViewMode("citations"),
    storePath,
  );
  release();
  await expect(page.getByTestId("projection-title")).toContainText("Citation");
  await page.waitForTimeout(1000);
  expect((await state(page)).extraNodes).toEqual([]);
  await expect(page.getByTestId("sigma-canvas-container")).toHaveAttribute(
    "data-renderer-generation",
    "2",
  );
});

test("clipboard denial and missing artifacts show honest recovery, never false success", async ({
  page,
}) => {
  await page.addInitScript(() =>
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: () => Promise.reject(new Error("denied")) },
      configurable: true,
    }),
  );
  await page.goto("/");
  await ready(page);
  await page.getByTestId("open-export-menu").click();
  await page.getByTestId("share-view-btn").click();
  await expect(page.getByLabel("Share URL to copy")).toBeVisible();
  await expect(page.getByTestId("share-view-btn")).not.toContainText("Copied");
  await page.route("**/api/analytics/overview", (r) =>
    r.fulfill({
      status: 503,
      body: '{"detail":"Missing frozen artifact"}',
      contentType: "application/json",
    }),
  );
  await page.goto("/?tab=analytics");
  await expect(page.getByRole("alert")).toContainText("Analytics unavailable", {
    timeout: 20000,
  });
  await expect(page.getByRole("button", { name: "Retry" })).toBeVisible();
  await expect(page.locator("main")).not.toContainText("96.50%");
});

test("topic-cell chart actions open the correct venue/year/topic and expose source papers", async ({
  page,
}) => {
  await page.goto("/?tab=analytics");
  await expect(page.getByTestId("analytics-view")).toBeVisible();
  await page
    .getByRole("button", { name: "Topic evolution", exact: true })
    .click();
  await page.getByLabel("Topic venue").selectOption("venue:ijcai");
  await page.getByLabel("Topic first year").fill("2023");
  await page.getByLabel("Topic last year").fill("2023");
  await page.getByText("Topic cells and filtered graphs · data").click();
  await page
    .getByRole("button", { name: "Causal inference → papers", exact: true })
    .click();
  await expect(page.getByTestId("projection-title")).toContainText(
    "Heterogeneous",
  );
  const s = await state(page);
  expect(s.filters).toMatchObject({
    venue: "venue:ijcai",
    yearMin: 2023,
    yearMax: 2023,
    topicId: "topic:causal-inference",
    preset: "researcher_paper_topic",
  });
  const graph = await exportSlice(page);
  expect(graph.edges.length).toBeGreaterThan(0);
  expect(graph.nodes.filter((n: any) => n.label === "Paper").length).toBeGreaterThan(0);
  expect(
    graph.nodes
      .filter((n: any) => n.label === "Paper")
      .every((n: any) => n.year === 2023 && n.venue === "venue:ijcai"),
  ).toBe(true);
  expect(
    graph.edges
      .filter((e: any) => e.relation === "HAS_TOPIC")
      .every((e: any) => e.target === "topic:causal-inference"),
  ).toBe(true);
  await expect(
    page.getByRole("button", { name: "← Back to finding" }),
  ).toBeVisible();
});

test("reciprocal edges have distinct selectable lanes and exact export identity", async ({
  page,
}) => {
  const n = (id: string, x: number) => ({
    id,
    label: "Paper",
    name: id,
    group: "2021",
    score: 1,
    displayed_degree: 2,
    displayed_strength: 0,
    x,
    y: 0,
    year: 2021,
    properties: {},
  });
  const e = (id: string, source: string, target: string) => ({
    edge_id: id,
    relation: "CITES",
    source,
    target,
    directed: true,
    symmetric: false,
    evidence_kind: "observed",
    evidence_ids: [],
    support_count: 1,
    graph_version: "synthetic-visual-fixture",
    method_version: "test-only",
    validation_status: "accepted",
    properties: {},
  });
  const nodes = [n("paper:fixture-a", -0.5), n("paper:fixture-b", 0.5)],
    edges = [
      e("edge:fixture-forward", nodes[0].id, nodes[1].id),
      e("edge:fixture-backward", nodes[1].id, nodes[0].id),
    ];
  await page.route("**/api/views/**", (r) =>
    r.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        view: "citations",
        title: "Invented reciprocal rendering fixture",
        full_node_count: 2,
        full_edge_count: 2,
        displayed_node_count: 2,
        displayed_edge_count: 2,
        nodes,
        edges,
        available_communities: [],
      }),
    }),
  );
  await page.goto("/?mode=citations");
  await ready(page);
  const lanes = page.locator(
    'svg[aria-label="Parallel and reciprocal relationship lanes"] path[data-edge-id]',
  );
  await expect(lanes).toHaveCount(2);
  expect(await lanes.nth(0).getAttribute("d")).not.toBe(
    await lanes.nth(1).getAttribute("d"),
  );
  const graph = await exportSlice(page);
  expect(ids(graph).edges).toEqual([
    "edge:fixture-backward",
    "edge:fixture-forward",
  ]);
  await lanes.nth(0).focus();
  await page.keyboard.press("Enter");
  await expect
    .poll(async () =>
      page.evaluate(
        () => (window as any).__explorerStore.getState().selectedEdgeId,
      ),
    )
    .toBe("edge:fixture-backward");
  await expect(page.getByTestId("displayed-counts")).toContainText("2 edges");
});

test("reduced-motion responsive findings remain keyboard accessible in both themes", async ({
  page,
}) => {
  test.setTimeout(60000);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/?tab=analytics");
  await expect(page.getByTestId("analytics-view")).toBeVisible();
  for (const width of [390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const dark of [true, false]) {
      await page.evaluate((d) => {
        const s = (window as any).__explorerStore;
        if (s.getState().darkMode !== d) s.getState().toggleDarkMode();
      }, dark);
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
      await expect(
        page.getByRole("button", { name: "Topic evolution", exact: true }),
      ).toBeInViewport();
    }
  }
  await page
    .getByRole("button", { name: "Evidence sensitivity", exact: true })
    .focus();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("button", { name: "Topic evolution", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByLabel("Topic venue")).toBeVisible();
  await expect(
    page.getByText("Topic cells and filtered graphs · data"),
  ).toBeVisible();
});

test("node positions survive selection and expansion; unmount removes renderer listeners", async ({ page }) => {
  await page.goto('/?mode=researchers');
  await ready(page);
  const original = await exportSlice(page);
  const id = original.nodes[0].id;
  const before = await page.evaluate(id => {
    const el = document.querySelector('[data-testid="sigma-canvas-container"]') as any;
    const sigma = el.__sigma;
    (window as any).__retainedSigma = sigma;
    const graph = sigma.getGraph();
    // Apply the same Graphology coordinate update used by the pointer drag handler.
    graph.setNodeAttribute(id, 'x', graph.getNodeAttribute(id,'x') + .125);
    return {x:graph.getNodeAttribute(id,'x'), y:graph.getNodeAttribute(id,'y')};
  }, id);
  await page.evaluate(id => (window as any).__explorerStore.getState().selectNode(id), id);
  await page.getByTestId('canvas-expand-hop').click();
  await expect.poll(() => page.evaluate(() => (window as any).__explorerStore.getState().extraNodes.length)).toBeGreaterThan(0);
  const after = await page.evaluate(id => {
    const el = document.querySelector('[data-testid="sigma-canvas-container"]') as any;
    const sigma=el.__sigma, graph=sigma.getGraph();
    return {same:sigma===(window as any).__retainedSigma,x:graph.getNodeAttribute(id,'x'),y:graph.getNodeAttribute(id,'y')};
  },id);
  expect(after).toEqual({same:true,...before});
  await page.getByTestId('tab-analytics').click();
  await expect(page.getByTestId('analytics-view')).toBeVisible();
  expect(await page.evaluate(() => (window as any).__retainedSigma.eventNames().length)).toBe(0);
  await page.getByTestId('tab-graph').click();
  await ready(page);
  expect(await page.getByTestId('sigma-canvas-container').locator('canvas').count()).toBe(7);
});
