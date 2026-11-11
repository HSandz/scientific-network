import { test, expect, type Page, type Locator } from "@playwright/test";
import path from "node:path";
test.use({ viewport: { width: 1440, height: 900 } });
const out = process.env.EXPLORER_SCREENSHOT_DIR || "/tmp/explorer-focus";
async function identity(canvas: Locator, exclude?: string) {
  await expect
    .poll(() => canvas.evaluate((el: any) => el.__sigma?.getGraph().order || 0))
    .toBeGreaterThan(0);
  return canvas.evaluate((el: any, exclude) => {
    const s = el.__sigma,
      g = s.getGraph();
    const nodes = g
      .nodes()
      .map((id: string) => ({
        id,
        ...s.graphToViewport(g.getNodeAttributes(id)),
        neighbors: g.neighbors(id),
      }))
      .filter(
        (n: any) =>
          n.id !== exclude &&
          n.x > 100 &&
          n.y > 100 &&
          n.x < el.clientWidth - 100 &&
          n.y < el.clientHeight - 180,
      )
      .sort(
        (a: any, b: any) =>
          b.neighbors.length - a.neighbors.length || a.id.localeCompare(b.id),
      );
    return nodes[0];
  }, exclude);
}
async function hover(page: Page, canvas: Locator, n: any) {
  const b = (await canvas.boundingBox())!;
  await page.mouse.move(b.x + n.x, b.y + n.y);
  await expect(canvas).toHaveAttribute("data-focus-node", n.id);
}
async function verifyLabels(canvas: Locator, n: any) {
  await expect
    .poll(
      async () =>
        JSON.parse(
          (await canvas.getAttribute("data-rendered-labels")) || "[]",
        ).filter((l: any) => l.kind === "neighbor").length,
    )
    .toBeGreaterThanOrEqual(2);
  const check = await canvas.evaluate((el: any, n) => {
    const s = el.__sigma,
      g = s.getGraph(),
      labels = JSON.parse(el.dataset.renderedLabels);
    const calls = s.getCanvases().labels.__textDraws || [];
    return labels.map((l: any) => {
      const p = s.framedGraphToViewport(s.getNodeDisplayData(l.id));
      return {
        ...l,
        adjacent: g.areNeighbors(n.id, l.id),
        fullName: g.getNodeAttribute(l.id, "fullLabel"),
        p,
        painted: calls.some(
          (c: any) =>
            c.text === l.text &&
            Math.abs(c.x - (l.x + 2)) < 0.1 &&
            Math.abs(c.y - (l.y + 12)) < 0.1,
        ),
      };
    });
  }, n);
  expect(check.some((l: any) => l.id === n.id && l.kind === "focus")).toBe(
    true,
  );
  for (const l of check) {
    expect(l.painted).toBe(true); // Actual fillText on Sigma's label canvas, not just eligibility/store state.
    expect(l.fullName.startsWith(l.text.replace(/…$/, ""))).toBe(true);
    if (l.kind === "neighbor") expect(l.adjacent).toBe(true);
    // Text must remain next to its own node. This catches raw-vs-normalized coordinates before Sigma.process().
    expect(
      Math.hypot(
        l.p.x - Math.max(l.rect.x1, Math.min(l.p.x, l.rect.x2)),
        l.p.y - Math.max(l.rect.y1, Math.min(l.p.y, l.rect.y2)),
      ),
    ).toBeLessThan(125);
    expect(l.rect.x1).toBeGreaterThanOrEqual(4);
    expect(l.rect.y1).toBeGreaterThanOrEqual(4);
  }
  const size = await canvas.boundingBox();
  for (let i = 0; i < check.length; i++) {
    expect(check[i].rect.x2).toBeLessThanOrEqual(size!.width - 4);
    expect(check[i].rect.y2).toBeLessThanOrEqual(size!.height - 4);
    for (let j = i + 1; j < check.length; j++) {
      const a = check[i].rect,
        b = check[j].rect;
      expect(a.x1 < b.x2 && a.x2 > b.x1 && a.y1 < b.y2 && a.y2 > b.y1).toBe(
        false,
      );
    }
  }
  return check;
}
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    const fill = CanvasRenderingContext2D.prototype.fillText,
      clear = CanvasRenderingContext2D.prototype.clearRect;
    CanvasRenderingContext2D.prototype.fillText = function (
      text,
      x,
      y,
      ...args
    ) {
      const c = this.canvas as any;
      (c.__textDraws ||= []).push({ text: String(text), x, y });
      return fill.call(this, text, x, y, ...args);
    };
    CanvasRenderingContext2D.prototype.clearRect = function (x, y, w, h) {
      (this.canvas as any).__textDraws = [];
      return clear.call(this, x, y, w, h);
    };
  });
});
for (const mode of [
  "researchers",
  "organizations",
  "citations",
  "heterogeneous",
])
  test(`${mode}: actual overview neighbor text, adjacency, focus precedence and geometry`, async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto(`/?mode=${mode}`);
    const canvas = page.getByTestId("sigma-canvas-container");
    await expect(canvas).toHaveAttribute("data-label-band", "overview");
    await expect(canvas).toHaveAttribute("data-rendered-labels", "[]");
    const n = await identity(canvas);
    expect(n.neighbors.length).toBeGreaterThanOrEqual(3);
    await hover(page, canvas, n);
    await verifyLabels(canvas, n);
    await page.screenshot({ path: path.join(out, `${mode}-neighbors.png`) });
    if (mode === "heterogeneous") await expect(canvas).toHaveScreenshot("hover-neighborhood.png", {maxDiffPixelRatio:.01});
    await page.mouse.move(500, 20);
    await expect(canvas).toHaveAttribute("data-rendered-labels", "[]");
    const other = await identity(canvas, n.id);
    await hover(page, canvas, other);
    await verifyLabels(canvas, other);
    const b = (await canvas.boundingBox())!;
    await page.mouse.click(b.x + other.x, b.y + other.y);
    await page.mouse.move(500, 20);
    await expect(canvas).toHaveAttribute("data-focus-node", other.id);
    await verifyLabels(canvas, other);
    await page.screenshot({
      path: path.join(out, `${mode}-selected-neighbors.png`),
    });
    await page.getByTestId("quick-sample-edge").click();
    await page.mouse.move(500, 20);
    await expect
      .poll(
        async () =>
          JSON.parse(
            (await canvas.getAttribute("data-rendered-labels")) || "[]",
          ).filter((l: any) => l.kind === "endpoint").length,
      )
      .toBe(2);
    const edgeHover = await identity(canvas);
    await hover(page, canvas, edgeHover);
    await verifyLabels(canvas, edgeHover);
    await page.getByTestId("theme-toggle").click();
    await page.evaluate(
      () =>
        new Promise((r) =>
          requestAnimationFrame(() => requestAnimationFrame(r)),
        ),
    );
    await hover(page, canvas, await identity(canvas));
    await verifyLabels(canvas, await identity(canvas));
    await page.getByRole("button", { name: "Zoom in", exact: true }).click();
    await expect(canvas).toHaveAttribute("data-label-band", "medium");
    await page
      .getByRole("button", { name: "Reset camera", exact: true })
      .click();
    await expect(canvas).toHaveAttribute("data-label-band", "overview");
    await page.mouse.move(500, 20);
    // Edge endpoints remain after hover exits; the selected edge has not been lost.
    await expect
      .poll(
        async () =>
          JSON.parse(
            (await canvas.getAttribute("data-rendered-labels")) || "[]",
          ).filter((l: any) => l.kind === "endpoint").length,
      )
      .toBe(2);
    expect(errors).toEqual([]);
  });

