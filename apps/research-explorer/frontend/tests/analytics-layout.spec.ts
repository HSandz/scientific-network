import { test, expect, type Locator } from "@playwright/test";
import path from "node:path";
const out = process.env.EXPLORER_SCREENSHOT_DIR || "/tmp/explorer-focus";
async function active(plot: Locator) {
  await plot.scrollIntoViewIfNeeded();
  await expect(plot).toHaveAttribute("data-chart-active", "true");
}
for (const [width, height] of [
  [1440, 900],
  [1024, 768],
  [768, 1024],
  [390, 844],
])
  test(`intentional section geometry and navigation at ${width}×${height}`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height });
    await page.emulateMedia({ reducedMotion: "reduce" });
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("/?tab=analytics");
    await expect(page.getByTestId("analytics-view")).toBeVisible();
    for (const theme of ["dark", "light"]) {
      if (theme === "light") await page.getByTestId("theme-toggle").click();
      for (const section of ["robustness", "sectors", "trajectories"]) {
        const el = page.locator("#analytics-" + section);
        await el.evaluate((e) => e.scrollIntoView({ block: "start" }));
        await expect(page.locator("#heading-" + section)).toBeInViewport();
        const cards = await el.locator(".analytics-panel").evaluateAll((els) =>
          els.map((e) => {
            const r = e.getBoundingClientRect();
            return {
              x: r.x,
              y: r.y,
              w: r.width,
              h: r.height,
              bottom: r.bottom,
            };
          }),
        );
        const sectionWidth = await el
          .locator(
            section === "sectors"
              ? ".sector-layout"
              : section === "robustness"
                ? ".robustness-layout"
                : ".trajectory-layout",
          )
          .evaluate((e) => e.clientWidth);
        if (section === "sectors" && sectionWidth > 850) {
          expect(Math.abs(cards[0].y - cards[1].y)).toBeLessThan(2);
          expect(Math.abs(cards[0].h - cards[1].h)).toBeLessThan(300);
          expect(cards[2].w).toBeGreaterThan(sectionWidth * 0.98);
          expect(
            cards[2].y - Math.max(cards[0].bottom, cards[1].bottom),
          ).toBeCloseTo(16, 0);
        } else
          for (let i = 0; i < cards.length; i++) {
            expect(cards[i].w).toBeGreaterThan(sectionWidth * 0.98);
            if (i) expect(cards[i].y - cards[i - 1].bottom).toBeCloseTo(16, 0);
          }
        const header = await page.locator("#heading-" + section).boundingBox(),
          nav = await page
            .getByRole("navigation", { name: "Analytical sections" })
            .boundingBox();
        expect(header!.y).toBeGreaterThanOrEqual(nav!.y + nav!.height);
        const activeNav = page.getByRole("navigation", {name:"Analytical sections"}).locator('[aria-pressed="true"]');
        await expect(activeNav).toHaveText(section === "robustness" ? "Evidence sensitivity" : section === "sectors" ? "Sectors" : "Citations");
        const activeBox = (await activeNav.boundingBox())!;
        expect(activeBox.x).toBeGreaterThanOrEqual(nav!.x);
        expect(activeBox.x + activeBox.width).toBeLessThanOrEqual(nav!.x + nav!.width + 1);

        expect(
          await page
            .getByTestId("analytics-view")
            .evaluate((e) => e.scrollWidth - e.clientWidth),
        ).toBeLessThanOrEqual(1);
        await page.screenshot({
          path: path.join(out, `layout-${section}-${width}-${theme}.png`),
        });
      }
    }
    expect(errors).toEqual([]);
  });

