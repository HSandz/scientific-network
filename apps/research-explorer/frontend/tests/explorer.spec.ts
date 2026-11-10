import { test, expect } from "@playwright/test";
import path from "path";

const ARTIFACT_DIR =
  process.env.EXPLORER_SCREENSHOT_DIR ||
  "/home/san/.gemini/antigravity-cli/brain/7dfac094-4740-45fc-9c25-6d095da4fba9";

test.describe("Scientific Network Explorer E2E Verification", () => {
  test("1. Loads Mode A, verifies release-v4 inventory, switches across Modes B, C, D, and toggles theme", async ({
    page,
  }) => {
    const consoleErrors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto("/");

    // Verify header and release v4 graph version badge
    await expect(page.getByTestId("graph-version-badge")).toContainText(
      "release-d3c788c3114a",
      { timeout: 15_000 }
    );

    // Verify Mode A (Researcher Collaboration) loads with full projection count 32,189
    await expect(page.getByTestId("projection-title")).toContainText(
      "Researcher Collaboration"
    );
    await expect(page.getByTestId("full-projection-counts")).toContainText(
      "32,189"
    );
    await expect(page.getByTestId("graph-legend")).toBeVisible();

    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "explorer-mode-a-researchers.png"),
    });

    // Switch to Mode B (Organization Collaboration)
    await page.getByTestId("mode-organizations").click();
    await expect(page.getByTestId("projection-title")).toContainText(
      "Organization Collaboration"
    );
    await expect(page.getByTestId("full-projection-counts")).toContainText(
      "2,047"
    );

    // Filter Cross-Sector Only in Mode B
    await page.getByTestId("filter-cross-sector").check();
    await expect(page.getByTestId("displayed-counts")).toBeVisible();

    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "explorer-mode-b-organizations.png"),
    });

    // Switch to Mode C (Within-Corpus Citation Network)
    await page.getByTestId("mode-citations").click();
    await expect(page.getByTestId("projection-title")).toContainText(
      "Citation Network"
    );
    await expect(page.getByTestId("full-projection-counts")).toContainText(
      "13,617"
    );

    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "explorer-mode-c-citations.png"),
    });

    // Switch to Mode D (Heterogeneous Knowledge Graph)
    await page.getByTestId("mode-heterogeneous").click();
    await expect(page.getByTestId("projection-title")).toContainText(
      "Heterogeneous Knowledge Graph"
    );
    await expect(page.getByTestId("full-projection-counts")).toContainText(
      "47,875"
    );

    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "explorer-mode-d-heterogeneous.png"),
    });

    // Toggle light/dark theme
    const html = page.locator("html");
    await expect(html).toHaveClass(/dark/);
    await page.getByTestId("theme-toggle").click();
    await expect(html).not.toHaveClass(/dark/);
    await page.getByTestId("theme-toggle").click();
    await expect(html).toHaveClass(/dark/);

    expect(consoleErrors).toEqual([]);
  });

  test("2. Searches full database beyond top-100 via keyboard shortcut (/), expands +1 hop neighborhood, and inspects Mode E edge provenance", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByTestId("projection-title")).toContainText(
      "Researcher Collaboration",
      { timeout: 15_000 }
    );

    // Press `/` to open global search modal
    await page.keyboard.press("/");
    await expect(page.getByTestId("search-modal")).toBeVisible();

    // Press Escape to close and reopen via button
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("search-modal")).toBeHidden();

    await page.getByTestId("open-global-search").click();
    const input = page.getByTestId("global-search-input");

    // Test accent-insensitive search: typing "Tuomas Sandholm" matches "Tüomas Sandholm"
    await input.fill("Tuomas Sandholm");
    await expect(page.getByTestId("search-modal")).toContainText("Tüomas Sandholm", {
      timeout: 10_000,
    });

    // Test keyboard ArrowDown and Enter navigation in search modal
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("Enter");

    // Right inspector should now display Tüomas Sandholm
    await expect(page.getByTestId("inspector-node-name")).toContainText(
      "Tüomas Sandholm",
      { timeout: 10_000 }
    );

    // Search Piotr Faliszewski
    await page.getByTestId("open-global-search").click();
    await input.fill("Piotr Faliszewski");
    await expect(page.getByTestId("search-modal")).toContainText("Piotr Faliszewski", {
      timeout: 10_000,
    });

    // Wait for search result outside top-100 illustration and click Focus & +1 Hop
    const focusBtn = page
      .locator('[data-testid^="search-focus-graph-researcher:"]')
      .first();
    await expect(focusBtn).toBeVisible({ timeout: 10_000 });
    await focusBtn.click();

    // Right inspector should now display Piotr Faliszewski
    await expect(page.getByTestId("inspector-node-name")).toContainText(
      "Piotr Faliszewski",
      { timeout: 10_000 }
    );

    // Inspect an edge's Mode E provenance using the quick sample edge button
    await page.getByTestId("quick-sample-edge").click();
    await expect(
      page.getByTestId("evidence-derivation-explanation")
    ).toBeVisible({ timeout: 10_000 });

    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "explorer-mode-e-evidence-inspector.png"),
    });
  });

  test("3. Navigates Table View, Analytics View, Shortest-Path Finder, and Entity Comparison", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByTestId("graph-version-badge")).toBeVisible({
      timeout: 15_000,
    });

    // Switch to Table View
    await page.getByTestId("tab-table").click();
    await expect(page.getByTestId("table-view")).toBeVisible();

    // Switch to Accepted Edges table
    await page.getByTestId("table-mode-edges").click();
    const firstEdgeRow = page
      .locator('[data-testid^="table-edge-row-"]')
      .first();
    await expect(firstEdgeRow).toBeVisible({ timeout: 10_000 });
    await firstEdgeRow.click();
    await expect(
      page.getByTestId("evidence-derivation-explanation")
    ).toBeVisible({ timeout: 10_000 });

    // Switch to Analytics View
    await page.getByTestId("tab-analytics").click();
    await expect(page.getByTestId("analytics-view")).toBeVisible();
    await expect(page.getByTestId("analytics-view")).toContainText("96.50%");
    await expect(page.getByTestId("analytics-view")).toContainText("73.71%");
    await expect(page.getByTestId("analytics-view")).toContainText("48,259 / 65,469");
    await expect(page.getByTestId("analytics-view")).toContainText("85.00%");
    await expect(page.getByTestId("analytics-view")).toContainText("68.63%");
    await expect(page.getByTestId("analytics-view")).toContainText("0.4667");

    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "explorer-analytics-overview.png"),
    });

    // Open Shortest-Path Finder Modal and run path discovery
    await page.getByTestId("open-path-finder").click();
    await expect(page.getByTestId("path-finder-modal")).toBeVisible();
    await expect(page.getByTestId("path-finder-modal")).toHaveAttribute("role", "dialog");
    await expect(page.getByTestId("path-finder-modal")).toHaveAttribute("aria-modal", "true");
    await page.getByTestId("run-path-search-btn").click();
    await expect(page.getByTestId("path-finder-modal")).toContainText(
      "Path Found",
      { timeout: 15_000 }
    );
    await page.keyboard.press("Escape");

    // Open Compare Modal and verify Shanghai Jiao Tong University vs Tencent comparison
    await page.getByTestId("open-compare-modal").click();
    await expect(page.getByTestId("compare-modal")).toBeVisible();
    await expect(page.getByTestId("compare-modal")).toHaveAttribute("role", "dialog");
    await expect(page.getByTestId("compare-modal")).toHaveAttribute("aria-modal", "true");
    await expect(page.getByTestId("compare-modal")).toContainText(
      "Shanghai Jiao Tong University",
      { timeout: 15_000 }
    );
    await expect(page.getByTestId("compare-modal")).toContainText(
      "Tencent (China)"
    );
    await page.keyboard.press("Escape");

    // Open Caveats Modal and verify unified denominators and gate status
    await page.getByTestId("open-caveats-modal").click();
    await expect(page.getByTestId("caveats-modal")).toBeVisible();
    await expect(page.getByTestId("caveats-modal")).toHaveAttribute("role", "dialog");
    await expect(page.getByTestId("caveats-modal")).toHaveAttribute("aria-modal", "true");
    await expect(page.getByTestId("caveats-modal")).toContainText("48,259/65,469");
    await expect(page.getByTestId("caveats-modal")).toContainText("85.00%");
    await expect(page.getByTestId("caveats-modal")).toContainText("68.63%");
    await expect(page.getByTestId("caveats-modal")).toContainText("0.4667");
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("caveats-modal")).toBeHidden();
  });

  test("4. Verifies contextual inspector, responsive tablet/phone drawers, table DB incident edge counts, and theme persistence", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByTestId("displayed-counts")).toBeVisible({
      timeout: 15_000,
    });

    // Inspector should be closed initially when nothing is selected
    await expect(page.getByTestId("right-inspector")).toHaveCount(0);

    // Table view should not render graph filter sidebar and should display DB incident edges
    await page.getByTestId("tab-table").click();
    await expect(page.getByTestId("left-sidebar")).toHaveCount(0);
    await expect(page.getByTestId("table-view")).toContainText("58 edges", {
      timeout: 10_000,
    });

    // Toggle to light theme and reload to verify localStorage persistence
    await page.getByTestId("theme-toggle").click();
    await expect(page.locator("html")).not.toHaveClass(/dark/);
    await page.reload();
    await expect(page.locator("html")).not.toHaveClass(/dark/);
    await page.getByTestId("theme-toggle").click();
    await expect(page.locator("html")).toHaveClass(/dark/);

    // Verify soft graphite dark tokens (not harsh #101010 or #171717)
    const groundBg = await page.evaluate(() => {
      const el = document.querySelector(".bg-ground");
      return el ? window.getComputedStyle(el).backgroundColor : "";
    });
    expect(groundBg).toBe("rgb(30, 30, 30)");

    // Verify phone viewport (390x844) keeps full workspace width and compact layout
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    await expect(page.getByTestId("displayed-counts")).toBeVisible({
      timeout: 15_000,
    });
    const mainWidth = await page
      .locator("main")
      .evaluate((el) => el.getBoundingClientRect().width);
    expect(mainWidth).toBeGreaterThanOrEqual(380);

    // Verify phone header is a single compact row (<= 60px)
    const headerBox = await page.locator("header").boundingBox();
    expect(headerBox?.height).toBeLessThanOrEqual(60);

    // Verify phone graph canvas height is >= 422px (>= 50% of 844px) and starts in upper third (top <= 281px)
    const canvasBox = await page.getByTestId("sigma-canvas-container").boundingBox();
    expect(canvasBox?.height).toBeGreaterThanOrEqual(422);
    expect(canvasBox?.y).toBeLessThanOrEqual(281);

    await page.locator('[data-testid^="quick-node-"]').first().click();
    await expect(page.getByTestId("inspector-mobile-back")).toBeVisible();
    await page.getByTestId("inspector-mobile-back").click();
    await expect(page.getByTestId("right-inspector")).toHaveCount(0);

    // Verify 1100px desktop keeps graph width >= 600px when inspector is open
    await page.setViewportSize({ width: 1100, height: 800 });
    await page.locator('[data-testid^="quick-node-"]').first().click();
    await expect(page.getByTestId("right-inspector")).toBeVisible();
    const canvas1100 = await page.getByTestId("sigma-canvas-container").boundingBox();
    expect(canvas1100?.width).toBeGreaterThanOrEqual(600);

    // Switching to table restores wide view, return to graph restores inspector
    await page.getByTestId("tab-table").click();
    await expect(page.getByTestId("right-inspector")).toHaveCount(0);
    await page.getByTestId("tab-graph").click();
    await expect(page.getByTestId("right-inspector")).toBeVisible();
  });
});
