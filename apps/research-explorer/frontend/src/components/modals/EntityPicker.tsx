import React, { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, ChevronDown } from "lucide-react";
import { explorerApi } from "../../lib/api";
import { LABEL_COLORS } from "../../lib/colors";
import { NodeLabel } from "../../types/explorer";

const KNOWN_ENTITY_NAMES: Record<string, { name: string; label: NodeLabel }> = {
  "researcher:openalex:A5017743551": { name: "Bo An", label: "Researcher" },
  "researcher:openalex:A5000021048": {
    name: "Bowen Baker",
    label: "Researcher",
  },
  "researcher:openalex:A5003235897": {
    name: "Warut Suksompong",
    label: "Researcher",
  },
  "researcher:openalex:A5023888391": {
    name: "Piotr Faliszewski",
    label: "Researcher",
  },
  "organization:I183067930": {
    name: "Shanghai Jiao Tong University",
    label: "Organization",
  },
  "organization:I2250653659": {
    name: "Tencent (China)",
    label: "Organization",
  },
  "organization:I99065089": {
    name: "Tsinghua University",
    label: "Organization",
  },
  "organization:I4210095624": {
    name: "Alibaba Group (China)",
    label: "Organization",
  },
  "organization:I20231570": {
    name: "Peking University",
    label: "Organization",
  },
  "organization:I1290206253": {
    name: "Microsoft (United States)",
    label: "Organization",
  },
  "paper:aaai:2021:17325": {
    name: "Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting",
    label: "Paper",
  },
  "topic:causal-inference": {
    name: "Causal inference",
    label: "Topic",
  },
};

function inferLabelFromId(id: string): NodeLabel {
  if (id.startsWith("organization:")) return "Organization";
  if (id.startsWith("paper:")) return "Paper";
  if (id.startsWith("topic:")) return "Topic";
  if (id.startsWith("venue:")) return "Venue";
  return "Researcher";
}

interface EntityPickerProps {
  label: string;
  valueId: string;
  resolvedName?: string;
  resolvedLabel?: NodeLabel;
  allowedLabels?: NodeLabel[];
  onChange: (id: string, name?: string, label?: NodeLabel) => void;
  testIdPrefix: string;
}

