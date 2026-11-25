import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SCREENSHOT_DIR =
  process.env.NAVIGATOR_SCREENSHOT_DIR ||
  path.resolve(HERE, "../../../../reports/runs/WORK-2026-11-25-006/screenshots");
const TIMINGS_PATH =
  process.env.NAVIGATOR_TIMINGS_PATH ||
  path.resolve(HERE, "../../../../reports/runs/WORK-2026-11-25-006/load-timings.json");

async function expectChartRendered(page: Page, label: string) {
  const container = page.locator(`[data-chart-label="${label}"]`);
  await container.scrollIntoViewIfNeeded();
  await expect(container).toBeVisible({ timeout: 15_000 });
  await expect(container).toHaveAttribute("data-chart-active", "true", { timeout: 15_000 });
  await expect(container).toHaveAttribute("data-chart-rendered", "true", { timeout: 15_000 });
  const seriesCount = Number(await container.getAttribute("data-chart-series-count"));
  const pointCount = Number(await container.getAttribute("data-chart-point-count"));
  expect(seriesCount).toBeGreaterThan(0);
  expect(pointCount).toBeGreaterThan(0);

  const nonZeroPixels = await container.evaluate((el) => {
    const canvas = el.querySelector("canvas");
    if (!canvas || canvas.width === 0 || canvas.height === 0) return 0;
    const ctx = canvas.getContext("2d");
    if (!ctx) return 0;
    const img = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    let count = 0;
    for (let i = 3; i < img.length; i += 4) {
      if (img[i] > 0) {
        count++;
        if (count > 200) break;
      }
    }
    return count;
  });
  expect(nonZeroPixels).toBeGreaterThan(100);
}

