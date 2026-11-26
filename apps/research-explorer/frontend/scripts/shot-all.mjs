// Screenshot every Navigator page: desktop light, desktop dark and mobile.
// Usage: node scripts/shot-all.mjs <outdir>   (BASE defaults to http://127.0.0.1:5175)
import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const [outDir] = process.argv.slice(2);
const base = process.env.BASE || "http://127.0.0.1:5175";
const PAGES = [
  ["01-pulse", "/"],
  ["02-ask", "/ask", "demo"],
  ["03-trends", "/trends"],
  ["04-topics", "/topics"],
  ["05-topic", "/topics/method:Q3621696"],
  ["06-groups", "/groups/organization:I19820366"],
  ["07-map", "/map"],
  ["08-network", "/network"],
  ["09-node", "/node/researcher:openalex:A5008056593"],
  ["10-explore", "/explore"],
  ["11-about", "/about"],
];
const VARIANTS = [
  ["desktop-light", 1440, 900, "light"],
  ["desktop-dark", 1440, 900, "dark"],
  ["mobile", 390, 844, "light"],
];
const browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", args: ["--no-sandbox"] });
const errors = [];
for (const [variant, width, height, scheme] of VARIANTS) {
  fs.mkdirSync(path.join(outDir, variant), { recursive: true });
  for (const [name, route, action] of PAGES) {
    const ctx = await browser.newContext({ viewport: { width, height }, colorScheme: scheme, reducedMotion: "reduce" });
    const page = await ctx.newPage();
    page.on("pageerror", (e) => errors.push(`${variant} ${route}: ${e.message}`));
    await page.goto(base + route, { waitUntil: "networkidle" }).catch(() => {});
    await page.locator("#main-content > *").first().waitFor();
    if (action === "demo") {
      await page.getByTestId("demo-btn-demo-01-worked-example").click();
      await page.getByTestId("faithfulness-badge").waitFor({ timeout: 30_000 });
      await page.evaluate(() => { const c = document.querySelector(".convo-scroll"); if (c) c.scrollTop = 0; });
    }
    await page.waitForTimeout(name === "10-explore" ? 3500 : 1500);
    await page.screenshot({ path: path.join(outDir, variant, `${name}.png`) });
    await ctx.close();
  }
  console.log("done", variant);
}
console.log(errors.length ? `ERRORS:\n${errors.join("\n")}` : "no page errors");
await browser.close();
