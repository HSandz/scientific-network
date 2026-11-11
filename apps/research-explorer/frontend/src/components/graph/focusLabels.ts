import type Sigma from "sigma";
import {
  focusLabelBudget,
  labelBudget,
  zoomBand,
  type ZoomBand,
} from "../../lib/labelPolicy";
import { getThemeTokens, truncateCanvasLabel } from "../../lib/colors";
import { useExplorerStore } from "../../stores/useExplorerStore";

type Rect = { x1: number; y1: number; x2: number; y2: number };
type Label = {
  id: string;
  text: string;
  kind: "focus" | "endpoint" | "neighbor" | "routine";
  rect: Rect;
  x: number;
  y: number;
  anchorX: number;
  anchorY: number;
};
const intersects = (a: Rect, b: Rect) =>
  a.x1 < b.x2 && a.x2 > b.x1 && a.y1 < b.y2 && a.y2 > b.y1;

/** Plan in priority order, paint through Sigma's normal label callback. Hover draws rings only.
 * This avoids Sigma's insertion-order forced dispatch giving routine labels priority over focus.
 * No graph mutation, extra canvas, per-node DOM or camera-frame React updates are needed.
 */
export function createCustomSigmaRenderers(
  isDark: boolean,
  getSigma: () => Sigma | null,
) {
  const tokens = getThemeTokens(isDark);
  const placements = new Map<string, Label>();
  const painted = new Map<string, Label>();
  let band: ZoomBand = "overview";
  let started = 0;
  let pending = true;
  const plan = () => {
    pending = false;
    started = performance.now();
    placements.clear();
    painted.clear();
    const sigma = getSigma();
    if (!sigma) return;
    const graph = sigma.getGraph(),
      state = useExplorerStore.getState();
    const { width, height } = sigma.getDimensions();
    band = zoomBand(sigma.getCamera().ratio, band);
    const routineBudget = labelBudget(band, width, height);
    const focusBudget = focusLabelBudget(band, width, height);
    const focus = state.hoveredNodeId || state.selectedNodeId;
    const neighbors = new Set(
      focus && graph.hasNode(focus) ? graph.neighbors(focus) : [],
    );
    const endpoints = new Set(
      state.selectedEdgeId && graph.hasEdge(state.selectedEdgeId)
        ? graph.extremities(state.selectedEdgeId)
        : [],
    );
    const interacting = Boolean(focus || endpoints.size);
    const candidates: {
      id: string;
      x: number;
      y: number;
      radius: number;
      kind: Label["kind"];
      priority: number;
    }[] = [];
    const obstacles: (Rect & { id: string })[] = [];
    graph.forEachNode((id) => {
      const d = sigma.getNodeDisplayData(id);
      if (!d || d.hidden) return;
      const p = sigma.framedGraphToViewport(d),
        radius = sigma.scaleSize(d.size) + 3;
      if (p.x < 0 || p.y < 0 || p.x > width || p.y > height) return;
      obstacles.push({
        id,
        x1: p.x - radius,
        x2: p.x + radius,
        y1: p.y - radius,
        y2: p.y + radius,
      });
      const kind =
        id === focus
          ? "focus"
          : endpoints.has(id)
            ? "endpoint"
            : neighbors.has(id)
              ? "neighbor"
              : "routine";
      if (interacting && kind === "routine") return;
      candidates.push({
        id,
        ...p,
        radius,
        kind,
        priority:
          { focus: 3, endpoint: 2, neighbor: 1, routine: 0 }[kind] * 1e6 +
          graph.degree(id),
      });
    });
    candidates.sort(
      (a, b) => b.priority - a.priority || a.id.localeCompare(b.id),
    );
    const context = sigma.getCanvases().labels.getContext("2d");
    if (!context) return;
    const fontSize = sigma.getSetting("labelSize");
    context.font = `${sigma.getSetting("labelWeight")} ${fontSize}px ${sigma.getSetting("labelFont")}`;
    let neighborCount = 0,
      routineCount = 0;
    // Reserve overlays so text cannot be hidden behind the hover card / controls.
    const reserved: Rect[] = neighbors.size
      ? [{ x1: 0, y1: 0, x2: width, y2: 48 }]
      : [];
    sigma
      .getContainer()
      .parentElement?.querySelectorAll<HTMLElement>("[data-label-obstacle]")
      .forEach((el) => {
        const r = el.getBoundingClientRect(),
          c = sigma.getContainer().getBoundingClientRect();
        reserved.push({
          x1: r.left - c.left - 4,
          y1: r.top - c.top - 4,
          x2: r.right - c.left + 4,
          y2: r.bottom - c.top + 4,
        });
      });
    for (const node of candidates) {
      if (node.kind === "routine" && routineCount >= routineBudget) continue;
      if (node.kind === "neighbor" && neighborCount >= focusBudget) continue;
      const text = truncateCanvasLabel(
        String(
          graph.getNodeAttribute(node.id, "fullLabel") ||
            graph.getNodeAttribute(node.id, "label"),
        ),
        node.kind === "focus" ? 48 : 32,
      );
      const w = context.measureText(text).width + 8,
        h = fontSize + 6,
        gap = node.radius + 4;
      const positions = (interacting ? [0, 16, 40, 72] : [0]).flatMap(
        (offset) => {
          const distance = gap + offset;
          return [
            [node.x + distance, node.y - h / 2],
            [node.x - distance - w, node.y - h / 2],
            [node.x - w / 2, node.y - distance - h],
            [node.x - w / 2, node.y + distance],
            [node.x + distance, node.y - h - 8],
            [node.x - distance - w, node.y - h - 8],
            [node.x + distance, node.y + 8],
            [node.x - distance - w, node.y + 8],
          ];
        },
      );
      for (const [x, y] of positions) {
        const rect = { x1: x - 3, y1: y - 2, x2: x + w + 3, y2: y + h + 2 };
        if (
          rect.x1 < 4 ||
          rect.y1 < 4 ||
          rect.x2 > width - 4 ||
          rect.y2 > height - 4
        )
          continue;
        if (
          reserved.some((b) => intersects(rect, b)) ||
          [...placements.values()].some((b) => intersects(rect, b.rect))
        )
          continue;
        if (
          obstacles.some(
            (b) =>
              b.id !== node.id &&
              (!interacting ||
                b.id === focus ||
                neighbors.has(b.id) ||
                endpoints.has(b.id)) &&
              intersects(rect, b),
          )
        )
          continue;
        placements.set(node.id, {
          id: node.id,
          text,
          kind: node.kind,
          rect,
          x,
          y,
          anchorX: node.x,
          anchorY: node.y,
        });
        if (node.kind === "neighbor") neighborCount++;
        if (node.kind === "routine") routineCount++;
        break;
      }
    }
    const container = sigma.getContainer();
    container.dataset.labelBand = band;
    container.dataset.labelBudget = String(routineBudget);
    container.dataset.focusLabelBudget = String(interacting ? focusBudget : 0);
    container.dataset.labelBoxes = "[]";
    container.dataset.renderedLabels = "[]";
    container.dataset.focusNode = focus || "";
    container.dataset.focusNeighborCount = String(neighbors.size);
    container.dataset.labelPlacementMs = String(performance.now() - started);
  };
  const drawLabel = (
    context: CanvasRenderingContext2D,
    data: {
      key?: string;
      x: number;
      y: number;
      size: number;
      label?: string | null;
    },
    settings: { labelSize: number; labelFont: string; labelWeight: string },
  ) => {
    if (pending) plan();
    const label = data.key ? placements.get(data.key) : undefined;
    if (!label) return;
    context.save();
    context.font = `${settings.labelWeight} ${settings.labelSize}px ${settings.labelFont}`;
    const nearestX = Math.max(
      label.rect.x1,
      Math.min(label.anchorX, label.rect.x2),
    );
    const nearestY = Math.max(
      label.rect.y1,
      Math.min(label.anchorY, label.rect.y2),
    );
    if (label.kind !== "routine") {
      context.beginPath();
      context.moveTo(label.anchorX, label.anchorY);
      context.lineTo(nearestX, nearestY);
      context.strokeStyle = tokens.focusRing;
      context.globalAlpha = 0.5;
      context.lineWidth = 0.75;
      context.stroke();
      context.globalAlpha = 1;
    }
    context.fillStyle = tokens.labelPillBg;
    context.beginPath();
    context.roundRect(
      label.x - 2,
      label.y,
      label.rect.x2 - label.rect.x1 - 6,
      settings.labelSize + 6,
      4,
    );
    context.fill();
    context.fillStyle = tokens.labelInk;
    context.fillText(label.text, label.x + 2, label.y + settings.labelSize);
    context.restore();
    painted.set(label.id, label);
  };
  const drawHover = (
    context: CanvasRenderingContext2D,
    data: {
      key?: string;
      x: number;
      y: number;
      size: number;
      highlighted?: boolean;
    },
  ) => {
    if (
      data.key &&
      useExplorerStore.getState().hoveredNodeId !== data.key &&
      !data.highlighted
    )
      return;
    context.save();
    context.beginPath();
    context.arc(data.x, data.y, data.size + 3, 0, Math.PI * 2);
    context.strokeStyle = tokens.focusRing;
    context.lineWidth = 1.75;
    context.stroke();
    context.restore();
  };
  const afterRender = () => {
    if (pending) plan();
    const sigma = getSigma();
    if (!sigma) return;
    const labels = [...painted.values()],
      container = sigma.getContainer();
    container.dataset.renderedLabels = JSON.stringify(labels);
    container.dataset.labelBoxes = JSON.stringify(labels.map((l) => l.rect));
    const total = Number(container.dataset.focusNeighborCount),
      shown = labels.filter(
        (l) =>
          l.kind === "neighbor" ||
          (l.kind === "endpoint" &&
            sigma.getGraph().hasNode(container.dataset.focusNode || "") &&
            sigma.getGraph().areNeighbors(l.id, container.dataset.focusNode!)),
      ).length;
    const notice = container.parentElement?.querySelector<HTMLElement>(
      "[data-focus-label-summary]",
    );
    if (notice) {
      notice.hidden = !total;
      const remaining = Math.max(0, total - shown);
      notice.textContent = `${shown} of ${total} displayed neighbors labeled${remaining ? ` · +${remaining} more neighbors` : ""}. Select a node to inspect connections; zoom for more names.`;
    }
  };
  return {
    prepare: () => {
      pending = true;
    },
    drawLabel,
    drawHover,
    afterRender,
  };
}
