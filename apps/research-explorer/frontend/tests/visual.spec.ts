import { test, expect } from "@playwright/test";
// Frozen release and reduced motion make these reviewed Chromium baselines reproducible.
test.use({ reducedMotion: "reduce", viewport: { width: 1440, height: 900 } });
test("analytics overview desktop and mobile visual baseline", async ({
  page,
}) => {
  await page.goto("/?tab=analytics");
  await expect(
    page.getByRole("heading", {
      name: "Explore the AI Research Network",
      exact: true,
    }),
  ).toBeInViewport();
  await expect(page.getByTestId("analytics-view")).toContainText("96.50%");
  await expect(page).toHaveScreenshot("analytics-overview-desktop.png", {
    maxDiffPixelRatio: 0.01,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page).toHaveScreenshot("analytics-overview-mobile.png", {
    maxDiffPixelRatio: 0.01,
  });
});
test("graph fit-view and close-view visual baselines", async ({ page }) => {
  await page.goto("/?mode=heterogeneous");
  const canvas = page.getByTestId("sigma-canvas-container");
  await expect(page.getByTestId("displayed-counts")).toContainText(
    /Displayed: [1-9]/,
  );
  await expect(canvas).toHaveAttribute("data-label-band", "overview");
  await expect(page).toHaveScreenshot("graph-overview.png", {
    maxDiffPixelRatio: 0.01,
  });
  for (let i = 0; i < 4; i++)
    await page.getByRole("button", { name: "Zoom in", exact: true }).click();
  await expect(canvas).toHaveAttribute("data-label-band", "close");
  await expect(page).toHaveScreenshot("graph-close.png", {
    maxDiffPixelRatio: 0.01,
  });
});
