import type { Page } from "@playwright/test";

/**
 * In-app navigation for the redesigned shell (WORK-2026-11-26-003). The v4 Analytics dashboard
 * now lives under Network → "Release graph (v4) analysis" and the graph under Explore; these
 * helpers click through the rail on desktop or the bottom tab bar's More sheet on narrow
 * screens, so Explorer state is kept exactly as the old in-page tabs kept it.
 */
async function openFromNav(page: Page, key: "network" | "explore") {
  const rail = page.getByTestId(`nav-${key}`);
  if (await rail.isVisible()) {
    await rail.click();
    return;
  }
  await page.getByTestId("tabbar-more").click();
  await page.getByRole("menuitem", { name: key === "network" ? "Network" : "Explore" }).click();
}

export async function openReleaseAnalysis(page: Page) {
  await openFromNav(page, "network");
  await page.getByTestId("network-view-release").click();
}

export async function openExploreGraph(page: Page) {
  await openFromNav(page, "explore");
  await page.getByTestId("tab-graph").click();
}
