import { test, expect, type Page } from "@playwright/test";
import path from "node:path";
const output =
  process.env.EXPLORER_SCREENSHOT_DIR || "/tmp/scientific-network-redesign";
const sections = [
  "overview",
  "quality",
  "robustness",
  "topics",
  "communities",
  "sectors",
  "trajectories",
];
async function dashboard(page: Page) {
  await page.goto("/?tab=analytics");
  await expect(page.getByTestId("analytics-view")).toBeVisible();
}
async function section(page: Page, id: string) {
  const el = page.locator(`#analytics-${id}`);
  await el.evaluate((e) => e.scrollIntoView({ block: "start" }));
  return el;
}

test("seven sections coexist, anchors navigate and all figures use one cached analytics response", async ({
  page,
}) => {
  let requests = 0;
  page.on("response", (r) => {
    if (r.url().includes("/analytics/overview") && r.status() === 200)
      requests++;
  });
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await dashboard(page);
  await expect(page.locator("[data-analytics-section]")).toHaveCount(7);
  await expect(
    page.getByRole("heading", {
      name: "Explore the AI Research Network",
      exact: true,
    }),
  ).toBeInViewport();
  for (const id of sections) {
    await section(page, id);
    await expect(page.locator(`#heading-${id}`)).toBeInViewport();
  }
  await page
    .getByRole("button", { name: "Topic evolution", exact: true })
    .click();
  await expect(
    page.getByLabel("Topic venue", { exact: true }),
  ).toBeInViewport();
  await expect(
    page.getByRole("button", { name: "Topic evolution", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  expect(requests).toBe(1);
  expect(errors).toEqual([]);
});

test("chart filters preserve instance, correct data/keyboard actions and reduced motion", async ({
  page,
}) => {
  await dashboard(page);
  await page
    .getByRole("button", { name: "Topic evolution", exact: true })
    .click();
  const plot = page.locator(
    '[data-chart-label="Year by inferred topic share"]',
  );
  await plot.scrollIntoViewIfNeeded();
  await expect(plot).toHaveAttribute("data-chart-active", "true");
  const generation = await plot.getAttribute("data-chart-generation");
  await page
    .getByLabel("Topic selection", { exact: true })
    .selectOption("topic:causal-inference");
  await plot.scrollIntoViewIfNeeded();
  expect(await plot.getAttribute("data-chart-generation")).toBe(generation);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(plot).toHaveAttribute("data-animation", "reduced");
  await expect(plot).toHaveAttribute("data-entrance-duration", "0");
  await page.getByText("Topic cells and filtered graphs · data").click();
  await expect(
    page.getByRole("table", { name: "Topic cells and filtered graphs" }),
  ).toContainText("Causal inference");
  await page.getByLabel("Topic first year").fill("2023");
  await page.getByLabel("Topic last year").fill("2023");
  const table = page.getByRole("table", {
    name: "Topic cells and filtered graphs",
  });
  await table
    .getByRole("button", { name: "Causal inference → papers" })
    .click();
  await expect(page.getByTestId("projection-title")).toContainText(
    "Heterogeneous",
  );
  await page.getByRole("button", { name: "← Back to finding" }).click();
  await expect(page.getByLabel("Topic first year")).toHaveValue("2023");
  await expect(
    page.getByRole("button", { name: "Topic evolution", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
});

test("viewport chart lifecycle bounds instances and entrance animations do not replay", async ({
  page,
}) => {
  await dashboard(page);
  let max = 0;
  for (let round = 0; round < 2; round++)
    for (const id of [
      "robustness",
      "topics",
      "communities",
      "sectors",
      "trajectories",
    ]) {
      await section(page, id);
      await page.waitForTimeout(80);
      max = Math.max(
        max,
        await page.locator('[data-chart-active="true"]').count(),
      );
    }
  expect(max).toBeLessThanOrEqual(8);
  await section(page, "robustness");
  const plot = page.locator(
    '[data-chart-label="Base versus strict researcher connectivity"]',
  );
  await plot.scrollIntoViewIfNeeded();
  await expect(plot).toHaveAttribute("data-chart-active", "true");
  await expect(plot).toHaveAttribute("data-entrance-duration", "0");
  await page.getByTestId("tab-table").click();
  await expect(page.locator('[data-chart-active="true"]')).toHaveCount(0);
});

for (const mode of [
  "researchers",
  "organizations",
  "citations",
  "heterogeneous",
])
  test(`${mode}: inverse zoom budgets, collision geometry, hover and selection`, async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto(`/?mode=${mode}`);
    const canvas = page.getByTestId("sigma-canvas-container");
    await expect(canvas).toHaveAttribute("data-label-band", "overview");
    await expect(page.getByTestId("displayed-counts")).toContainText(
      /Displayed: [1-9]/,
    );
    await expect(canvas).toHaveAttribute("data-label-boxes", "[]");
    await page.getByRole("button", { name: "Zoom in", exact: true }).click();
    await expect(canvas).toHaveAttribute("data-label-band", "medium");
    const medium = Number(await canvas.getAttribute("data-label-budget"));
    // Aim at an actual node before close zoom: an empty part of the map has no labels to reveal.
    await canvas.evaluate((el: any) => {
      const sigma = el.__sigma,
        graph = sigma.getGraph();
      const id = graph
        .nodes()
        .sort((a: string, b: string) => graph.degree(b) - graph.degree(a))[0];
      const d = sigma.getNodeDisplayData(id);
      sigma.getCamera().setState({ x: d.x, y: d.y });
    });
    for (let i = 0; i < 4; i++)
      await page.getByRole("button", { name: "Zoom in", exact: true }).click();
    await expect(canvas).toHaveAttribute("data-label-band", "detail");
    expect(
      Number(await canvas.getAttribute("data-label-budget")),
    ).toBeGreaterThan(medium);
    const boxes = JSON.parse((await canvas.getAttribute("data-label-boxes"))!);
    expect(boxes.length).toBeGreaterThan(0);
    for (let i = 0; i < boxes.length; i++)
      for (let j = i + 1; j < boxes.length; j++) {
        const a = boxes[i],
          b = boxes[j];
        expect(a.x1 < b.x2 && a.x2 > b.x1 && a.y1 < b.y2 && a.y2 > b.y1).toBe(
          false,
        );
      }
    await page.screenshot({ path: path.join(output, `${mode}-close.png`) });
    await page
      .getByRole("button", { name: "Reset camera", exact: true })
      .click();
    await expect(canvas).toHaveAttribute("data-label-band", "overview");
    await expect(canvas).toHaveAttribute("data-label-boxes", "[]");
    const identity = await canvas.evaluate((el: any) => {
      const sigma = el.__sigma,
        graph = sigma.getGraph();
      const id = graph.nodes().find((id: string) => {
        const d = sigma.getNodeDisplayData(id),
          p = sigma.framedGraphToViewport(d);
        return (
          p.x > 60 &&
          p.y > 60 &&
          p.x < el.clientWidth - 60 &&
          p.y < el.clientHeight - 60
        );
      });
      const point = sigma.framedGraphToViewport(sigma.getNodeDisplayData(id));
      return { id, name: graph.getNodeAttribute(id, "label"), ...point };
    });
    const bounds = (await canvas.boundingBox())!;
    await page.mouse.move(bounds.x + identity.x, bounds.y + identity.y);
    await expect
      .poll(() =>
        page.evaluate(
          () => (window as any).__explorerStore.getState().hoveredNodeId,
        ),
      )
      .toBe(identity.id);
    await page.screenshot({ path: path.join(output, `${mode}-hover.png`) });
    await page.mouse.click(bounds.x + identity.x, bounds.y + identity.y);
    await expect(page.getByTestId("inspector-node-name")).toBeVisible();
    await page.screenshot({ path: path.join(output, `${mode}-selected.png`) });
    await page.getByTestId("theme-toggle").click();
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(canvas).toBeVisible();
    expect(errors).toEqual([]);
  });

test("responsive sections, chart geometry and scientific caveats in both themes", async ({
  page,
}) => {
  test.setTimeout(120000);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await dashboard(page);
  for (const [width, height] of [
    [1440, 900],
    [1024, 768],
    [768, 1024],
    [390, 844],
  ])
    for (const dark of [true, false]) {
      await page.setViewportSize({ width, height });
      await page.evaluate((d) => {
        const s = (window as any).__explorerStore;
        if (s.getState().darkMode !== d) s.getState().toggleDarkMode();
      }, dark);
      for (const id of sections) {
        await section(page, id);
        await page.waitForTimeout(100);
        await expect(page.locator(`#heading-${id}`)).toBeInViewport();
        expect(
          await page.evaluate(() => document.documentElement.scrollWidth),
        ).toBeLessThanOrEqual(width);
        expect(
          await page
            .getByTestId("analytics-view")
            .evaluate((e) => e.scrollWidth),
        ).toBeLessThanOrEqual(width);
        await page.screenshot({
          path: path.join(
            output,
            `dashboard-${id}-${width}-${dark ? "dark" : "light"}.png`,
          ),
        });
      }
    }
  await section(page, "quality");
  await expect(
    page.getByText("AI-assessed only. No independent human validation.", {
      exact: false,
    }),
  ).toBeVisible();
});

test("missing derived artifacts retain safe visible sections", async ({
  page,
  request,
}) => {
  const response = await request.get(
    "http://127.0.0.1:" +
      (process.env.PLAYWRIGHT_API_PORT || "8000") +
      "/api/analytics/overview",
  );
  const data = await response.json();
  data.explorer_derived = null;
  data.quality.affiliation_coverage = null;
  await page.route("**/api/graph/summary", async (route) => {
    const response = await route.fetch();
    const summary = await response.json();
    summary.quality.affiliation_coverage = null;
    await route.fulfill({ json: summary });
  });
  data.topic_shares_by_year_venue = { rows: [] };
  data.robustness = {};
  await page.route("**/api/analytics/overview", (r) =>
    r.fulfill({ json: data }),
  );
  await dashboard(page);
  await expect(page.locator("[data-analytics-section]")).toHaveCount(7);
  await section(page, "quality");
  await expect(page.getByText(/Target 80% · Value unavailable/)).toBeVisible();
  await section(page, "robustness");
  await expect(
    page.getByText("Strict summaries unavailable", { exact: false }),
  ).toBeVisible();
  await section(page, "topics");
  await expect(
    page.getByText(
      "No measured values available for topic fractional prevalence change.",
    ),
  ).toBeAttached();
  await section(page, "trajectories");
  await expect(
    page.getByText("Exploratory cohort artifact unavailable."),
  ).toBeVisible();
});

test("rendered heatmap values match the API and a real canvas click opens the exact slice", async ({
  page,
}) => {
  let analytics: any;
  page.on("response", async (response) => {
    if (
      response.url().includes("/analytics/overview") &&
      response.status() === 200
    )
      analytics = await response.json();
  });
  await dashboard(page);
  await page
    .getByRole("button", { name: "Topic evolution", exact: true })
    .click();
  const plot = page.locator(
    '[data-chart-label="Year by inferred topic share"]',
  );
  await plot.scrollIntoViewIfNeeded();
  await expect(plot).toHaveAttribute("data-chart-active", "true");
  const rendered = await plot.evaluate(
    (el: any) => el.__chart.getOption().series[0].data,
  );
  const rows = analytics.topic_shares_by_year_venue.rows.filter(
    (r: any) => r.venue_id === "venue:aaai",
  );
  expect(rendered.map((r: number[]) => r[2])).toEqual(
    rows.map((r: any) => 100 * r.share_of_fractional_topic_mass),
  );
  const point = await plot.evaluate((el: any) =>
    el.__chart.convertToPixel(
      { seriesIndex: 0 },
      el.__chart.getOption().series[0].data[0].slice(0, 2),
    ),
  );
  const box = (await plot.boundingBox())!;
  await page.mouse.click(box.x + point[0], box.y + point[1]);
  await expect(page.getByTestId("projection-title")).toContainText(
    "Heterogeneous",
  );
  expect(
    await page.evaluate(
      () => (window as any).__explorerStore.getState().filters,
    ),
  ).toMatchObject({
    yearMin: rows[0].year,
    yearMax: rows[0].year,
    venue: rows[0].venue_id,
    topicId: rows[0].topic_id,
  });
});

 test("restoring a saved analytics view scrolls from another visible section", async ({page}) => {
  await dashboard(page);
  await page.getByRole("button", {name:"Topic evolution", exact:true}).click();
  await page.getByTestId("open-export-menu").click();
  await page.getByLabel("Save workspace", {exact:true}).fill("Scroll restore");
  await page.getByTestId("save-workspace-bookmark").click();
  await page.getByRole("button", {name:"Overview", exact:true}).click();
  await expect(page.locator("#heading-overview")).toBeInViewport();
  await page.getByTestId("open-export-menu").click();
  await page.getByRole("button", {name:"Restore Scroll restore", exact:true}).click();
  await expect(page.locator("#heading-topics")).toBeInViewport();
 });