export const EntityPicker: React.FC<EntityPickerProps> = ({
  label,
  valueId,
  resolvedName,
  resolvedLabel,
  allowedLabels,
  onChange,
  testIdPrefix,
}) => {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [customName, setCustomName] = useState<string | null>(null);
  const [customLabel, setCustomLabel] = useState<NodeLabel | null>(null);
  const [activeIndex, setActiveIndex] = useState<number>(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Reset custom resolution whenever valueId changes
  useEffect(() => {
    setCustomName(null);
    setCustomLabel(null);
  }, [valueId]);

  useEffect(() => {
    const onOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener("mousedown", onOutside);
    }
    return () => document.removeEventListener("mousedown", onOutside);
  }, [open]);

  // Query node detail dynamically when entity is not in known dictionary
  const nodeDetailQuery = useQuery({
    queryKey: ["picker-node-detail", valueId],
    queryFn: ({ signal }) => explorerApi.getNodeDetail(valueId, signal),
    enabled: Boolean(
      valueId &&
        !resolvedName &&
        !customName &&
        !KNOWN_ENTITY_NAMES[valueId]
    ),
    staleTime: 300_000,
  });

  const searchQuery = useQuery({
    queryKey: ["entity-picker-search", query, allowedLabels],
    queryFn: ({ signal }) =>
      explorerApi.search(
        {
          q: query,
          label: allowedLabels,
          limit: 8,
        },
        signal
      ),
    enabled: open,
  });

  const results = searchQuery.data?.results || [];

  useEffect(() => {
    setActiveIndex(-1);
  }, [query, results.length]);

  const known = KNOWN_ENTITY_NAMES[valueId];
  const dynamicName = nodeDetailQuery.data?.node?.name;
  const dynamicLabel = nodeDetailQuery.data?.node?.label;
  const displayName =
    resolvedName || customName || known?.name || dynamicName || valueId;
  const displayLabel =
    resolvedLabel ||
    customLabel ||
    known?.label ||
    dynamicLabel ||
    inferLabelFromId(valueId);

  const selectItem = (item: { id: string; name: string; label: NodeLabel }) => {
    setCustomName(item.name);
    setCustomLabel(item.label);
    onChange(item.id, item.name, item.label);
    setOpen(false);
    triggerRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open) {
      if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        setOpen(true);
      }
      return;
    }

    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      setOpen(false);
      triggerRef.current?.focus();
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (results.length > 0) {
        setActiveIndex((prev) => (prev + 1) % results.length);
      }
      return;
    }

    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (results.length > 0) {
        setActiveIndex((prev) =>
          prev <= 0 ? results.length - 1 : prev - 1
        );
      }
      return;
    }

    if (e.key === "Enter") {
      if (activeIndex >= 0 && activeIndex < results.length) {
        e.preventDefault();
        selectItem(results[activeIndex]);
      }
    }
  };

  return (
    <div
      ref={wrapperRef}
      data-picker-open={open ? "true" : "false"}
      className="relative space-y-1.5"
      onKeyDown={handleKeyDown}
    >
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-ink">{label}</span>
        <span className="text-muted">{displayLabel}</span>
      </div>

      {/* Primary human-readable entity selector trigger */}
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={`${label}: ${displayName}`}
        aria-controls={`${testIdPrefix}-listbox`}
        onClick={() => setOpen((v) => !v)}
        data-testid={`${testIdPrefix}-picker-trigger`}
        className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-[6px] border border-control bg-surface hover:bg-raised text-left transition-colors"
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 min-w-0">
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{
                backgroundColor: LABEL_COLORS[displayLabel] || "#6e7681",
              }}
            />
            <span className="text-xs font-semibold text-ink truncate">
              {displayName}
            </span>
          </div>
          <div className="font-mono text-xs text-faint truncate mt-0.5 pl-4">
            {valueId}
          </div>
        </div>
        <ChevronDown
          className={`w-4 h-4 text-muted shrink-0 transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Dropdown search popover */}
      {open && (
        <div className="absolute left-0 right-0 top-full mt-1 rounded-[8px] border border-border bg-surface p-2.5 z-50 space-y-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-faint absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              ref={searchInputRef}
              type="text"
              autoFocus
              role="combobox"
              aria-autocomplete="list"
              aria-expanded={true}
              aria-label={`Search ${label}`}
              aria-controls={`${testIdPrefix}-listbox`}
              aria-activedescendant={
                activeIndex >= 0 ? `${testIdPrefix}-opt-${activeIndex}` : undefined
              }
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search entity by name, DOI, or ORCID..."
              data-testid={`${testIdPrefix}-search-input`}
              className="w-full ledger-input h-8 pl-8 text-xs"
            />
          </div>

          <div
            id={`${testIdPrefix}-listbox`}
            role="listbox"
            className="max-h-52 overflow-y-auto divide-y divide-rule"
          >
            {searchQuery.isLoading && (
              <div className="py-3 text-center text-xs text-muted">
                Searching entities...
              </div>
            )}

            {!searchQuery.isLoading &&
              results.map((item, idx) => {
                const isActive = idx === activeIndex;
                const isSelected = item.id === valueId;
                return (
                  <button
                    key={item.id}
                    id={`${testIdPrefix}-opt-${idx}`}
                    role="option"
                    aria-selected={isSelected || isActive}
                    type="button"
                    onClick={() => selectItem(item)}
                    onMouseEnter={() => setActiveIndex(idx)}
                    data-testid={`${testIdPrefix}-option-${item.id}`}
                    className={`w-full px-2.5 py-2 text-left flex items-center justify-between gap-2 text-xs transition-colors ${
                      isActive
                        ? "bg-active"
                        : isSelected
                        ? "bg-raised"
                        : "hover:bg-raised"
                    }`}
                  >
                    <div className="min-w-0">
                      <div className="font-medium text-ink truncate">
                        {item.name}
                      </div>
                      <div className="font-mono text-xs text-faint truncate">
                        {item.label} · {item.id}
                      </div>
                    </div>
                    <span className="text-xs text-muted tabular-nums shrink-0">
                      {item.score.toFixed(1)}
                    </span>
                  </button>
                );
              })}

            {!searchQuery.isLoading && results.length === 0 && (
              <div className="py-3 text-center text-xs text-muted">
                No matching entities found.
              </div>
            )}
          </div>

          {/* Progressive disclosure for direct stable ID entry */}
          <details className="pt-1 border-t border-rule text-xs">
            <summary className="cursor-pointer text-muted hover:text-ink py-1">
              Enter stable ID directly
            </summary>
            <input
              type="text"
              value={valueId}
              onChange={(e) => {
                setCustomName(null);
                onChange(e.target.value);
              }}
              data-testid={`${testIdPrefix}-raw-id-input`}
              className="w-full ledger-input h-7 text-xs font-mono mt-1"
            />
          </details>
        </div>
      )}
    </div>
  );
};
