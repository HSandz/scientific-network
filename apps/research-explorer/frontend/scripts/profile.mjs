// Local descriptive browser timings, not a capacity benchmark. No production writes.
import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
const [base, output] = process.argv.slice(2);
if (!base || !output)
  throw Error(
    "Usage: node scripts/profile.mjs BASE_URL UNIQUE_OUTPUT_DIRECTORY",
  );
await mkdir(output, { recursive: false });
const browser = await chromium.launch({
  executablePath: "/usr/bin/google-chrome",
  args: ["--no-sandbox"],
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
});
const page = await context.newPage();
const result = {
  base,
  environment:
    "Chromium, Linux/WSL, local Vite dev + FastAPI + same local Neo4j; 1440x900, no throttling; one cold browser then warm reload",
  samples: [],
};
for (const phase of ["cold", "warm"]) {
  const begin = performance.now();
  await page.goto(`${base}/?mode=researchers`);
  await page.waitForFunction(() =>
    /Displayed: [1-9][\d,]* nodes/.test(
      document.querySelector('[data-testid="displayed-counts"]')?.textContent ||
        "",
    ),
  );
  await page.evaluate(
    () =>
      new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))),
  );
  result.samples.push({ phase, graph_ready_ms: performance.now() - begin });
}
const metrics = await page.evaluate(async () => {
  const store =
    window.__explorerStore ||
    (await import("/src/stores/useExplorerStore.ts")).useExplorerStore;
  const view = await (await fetch("/api/views/researchers?limit=100"))
    .json()
    .catch(() => ({ nodes: [] }));
  const ids = view.nodes.slice(0, 12).map((n) => n.id);
  const container = document.querySelector(
    '[data-testid="sigma-canvas-container"]',
  );
  let canvasInsertions = 0;
  const observer = new MutationObserver((rows) => {
    for (const row of rows)
      for (const el of row.addedNodes)
        if (el.nodeName === "CANVAS") canvasInsertions++;
  });
  observer.observe(container, { childList: true, subtree: true });
  const samples = [],
    frames = [];
  for (const id of ids) {
    const t = performance.now();
    store.getState().selectNode(id);
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    samples.push(performance.now() - t);
  }
  let last = await new Promise(requestAnimationFrame);
  for (let i = 0; i < 120; i++) {
    const now = await new Promise(requestAnimationFrame);
    frames.push(now - last);
    last = now;
  }
  observer.disconnect();
  samples.sort((a, b) => a - b);
  frames.sort((a, b) => a - b);
  return {
    selection_samples_ms: samples,
    selection_median_ms: samples[Math.floor(samples.length / 2)],
    frame_intervals_ms: frames,
    frame_p95_ms: frames[Math.floor(frames.length * 0.95)],
    canvas_insertions_during_12_selections: canvasInsertions,
    js_heap_bytes: performance.memory?.usedJSHeapSize ?? null,
  };
});
result.interaction = metrics;
const expansionStart = performance.now();
const response = page.waitForResponse(
  (r) => r.url().includes("/neighbors?") && r.status() === 200,
);
await page.getByTestId("canvas-expand-hop").click();
await response;
await page.evaluate(
  () =>
    new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))),
);
result.expansion_response_and_two_frames_ms =
  performance.now() - expansionStart;
result.browser_version = browser.version();
await writeFile(
  path.join(output, "profile.json"),
  JSON.stringify(result, null, 2) + "\n",
);
await page.screenshot({ path: path.join(output, "profile.png") });
await browser.close();
console.log(JSON.stringify(result));
