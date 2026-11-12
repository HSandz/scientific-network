# Consolidate LLM review wording

Status: complete. Scope: report/latex/ only; no commit authorized.

Consolidate AI-review mentions to one neutral passage per edition, identify
GPT-6.1-Sol for report review, and remove repeated evaluator-related limitation
prose. Preserve recorded evaluation outcomes and avoid attributing historical
edge/topic judgments to a different model. Preserve material data facts.


## Results

One neutral LLM-review passage per language now identifies GPT-6.1-Sol for
report review. Repeated AI-use disclosure, reviewer-independence caveats and
human-validation caveats removed. Historical evaluation numbers and data facts
retained; historical edge/topic review is not falsely attributed to GPT-6.1-Sol.

`make -C report/latex all` and `.venv/bin/python
report/latex/scripts/verify-report.py` passed (exit 0). Both editions remain
24 portrait A4 pages; numerical parity and pinned-source checks pass. Extracted
PDF text confirms exactly one GPT-6.1-Sol mention per edition. Quality and
conclusion pages rendered and inspected in both languages: no overflow, clipping,
or broken Vietnamese accents. First image-render attempts using the system and
project Python failed because PyMuPDF is unavailable; Poppler rendering succeeded.
Outside-report source diff unchanged; no staging, commit or external action.
Evidence: `review/llm-wording-2026-11-12/`.
Next step: human proofreading before submission.
