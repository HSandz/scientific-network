// Dev helper: ask a live question through the UI (cache off) and time the stream as the user sees it.
// Usage: node scripts/live-ask.mjs <outdir> "<question>" [tag]
import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
const [outDir, question, tag = "live"] = process.argv.slice(2);
const base = process.env.BASE || "http://127.0.0.1:5175";
fs.mkdirSync(outDir, { recursive: true });
const browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", args: ["--no-sandbox"] });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: "light" });
const page = await ctx.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto(base + "/ask", { waitUntil: "networkidle" });
await page.getByTestId("ask-settings").click();
await page.getByTestId("ask-use-cache").uncheck();
await page.keyboard.press("Escape");
await page.getByTestId("ask-input").fill(question);
const t0 = Date.now();
await page.getByTestId("ask-submit").click();
const marks = {};
const until = Date.now() + 180000;
let shotMid = false;
while (Date.now() < until) {
  const s = await page.evaluate(() => ({
    steps: document.querySelectorAll('[data-testid="ask-trace"] li[data-state="done"]').length,
    active: document.querySelectorAll('[data-testid="ask-trace"] li[data-state="active"]').length,
    answer: (document.querySelector('[data-testid="ask-answer-text"]')?.textContent || "").length,
    done: !!document.querySelector('[data-testid="faithfulness-badge"]') || !!document.querySelector(".checkline.is-warn"),
    graph: Number(document.querySelector('[data-testid="ask-subgraph"]')?.getAttribute("data-graph-revealed") ?? -1),
  }));
  const t = (Date.now() - t0) / 1000;
  if (s.steps >= 1 && marks.first_step_done == null) marks.first_step_done = t;
  if (s.graph >= 1 && marks.graph_first_hop == null) marks.graph_first_hop = t;
  if (s.answer > 0 && marks.first_answer_text == null) marks.first_answer_text = t;
  if (s.answer > 0 && !shotMid) { await page.screenshot({ path: path.join(outDir, `${tag}-streaming.png`) }); shotMid = true; }
  if (s.done) { marks.done = t; marks.steps_done = s.steps; break; }
  await page.waitForTimeout(100);
}
await page.waitForTimeout(500);
await page.screenshot({ path: path.join(outDir, `${tag}-done.png`) });
const faithful = await page.getByTestId("faithfulness-badge").getAttribute("data-passed").catch(() => null);
const answer = await page.getByTestId("ask-answer-text").textContent().catch(() => "");
const out = { question, marks, faithful, answer_chars: (answer || "").length, errors };
console.log(JSON.stringify(out));
fs.writeFileSync(path.join(outDir, `${tag}.json`), JSON.stringify(out, null, 2));
await browser.close();
