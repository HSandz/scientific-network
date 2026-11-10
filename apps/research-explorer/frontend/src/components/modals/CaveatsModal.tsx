import React, { useRef } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  X,
} from "lucide-react";
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

  const q = summary?.quality;
  const caveats = summary?.scientific_caveats || [
    "Release scope (D040): AAAI and IJCAI 2021–2025 main-track papers from roster v10 (13,617 core papers); 62 unresolved or unavailable candidates are excluded.",
    "Edge precision is 96.50% (193/200, Wilson 95% CI: 92.95%–98.29%, target 90.0% PASS) under the frozen dual-agent AI-assessed audit (agent-audit-v1). Human validation was not performed; Wilson intervals capture sampling variance only, not evaluator error.",
    "Affiliation coverage is 73.71% (48,259/65,469 authorship positions on OpenAlex-matched works; 48,259/65,507 = 73.67% across all official authorship positions; 48,259/50,437 = 95.68% conditional on accepted authorships; 10,037/13,617 core papers with ≥1 accepted AFFILIATED_WITH edge), missing the 80.0% target (FAIL) because OpenAlex omits institution metadata on a subset of works (especially IJCAI 2022–2024).",
    "Topic assignments (HAS_TOPIC) use embedding inference (bge-small-en-v1.5, threshold 0.56, max 3 leaf topics), covering 85.00% of core papers (11,575/13,617, target 80.0% PASS; 2,042 abstained). Historical AI-assessed topic-label precision is 68.63% (140/204, target 95.0% FAIL) and historical blind dual-agent micro-F1 is 0.4667 (vs phrase-baseline micro-F1 0.2301, precision 0.9286 at 26.0% test coverage).",
    "Citation edges (CITES) are restricted to within-corpus core-to-core references (19,351 edges across 8,907 papers); raw in-degree and PageRank are not exposure-time normalized.",
    "Geometric distance on the 2D graph canvas is a deterministic layout aid only and does not represent a scientifically measured variable.",
  ];

  const domainNodesText =
    summary?.total_nodes !== undefined
      ? `${summary.total_nodes.toLocaleString()} domain nodes (target ≥ 2,000)`
      : "47,875 domain nodes (target ≥ 2,000)";
  const coreEdgesText =
    summary?.unique_core_factual_edges !== undefined
      ? `${summary.unique_core_factual_edges.toLocaleString()} unique R1–R4 core factual edges (target ≥ 5,000)`
      : "110,026 unique R1–R4 core factual edges (target ≥ 5,000)";

  const edgePrecText = q?.edge_precision !== undefined
    ? `${(q.edge_precision * 100).toFixed(2)}% AI-assessed edge precision (${q.edge_precision_correct ?? 193}/${q.edge_precision_total ?? 200}, Wilson 95% CI: ${(((q.edge_precision_wilson_lower ?? 0.9295)) * 100).toFixed(2)}%–${(((q.edge_precision_wilson_upper ?? 0.9829)) * 100).toFixed(2)}%, target ${(((q.edge_precision_target ?? 0.9)) * 100).toFixed(1)}% PASS)`
    : "96.50% AI-assessed edge precision (193/200, Wilson 95% CI: 92.95%–98.29%, target 90.0% PASS)";

  const affilText = q?.affiliation_coverage !== undefined
    ? `Affiliation coverage is ${(q.affiliation_coverage * 100).toFixed(2)}% (${(q.affiliation_positions_resolved ?? 48259).toLocaleString()} / ${(q.affiliation_positions_eligible ?? 65469).toLocaleString()} authorship positions on OpenAlex-matched works; ${(q.affiliation_papers_with_edge ?? 10037).toLocaleString()} / ${(q.affiliation_papers_eligible ?? 13617).toLocaleString()} core papers; target ${(((q.affiliation_target ?? 0.8)) * 100).toFixed(1)}% FAIL).`
    : "Affiliation coverage is 73.71% (48,259 / 65,469 authorship positions on OpenAlex-matched works; 10,037 / 13,617 core papers; target 80.0% FAIL).";

  const topicText = q?.topic_coverage !== undefined
    ? `Topic coverage is ${(q.topic_coverage * 100).toFixed(2)}% (${(q.topic_papers_labeled ?? 11575).toLocaleString()} / ${(q.topic_papers_eligible ?? 13617).toLocaleString()} core papers, target ${(((q.topic_coverage_target ?? 0.8)) * 100).toFixed(1)}% PASS). AI-assessed topic-label precision is ${(((q.topic_precision ?? 0.6863)) * 100).toFixed(2)}% (140/204, target ${(((q.topic_precision_target ?? 0.95)) * 100).toFixed(1)}% FAIL) and historical micro-F1 is ${(q.topic_embedding_micro_f1 ?? 0.4667).toFixed(4)} (vs ${(q.topic_phrase_baseline_f1 ?? 0.2301).toFixed(4)} phrase baseline).`
    : "Topic coverage is 85.00% (11,575 / 13,617 core papers, target 80.0% PASS). AI-assessed topic-label precision is 68.63% (140/204, target 95.0% FAIL) and historical micro-F1 is 0.4667 (vs 0.2301 phrase baseline).";

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
              Release v4 (<span className="font-mono">release-d3c788c3114a</span>) · D040 OpenAlex-backed evidence protocol
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
                <span>Core size &amp; factual gates: PASS</span>
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