test.describe("Research Trend Navigator pages (M4)", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
  });

  test("1. Enriched Explorer bar toggles on Explorer view and shows v4 header badge", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/");
    await expect(page.getByTestId("graph-version-badge")).toContainText("release-d3c788c3114a", { timeout: 15_000 });
    await page.getByTestId("toggle-enriched-explorer").click();
    await expect(page.getByTestId("enriched-explorer-panel")).toBeVisible();
    expect(errors).toEqual([]);
  });

  test("2. Trends page renders share lines, heatmap, leaderboards, tooltip, and enriched badge", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/?tab=trends");
    await expect(page.getByTestId("page-trends")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("graph-version-badge")).toContainText("enriched-cb371912e308");
    await expect(page.getByTestId("page-trends")).toContainText("descriptive");
    await expectChartRendered(page, "Method share trend lines");
    await expectChartRendered(page, "Method share heatmap");
    const tooltipBtn = page.getByRole("button", { name: /Metric definition for/i }).first();
    await tooltipBtn.focus();
    await expect(page.getByRole("tooltip")).toBeVisible();
    await tooltipBtn.blur();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "01-trends.png") });
    expect(errors).toEqual([]);
  });

  test("3. Topic / Method Subject page renders annual share chart and PPR lift tables", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/?tab=subjects");
    await expect(page.getByTestId("page-subjects")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("graph-version-badge")).toContainText("enriched-cb371912e308");
    await expect(page.getByTestId("page-subjects")).toContainText("PPR Lift");
    await expectChartRendered(page, "Subject annual share chart");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "02-subject.png") });
    expect(errors).toEqual([]);
  });

  test("4. Groups page renders RCA matrix heatmap, anchored communities, and roll-ups", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/?tab=groups");
    await expect(page.getByTestId("page-groups")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("page-groups")).toContainText("Organization-Anchored Communities");
    await expect(page.getByTestId("page-groups")).toContainText("State Council");
    await expectChartRendered(page, "Organization by topic RCA heatmap");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "03-groups.png") });
    expect(errors).toEqual([]);
  });

  test("5. Communities page renders super-node map and expands members", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/?tab=communities");
    await expect(page.getByTestId("page-communities")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("expand-community-members").click();
    await expect(page.getByTestId("community-members-panel")).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "04-communities.png") });
    expect(errors).toEqual([]);
  });

  test("6. Network Science page renders small-world tables and all three S1 charts", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/?tab=network");
    await expect(page.getByTestId("page-network-science")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("page-network-science")).toContainText("igraph average local clustering");
    await expectChartRendered(page, "N1 path length histogram");
    await expectChartRendered(page, "N1 L and C evolution chart");
    await expectChartRendered(page, "N1 degree distribution");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "05-network-science.png") });
    expect(errors).toEqual([]);
  });

  test("7. Ask page runs scripted demo trace, verifies faithfulness, keyboard nav, and contrast", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/?tab=ask");
    await expect(page.getByTestId("page-ask")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("demo-btn-demo-01-worked-example").click();
    await expect(page.getByTestId("ask-answer-text")).not.toBeEmpty({ timeout: 30_000 });
    await expect(page.getByTestId("faithfulness-badge")).toContainText("Verified");
    await expect(page.getByTestId("ask-trace")).toBeVisible();
    await expect(page.getByTestId("ask-subgraph")).toBeVisible();

    // 2026-11-26 evidence labelling: the share-growth answer is an aggregate claim, so it points to its
    // trace step and lists example papers separately; nothing is labelled a citation.
    const stepRefs = page.getByTestId("answer-step-ref");
    await expect(stepRefs.first()).toBeVisible();
    await expect(page.getByTestId("answer-citation-ref")).toHaveCount(0);
    await expect(page.getByTestId("ask-citations")).toContainText("Citations");
    await expect(page.getByTestId("ask-citations-empty")).toBeVisible();
    await expect(page.getByTestId("ask-result-papers")).toContainText("Papers in this result");
    await expect(page.getByTestId("ask-result-papers-step").first()).toContainText("Step 2");
    await expect(page.getByTestId("page-ask")).not.toContainText("Cited Papers");
    await stepRefs.first().click();
    await expect(page.locator("#ask-step-2")).toBeFocused();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "06-ask-demo-trace.png") });

    // Co-occurrence demo: 0 inline paper IDs remain in the answer; both steps list their example papers.
    await page.getByTestId("demo-btn-demo-03-method-task-cooccurrence").click();
    await expect(page.getByTestId("faithfulness-badge")).toContainText("Verified", { timeout: 30_000 });
    await expect(page.getByTestId("ask-answer-text")).not.toContainText("paper:");
    await expect(page.getByTestId("ask-result-papers-step")).toHaveCount(2);

    await page.getByTestId("tab-ask").focus();
    await page.keyboard.press("Tab");
    const focusedTag = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedTag).toBe("BUTTON");
    const contrastOk = await page.evaluate(() => {
      const s = getComputedStyle(document.body);
      return s.color !== s.backgroundColor;
    });
    expect(contrastOk).toBe(true);
    expect(errors).toEqual([]);
  });

  test("8. Node 360 page renders properties, CC BY-SA attribution, and activity sparkline", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/?tab=node360");
    await expect(page.getByTestId("page-node360")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("page-node360")).toContainText("Neighborhood");
    await expect(page.getByTestId("page-node360")).toContainText("CC BY-SA 4.0");
    await expectChartRendered(page, "Node 2021-2025 activity sparkline");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "07-node360.png") });
    expect(errors).toEqual([]);
  });

  test("9. About page renders E4 intervals, Phase 2 QA benchmark results, and disclosures", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/?tab=about");
    await expect(page.getByTestId("page-about-data")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("page-about-data")).toContainText("enriched-cb371912e308");
    await expect(page.getByTestId("page-about-data")).toContainText("AI-assessed");
    await expect(page.getByTestId("page-about-data")).toContainText("qa-eval-v1");
    await expect(page.getByTestId("page-about-data")).toContainText("0.4273");
    await expect(page.getByTestId("page-about-data")).toContainText("S4 · Full multi-hop");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "08-about-data.png"), fullPage: true });
    expect(errors).toEqual([]);
  });

  test("10. Precomputed Navigator dashboard routes load in < 2000ms locally", async ({ page }) => {
    const routes: Array<{ tab: string; testId: string; readyText: string }> = [
      { tab: "trends", testId: "page-trends", readyText: "Matching:" },
      { tab: "groups", testId: "page-groups", readyText: "Organization-Anchored Communities" },
      { tab: "communities", testId: "page-communities", readyText: "Super-Node" },
      { tab: "network", testId: "page-network-science", readyText: "igraph average local clustering" },
    ];
    // Warm the API/Vite runtime before timing interactive precomputed route switches
    await page.goto("/?tab=trends");
    await expect(page.getByTestId("page-trends")).toContainText("Matching:", { timeout: 15_000 });

    const timings: Record<string, number> = {};
    for (const r of routes) {
      const t0 = Date.now();
      await page.getByTestId(`tab-${r.tab}`).click();
      await expect(page.getByTestId(r.testId)).toContainText(r.readyText, { timeout: 5_000 });
      const dt = Date.now() - t0;
      timings[r.tab] = dt;
      expect(dt).toBeLessThan(2000);
    }
    fs.mkdirSync(path.dirname(TIMINGS_PATH), { recursive: true });
    fs.writeFileSync(TIMINGS_PATH, JSON.stringify({ measured_ms: timings, budget_ms: 2000 }, null, 2) + "\n");
  });
});
