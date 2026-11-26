// Dev helper: screenshot app routes. Usage: node scripts/shot.mjs <outdir> <width> <theme> <path>[ <path>...]
import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
const [outDir, width = "1440", theme = "light", ...paths] = process.argv.slice(2);
const base = process.env.BASE || "http://127.0.0.1:5175";
fs.mkdirSync(outDir, { recursive: true });
const browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", args: ["--no-sandbox"] });
const w = Number(width);
const ctx = await browser.newContext({ viewport: { width: w, height: w <= 768 ? 844 : 900 }, colorScheme: theme === "dark" ? "dark" : "light", deviceScaleFactor: 1 });
const page = await ctx.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
for (const p of paths) {
  const [route, wait = "1500", full = ""] = p.split("|");
  await page.goto(base + route, { waitUntil: "networkidle" }).catch(() => {});
  await page.waitForTimeout(Number(wait));
  const name = (route.replace(/[^a-z0-9]+/gi, "_") || "root") + `-${w}-${theme}${full ? "-full" : ""}.png`;
  if (full) {
    // Expand the internal scroller so a full-page shot shows everything.
    await page.evaluate(() => { const m = document.getElementById("main-content"); if (m) { document.querySelector(".app-shell").style.height = "auto"; document.querySelector(".shell-main").style.height = "auto"; m.style.overflow = "visible"; document.querySelector(".app-shell").style.overflow = "visible"; } });
  }
  await page.screenshot({ path: path.join(outDir, name), fullPage: !!full });
  console.log("shot", name);
}
if (errors.length) console.log("ERRORS:\n" + errors.join("\n"));
await browser.close();
