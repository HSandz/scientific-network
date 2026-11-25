import React, { useId, useState } from "react";
import { Info } from "lucide-react";

export interface MetricTooltipProps {
  label: string;
  definition: string;
  denominator?: string;
  network?: string;
  graphVersion?: string;
}

/** Accessible hover/keyboard-focus metric definition tooltip (spec §6.5). */
export const MetricTooltip: React.FC<MetricTooltipProps> = ({
  label,
  definition,
  denominator = "Corpus total / projection denominator",
  network = "enriched-cb371912e308",
  graphVersion = "enriched-cb371912e308",
}) => {
  const [open, setOpen] = useState(false);
  const tid = useId();

  return (
    <span className="relative inline-flex items-center gap-1">
      <span>{label}</span>
      <button
        type="button"
        aria-describedby={open ? tid : undefined}
        aria-label={`Metric definition for ${label}`}
        onClick={() => setOpen((v) => !v)}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        className="inline-flex items-center justify-center w-4 h-4 rounded-full text-faint hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--accent)]"
      >
        <Info className="w-3.5 h-3.5" />
      </button>
      {open && (
        <span
          id={tid}
          role="tooltip"
          className="absolute left-0 top-full mt-1.5 z-50 w-72 p-2.5 rounded-[8px] border border-control bg-surface text-ink shadow-lg text-[11px] leading-snug text-left font-normal"
        >
          <span className="block font-semibold mb-1">{label}</span>
          <span className="block text-muted mb-1">{definition}</span>
          <span className="block text-faint">Denominator: {denominator}</span>
          <span className="block text-faint font-mono mt-0.5">
            {network} · {graphVersion}
          </span>
        </span>
      )}
    </span>
  );
};
