// Read-only UI verification; screenshots require visual inspection after capture.
import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
const [base, output] = process.argv.slice(2);
if (!base || !output) throw Error("Usage: node scripts/verify-visuals.mjs BASE_URL UNUSED_OUTPUT_DIRECTORY");
await mkdir(output, { recursive: false });
const browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", args: ["--no-sandbox"] });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce" });
const errors = [], observations = [];
page.on("pageerror", e => errors.push(e.message));
page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
const capture = async (name) => {
  await page.screenshot({ path: path.join(output, name + ".png") });
  observations.push({ name, viewport: page.viewportSize(), overflow: await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), alerts: await page.locator('[role="alert"]').allTextContents() });
};
try {
  for (const mode of ["heterogeneous", "organizations", "researchers", "citations"]) {
    await page.goto(`${base}/?mode=${mode}`);
    await page.waitForFunction(() => /Displayed: [1-9]/.test(document.querySelector('[data-testid="displayed-counts"]')?.textContent || ""));
    await capture(`mode-${mode}`);
  }
  await page.goto(`${base}/?mode=organizations`);
  await page.waitForFunction(() => /Displayed: [1-9]/.test(document.querySelector('[data-testid="displayed-counts"]')?.textContent || ""));
  for (const width of [390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const dark of [true, false]) {
      if (await page.locator("html").evaluate(el => el.classList.contains("dark")) !== dark) await page.getByTestId("theme-toggle").click();
      await page.waitForTimeout(150);
      await capture(`graph-${width}-${dark ? "dark" : "light"}`);
    }
  }
  await page.getByTestId("tab-analytics").click();
  await page.getByTestId("analytics-view").waitFor();
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const dark of [true, false]) {
      if (await page.locator("html").evaluate(el => el.classList.contains("dark")) !== dark) await page.getByTestId("theme-toggle").click();
      for (const [section, label] of [["robustness", "Evidence sensitivity"], ["topics", "Topic evolution"], ["communities", "Components & communities"], ["sectors", "Academia–industry"], ["trajectories", "Citations & annual metrics"]]) {
        await page.getByRole("button", { name: label, exact: true }).click();
        // Scroll the first analytical panel into view, keeping charts readable on phones.
        await page.getByTestId("analytics-view").locator("section").nth(2).scrollIntoViewIfNeeded();
        await page.waitForTimeout(180);
        await capture(`${section}-${width}-${dark ? "dark" : "light"}`);
      }
    }
  }
  await writeFile(path.join(output, "verification.json"), JSON.stringify({ base, reducedMotion: true, errors, observations }, null, 2));
  if (errors.length || observations.some(o => o.overflow || o.alerts.length)) throw Error("Inspect verification.json for browser errors/overflow/alerts");
  console.log(JSON.stringify({ screenshots: observations.length, browserErrors: errors.length, overflows: 0, alerts: 0 }));
} finally { await browser.close(); }
