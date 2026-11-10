import React, { useRef } from "react";
import { AlertTriangle, CheckCircle2, X } from "lucide-react";
import { useModalDialog } from "../../lib/useModalDialog";
import { useExplorerStore } from "../../stores/useExplorerStore";
import { GraphSummaryResponse } from "../../types/explorer";

interface CaveatsModalProps {
  summary?: GraphSummaryResponse;
}

export const CaveatsModal: React.FC<CaveatsModalProps> = ({ summary }) => {
  const { caveatsModalOpen, setCaveatsModalOpen } = useExplorerStore();
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const dialogRef = useModalDialog({
    isOpen: caveatsModalOpen,
    onClose: () => setCaveatsModalOpen(false),
    initialFocusRef: closeButtonRef,
  });

  if (!caveatsModalOpen) return null;

  const caveats = summary?.scientific_caveats || [
    "Evidence unavailable. No independent human validation; reviewer independence and verified course accuracy not established.",
  ];
  const q = summary?.quality;
  const number = (n: number | undefined) =>
    n === undefined || n === null ? "Unavailable" : n.toLocaleString();
  const percent = (n: number | undefined) =>
    n === undefined || n === null ? "Unavailable" : `${(n * 100).toFixed(2)}%`;
  const domainNodesText = `${number(summary?.total_nodes)} domain nodes`;
  const coreEdgesText = `${number(summary?.unique_core_factual_edges)} unique R1–R4 factual edges`;
  const edgePrecText = `${percent(q?.edge_precision)} AI-assessed edge precision (${number(q?.edge_precision_correct)}/${number(q?.edge_precision_total)}, Wilson 95% CI: ${percent(q?.edge_precision_wilson_lower)}–${percent(q?.edge_precision_wilson_upper)}, target ${percent(q?.edge_precision_target)}, ${q?.edge_precision_status || "Unavailable"})`;
  const affilText = `Affiliation coverage ${percent(q?.affiliation_coverage)} (${number(q?.affiliation_positions_resolved)} / ${number(q?.affiliation_positions_eligible)} authorship positions on matched works; target ${percent(q?.affiliation_target)}, ${q?.affiliation_status || "Unavailable"}).`;
  const topicText = `Topic coverage ${percent(q?.topic_coverage)} (${number(q?.topic_papers_labeled)} / ${number(q?.topic_papers_eligible)} core papers; target ${percent(q?.topic_coverage_target)}, ${q?.topic_coverage_status || "Unavailable"}). AI-assessed topic-label precision ${percent(q?.topic_precision)} (${number(q?.topic_precision_true_positive)} / ${number(q?.topic_precision_predicted_labels)} weighted label judgments; target ${percent(q?.topic_precision_target)}, ${q?.topic_precision_status || "Unavailable"}). Historical micro-F1 ${q?.topic_embedding_micro_f1?.toFixed(4) ?? "Unavailable"} vs ${q?.topic_phrase_baseline_f1?.toFixed(4) ?? "Unavailable"} phrase baseline.`;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/55"
      onClick={() => setCaveatsModalOpen(false)}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="caveats-modal-title"
        tabIndex={-1}
        className="w-full max-w-2xl bg-surface rounded-[8px] border border-border overflow-hidden flex flex-col max-h-[85vh] outline-none"
        onClick={(e) => e.stopPropagation()}
        data-testid="caveats-modal"
      >
        <div className="px-5 py-3.5 border-b border-border flex items-center justify-between gap-3">
          <div>
            <h2
              id="caveats-modal-title"
              className="text-base font-semibold text-ink"
            >
              Scientific evidence standards, quality gates &amp; limitations
            </h2>
            <p className="text-xs text-muted mt-0.5">
              Release v4 (
              <span className="font-mono">
                {summary?.graph_version || "Unavailable"}
              </span>
              ) · D040 OpenAlex-backed evidence protocol
            </p>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={() => setCaveatsModalOpen(false)}
            aria-label="Close caveats modal"
            className="ledger-btn min-h-[36px] sm:h-7 px-2.5 text-xs shrink-0"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto space-y-4 text-xs">
          {/* Gate Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="p-3.5 rounded-[8px] bg-ground border border-border">
              <div className="font-semibold text-ink flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-[var(--positive)] shrink-0" />
                <span>
                  Core size &amp; factual gates:{" "}
                  {summary ? "See measured size inventory" : "Unavailable"}
                </span>
              </div>
              <p className="text-xs mt-1 text-muted leading-relaxed tabular-nums">
                {domainNodesText} and {coreEdgesText}.
              </p>
            </div>

            <div className="p-3.5 rounded-[8px] bg-ground border border-border">
              <div className="font-semibold text-ink flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-[var(--warning)] shrink-0" />
                <span>AI-assessed precision &amp; coverage limits</span>
              </div>
              <p className="text-xs mt-1 text-muted leading-relaxed tabular-nums">
                {edgePrecText}. {affilText} {topicText}
              </p>
            </div>
          </div>

          {/* Detailed Caveats */}
          <div className="space-y-2">
            <div className="text-xs font-medium text-ink">
              Mandatory methodological disclosures
            </div>
            <ul className="space-y-2">
              {caveats.map((item, idx) => (
                <li
                  key={idx}
                  className="p-3 rounded-[6px] bg-ground border border-border text-muted leading-relaxed"
                >
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
