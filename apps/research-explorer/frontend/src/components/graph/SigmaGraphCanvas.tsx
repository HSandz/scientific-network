import { labelBudget, zoomBand, type ZoomBand } from "../../lib/labelPolicy";
import { parallelGroups, lanePath } from "../../lib/edgeLanes";
import React, { useEffect, useMemo, useRef, useState } from "react";
import Graph from "graphology";
import Sigma from "sigma";
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Share2,
  Loader2,
  AlertCircle,
  CircleDot,
  X,
  Info,
  ArrowLeft,
  Focus,
  RefreshCw,
} from "lucide-react";
import { useExplorerStore } from "../../stores/useExplorerStore";
import {
  getCommunityColor,
  getNodeColor,
  getThemeTokens,
  LABEL_COLORS,
  SECTOR_COLORS,
  truncateCanvasLabel,
  YEAR_COLORS,
} from "../../lib/colors";
import {
  EdgeFilterMode,
  GraphEdge,
  GraphNode,
  GraphViewResponse,
  LayoutMode,
  NodeLabel,
  ViewMode,
} from "../../types/explorer";

interface SigmaGraphCanvasProps {
  viewData?: GraphViewResponse;
  nodes: GraphNode[];
  edges: GraphEdge[];
  rawEdgesCount?: number;
  isLoading: boolean;
  error?: Error | null;
  onRetry: () => void;
  onExpandNode: (
    nodeId: string,
    replace?: boolean,
    exploreAll?: boolean,
  ) => void;
  isExpanding: boolean;
}

function createCustomSigmaRenderers(isDark: boolean, getSigma: () => Sigma | null = () => null) {
  const tokens = getThemeTokens(isDark);
  const drawnBoxes: Array<{ x1: number; y1: number; x2: number; y2: number }> =
    [];
  let band: ZoomBand = "overview";
  const eligible = new Set<string>();
  const obstacles: Array<{ x: number; y: number; radius: number; id: string }> = [];
  const prepare = () => {
    drawnBoxes.length = 0;
    eligible.clear();
    obstacles.length = 0;
    const sigma = getSigma();
    if (!sigma) return;
    const { width, height } = sigma.getDimensions();
    band = zoomBand(sigma.getCamera().ratio, band);
    const budget = labelBudget(band, width, height);
    const state = useExplorerStore.getState();
    const focus = state.hoveredNodeId || state.selectedNodeId;
    const graph = sigma.getGraph();
    const candidates: Array<{ id: string; priority: number }> = [];
    graph.forEachNode((id) => {
      const d = sigma.getNodeDisplayData(id);
      if (!d || d.hidden) return;
      const pos = sigma.framedGraphToViewport(d);
      if (pos.x < 0 || pos.y < 0 || pos.x > width || pos.y > height) return;
      obstacles.push({ ...pos, radius: sigma.scaleSize(d.size) + 3, id });
      const adjacent = focus && graph.hasNode(focus) && graph.areNeighbors(id, focus);
      candidates.push({ id, priority: (adjacent ? 10000 : 0) + graph.degree(id) });
    });
    candidates.sort((a,b) => b.priority - a.priority || a.id.localeCompare(b.id));
    candidates.slice(0, budget).forEach(n => eligible.add(n.id));
    const container = sigma.getContainer();
    container.dataset.labelBand = band;
    container.dataset.labelBudget = String(budget);
    container.dataset.labelBoxes = "[]";
  };

  const overlapsExisting = (rect: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  }) => {
    for (const b of drawnBoxes) {
      if (
        rect.x1 < b.x2 &&
        rect.x2 > b.x1 &&
        rect.y1 < b.y2 &&
        rect.y2 > b.y1
      ) {
        return true;
      }
    }
    return false;
  };

  const drawLabel = (
    context: CanvasRenderingContext2D,
    data: {
      key?: string;
      x: number;
      y: number;
      size: number;
      label?: string | null;
      color?: string;
      forceLabel?: boolean;
      highlighted?: boolean;
    },
    settings: { labelSize: number; labelFont: string; labelWeight: string },
  ) => {
    if (!data.label || data.highlighted || !data.key || !eligible.has(data.key)) return;
    const text = truncateCanvasLabel(String(data.label), 32);
    const fontSize = settings.labelSize || 12;
    context.save();
    context.font = `${settings.labelWeight || "500"} ${fontSize}px ${settings.labelFont}`;
    const textWidth = context.measureText(text).width;
    const boxW = textWidth + 8;
    const boxH = fontSize + 6;

    const canvasW =
      context.canvas?.clientWidth || context.canvas?.width || 1440;
    const canvasH =
      context.canvas?.clientHeight || context.canvas?.height || 900;

    // 4-way candidate placement: Right, Left, Above, Below
    const candidates = [
      { x: data.x + data.size + 4, y: data.y - fontSize / 2 - 3 },
      { x: data.x - data.size - boxW - 4, y: data.y - fontSize / 2 - 3 },
      { x: data.x - boxW / 2, y: data.y - data.size - boxH - 4 },
      { x: data.x - boxW / 2, y: data.y + data.size + 4 },
    ];

    let chosenCandidate: {
      x: number;
      y: number;
      rect: { x1: number; y1: number; x2: number; y2: number };
    } | null = null;
    for (const c of candidates) {
      const padded = {
        x1: c.x - 3,
        y1: c.y - 2,
        x2: c.x + boxW + 3,
        y2: c.y + boxH + 2,
      };
      if (
        padded.x1 >= 4 &&
        padded.y1 >= 4 &&
        padded.x2 <= canvasW - 4 &&
        padded.y2 <= canvasH - 4
      ) {
        if (!overlapsExisting(padded) && !obstacles.some(n => n.id !== data.key &&
          n.x + n.radius > padded.x1 && n.x - n.radius < padded.x2 &&
          n.y + n.radius > padded.y1 && n.y - n.radius < padded.y2)) {
          chosenCandidate = { ...c, rect: padded };
          break;
        }
      }
    }

    // Forced dispatch never bypasses collision rejection. Identity remains in the inspector/hover overlay.
    if (!chosenCandidate) {
      context.restore();
      return;
    }

    drawnBoxes.push(chosenCandidate.rect);
    const container = getSigma()?.getContainer();
    if (container) container.dataset.labelBoxes = JSON.stringify(drawnBoxes);
    context.fillStyle = tokens.labelPillBg;
    context.beginPath();
    if (context.roundRect) {
      context.roundRect(
        chosenCandidate.x - 2,
        chosenCandidate.y,
        boxW,
        boxH,
        4,
      );
      context.fill();
    } else {
      context.fillRect(chosenCandidate.x - 2, chosenCandidate.y, boxW, boxH);
    }
    context.fillStyle = tokens.labelInk;
    context.fillText(text, chosenCandidate.x + 2, chosenCandidate.y + fontSize);
    context.restore();
  };

  const drawHover = (
    context: CanvasRenderingContext2D,
    data: {
      x: number;
      y: number;
      size: number;
      label?: string | null;
      color?: string;
    },
    settings: { labelSize: number; labelFont: string; labelWeight: string },
  ) => {

    const fontSize = settings.labelSize || 12;
    const font = `${settings.labelWeight || "600"} ${fontSize}px ${settings.labelFont}`;
    context.save();
    context.font = font;

    const bgFill = tokens.hoverBg;
    const strokeColor = tokens.hoverStroke;
    const textColor = tokens.hoverInk;

    const labelText = data.label
      ? truncateCanvasLabel(String(data.label), 48)
      : "";
    if (labelText) {
      const textWidth = context.measureText(labelText).width;
      const boxW = textWidth + 12;
      const boxH = fontSize + 8;
      let boxX = data.x + data.size + 4;
      let boxY = data.y - fontSize / 2 - 4;
      let textY = data.y + fontSize / 3;

      const candidateRight = {
        x1: boxX - 2,
        y1: boxY - 2,
        x2: boxX + boxW + 2,
        y2: boxY + boxH + 2,
      };
      if (overlapsExisting(candidateRight)) {
        // Flip to left of node if right side overlaps another highlighted endpoint
        const leftX = data.x - data.size - boxW - 4;
        const candidateLeft = {
          x1: leftX - 2,
          y1: boxY - 2,
          x2: leftX + boxW + 2,
          y2: boxY + boxH + 2,
        };
        if (!overlapsExisting(candidateLeft) && leftX >= 6) {
          boxX = leftX;
        } else {
          // Place above node
          boxY = data.y - data.size - boxH - 6;
          textY = boxY + fontSize + 1;
        }
      }

      drawnBoxes.push({
        x1: boxX - 2,
        y1: boxY - 2,
        x2: boxX + boxW + 2,
        y2: boxY + boxH + 2,
      });

      context.fillStyle = bgFill;
      context.strokeStyle = strokeColor;
      context.lineWidth = 1;
      context.beginPath();
      context.roundRect(boxX, boxY, boxW, boxH, 4);
      context.fill();
      context.stroke();

      context.fillStyle = textColor;
      context.fillText(labelText, boxX + 6, textY);
    }

    // Outer focus ring around the node
    context.beginPath();
    context.arc(data.x, data.y, data.size + 3, 0, Math.PI * 2);
    context.strokeStyle = tokens.focusRing;
    context.lineWidth = 1.75;
    context.stroke();
    context.restore();
  };

  return { drawLabel, drawHover, prepare };
}

