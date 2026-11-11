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

test('analytical section layouts desktop and phone in both themes',async({page})=>{
  test.setTimeout(90000);
  await page.goto('/?tab=analytics');await expect(page.getByTestId('analytics-view')).toBeVisible();
  for(const width of [1440,390]) {
    await page.setViewportSize({width,height:width===1440?900:844});
    for(const dark of [true,false]) {
      await page.evaluate(d=>{const s=(window as any).__explorerStore;if(s.getState().darkMode!==d)s.getState().toggleDarkMode();},dark);
      for(const section of ['robustness','sectors','trajectories']) {
        const el=page.locator('#analytics-'+section);await el.evaluate(e=>e.scrollIntoView({block:'start'}));
        await expect(el.locator('[data-chart-label]').first()).toHaveAttribute('data-chart-active','true');
        await expect(page).toHaveScreenshot(`analytics-${section}-${width}-${dark?'dark':'light'}.png`,{maxDiffPixelRatio:.01});
      }
    }
  }
});
