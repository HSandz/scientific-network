import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SCREENSHOT_DIR =
  process.env.NAVIGATOR_SCREENSHOT_DIR ||
  path.resolve(HERE, "../../../../reports/runs/WORK-2026-11-25-005/screenshots");

test.describe("Research Trend Navigator pages (M3)", () => {
  test("every new Navigator page loads, has working interactions, keyboard nav, contrast, and saves screenshots", async ({
    page,
  }) => {
    test.setTimeout(120_000);
    const errors: string[] = [];
    page.on("pageerror", (e) => {
      errors.push(e.message);
      console.log("[PAGEERROR]", e.message);
    });
    await page.setViewportSize({ width: 1440, height: 900 });

    // Start at Explorer Graph + verify Enriched v5 bar
    console.log("[e2e] goto /");
    await page.goto("/");
    await expect(page.getByTestId("tab-trends")).toBeVisible({ timeout: 20_000 });
    await page.getByTestId("toggle-enriched-explorer").click();
    await expect(page.getByTestId("enriched-explorer-panel")).toBeVisible();

    // 1. Trends page
    console.log("[e2e] trends");
    await page.getByTestId("tab-trends").click();
    await expect(page.getByTestId("page-trends")).toBeVisible();
    await expect(page.getByTestId("page-trends")).toContainText("descriptive");
    const tooltipBtn = page.getByRole("button", { name: /Metric definition for/i }).first();
    await tooltipBtn.focus();
    await expect(page.getByRole("tooltip")).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "01-trends.png") });

    // 2. Topic / Method Subject page
    console.log("[e2e] subjects");
    await page.getByTestId("tab-subjects").click();
    await expect(page.getByTestId("page-subjects")).toBeVisible();
    await expect(page.getByTestId("page-subjects")).toContainText("PPR Lift");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "02-subject.png") });

    // 3. Groups page
    console.log("[e2e] groups");
    await page.getByTestId("tab-groups").click();
    await expect(page.getByTestId("page-groups")).toBeVisible();
    await expect(page.getByTestId("page-groups")).toContainText("Organization-Anchored Communities");
    await expect(page.getByTestId("page-groups")).toContainText("State Council");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "03-groups.png") });

    // 4. Communities page + Super-node expansion
    console.log("[e2e] communities");
    await page.getByTestId("tab-communities").click();
    await expect(page.getByTestId("page-communities")).toBeVisible();
    await page.getByTestId("expand-community-members").click();
    await expect(page.getByTestId("community-members-panel")).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "04-communities.png") });

    // 5. Network Science page
    console.log("[e2e] network science");
    await page.getByTestId("tab-network").click();
    await expect(page.getByTestId("page-network-science")).toBeVisible();
    await expect(page.getByTestId("page-network-science")).toContainText("igraph average local clustering");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "05-network-science.png") });

    // 6. Ask page: scripted demo trace, subgraph & citations -> Node 360
    console.log("[e2e] ask demo");
    await page.getByTestId("tab-ask").click();
    await expect(page.getByTestId("page-ask")).toBeVisible();
    await page.getByTestId("demo-btn-demo-01-worked-example").click();
    await expect(page.getByTestId("ask-answer-text")).not.toBeEmpty({ timeout: 30_000 });
    await expect(page.getByTestId("ask-trace")).toBeVisible();
    await expect(page.getByTestId("ask-subgraph")).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "06-ask-demo-trace.png") });

    // Keyboard Tab navigation + contrast sanity check
    await page.getByTestId("tab-ask").focus();
    await page.keyboard.press("Tab");
    const focusedTag = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedTag).toBe("BUTTON");
    const contrastOk = await page.evaluate(() => {
      const s = getComputedStyle(document.body);
      return s.color !== s.backgroundColor;
    });
    expect(contrastOk).toBe(true);

    // 7. Node 360 page
    console.log("[e2e] node360");
    await page.getByTestId("tab-node360").click();
    await expect(page.getByTestId("page-node360")).toBeVisible();
    await expect(page.getByTestId("page-node360")).toContainText("Neighborhood");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "07-node360.png") });

    // 8. About the data page
    console.log("[e2e] about");
    await page.getByTestId("tab-about").click();
    await expect(page.getByTestId("page-about-data")).toBeVisible();
    await expect(page.getByTestId("page-about-data")).toContainText("enriched-cb371912e308");
    await expect(page.getByTestId("page-about-data")).toContainText("AI-assessed");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "08-about-data.png") });

    expect(errors).toEqual([]);
  });
});
