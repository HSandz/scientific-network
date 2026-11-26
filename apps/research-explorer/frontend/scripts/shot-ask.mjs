// Dev helper: run Ask demos and capture each evidence tab. Usage: node scripts/shot-ask.mjs <outdir> <demoId> [width] [theme]
import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
const [outDir, demo = "demo-01-worked-example", width = "1440", theme = "light"] = process.argv.slice(2);
const base = process.env.BASE || "http://127.0.0.1:5175";
fs.mkdirSync(outDir, { recursive: true });
const browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", args: ["--no-sandbox"] });
const w = Number(width);
const ctx = await browser.newContext({ viewport: { width: w, height: w <= 768 ? 844 : 900 }, colorScheme: theme });
const page = await ctx.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
await page.goto(base + "/ask", { waitUntil: "networkidle" });
await page.getByTestId(`demo-btn-${demo}`).click();
await page.waitForTimeout(1600);
await page.screenshot({ path: path.join(outDir, `${demo}-${w}-${theme}-mid.png`) });
await page.getByTestId("faithfulness-badge").waitFor({ timeout: 30000 }).catch(() => {});
await page.waitForTimeout(1200);
const tag = `${demo}-${w}-${theme}`;
await page.screenshot({ path: path.join(outDir, `${tag}-done.png`) });
for (const t of ["chart", "table", "papers"]) {
  const b = page.getByTestId(`ev-tab-${t}`);
  if (await b.isVisible()) { await b.click(); await page.waitForTimeout(900); await page.screenshot({ path: path.join(outDir, `${tag}-${t}.png`) }); }
}
console.log("url", page.url());
if (errors.length) console.log("ERRORS:\n" + errors.join("\n"));
await browser.close();
