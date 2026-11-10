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
  GraphEdge,
  GraphNode,
  GraphViewResponse,
  NodeLabel,
  ViewMode,
} from "../../types/explorer";

interface SigmaGraphCanvasProps {
  viewData?: GraphViewResponse;
  nodes: GraphNode[];
  edges: GraphEdge[];
  isLoading: boolean;
  error?: Error | null;
  onExpandNode: (nodeId: string, replace?: boolean) => void;
  isExpanding: boolean;
}

type LayoutMode = "seeded" | "circular" | "concentric";
type EdgeFilterMode = "all" | "strong" | "connected";

function createCustomSigmaRenderers(isDark: boolean) {
  const tokens = getThemeTokens(isDark);
  const drawnBoxes: Array<{ x1: number; y1: number; x2: number; y2: number }> = [];
  let resetScheduled = false;

  const ensureFrameReset = () => {
    if (!resetScheduled) {
      resetScheduled = true;
      queueMicrotask(() => {
        drawnBoxes.length = 0;
        resetScheduled = false;
      });
    }
  };

  const overlapsExisting = (rect: { x1: number; y1: number; x2: number; y2: number }) => {
    for (const b of drawnBoxes) {
      if (rect.x1 < b.x2 && rect.x2 > b.x1 && rect.y1 < b.y2 && rect.y2 > b.y1) {
        return true;
      }
    }
    return false;
  };

  const drawLabel = (
    context: CanvasRenderingContext2D,
    data: {
      x: number;
      y: number;
      size: number;
      label?: string | null;
      color?: string;
      forceLabel?: boolean;
      highlighted?: boolean;
    },
    settings: { labelSize: number; labelFont: string; labelWeight: string }
  ) => {
    ensureFrameReset();
    if (!data.label || data.highlighted) return;
    const text = truncateCanvasLabel(String(data.label), 32);
    const fontSize = settings.labelSize || 12;
    context.save();
    context.font = `${settings.labelWeight || "500"} ${fontSize}px ${settings.labelFont}`;
    const textWidth = context.measureText(text).width;
    const boxW = textWidth + 6;
    const boxH = fontSize + 4;
    let boxX = data.x + data.size + 3;
    const boxY = data.y - fontSize / 2 - 2;

    const canvasW = context.canvas?.clientWidth || context.canvas?.width || 1440;
    const canvasH = context.canvas?.clientHeight || context.canvas?.height || 900;

    if (boxX + boxW > canvasW - 8) {
      boxX = data.x - data.size - boxW - 3;
    }

    const padded = {
      x1: boxX - 4,
      y1: boxY - 2,
      x2: boxX + boxW + 4,
      y2: boxY + boxH + 2,
    };

    const isForced = Boolean(data.forceLabel || data.highlighted);
    if (!isForced) {
      if (padded.x1 < 4 || padded.y1 < 4 || padded.x2 > canvasW - 4 || padded.y2 > canvasH - 4) {
        context.restore();
        return;
      }
    }
    if (overlapsExisting(padded)) {
      context.restore();
      return;
    }

    drawnBoxes.push(padded);
    context.fillStyle = tokens.labelPillBg;
    context.fillRect(boxX - 2, boxY, boxW, boxH);
    context.fillStyle = tokens.labelInk;
    context.fillText(text, boxX + 1, data.y + fontSize / 3);
    context.restore();
  };

  const drawHover = (
    context: CanvasRenderingContext2D,
    data: { x: number; y: number; size: number; label?: string | null; color?: string },
    settings: { labelSize: number; labelFont: string; labelWeight: string }
  ) => {
    ensureFrameReset();
    const fontSize = settings.labelSize || 12;
    const font = `${settings.labelWeight || "600"} ${fontSize}px ${settings.labelFont}`;
    context.save();
    context.font = font;

    const bgFill = tokens.hoverBg;
    const strokeColor = tokens.hoverStroke;
    const textColor = tokens.hoverInk;

    const labelText = data.label ? truncateCanvasLabel(String(data.label), 48) : "";
    if (labelText) {
      const textWidth = context.measureText(labelText).width;
      const boxW = textWidth + 12;
      const boxH = fontSize + 8;
      let boxX = data.x + data.size + 4;
      let boxY = data.y - fontSize / 2 - 4;
      let textY = data.y + fontSize / 3;

      const candidateRight = { x1: boxX - 2, y1: boxY - 2, x2: boxX + boxW + 2, y2: boxY + boxH + 2 };
      if (overlapsExisting(candidateRight)) {
        // Flip to left of node if right side overlaps another highlighted endpoint
        const leftX = data.x - data.size - boxW - 4;
        const candidateLeft = { x1: leftX - 2, y1: boxY - 2, x2: leftX + boxW + 2, y2: boxY + boxH + 2 };
        if (!overlapsExisting(candidateLeft) && leftX >= 6) {
          boxX = leftX;
        } else {
          // Place above node
          boxY = data.y - data.size - boxH - 6;
          textY = boxY + fontSize + 1;
        }
      }

      drawnBoxes.push({ x1: boxX - 2, y1: boxY - 2, x2: boxX + boxW + 2, y2: boxY + boxH + 2 });

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

  return { drawLabel, drawHover };
}

export const SigmaGraphCanvas: React.FC<SigmaGraphCanvasProps> = ({
  viewData,
  nodes,
  edges,
  isLoading,
  error,
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
  } = useExplorerStore();

  const containerRef = useRef<HTMLDivElement | null>(null);
  const sigmaRef = useRef<Sigma | null>(null);
  const graphRef = useRef<Graph | null>(null);
  const draggedNodeRef = useRef<string | null>(null);
  const isDraggingRef = useRef<boolean>(false);

  const [layoutMode, setLayoutMode] = useState<LayoutMode>("seeded");
  const [edgeFilterMode, setEdgeFilterMode] = useState<EdgeFilterMode>("all");
  const [scopeNoteOpen, setScopeNoteOpen] = useState<boolean>(false);
  const [webglError, setWebglError] = useState<string | null>(null);

  const renderedGraph = useMemo(() => {
    if (edgeFilterMode === "all") {
      return { nodes, edges };
    }
    if (edgeFilterMode === "strong") {
      const strongEdges = edges.filter(
        (e) =>
          (e.support_count ?? 1) >= 2 ||
          (typeof e.fractional_weight === "number" && e.fractional_weight >= 0.45)
      );
      const effectiveEdges = strongEdges.length > 0 ? strongEdges : edges;
      return { nodes, edges: effectiveEdges };
    }
    // "connected": hide slice-level isolates
    const connectedIds = new Set<string>();
    for (const e of edges) {
      connectedIds.add(e.source);
      connectedIds.add(e.target);
    }
    const connectedNodes = nodes.filter(
      (n) => connectedIds.has(n.id) || n.id === selectedNodeId
    );
    return {
      nodes: connectedNodes.length > 0 ? connectedNodes : nodes,
      edges,
    };
  }, [nodes, edges, edgeFilterMode, selectedNodeId]);

  const activeNodes = renderedGraph.nodes;
  const activeEdges = renderedGraph.edges;

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

  const activeFocusNodeId = hoveredNodeId || selectedNodeId;

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
    if (!container || activeNodes.length === 0) {
      if (sigmaRef.current) {
        sigmaRef.current.kill();
        sigmaRef.current = null;
      }
      return;
    }

    const tokens = getThemeTokens(darkMode);
    const graph = new Graph({ multi: false, type: "mixed" });
    const maxScore = Math.max(1, ...activeNodes.map((n) => n.score || 1));

    const count = activeNodes.length;
    activeNodes.forEach((n, index) => {
      let x = n.x;
      let y = n.y;
      if (layoutMode === "circular") {
        const angle = (2 * Math.PI * index) / Math.max(1, count);
        x = Math.cos(angle);
        y = Math.sin(angle);
      } else if (layoutMode === "concentric") {
        const rankRatio = index / Math.max(1, count);
        const ring = rankRatio < 0.15 ? 0.25 : rankRatio < 0.5 ? 0.6 : 1.0;
        const angle = (2 * Math.PI * index * 3) / Math.max(1, count);
        x = ring * Math.cos(angle);
        y = ring * Math.sin(angle);
      }

      const normalizedScore = Math.sqrt(Math.max(0.05, n.score) / maxScore);
      const size = 4.5 + normalizedScore * 13;
      const maxChars = n.label === "Paper" ? 30 : 26;

      graph.addNode(n.id, {
        label: truncateCanvasLabel(n.name, maxChars),
        fullLabel: n.name,
        x,
        y,
        size,
        color: getNodeColor(n, viewMode),
        nodeType: n.label,
        score: n.score,
      });
    });

    activeEdges.forEach((e) => {
      if (!graph.hasNode(e.source) || !graph.hasNode(e.target)) return;
      if (e.source === e.target) return;
      const existingEdge =
        graph.edge(e.source, e.target) || graph.edge(e.target, e.source);
      if (existingEdge) return;

      const weightVal = e.fractional_weight ?? e.support_count ?? 1;
      const isDirected = e.directed && !e.symmetric;
      const baseMin = isDirected ? 1.55 : 1.15;
      const size = Math.min(
        4.8,
        Math.max(baseMin, 1.05 + Math.log1p(weightVal) * 1.15)
      );

      try {
        graph.addEdgeWithKey(e.edge_id, e.source, e.target, {
          size,
          color: tokens.contextEdge,
          type: isDirected ? "arrow" : "line",
          relation: e.relation,
        });
      } catch {
        // Ignore duplicate edge key
      }
    });

    graphRef.current = graph;

    if (sigmaRef.current) {
      sigmaRef.current.kill();
      sigmaRef.current = null;
    }

    try {
      const customRenderers = createCustomSigmaRenderers(darkMode);
      const sigma = new Sigma(graph, container, {
        allowInvalidContainer: true,
        enableEdgeEvents: true,
        renderLabels: true,
        labelFont: "Geist, system-ui, sans-serif",
        labelSize: 12,
        labelWeight: "500",
        labelColor: { color: tokens.labelInk },
        labelDensity: 0.25,
        labelGridCellSize: 160,
        labelRenderedSizeThreshold: 6.5,
        defaultEdgeType: "line",
        zIndex: true,
        defaultDrawNodeLabel: customRenderers.drawLabel,
        defaultDrawNodeHover: customRenderers.drawHover,
      });

      sigma.on("clickNode", ({ node }) => {
        if (isDraggingRef.current) return;
        const nObj = nodeById.get(node);
        selectNode(node, nObj?.name || node);
      });

      sigma.on("clickEdge", ({ edge }) => {
        const eObj = edgeById.get(edge);
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
      setWebglError(null);
    } catch (err) {
      setWebglError(
        err instanceof Error ? err.message : "WebGL context initialization failed"
      );
    }

    return () => {
      if (sigmaRef.current) {
        sigmaRef.current.kill();
        sigmaRef.current = null;
      }
    };
  }, [activeNodes, activeEdges, viewMode, layoutMode]);

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
    const customRenderers = createCustomSigmaRenderers(darkMode);
    sigma.setSetting("labelColor", { color: tokens.labelInk });
    sigma.setSetting("defaultDrawNodeLabel", customRenderers.drawLabel);
    sigma.setSetting("defaultDrawNodeHover", customRenderers.drawHover);

    const selectedEdgeObj = selectedEdgeId ? edgeById.get(selectedEdgeId) : null;

    sigma.setSetting("nodeReducer", (node, data) => {
      const res = { ...data };

      if (selectedEdgeObj) {
        const isEndpoint =
          node === selectedEdgeObj.source || node === selectedEdgeObj.target;
        res.highlighted = isEndpoint;
        res.forceLabel = isEndpoint;
        res.zIndex = isEndpoint ? 10 : 1;
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
        // Force label only on the center node; let Sigma's spatial grid place non-overlapping neighbor labels
        res.forceLabel = isCenter;
        res.zIndex = isCenter ? 12 : isNeighbor ? 6 : 1;
        if (!isNeighbor) {
          res.color = tokens.dimmedNode;
          res.label = "";
        }
        return res;
      }

      // At rest, let Sigma's 160px spatial grid choose the highest-degree node per cell with zero overlap
      res.forceLabel = false;
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
          eObj.source === activeFocusNodeId || eObj.target === activeFocusNodeId;
        res.color = isIncident ? tokens.focusedEdge : tokens.dimmedEdge;
        res.size = isIncident ? Math.max(2.6, (data.size || 1.2) * 1.55) : 0.85;
        res.zIndex = isIncident ? 8 : 0;
        return res;
      }

      res.color = tokens.contextEdge;
      return res;
    });

    sigma.refresh();
  }, [
    activeFocusNodeId,
    selectedEdgeId,
    focusNeighbors,
    edgeById,
    darkMode,
  ]);

  const handleZoomIn = () => {
    sigmaRef.current?.getCamera().animatedZoom({ duration: 200 });
  };

  const handleZoomOut = () => {
    sigmaRef.current?.getCamera().animatedUnzoom({ duration: 200 });
  };

  const handleResetCamera = () => {
    sigmaRef.current?.getCamera().animatedReset({ duration: 250 });
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
            onChange={(e) => setEdgeFilterMode(e.target.value as EdgeFilterMode)}
            className="hidden md:inline-block ledger-input !h-[30px] !py-0 !px-2 text-xs"
            title="Filter rendered canvas links or hide slice-level isolates"
          >
            <option value="all">All subgraph links</option>
            <option value="strong">Strong links (≥2 papers)</option>
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
          </div>
        </div>
      </div>

      {/* Collapsible scope note banner when toggled */}
      {scopeNoteOpen && (
        <div className="shrink-0 bg-raised border-b border-border px-5 py-2 flex items-center justify-between gap-4 text-[13px] text-muted">
          <span>
            {viewData?.metric_scope_note ||
              "Node size and score reflect full release-projection centrality; displayed degree and edge counts reflect the currently rendered subgraph."}
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
                Relax the minimum shared paper threshold, sector filter, or publication year window.
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
                    12-color palette cycles by community rank; node size = full-projection fractional strength.
                  </p>
                </div>
              )}
              {viewMode === "organizations" && (
                <div className="space-y-1.5">
                  <div className="flex flex-wrap gap-2">
                    {(
                      ["academia", "industry", "government", "nonprofit"] as const
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
                    Directed arrow: citing → cited paper (R4); size = in-corpus citations.
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
                  (12-color palette cycles by community rank; shared color ≠ same community · size = fractional strength)
                </span>
              </>
            )}

            {viewMode === "organizations" && (
              <>
                {(
                  ["academia", "industry", "government", "nonprofit"] as const
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
                  · Arrow: citing → cited paper (R4) · Size = in-corpus citations
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
                    `${sampleEdge.source_name || sampleEdge.source} → ${sampleEdge.relation} → ${sampleEdge.target_name || sampleEdge.target}`
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
