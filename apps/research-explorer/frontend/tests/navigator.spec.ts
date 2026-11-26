import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

/**
 * One test per Navigator page, against the enriched graph (neo4j-enriched, Bolt 7690).
 * The live Ask test also needs the local language model and skips when it is not running.
 */
const HERE = path.dirname(fileURLToPath(import.meta.url));
const RUN_DIR = process.env.NAVIGATOR_RUN_DIR || path.resolve(HERE, "../../../../reports/runs/WORK-2026-11-26-003");
const LLM_URL = process.env.NAVIGATOR_LLM_URL || "http://127.0.0.1:8080/v1";
const LOAD_BUDGET_MS = 2000;
const timings: Record<string, number> = {};
const coldTimings: Record<string, number> = {};
const pageErrors = new WeakMap<Page, string[]>();

/**
 * Open a route inside the running app and time it until the first thing a reader came for is on
 * screen. The shell is loaded first, so the budget covers the page and its precomputed data, not
 * the Vite dev server transforming modules for a fresh browser (that cold time is recorded only).
 */
async function open(page: Page, route: string, ready: string) {
  if (page.url() === "about:blank") {
    const cold0 = Date.now();
    await page.goto("/about");
    await expect(page.getByTestId("about-versions")).toBeVisible({ timeout: 20_000 });
    coldTimings[route] = Date.now() - cold0;
    if (route === "/about") {
      await page.goto("/topics");
      await expect(page.getByTestId("topics-search")).toBeVisible({ timeout: 20_000 });
    }
  }
  const t0 = Date.now();
  await page.evaluate((to) => {
    window.history.pushState({}, "", to);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, route);
  await expect(page.locator(ready).first()).toBeVisible({ timeout: 10_000 });
  const ms = Date.now() - t0;
  timings[route] = ms;
  expect(ms, `${route} load time`).toBeLessThan(LOAD_BUDGET_MS);
}

/** A chart must say it rendered, hold data points and have painted marks. */
async function expectChart(page: Page, label: string) {
  const chart = page.locator(`[data-chart-label="${label}"]`).first();
  await chart.scrollIntoViewIfNeeded();
  await expect(chart).toHaveAttribute("data-chart-rendered", "true", { timeout: 10_000 });
  expect(Number(await chart.getAttribute("data-chart-point-count"))).toBeGreaterThan(0);
  const marks = await chart.evaluate(
    (el) =>
      Array.from(el.querySelectorAll("*")).filter((m) => {
        const b = m.getBoundingClientRect();
        if (!(b.width > 0 || b.height > 0)) return false;
        if (m instanceof SVGGeometryElement) return true;
        const bg = getComputedStyle(m).backgroundColor;
        return bg !== "transparent" && bg !== "rgba(0, 0, 0, 0)";
      }).length,
  );
  expect(marks, `${label}: painted marks`).toBeGreaterThan(0);
}

/** Tab into the page content and require a visible focus indicator on each stop. */
async function expectVisibleFocus(page: Page, stops = 4) {
  await page.locator("#main-content").focus();
  for (let i = 0; i < stops; i++) {
    await page.keyboard.press("Tab");
    const ring = await page.evaluate(() => {
      const el = document.activeElement as HTMLElement | null;
      if (!el || el === document.body) return "nothing focused";
      const has = (n: Element) => {
        const s = getComputedStyle(n);
        return (s.outlineStyle !== "none" && parseFloat(s.outlineWidth) > 0) || s.boxShadow !== "none";
      };
      const wrapper = el.parentElement;
      return has(el) || (wrapper && has(wrapper)) ? "ok" : el.outerHTML.slice(0, 160);
    });
    expect(ring).toBe("ok");
  }
}

test.describe("Research Trend Navigator pages", () => {
  test.use({ colorScheme: "light", viewport: { width: 1440, height: 900 } });

  test.beforeAll(async ({ request }) => {
    // The first request after an API start builds caches; the budget is for precomputed page loads.
    for (const url of ["/api/pulse", "/api/trends?kind=Method", "/api/groups", "/api/communities", "/api/network-science", "/api/subjects?limit=5", "/api/about-data"]) {
      await request.get(url, { timeout: 40_000 }).catch(() => undefined);
    }
  });

  test.beforeEach(async ({ page }) => {
    const errors: string[] = [];
    pageErrors.set(page, errors);
    page.on("pageerror", (e) => errors.push(e.message));
  });

  test.afterEach(async ({ page }) => {
    expect(pageErrors.get(page)).toEqual([]);
  });

  test.afterAll(() => {
    fs.mkdirSync(RUN_DIR, { recursive: true });
    fs.writeFileSync(path.join(RUN_DIR, "load-timings.json"), JSON.stringify({ budget_ms: LOAD_BUDGET_MS, in_app_ms: timings, cold_dev_server_shell_ms: coldTimings }, null, 2) + "\n");
  });

  test("Pulse: headline, momentum strip, leaders and small-world summary", async ({ page }) => {
    await open(page, "/", '[data-testid="strip-row"]');
    await expect(page.getByTestId("pulse-headline")).toContainText("heating fastest");
    await expectChart(page, "Pulse thermal strip");
    await expect(page.getByTestId("leader-card").first()).toBeVisible();
    await expect(page.getByTestId("pulse-smallworld")).toContainText("small world");
    await expectVisibleFocus(page);
    await page.getByTestId("pulse-how").click();
    await expect(page.getByRole("dialog")).toContainText("AI-assessed");
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("pulse-how")).toBeFocused();
  });

  test("Ask (recorded): demo answer, trace, evidence and measurement note", async ({ page }) => {
    await open(page, "/ask", '[data-testid="demo-btn-demo-01-worked-example"]');
    await page.getByTestId("demo-btn-demo-01-worked-example").click();
    await expect(page.getByTestId("ask-answer-text")).not.toBeEmpty({ timeout: 30_000 });
    await expect(page.getByTestId("faithfulness-badge")).toHaveAttribute("data-passed", "true", { timeout: 30_000 });
    await expect(page.getByTestId("faithfulness-badge")).toContainText("recorded answer");
    await expect(page.getByTestId("ask-answer-text")).not.toContainText("paper:");
    await expect(page.getByTestId("ask-trace")).toBeVisible();
    await expect(page.getByTestId("ask-subgraph")).toBeVisible();
    expect(Number(await page.getByTestId("ask-subgraph").getAttribute("data-graph-nodes"))).toBeGreaterThan(1);
    // Evidence labelling: aggregate claims list example papers; nothing is passed off as a citation.
    await page.getByTestId("ev-tab-papers").click();
    await expect(page.getByTestId("ask-papers")).toContainText("Cited in the answer");
    await expect(page.getByTestId("ask-result-papers")).toBeVisible();
    await expect(page.getByTestId("answer-footnote").filter({ visible: true }).first()).toBeVisible();
    await page.getByTestId("ask-how").click();
    await expect(page.getByRole("dialog")).toContainText("ever affiliated");
    await page.keyboard.press("Escape");
    await expectVisibleFocus(page);
  });

  test("Ask (live): the local model streams steps before the checked answer", async ({ page, request }) => {
    const up = await request.get(`${LLM_URL}/models`, { timeout: 3000 }).then((r) => r.ok()).catch(() => false);
    test.skip(!up, "local language model is not running");
    test.setTimeout(240_000);
    await open(page, "/ask", '[data-testid="ask-input"]');
    await page.getByTestId("ask-settings").click();
    await page.getByTestId("ask-use-cache").uncheck();
    await page.keyboard.press("Escape");
    await page.getByTestId("ask-input").fill("Which datasets are used most by papers on knowledge graph completion?");
    await page.getByTestId("ask-input").press("Enter");
    await expect(page.locator('[data-testid="ask-trace"] li[data-state="done"]').first()).toBeVisible({ timeout: 120_000 });
    await expect(page.getByTestId("faithfulness-badge")).toBeVisible({ timeout: 180_000 });
    await expect(page.getByTestId("ask-answer-text")).not.toBeEmpty();
    await expect(page.getByTestId("faithfulness-badge")).not.toContainText("recorded answer");
  });

  test("Trends: filters, chart, boards and heat table", async ({ page }) => {
    await open(page, "/trends", '[data-testid="board-rising"] li');
    await expectChart(page, "Trend share lines");
    await expectChart(page, "Trends heat map");
    for (const board of ["board-rising", "board-emerging", "board-declining"]) await expect(page.getByTestId(board)).toBeVisible();
    await page.getByTestId("trends-kind-task").click();
    await expect(page.getByTestId("trends-kind-task")).toHaveAttribute("aria-pressed", "true");
    await expectChart(page, "Trend share lines");
    await expectVisibleFocus(page);
  });

  test("Topic: index search, hero chart, leading groups and brief", async ({ page }) => {
    await open(page, "/topics", '[data-testid="subject-row"]');
    await page.getByTestId("topics-search").fill("diffusion");
    await expect(page.getByTestId("subject-row").first()).toContainText(/diffusion/i);
    await page.getByTestId("subject-row").first().click();
    await expect(page.getByTestId("topic-headline")).toBeVisible();
    await expect(page).toHaveURL(/\/topics\/.+/);
    await page.goBack();
    await expect(page.getByTestId("topics-search")).toBeVisible();
    await open(page, "/topics/method:Q3621696", '[data-testid="topic-headline"]');
    await expect(page.locator("[data-chart-label]").first()).toHaveAttribute("data-chart-rendered", "true");
    await expectChart(page, "Leading groups specialisation");
    await expect(page.getByTestId("topic-brief")).toContainText(/Large language models appear in \d+ papers/);
    await expect(page.getByTestId("page-subjects")).toContainText("not by a language model");
    await expectVisibleFocus(page);
  });

  test("Groups: directory, profile with charts, and topic matrix", async ({ page }) => {
    await open(page, "/groups", '[data-testid="org-row"]');
    await page.getByTestId("groups-search").fill("Chinese Academy of Sciences");
    await page.getByTestId("org-row").first().click();
    await expect(page).toHaveURL(/\/groups\/organization/);
    await expect(page.getByTestId("group-profile")).toContainText("Chinese Academy of Sciences");
    await expectChart(page, "Organization specialisations");
    await expectChart(page, "Organization partners");
    await page.getByTestId("groups-matrix-tab").click();
    await expectChart(page, "Organization by topic matrix");
    await expectVisibleFocus(page);
  });

  test("Map: bubbles, side panel and members", async ({ page }) => {
    await open(page, "/map", '[data-testid^="supernode-"]');
    await expectChart(page, "Cluster map");
    await page.locator('[data-testid^="supernode-"]').first().focus();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/\/map\/.+/);
    await expect(page.getByTestId("community-panel")).toBeVisible();
    await page.getByTestId("expand-community-members").click();
    await expect(page.getByTestId("community-members-panel")).toBeVisible();
    await expectVisibleFocus(page);
  });

  test("Network: small-world verdict, charts, rankings and release checks", async ({ page }) => {
    await open(page, "/network", '[data-testid="network-verdict"]');
    await expect(page.getByTestId("network-verdict")).not.toBeEmpty();
    for (const label of ["Path length distribution", "Degree distribution", "Centrality ranking"]) await expectChart(page, label);
    await page.getByTestId("network-N2").click();
    await expect(page.getByTestId("network-N2")).toHaveAttribute("aria-pressed", "true");
    await expectChart(page, "Degree distribution");
    await expect(page.getByTestId("network-view-release")).toBeVisible();
    await expectVisibleFocus(page);
  });

  test("Node: profile with activity, connections and all data", async ({ page }) => {
    await open(page, "/node/researcher:openalex:A5008056593", '[data-testid="node-connection"]');
    await expect(page.getByTestId("node-name")).not.toContainText("researcher:");
    await expectChart(page, "Papers per year");
    await expect(page.getByTestId("node-all-data")).not.toHaveAttribute("open", "");
    await page.getByTestId("node-all-data").locator("summary").click();
    await expect(page.getByTestId("node-all-data")).toContainText("graph_version");
    await expectVisibleFocus(page);
    await page.getByTestId("node-connection").first().click();
    await expect(page).toHaveURL(/\/node\/.+/);
    await expect(page.getByTestId("node-name")).toBeVisible();
  });

  test("About: versions, quality intervals, benchmark disclosures and licences", async ({ page }) => {
    await open(page, "/about", '[data-testid="about-versions"]');
    const about = page.getByTestId("page-about-data");
    await expect(page.getByTestId("about-ai-statement")).toContainText("AI-assessed");
    await expect(about).toContainText("enriched-cb371912e308");
    await expect(about).toContainText("37ee8c59d8245d452e42575b7afbb13808b5f835d51c9ee838bd5581434633e3");
    await expect(page.getByTestId("about-quality")).toContainText("95.1%");
    await expect(page.getByTestId("about-quality")).toContainText("50.0%");
    const bench = page.getByTestId("about-benchmark");
    await expect(bench).toContainText("agreement with the graph, not truth");
    await expect(bench).toContainText("0.43");
    await expect(bench).toContainText("Supplementary check against the literature");
    await expect(about).toContainText("CC BY-SA 4.0");
    await expectVisibleFocus(page, 2);
  });

  test("Explore: graph canvas, popovers, tools and subject finder", async ({ page }) => {
    await open(page, "/explore", '[data-testid="sigma-canvas-container"] canvas');
    // The v4 Explorer folds its filter rail after another page has been open; the toolbar reopens it.
    if (!(await page.getByTestId("left-sidebar").isVisible())) await page.getByTestId("toggle-left-sidebar").click();
    await page.getByTestId("projection-info").click();
    await expect(page.getByRole("dialog", { name: "What this projection contains" })).toContainText("predicates");
    await page.keyboard.press("Escape");
    await page.getByTestId("toggle-enriched-explorer").click();
    await expect(page.getByTestId("enriched-explorer-panel")).toBeVisible();
    await expect(page.getByTestId("enriched-explorer-panel").locator(".echip").first()).toBeVisible();
    await expectVisibleFocus(page);
  });
});