export const SigmaGraphCanvas: React.FC<SigmaGraphCanvasProps> = ({
  viewData,
  nodes,
  edges,
  rawEdgesCount,
  isLoading,
  error,
  onRetry,
  onExpandNode,
  isExpanding,
}) => {
  const {
    darkMode,
    viewMode,
    setViewMode,
    leftSidebarOpen,
    selectedNodeId,
    selectedEdgeId,
    hoveredNodeId,
    selectNode,
    selectEdge,
    clearSelection,
    setHoveredNodeId,
    extraNodes,
    clearExtraSubgraph,
    layoutMode,
    setLayoutMode,
    edgeFilterMode,
    setEdgeFilterMode,
    graphViewScope,
    restorePriorGraphScope,
    expansionError,
    setExpansionError,
    cameraState,
    setCameraState,
  } = useExplorerStore();

  const containerRef = useRef<HTMLDivElement | null>(null);
  const sigmaRef = useRef<Sigma | null>(null);
  const graphRef = useRef<Graph | null>(null);
  const positionCache = useRef(new Map<string, { x: number; y: number }>());
  const draggedNodeRef = useRef<string | null>(null);
  const isDraggingRef = useRef<boolean>(false);
  const [scopeNoteOpen, setScopeNoteOpen] = useState<boolean>(false);
  const [webglError, setWebglError] = useState<string | null>(null);

  // Authoritative rendered nodes & edges passed from App.tsx effectiveGraph
  const activeNodes = nodes;
  const activeEdges = edges;

  const nodeById = useMemo(() => {
    const map = new Map<string, GraphNode>();
    for (const n of activeNodes) map.set(n.id, n);
    return map;
  }, [activeNodes]);

  const edgeById = useMemo(() => {
    const map = new Map<string, GraphEdge>();
    for (const e of activeEdges) map.set(e.edge_id, e);
    return map;
  }, [activeEdges]);

  const nodeMapRef = useRef(nodeById),
    edgeMapRef = useRef(edgeById);
  nodeMapRef.current = nodeById;
  edgeMapRef.current = edgeById;
  const previousLayout = useRef(layoutMode);
  const laneOverlayRef = useRef<SVGSVGElement | null>(null);
  const groupsRef = useRef(parallelGroups(edges));
  groupsRef.current = parallelGroups(edges);
  const reducedMotion = () =>
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const activeFocusNodeId =
    hoveredNodeId ||
    (selectedNodeId && nodeById.has(selectedNodeId) ? selectedNodeId : null);

  const focusNeighbors = useMemo(() => {
    const set = new Set<string>();
    if (!activeFocusNodeId) return set;
    set.add(activeFocusNodeId);
    for (const e of activeEdges) {
      if (e.source === activeFocusNodeId) set.add(e.target);
      if (e.target === activeFocusNodeId) set.add(e.source);
    }
    return set;
  }, [activeFocusNodeId, activeEdges]);

  // Build Graphology instance and mount Sigma WebGL renderer
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const tokens = getThemeTokens(darkMode);
    const graph = graphRef.current || new Graph({ multi: true, type: "mixed" });
    const relayout = previousLayout.current !== layoutMode;
    previousLayout.current = layoutMode;
    const nextNodes = new Set(activeNodes.map((n) => n.id));
    const nextEdges = new Set(activeEdges.map((e) => e.edge_id));
    for (const id of graph.edges()) if (!nextEdges.has(id)) graph.dropEdge(id);
    for (const id of graph.nodes()) {
      positionCache.current.set(id, {
        x: graph.getNodeAttribute(id, "x"),
        y: graph.getNodeAttribute(id, "y"),
      });
      if (!nextNodes.has(id)) graph.dropNode(id);
    }
    const sizeMetric = (n: GraphNode) => viewMode === "citations" ? n.full_metrics?.in_degree : n.full_metrics?.degree_strength;
    const maxScore = Math.max(1, ...activeNodes.map((n) => sizeMetric(n) ?? 0));
    const count = activeNodes.length;

    // Viewport-aware sizing scale
    const containerWidth = container.clientWidth || 1200;
    const viewportScale = Math.max(0.65, Math.min(1.2, containerWidth / 1200));

    // Concentric layout distribution helper
    const concentricRings = [0.22, 0.45, 0.72, 1.0];

    activeNodes.forEach((n, index) => {
      let x = n.x;
      let y = n.y;

      if (layoutMode === "circular") {
        const angle = (2 * Math.PI * index) / Math.max(1, count);
        x = Math.cos(angle);
        y = Math.sin(angle);
      } else if (layoutMode === "concentric") {
        const rankRatio = index / Math.max(1, count);
        const ringIdx =
          rankRatio < 0.1 ? 0 : rankRatio < 0.3 ? 1 : rankRatio < 0.6 ? 2 : 3;
        const ringRadius = concentricRings[ringIdx];
        const nodesInRing = activeNodes.filter((_, i) => {
          const r = i / Math.max(1, count);
          const ri = r < 0.1 ? 0 : r < 0.3 ? 1 : r < 0.6 ? 2 : 3;
          return ri === ringIdx;
        });
        const indexInRing = nodesInRing.findIndex((item) => item.id === n.id);
        const angle =
          (2 * Math.PI * Math.max(0, indexInRing)) /
          Math.max(1, nodesInRing.length);
        x = ringRadius * Math.cos(angle);
        y = ringRadius * Math.sin(angle);
      } else {
        // Seeded / Force: if position is missing, place with subtle deterministic spiral
        if (x === 0 && y === 0 && index > 0) {
          const angle = index * 0.8;
          const radius = 0.15 + (index / Math.max(1, count)) * 0.85;
          x = radius * Math.cos(angle);
          y = radius * Math.sin(angle);
        }
      }

      const metric = sizeMetric(n);
      const normalizedScore = Math.sqrt(Math.max(0.05, metric ?? 0) / maxScore);
      const size =
        (viewMode === "heterogeneous" || metric == null ? 6.5 : 4.0 + normalizedScore * 12) *
        viewportScale;
      const maxChars = n.label === "Paper" ? 30 : 26;

      const attributes = {
        label: truncateCanvasLabel(n.name, maxChars),
        fullLabel: n.name,
        x,
        y,
        size,
        color: getNodeColor(n, viewMode),
        nodeType: n.label,
        score: n.score,
      };
      if (graph.hasNode(n.id)) {
        if (!relayout) {
          attributes.x = graph.getNodeAttribute(n.id, "x");
          attributes.y = graph.getNodeAttribute(n.id, "y");
        }
        graph.mergeNodeAttributes(n.id, attributes);
      } else {
        const cached = positionCache.current.get(n.id);
        graph.addNode(
          n.id,
          !relayout && cached ? { ...attributes, ...cached } : attributes,
        );
      }
    });

    activeEdges.forEach((e) => {
      if (!graph.hasNode(e.source) || !graph.hasNode(e.target)) return;
      if (e.source === e.target) return;

      const comparable = e.relation === "COAUTHORED_WITH" || e.relation === "COLLABORATED_WITH";
      const weightVal = comparable ? (e.fractional_weight ?? 0) : 0;
      const isDirected = e.directed && !e.symmetric;
      const baseMin = isDirected ? 1.55 : 1.15;
      const size = Math.min(
        4.8,
        Math.max(baseMin, 1.05 + Math.log1p(weightVal) * 1.15),
      );

      const attributes = {
        size,
        color: tokens.contextEdge,
        type: isDirected ? "arrow" : "line",
        relation: e.relation,
        hidden: groupsRef.current.some((g) => g.some((member) => member.edge_id === e.edge_id)),
      };
      if (graph.hasEdge(e.edge_id)) graph.mergeEdgeAttributes(e.edge_id, attributes);
      else graph.addEdgeWithKey(e.edge_id, e.source, e.target, attributes);
    });

    graphRef.current = graph;

    if (sigmaRef.current) {
      sigmaRef.current.refresh();
      return;
    }

    try {
      const customRenderers = createCustomSigmaRenderers(darkMode, () => sigmaRef.current);
      const sigma = new Sigma(graph, container, {
        allowInvalidContainer: true,
        enableEdgeEvents: true,
        renderLabels: true,
        labelFont: "Geist, system-ui, sans-serif",
        labelSize: 12,
        labelWeight: "500",
        labelColor: { color: tokens.labelInk },
        labelDensity: 0,
        labelGridCellSize: 140,
        labelRenderedSizeThreshold: 5.5,
        defaultEdgeType: "line",
        zIndex: true,
        defaultDrawNodeLabel: customRenderers.drawLabel,
        defaultDrawNodeHover: customRenderers.drawHover,
      });

      container.dataset.rendererGeneration = String(
        Number(container.dataset.rendererGeneration || 0) + 1,
      );
      const syncLanes = () => {
        const overlay = laneOverlayRef.current;
        if (!overlay) return;
        const state = useExplorerStore.getState();
        const theme = getThemeTokens(state.darkMode);
        const ns = "http://www.w3.org/2000/svg";
        const fragment = document.createDocumentFragment();
        for (const group of groupsRef.current) {
          const canonical = [group[0].source, group[0].target].sort();
          if (!graph.hasNode(canonical[0]) || !graph.hasNode(canonical[1]))
            continue;
          const a = sigma.graphToViewport(
            graph.getNodeAttributes(canonical[0]) as any,
          );
          const b = sigma.graphToViewport(
            graph.getNodeAttributes(canonical[1]) as any,
          );
          group.forEach((edge, index) => {
            const c = lanePath(a, b, index, group.length);
            const forward = edge.source === canonical[0],
              start = forward ? a : b,
              end = forward ? b : a;
            const length = Math.max(1, Math.hypot(end.x - c.x, end.y - c.y));
            const endSize = graph.getNodeAttribute(edge.target, "size") + 5;
            const ex = end.x - ((end.x - c.x) / length) * endSize,
              ey = end.y - ((end.y - c.y) / length) * endSize;
            const path = document.createElementNS(ns, "path");
            path.setAttribute(
              "d",
              `M ${start.x} ${start.y} Q ${c.x} ${c.y} ${ex} ${ey}`,
            );
            const color =
              state.selectedEdgeId === edge.edge_id
                ? theme.focusedEdge
                : theme.contextEdge;
            path.setAttribute("stroke", color);
            path.setAttribute("fill", "none");
            path.setAttribute(
              "stroke-width",
              state.selectedEdgeId === edge.edge_id ? "3.5" : "2",
            );
            path.setAttribute(
              "stroke-dasharray",
              edge.evidence_kind === "inferred_topic"
                ? "5 4"
                : edge.evidence_kind === "curated_taxonomy"
                  ? "2 3"
                  : edge.evidence_kind === "derived"
                    ? "10 3"
                    : "none",
            );
            path.setAttribute("pointer-events", "stroke");
            path.setAttribute("tabindex", "0");
            path.setAttribute("role", "button");
            path.dataset.edgeId = edge.edge_id;
            const description = `${edge.source_name || edge.source} ${edge.directed ? "→" : "↔"} ${edge.relation} ${edge.target_name || edge.target}; ${edge.evidence_kind}; ${edge.support_count} supports; ${edge.edge_id}`;
            path.setAttribute("aria-label", description);
            const title = document.createElementNS(ns, "title");
            title.textContent = description;
            path.appendChild(title);
            const inspect = () =>
              useExplorerStore
                .getState()
                .selectEdge(edge.edge_id, edge.relation);
            path.addEventListener("click", inspect);
            path.addEventListener("keydown", (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                inspect();
              }
            });
            fragment.appendChild(path);
            if (edge.directed && !edge.symmetric) {
              const arrow = document.createElementNS(ns, "path");
              const ux = (ex - c.x) / length,
                uy = (ey - c.y) / length;
              arrow.setAttribute(
                "d",
                `M ${ex} ${ey} L ${ex - ux * 9 - uy * 4} ${ey - uy * 9 + ux * 4} L ${ex - ux * 9 + uy * 4} ${ey - uy * 9 - ux * 4} Z`,
              );
              arrow.setAttribute("fill", color);
              fragment.appendChild(arrow);
            }
          });
        }
        overlay.replaceChildren(fragment);
      };
      sigma.on("afterRender", syncLanes);
      sigma.getCamera().on("updated", () => {
        const c = sigma.getCamera().getState();
        container.dataset.camera = JSON.stringify(c);
      });
      sigma.on("clickNode", ({ node }) => {
        if (isDraggingRef.current) return;
        const nObj = nodeMapRef.current.get(node);
        selectNode(node, nObj?.name || node);
      });

      sigma.on("clickEdge", ({ edge }) => {
        const eObj = edgeMapRef.current.get(edge);
        const label = eObj
          ? `${eObj.source_name || eObj.source} → ${eObj.relation} → ${eObj.target_name || eObj.target}`
          : edge;
        selectEdge(edge, label);
      });

      sigma.on("enterNode", ({ node }) => {
        setHoveredNodeId(node);
        container.style.cursor = "pointer";
      });

      sigma.on("leaveNode", () => {
        if (!draggedNodeRef.current) {
          setHoveredNodeId(null);
          container.style.cursor = "grab";
        }
      });

      sigma.on("downNode", (e) => {
        draggedNodeRef.current = e.node;
        isDraggingRef.current = false;
        sigma.getCamera().disable();
      });

      sigma.getMouseCaptor().on("mousemovebody", (e) => {
        if (!draggedNodeRef.current) return;
        isDraggingRef.current = true;
        const pos = sigma.viewportToGraph(e);
        graph.setNodeAttribute(draggedNodeRef.current, "x", pos.x);
        graph.setNodeAttribute(draggedNodeRef.current, "y", pos.y);
        e.preventSigmaDefault();
        e.original.preventDefault();
        e.original.stopPropagation();
      });

      sigma.getMouseCaptor().on("mouseup", () => {
        if (draggedNodeRef.current) {
          draggedNodeRef.current = null;
          sigma.getCamera().enable();
          setTimeout(() => {
            isDraggingRef.current = false;
          }, 50);
        }
      });

      sigmaRef.current = sigma;
      if (import.meta.env.DEV) (container as any).__sigma = sigma;
      setWebglError(null);
    } catch (err) {
      setWebglError(
        err instanceof Error
          ? err.message
          : "WebGL context initialization failed",
      );
    }
  }, [activeNodes, activeEdges, viewMode, layoutMode]);

  // One renderer per mounted canvas; listener/captor ownership ends with kill().
  useEffect(
    () => () => {
      sigmaRef.current?.kill();
      sigmaRef.current = null;
      graphRef.current = null;
    },
    [],
  );

  useEffect(() => {
    if (cameraState) sigmaRef.current?.getCamera().setState(cameraState);
  }, [cameraState]);

  // Refresh Sigma viewport when panels open/close or container resizes
  useEffect(() => {
    const container = containerRef.current;
    if (!container || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => {
      if (sigmaRef.current) {
        sigmaRef.current.refresh();
      }
    });
    ro.observe(container);
    return () => ro.disconnect();
  }, []);

  // Dynamic reducers for selection, neighborhood highlighting, theme switching, and collision-free labeling
  useEffect(() => {
    const sigma = sigmaRef.current;
    if (!sigma) return;

    const tokens = getThemeTokens(darkMode);
    const customRenderers = createCustomSigmaRenderers(darkMode, () => sigmaRef.current);
    sigma.setSetting("labelColor", { color: tokens.labelInk });
    sigma.setSetting("defaultDrawNodeLabel", customRenderers.drawLabel);
    sigma.setSetting("defaultDrawNodeHover", customRenderers.drawHover);

    const selectedEdgeObj = selectedEdgeId
      ? edgeById.get(selectedEdgeId)
      : null;
    sigma.on("beforeRender", customRenderers.prepare);
    sigma.setSetting("nodeReducer", (node, data) => {
      const res = { ...data };

      if (selectedEdgeObj) {
        const isEndpoint =
          node === selectedEdgeObj.source || node === selectedEdgeObj.target;
        res.highlighted = isEndpoint;
        res.forceLabel = false;
        res.zIndex = isEndpoint ? 20 : 1;
        if (!isEndpoint) {
          res.color = tokens.dimmedNode;
          res.label = "";
        }
        return res;
      }

      if (activeFocusNodeId) {
        const isCenter = node === activeFocusNodeId;
        const isNeighbor = focusNeighbors.has(node);
        res.highlighted = isCenter;
        res.zIndex = isCenter ? 25 : isNeighbor ? 12 : 1;

        if (!isNeighbor) {
          res.color = tokens.dimmedNode;
          res.label = "";
          res.forceLabel = false;
        } else {
          res.forceLabel = !isCenter;
        }
        return res;
      }

      // Dispatch to our screen-space policy; only its bounded eligible set can paint.
      res.forceLabel = true;
      return res;
    });

    sigma.setSetting("edgeReducer", (edge, data) => {
      const res = { ...data };
      const eObj = edgeById.get(edge);

      if (selectedEdgeId) {
        const isSelected = edge === selectedEdgeId;
        res.color = isSelected ? tokens.focusedEdge : tokens.dimmedEdge;
        res.size = isSelected ? Math.max(3.6, (data.size || 1.5) * 1.9) : 0.85;
        res.zIndex = isSelected ? 10 : 0;
        return res;
      }

      if (activeFocusNodeId && eObj) {
        const isIncident =
          eObj.source === activeFocusNodeId ||
          eObj.target === activeFocusNodeId;
        res.color = isIncident ? tokens.focusedEdge : tokens.dimmedEdge;
        res.size = isIncident ? Math.max(2.6, (data.size || 1.2) * 1.55) : 0.85;
        res.zIndex = isIncident ? 8 : 0;
        return res;
      }

      res.color = eObj?.evidence_kind === "derived" ? tokens.chartPrimarySeries : eObj?.evidence_kind === "inferred_topic" ? tokens.warning : eObj?.evidence_kind === "curated_taxonomy" ? tokens.chartSecondarySeries : tokens.contextEdge;
      return res;
    });

    sigma.refresh();
    return () => { sigma.off("beforeRender", customRenderers.prepare); };
  }, [
    activeNodes,
    activeFocusNodeId,
    selectedEdgeId,
    focusNeighbors,
    edgeById,
    nodeById,
    darkMode,
  ]);

  const handleZoomIn = () => {
    sigmaRef.current
      ?.getCamera()
      .animatedZoom({ duration: reducedMotion() ? 0 : 250 });
  };

  const handleZoomOut = () => {
    sigmaRef.current
      ?.getCamera()
      .animatedUnzoom({ duration: reducedMotion() ? 0 : 250 });
  };

  const handleResetCamera = () => {
    sigmaRef.current
      ?.getCamera()
      .animatedReset({ duration: reducedMotion() ? 0 : 250 });
  };

  const handleFitNeighborhood = () => {
    const sigma = sigmaRef.current;
    if (!sigma || !graphRef.current) return;
    if (activeFocusNodeId && graphRef.current.hasNode(activeFocusNodeId)) {
      const pos = graphRef.current.getNodeAttributes(activeFocusNodeId);
      sigma
        .getCamera()
        .animate(
          { x: pos.x, y: pos.y, ratio: 0.45 },
          { duration: reducedMotion() ? 0 : 300 },
        );
    } else {
      sigma.getCamera().animatedReset({ duration: reducedMotion() ? 0 : 250 });
    }
  };

  const hoveredNode = hoveredNodeId ? nodeById.get(hoveredNodeId) : null;
  const selectedNode = selectedNodeId ? nodeById.get(selectedNodeId) : null;

  const quickSelectNodes = useMemo(() => {
    return nodes
      .slice()
      .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id))
      .slice(0, 3);
  }, [nodes]);

  const sampleEdge = edges[0] || null;

  // Compute actual visible legend items for the active projection
  const visibleCommunityLegend = useMemo(() => {
    if (viewMode !== "researchers") return [];
    const counts = new Map<string, number>();
    for (const n of nodes) {
      if (n.label === "Researcher") {
        const cid = n.group || "unassigned";
        counts.set(cid, (counts.get(cid) || 0) + 1);
      }
    }
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, 4)
      .map(([cid, cnt]) => ({
        id: cid,
        label: `${cid} (${cnt})`,
        color: getCommunityColor(cid),
      }));
  }, [viewMode, nodes]);

  const modeButtons: Array<{ id: ViewMode; label: string }> = [
    { id: "researchers", label: "Researchers" },
    { id: "organizations", label: "Orgs" },
    { id: "citations", label: "Citations" },
    { id: "heterogeneous", label: "Full KG" },
  ];

  return (
    <div className="flex-1 flex flex-col min-w-0 min-h-0 overflow-hidden bg-ground select-none">
      {/* Band 1: Stable Workspace Header Bar above the plotting canvas */}
      <div className="shrink-0 bg-surface border-b border-border px-4 sm:px-5 py-1.5 sm:py-2 flex flex-wrap items-center justify-between gap-x-3 gap-y-1.5">
        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 min-w-0">
          {/* When left sidebar is closed, keep projection switcher accessible right here */}
          {!leftSidebarOpen && (
            <div
              className="ledger-segmented flex-wrap"
              role="radiogroup"
              aria-label="Network projection"
            >
              {modeButtons.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  role="radio"
                  aria-checked={viewMode === m.id}
                  data-active={viewMode === m.id}
                  onClick={() => setViewMode(m.id)}
                  data-testid={`mode-${m.id}`}
                  className="!px-2 sm:!px-2.5 !py-1 !text-[12px] sm:!text-[13px]"
                >
                  {m.label}
                </button>
              ))}
            </div>
          )}

          <div className="flex items-baseline gap-x-2 min-w-0">
            <h1
              data-testid="projection-title"
              className="text-xs sm:text-sm font-semibold text-ink truncate"
            >
              {viewData?.title || "Researcher Collaboration Network"}
            </h1>
            <span className="hidden sm:inline text-xs font-mono text-faint">
              {viewData?.relation || "COAUTHORED_WITH"}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 text-xs sm:text-[13px]">
            <span
              data-testid="displayed-counts"
              className="px-2 py-0.5 rounded-[4px] bg-raised text-ink font-medium tabular-nums"
            >
              Displayed: {activeNodes.length.toLocaleString()} nodes ·{" "}
              {activeEdges.length.toLocaleString()} edges
              {edgeFilterMode !== "all" &&
              (activeNodes.length !== nodes.length ||
                activeEdges.length !== edges.length)
                ? ` (of ${nodes.length}/${edges.length})`
                : ""}
            </span>
            {viewData && (
              <span
                data-testid="full-projection-counts"
                className="text-muted tabular-nums"
              >
                <span className="hidden sm:inline">Full projection: </span>
                <strong className="font-medium text-ink">
                  {viewData.full_node_count.toLocaleString()}
                </strong>{" "}
                nodes ·{" "}
                <strong className="font-medium text-ink">
                  {viewData.full_edge_count.toLocaleString()}
                </strong>{" "}
                edges
              </span>
            )}
            <button
              type="button"
              onClick={() => setScopeNoteOpen((v) => !v)}
              className="hidden sm:inline-flex items-center gap-1 text-[13px] text-muted hover:text-ink"
              title="Metric scope explanation"
            >
              <Info className="w-3.5 h-3.5 text-faint" />
              <span className="underline underline-offset-2">Scope note</span>
            </button>
          </div>
        </div>

        {/* Right side: Contextual selection actions + Edge visibility + Layout + Camera */}
        <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
          {selectedNode && (
            <div className="hidden sm:flex items-center gap-1.5 pr-2 border-r border-border">
              <button
                type="button"
                onClick={() => onExpandNode(selectedNode.id, false)}
                disabled={isExpanding}
                data-testid="canvas-expand-hop"
                className="ledger-btn ledger-btn-primary h-[28px] px-2.5 text-[13px]"
              >
                {isExpanding ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Share2 className="w-3.5 h-3.5" />
                )}
                <span>Expand +1 hop</span>
              </button>
              <button
                type="button"
                onClick={() => onExpandNode(selectedNode.id, true)}
                disabled={isExpanding}
                data-testid="canvas-isolate-ego"
                className="ledger-btn h-[28px] px-2.5 text-[13px]"
                title="Isolate 1-hop ego neighborhood"
              >
                <CircleDot className="w-3.5 h-3.5 text-muted" />
                <span>Ego view</span>
              </button>
              <button
                type="button"
                onClick={() => clearSelection()}
                className="ledger-btn h-[28px] px-2 text-[13px] text-muted"
                title="Clear selection"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {extraNodes.length > 0 && (
            <button
              type="button"
              onClick={clearExtraSubgraph}
              className="ledger-btn h-[28px] px-2 text-xs sm:text-[13px]"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset +{extraNodes.length}</span>
            </button>
          )}

          {/* Edge visibility filter */}
          <select
            aria-label="Canvas edge visibility"
            data-testid="canvas-edge-filter"
            value={edgeFilterMode}
            onChange={(e) =>
              setEdgeFilterMode(e.target.value as EdgeFilterMode)
            }
            className="hidden md:inline-block ledger-input !h-[30px] !py-0 !px-2 text-xs"
            title="Filter rendered canvas links or hide slice-level isolates"
          >
            <option value="all">All subgraph links</option>
            <option value="strong" disabled={viewMode === "citations"}>
              {viewMode === "citations"
                ? "Repeated collaborations (N/A for citations)"
                : "Repeated collaborations (≥2 papers)"}
            </option>
            <option value="connected">Hide slice isolates</option>
          </select>

          {/* Layout mode switcher */}
          <div
            className="hidden md:inline-flex ledger-segmented"
            role="group"
            aria-label="Graph layout"
          >
            {(
              [
                { id: "seeded", label: "Force" },
                { id: "concentric", label: "Radial" },
                { id: "circular", label: "Circle" },
              ] as Array<{ id: LayoutMode; label: string }>
            ).map((lm) => (
              <button
                key={lm.id}
                type="button"
                aria-pressed={layoutMode === lm.id}
                data-active={layoutMode === lm.id}
                onClick={() => setLayoutMode(lm.id)}
              >
                {lm.label}
              </button>
            ))}
          </div>

          {/* Camera zoom controls */}
          <div className="inline-flex items-center rounded-[6px] border border-border bg-surface">
            <button
              type="button"
              onClick={handleZoomIn}
              aria-label="Zoom in"
              title="Zoom in"
              className="p-2 md:p-1.5 text-muted hover:text-ink hover:bg-raised transition-colors"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={handleZoomOut}
              aria-label="Zoom out"
              title="Zoom out"
              className="p-2 md:p-1.5 text-muted hover:text-ink hover:bg-raised transition-colors border-l border-border"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={handleResetCamera}
              aria-label="Reset camera"
              title="Fit graph to view"
              className="p-2 md:p-1.5 text-muted hover:text-ink hover:bg-raised transition-colors border-l border-border"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={handleFitNeighborhood}
              aria-label="Focus neighborhood"
              title={
                activeFocusNodeId ? "Fit focused neighborhood" : "Center view"
              }
              className="p-2 md:p-1.5 text-muted hover:text-ink hover:bg-raised transition-colors border-l border-border"
            >
              <Focus className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Collapsible scope note banner when toggled */}
      {scopeNoteOpen && (
        <div className="shrink-0 bg-raised border-b border-border px-5 py-2 flex items-center justify-between gap-4 text-[13px] text-muted">
          <span>
            {viewData?.metric_scope_note ||
              "Mixed graph nodes have fixed size. Single-label projections scale within that projection. Layout coordinates are illustrative and do not imply similarity, geography or hierarchy."}
          </span>
          <button
            type="button"
            onClick={() => setScopeNoteOpen(false)}
            className="text-ink font-medium hover:underline shrink-0"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Band 2: Unobstructed Plotting Canvas */}
      <div className="flex-1 relative min-h-0 w-full overflow-hidden">
        <div
          ref={containerRef}
          data-testid="sigma-canvas-container"
          className="w-full h-full cursor-grab active:cursor-grabbing"
        />

        {/* Scope banner when in Ego or Path view */}
        {graphViewScope.kind !== "overview" && (
          <div
            data-testid="canvas-scope-banner"
            className="absolute top-3 left-4 z-20 flex items-center gap-2 bg-surface border border-border rounded-[6px] px-3 py-1.5 text-xs"
          >
            <button
              type="button"
              onClick={() => restorePriorGraphScope()}
              data-testid="scope-back-button"
              className="inline-flex items-center gap-1 font-medium text-ink hover:text-accent underline underline-offset-2"
              title="Return to previous overview / graph view"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to overview</span>
            </button>
            <span className="text-muted">·</span>
            <span className="font-medium text-ink truncate max-w-[180px] sm:max-w-xs">
              {graphViewScope.title}
            </span>
          </div>
        )}

        {/* Dense neighborhood badge */}
        {activeFocusNodeId && focusNeighbors.size - 1 > 12 && (
          <div
            data-testid="dense-neighborhood-badge"
            className="absolute top-12 left-4 z-20 bg-surface border border-border rounded-[6px] px-2.5 py-1 text-[11px] text-muted"
          >
            <span>
              Dense neighborhood: <strong>{focusNeighbors.size - 1}</strong>{" "}
              visible neighbors. Labels appear as you zoom; inspect complete list
              in right panel.
            </span>
          </div>
        )}

        <svg
          ref={laneOverlayRef}
          aria-label="Parallel and reciprocal relationship lanes"
          className="absolute inset-0 w-full h-full pointer-events-none"
          style={{ zIndex: 1 }}
        />
        {/* Empty strong link filter banner */}
        {edgeFilterMode === "strong" &&
          activeEdges.length === 0 &&
          nodes.length > 0 && (
            <div
              data-testid="empty-filter-banner"
              className="absolute top-3 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2.5 bg-surface border border-[var(--warning)]/50 rounded-[6px] px-3.5 py-2 text-xs"
            >
              <span className="text-ink">
                No collaboration links have ≥2 distinct supporting papers. Other
                predicates are preserved.
              </span>
              <button
                type="button"
                onClick={() => setEdgeFilterMode("all")}
                data-testid="reset-edge-filter-btn"
                className="ledger-btn h-6 px-2 text-[11px]"
              >
                Show all links
              </button>
            </div>
          )}

        {/* Inline expansion error banner with Retry */}
        {expansionError && (
          <div
            data-testid="expansion-error-banner"
            className="absolute top-3 right-4 z-20 flex items-center gap-2.5 bg-surface border border-[var(--negative)]/60 rounded-[6px] px-3.5 py-2 text-xs text-ink"
          >
            <AlertCircle className="w-3.5 h-3.5 text-[var(--negative)] shrink-0" />
            <span className="truncate max-w-xs">
              Expansion error: {expansionError.message}
            </span>
            <button
              type="button"
              onClick={() =>
                onExpandNode(expansionError.nodeId, expansionError.replace)
              }
              className="ledger-btn ledger-btn-primary h-6 px-2 text-[11px]"
            >
              Retry
            </button>
            <button
              type="button"
              onClick={() => setExpansionError(null)}
              className="text-muted hover:text-ink text-xs ml-1"
            >
              ×
            </button>
          </div>
        )}

        {/* Mobile floating bottom quick tools (md:hidden) */}
        <div className="md:hidden absolute bottom-4 right-4 z-20 flex items-center gap-1.5 bg-surface border border-border rounded-[6px] p-1">
          <select
            value={layoutMode}
            onChange={(e) => setLayoutMode(e.target.value as LayoutMode)}
            aria-label="Mobile layout selector"
            className="h-7 px-2 text-[11px] rounded bg-ground border border-border text-ink"
          >
            <option value="seeded">Force</option>
            <option value="concentric">Radial</option>
            <option value="circular">Circle</option>
          </select>
          <select
            value={edgeFilterMode}
            onChange={(e) =>
              setEdgeFilterMode(e.target.value as EdgeFilterMode)
            }
            aria-label="Mobile edge filter"
            className="h-7 px-2 text-[11px] rounded bg-ground border border-border text-ink"
          >
            <option value="all">All links</option>
            <option value="strong" disabled={viewMode === "citations"}>
              Repeated collaborations
            </option>
            <option value="connected">Hide isolates</option>
          </select>
          <button
            type="button"
            onClick={handleFitNeighborhood}
            aria-label="Fit mobile view"
            className="w-7 h-7 flex items-center justify-center rounded bg-ground border border-border text-muted hover:text-ink"
          >
            <Focus className="w-3 h-3" />
          </button>
        </div>

        {/* Transient Hover Preview Card (only while hovering a node) */}
        {hoveredNode && (
          <div className="pointer-events-none absolute bottom-4 left-5 z-20 max-w-sm bg-surface border border-border rounded-[8px] px-3.5 py-2.5">
            <div className="flex items-center justify-between gap-3 mb-1">
              <span className="text-xs font-medium text-muted">
                {hoveredNode.label} · {hoveredNode.group}
              </span>
              <span className="text-xs font-mono text-faint truncate max-w-[160px]">
                {hoveredNode.id}
              </span>
            </div>
            <div className="text-sm font-semibold text-ink leading-snug">
              {hoveredNode.name}
            </div>
            <div className="mt-1.5 flex items-center gap-3 text-xs text-muted tabular-nums">
              <span>
                Full-projection score:{" "}
                <strong className="font-medium text-ink">
                  {hoveredNode.score.toFixed(2)}
                </strong>
              </span>
              <span>
                Subgraph degree:{" "}
                <strong className="font-medium text-ink">
                  {hoveredNode.displayed_degree}
                </strong>
              </span>
            </div>
          </div>
        )}

        {/* Loading / Error / Empty states */}
        {isLoading && (
          <div className="absolute inset-0 z-30 flex items-center justify-center bg-ground/80">
            <div className="flex items-center gap-3 px-4 py-3 rounded-[8px] bg-surface border border-border">
              <Loader2 className="w-4 h-4 text-ink animate-spin" />
              <span className="text-[13px] font-medium text-ink">
                Loading Neo4j subgraph...
              </span>
            </div>
          </div>
        )}

        {error && !isLoading && (
          <div className="absolute inset-0 z-30 flex items-center justify-center bg-ground/85 p-6">
            <div className="max-w-md w-full bg-surface border border-border rounded-[8px] p-5">
              <div className="flex items-center gap-2 text-[var(--negative)] font-semibold text-sm mb-2">
                <AlertCircle className="w-4 h-4" />
                <span>Subgraph query error</span>
              </div>
              <p className="text-[13px] text-muted leading-relaxed">
                {error.message}
                <button className="ledger-btn mt-2 px-3 py-2" onClick={onRetry}>Retry</button>
              </p>
            </div>
          </div>
        )}

        {!isLoading && !error && nodes.length === 0 && (
          <div className="absolute inset-0 z-20 flex items-center justify-center p-6">
            <div className="max-w-sm w-full bg-surface border border-border rounded-[8px] p-5 text-center">
              <div className="text-sm font-semibold text-ink mb-1">
                No entities match current filters
              </div>
              <p className="text-[13px] text-muted">
                Relax the minimum shared paper threshold, sector filter, or
                publication year window.
              </p>
            </div>
          </div>
        )}

        {webglError && nodes.length > 0 && (
          <div className="absolute top-3 right-5 z-20 bg-surface border border-border rounded-[6px] px-3 py-1.5 text-xs text-muted">
            WebGL note: {webglError}
          </div>
        )}
      </div>

      {/* Band 3: Encoding Key & Keyboard-Accessible Top Entity Bar below the canvas */}
      <div className="shrink-0 bg-surface border-t border-border px-4 sm:px-5 py-1.5 sm:py-2 flex flex-nowrap md:flex-wrap items-center justify-between gap-x-3 gap-y-1.5 text-xs sm:text-[13px]">
        {/* Visual Encoding Legend */}
        <div
          data-testid="graph-legend"
          className="flex items-center gap-x-3 gap-y-1 min-w-0 shrink-0 md:shrink"
        >
          <details className="relative">
            <summary className="cursor-pointer text-xs py-1">Relationships</summary>
            <div className="absolute bottom-full left-0 mb-2 w-72 ledger-panel p-3 z-40 text-xs space-y-2">
              <p>Observed facts: graphite; inferred topics: ochre; curated taxonomy: grey; derived aggregations: blue. Arrows follow source → target.</p>
              <p>Parallel lanes: solid observed, dashed inferred, dotted taxonomy, long-dash derived. Each lane is separately selectable. Straight edges use evidence color.</p>
              <p>Width compares frozen fractional strength only within R7 or within R8. Other predicates have fixed width. Mixed-label nodes have fixed size. Routine labels stay hidden at fit view, then appear within a zoom- and viewport-dependent budget with collision suppression. Coordinates do not measure similarity or geography.</p>
            </div>
          </details>
          {/* Compact mobile Key disclosure */}
          <details className="md:hidden relative">
            <summary className="list-none cursor-pointer inline-flex items-center gap-1 px-2 py-1 rounded-[4px] border border-border bg-ground text-ink font-medium">
              <span>Key</span>
            </summary>
            <div className="absolute bottom-full left-0 mb-1.5 w-72 rounded-[8px] bg-surface border border-border p-3 z-40 space-y-2 text-xs">
              <div className="font-semibold text-ink">Visual encoding key</div>
              {viewMode === "researchers" && (
                <div className="space-y-1.5">
                  <div className="flex flex-wrap gap-2">
                    {visibleCommunityLegend.map((item) => (
                      <span
                        key={item.id}
                        className="inline-flex items-center gap-1 text-ink tabular-nums"
                      >
                        <span
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ backgroundColor: item.color }}
                        />
                        <span>{item.label}</span>
                      </span>
                    ))}
                  </div>
                  <p className="text-faint">
                    12-color palette cycles by community rank; node size =
                    full-projection fractional strength.
                  </p>
                </div>
              )}
              {viewMode === "organizations" && (
                <div className="space-y-1.5">
                  <div className="flex flex-wrap gap-2">
                    {(
                      [
                        "academia",
                        "industry",
                        "government",
                        "nonprofit",
                        "unknown",
                      ] as const
                    ).map((sec) => (
                      <span
                        key={sec}
                        className="inline-flex items-center gap-1 text-ink capitalize"
                      >
                        <span
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ backgroundColor: SECTOR_COLORS[sec] }}
                        />
                        <span>{sec}</span>
                      </span>
                    ))}
                  </div>
                  <p className="text-faint">
                    Node size = full-projection collaboration strength (R8).
                  </p>
                </div>
              )}
              {viewMode === "citations" && (
                <div className="space-y-1.5">
                  <div className="flex flex-wrap gap-2">
                    {([2021, 2022, 2023, 2024, 2025] as const).map((yr) => (
                      <span
                        key={yr}
                        className="inline-flex items-center gap-1 text-ink tabular-nums"
                      >
                        <span
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ backgroundColor: YEAR_COLORS[yr] }}
                        />
                        <span>{yr}</span>
                      </span>
                    ))}
                  </div>
                  <p className="text-faint">
                    Directed arrow: citing → cited paper (R4); size = in-corpus
                    citations.
                  </p>
                </div>
              )}
              {viewMode === "heterogeneous" && (
                <div className="flex flex-wrap gap-2">
                  {(
                    [
                      "Researcher",
                      "Paper",
                      "Organization",
                      "Topic",
                      "Venue",
                    ] as NodeLabel[]
                  ).map((lbl) => (
                    <span
                      key={lbl}
                      className="inline-flex items-center gap-1 text-ink"
                    >
                      <span
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{ backgroundColor: LABEL_COLORS[lbl] }}
                      />
                      <span>{lbl}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </details>

          {/* Desktop/Tablet inline encoding legend */}
          <div className="hidden md:flex flex-wrap items-center gap-x-3 gap-y-1 min-w-0">
            <span className="font-medium text-muted">Encoding:</span>

            {viewMode === "researchers" && (
              <>
                {visibleCommunityLegend.map((item) => (
                  <span
                    key={item.id}
                    className="inline-flex items-center gap-1.5 text-ink tabular-nums"
                  >
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: item.color }}
                    />
                    <span>{item.label}</span>
                  </span>
                ))}
                <span className="hidden xl:inline text-xs text-faint">
                  (12-color palette cycles by community rank; shared color ≠
                  same community · size = fractional strength)
                </span>
              </>
            )}

            {viewMode === "organizations" && (
              <>
                {(
                  ["academia", "industry", "government", "nonprofit", "unknown"] as const
                ).map((sec) => (
                  <span
                    key={sec}
                    className="inline-flex items-center gap-1.5 text-ink capitalize"
                  >
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: SECTOR_COLORS[sec] }}
                    />
                    <span>{sec}</span>
                  </span>
                ))}
                <span className="hidden lg:inline text-xs text-faint">
                  · Size = full-projection collaboration strength (R8)
                </span>
              </>
            )}

            {viewMode === "citations" && (
              <>
                {([2021, 2022, 2023, 2024, 2025] as const).map((yr) => (
                  <span
                    key={yr}
                    className="inline-flex items-center gap-1.5 text-ink tabular-nums"
                  >
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: YEAR_COLORS[yr] }}
                    />
                    <span>{yr}</span>
                  </span>
                ))}
                <span className="hidden lg:inline text-xs text-faint">
                  · Arrow: citing → cited paper (R4) · Size = in-corpus
                  citations
                </span>
              </>
            )}

            {viewMode === "heterogeneous" && (
              <>
                {(
                  [
                    "Researcher",
                    "Paper",
                    "Organization",
                    "Topic",
                    "Venue",
                  ] as NodeLabel[]
                ).map((lbl) => (
                  <span
                    key={lbl}
                    className="inline-flex items-center gap-1.5 text-ink"
                  >
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: LABEL_COLORS[lbl] }}
                    />
                    <span>{lbl}</span>
                  </span>
                ))}
              </>
            )}
          </div>
        </div>

        {/* Keyboard-accessible top entity & sample edge strip */}
        {quickSelectNodes.length > 0 && (
          <div className="flex items-center gap-1.5 min-w-0 max-w-full overflow-x-auto md:flex-wrap pr-2 sm:pr-0">
            <span className="hidden sm:inline text-muted font-medium shrink-0">
              Top entities:
            </span>
            {quickSelectNodes.map((n) => {
              const active = selectedNodeId === n.id;
              return (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => selectNode(n.id, n.name)}
                  data-testid={`quick-node-${n.id}`}
                  className={`px-2 py-0.5 rounded-[4px] border text-xs sm:text-[13px] transition-colors truncate max-w-[115px] sm:max-w-[130px] shrink-0 ${
                    active
                      ? "bg-active border-control text-ink font-medium"
                      : "bg-ground border-border text-muted hover:text-ink hover:bg-raised"
                  }`}
                  title={`Inspect ${n.name} (${n.id})`}
                >
                  {n.name}
                </button>
              );
            })}
            {sampleEdge && (
              <button
                type="button"
                onClick={() =>
                  selectEdge(
                    sampleEdge.edge_id,
                    `${sampleEdge.source_name || sampleEdge.source} → ${sampleEdge.relation} → ${sampleEdge.target_name || sampleEdge.target}`,
                  )
                }
                data-testid="quick-sample-edge"
                className="px-2 py-0.5 rounded-[4px] border border-border bg-ground hover:bg-raised text-xs sm:text-[13px] text-ink font-medium transition-colors shrink-0"
                title="Inspect edge evidence and provenance"
              >
                Sample edge
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