test("partnership bars select exact topic and names; evidence and comparison stay available", async ({
  page,
}) => {
  let data: any;
  page.on("response", async (r) => {
    if (r.url().includes("/analytics/overview") && r.status() === 200)
      data = await r.json();
  });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/?tab=analytics");
  await page.getByRole("button", { name: "Sectors", exact: true }).click();
  const plot = page.locator(
    '[data-chart-label="Leading cross-sector pair-topic evidence"]',
  );
  await active(plot);
  const index = 2,
    pair = data.academia_industry_pairs[index];
  const xy = await plot.evaluate(
    (el: any, i) =>
      el.__chart.convertToPixel({ seriesIndex: 0 }, [
        el.__chart.getOption().series[0].data[i].value,
        i,
      ]),
    index,
  );
  const b = (await plot.boundingBox())!;
  await page.mouse.click(b.x + xy[0] - 5, b.y + xy[1]);
  const detail = page.getByTestId("partnership-details");
  await expect(
    page.getByLabel("Selected partnership", { exact: true }),
  ).toHaveValue(String(index));
  await expect(detail).toContainText(
    `${pair.academia_organization} ↔ ${pair.industry_organization}`,
  );
  await expect(detail).toContainText(pair.topic);
  await expect(detail).toContainText(
    `${pair.supported_paper_count} distinct supporting papers`,
  );
  await detail.getByText("Selected partnership paper evidence · data").click();
  await expect(detail.getByRole("table")).toContainText(
    pair.supporting_papers[0].title,
  );
  await detail
    .getByRole("button", { name: "Compare portfolios & supporting papers" })
    .click();
  expect(
    await page.evaluate(() => {
      const s = (window as any).__explorerStore.getState();
      return [s.compareLeftId, s.compareRightId];
    }),
  ).toEqual([pair.academia_organization_id, pair.industry_organization_id]);
});

test("persistence cell identity survives reordered rows and missing years; tooltip escapes full names", async ({
  page,
  request,
}) => {
  const response = await request.get(
    `http://127.0.0.1:${process.env.PLAYWRIGHT_API_PORT || 8000}/api/analytics/overview`,
  );
  const data = await response.json();
  const pairs = data.explorer_derived.organization_pair_persistence
    .slice(0, 4)
    .reverse();
  pairs[0].source = "<img src=x onerror=alert(1)> & University";
  pairs[0].by_year = pairs[0].by_year.filter((y: any) => y.year !== 2023);
  data.explorer_derived.organization_pair_persistence = pairs;
  await page.route("**/api/analytics/overview", (r) =>
    r.fulfill({ json: data }),
  );
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/?tab=analytics");
  await page
    .getByRole("heading", {
      name: "Organization collaboration persistence by supported paper year",
      exact: true,
    })
    .scrollIntoViewIfNeeded();
  const plot = page.locator(
    '[data-chart-label="Organization pair-by-year persistence"]',
  );
  await active(plot);
  const rendered = await plot.evaluate(
    (el: any) => el.__chart.getOption().series[0].data,
  );
  expect(rendered[2].value).toEqual([2, 0, null]);
  expect(rendered[0].sourceId).toBe(pairs[0].source_id);
  const tooltip = await plot.evaluate((el: any) => {
    const o = el.__chart.getOption();
    return o.tooltip[0].formatter({
      data: o.series[0].data[0],
      value: o.series[0].data[0].value,
    });
  });
  expect(tooltip).toContain("&lt;img");
  expect(tooltip).not.toContain("<img");
  expect(tooltip).toContain(pairs[0].target);
  expect(tooltip).toContain("Year: 2021");
  expect(tooltip).toContain("Distinct supporting papers:");
  // Click a real canvas cell after rows were filtered/reversed; never derive its identity from dataIndex.
  const xy = await plot.evaluate((el: any) =>
    el.__chart.convertToPixel({ seriesIndex: 0 }, [1, 1]),
  );
  const b = (await plot.boundingBox())!;
  await page.mouse.click(b.x + xy[0], b.y + xy[1]);
  expect(
    await page.evaluate(() => {
      const s = (window as any).__explorerStore.getState();
      return [s.compareLeftId, s.compareRightId];
    }),
  ).toEqual([pairs[1].source_id, pairs[1].target_id]);
});

test("compact bridge summary retains complete ranking and exact researcher links", async ({
  page,
}) => {
  await page.goto("/?tab=analytics");
  await expect(page.getByTestId("analytics-view")).toBeVisible();
  const section = page.locator("#analytics-robustness");
  await section.evaluate((e) => e.scrollIntoView({ block: "start" }));
  await expect(section.locator(".bridge-matrix-row")).toHaveCount(6);
  await section.getByText("Bridge ranking comparison · data").click();
  const table = section.getByRole("table", {
    name: "Bridge ranking comparison",
  });
  await expect(table.locator("tbody tr")).toHaveCount(40);
  await expect(table).toContainText("Outside top 20");
  const target = await table.locator("tbody button").first().textContent();
  await table.locator("tbody button").first().click();
  await expect(page.getByTestId("inspector-node-name")).toHaveText(target!);
});