for (const count of [30, 100])
  test(`invented ${count}-neighbor fixture stays bounded and reports unlabeled connections`, async ({
    page,
    request,
  }) => {
    const response = await request.get(
      `http://127.0.0.1:${process.env.PLAYWRIGHT_API_PORT || 8000}/api/views/researchers?limit=120`,
    );
    const template = await response.json(),
      node = template.nodes[0],
      edge = template.edges[0];
    // Invented presentation-only stress fixture, never measured scientific evidence.
    const nodes = Array.from({ length: count + 1 }, (_, i) => ({
      ...node,
      id: `researcher:fixture-${i}`,
      name: `Invented researcher ${i}`,
      x: i ? Math.cos((i * 2 * Math.PI) / count) : 0,
      y: i ? Math.sin((i * 2 * Math.PI) / count) : 0,
      score: 1,
      full_metrics: { ...node.full_metrics, degree_strength: i ? 1 : count },
    }));
    const edges = nodes
      .slice(1)
      .map((n, i) => ({
        ...edge,
        edge_id: `fixture-edge-${i}`,
        source: nodes[0].id,
        target: n.id,
        source_name: nodes[0].name,
        target_name: n.name,
        evidence_ids: [],
        graph_version: "invented-fixture",
      }));
    await page.route("**/api/views/researchers?*", (r) =>
      r.fulfill({
        json: {
          ...template,
          nodes,
          edges,
          displayed_node_count: nodes.length,
          displayed_edge_count: edges.length,
          scientific_caveat: "Invented browser stress fixture",
        },
      }),
    );
    await page.goto("/?mode=researchers");
    const canvas = page.getByTestId("sigma-canvas-container");
    await expect
      .poll(() =>
        canvas.evaluate((el: any) => el.__sigma?.getGraph().order || 0),
      )
      .toBe(count + 1);
    const n = await canvas.evaluate((el: any) => ({
      id: "researcher:fixture-0",
      ...el.__sigma.graphToViewport({ x: 0, y: 0 }),
    }));
    await hover(page, canvas, n);
    const labels = await verifyLabels(canvas, n);
    expect(
      labels.filter((l: any) => l.kind === "neighbor").length,
    ).toBeLessThanOrEqual(12);
    expect(labels.length).toBeLessThan(count);
    await expect(page.getByTestId("dense-neighborhood-badge")).toContainText(
      `of ${count} displayed neighbors labeled`,
    );
    await expect(page.getByTestId("dense-neighborhood-badge")).toContainText(
      /\+\d+ more neighbors/,
    );
    await page.screenshot({
      path: path.join(out, `dense-${count}-neighbors.png`),
    });
  });
