# Research Trend Navigator — Live Demo Script Draft (5–7 minutes)

**Rule compliance**: Every walkthrough query in this script comes strictly from the 7 pre-cached scripted demos in `reports/final-exam/rag-v1/demo-cache.json` (`demo-01` through `demo-07`), which were verified disjoint from all 80 test questions in `data/manifests/qa-benchmark-v1/questions.jsonl`. No test question is ever demoed live, tuned on, or inspected.

**Pre-demo checklist (~30s before presenting)**:
1. Confirm backend + `neo4j-enriched` (Bolt 7690) are healthy; check `Use demo cache` toggle in **Ask** (`checked` by default as the primary reliability guard if the hosted/local SLM is offline or slow).
2. Open `?tab=trends` in desktop browser (`1440x900`).

---

## Segment 1 — Research Trends & Subject Drill-Down (1.5 min)
1. **Trends (`?tab=trends`)**:
   - Point out header badge **`enriched-cb371912e308`** (vs `release-d3c788c3114a` on the base Explorer tabs).
   - Hover/focus the **Annual share** and **Period Δ (pp)** `MetricTooltip` badges; emphasize the classification pill **`descriptive`** (historical 2021–2025 linear slopes and CAGR, not causal forecasting).
   - Filter or switch kind (`Topic` -> `Method`) to show the rendered multi-line chart and Top Method × Year Share Heatmap (note fast sub-second load from precomputed `analysis-final-exam-v2`).
2. **Topic / Method Subject (`?tab=subjects`)**:
   - Open e.g. Large Language Models or Diffusion Models from Trends; highlight the **AI-generated from graph data** / Wikipedia CC BY-SA 4.0 provenance badge, annual share trajectory, and **PPR Lift** / **RCA** table linking directly to specialized organizations.

## Segment 2 — Research Groups, Communities & Network Science (1.5 min)
3. **Groups (`?tab=groups`)**:
   - Show the **Organization × Topic RCA Heatmap**, organization-anchored communities (`>= 100` badged `large`), and non-government parent roll-up (explain honest scope: ministries/funding councils separated to avoid false institutional clusters).
4. **Communities (`?tab=communities`)**:
   - Click a Leiden super-node (`N1` / `L0`) to expand members; highlight the **`AI-generated from graph data`** label on community report summaries and clickable `[paper:...]` citations opening Node 360.
5. **Network Science (`?tab=network`)**:
   - Show **S1–S3** small-world comparison (`N1`, `N2`, `N4` against both Erdős–Rényi and degree-preserving rewired baselines, clustering definition disclosed via `MetricTooltip`), `N1` shortest-path histogram, `L`/`C` yearly evolution, and `log10–log10` degree distribution.

## Segment 3 — Grounded Multi-Hop & GraphRAG Ask Walkthrough (2.5 min)
Open **Ask** (`?tab=ask`), keep **`Use demo cache`** enabled (or run live against Qwen3.5-4B 4-bit where progressive SSE steps appear in ~1–2s):
1. **Flagship Multi-Hop + Aggregation (`demo-01-worked-example`)**:
   - Prompt: *"Which organizations collaborating with Tsinghua University increased their share of large-language-model papers after 2022?"*
   - Highlight:
     - Clean **Step 1 (`neighbors`) -> Step 2 (`aggregate`)** trace and collision-free concentric hop-1 subgraph.
     - Both **paper counts (`k of n`) and shares**, plus the config-driven minimum-paper threshold (`post_total >= 10, post_subject >= 2`: 37 qualified, 27 excluded below threshold) shown top 15 ranked by delta share.
     - **`Faithfulness: Verified`** badge + **`AI-generated from graph data`** label.
2. **Method Co-Occurrence with Verbatim Paper IDs (`demo-03-method-task-cooccurrence`)**:
   - Show Diffusion Models co-occurring tasks and datasets with verbatim clickable citations (`[paper:ijcai:2024:251]`, etc.).
3. **Ambiguous Name Guard & Co-Authorship Path (`demo-04-researcher-path`)**:
   - Trigger *"How is Shirui Pan connected to Chengjie Wang..."* -> show intentional **`needs_disambiguation`** stop when multiple researchers share `"Chengjie Wang"` rather than silently merging on name alone (D040 identity integrity).
4. **Corpus-Wide Global Map-Reduce (`demo-06-global-communities`)**:
   - Switch to **Global** summary over Leiden community reports showing major clusters (`N1:87`, `L0:122`, `N1:42`, etc.).

## Segment 4 — About the Data, Evaluation Results & Honest Limits (1 min)
Open **About** (`?tab=about`):
- Present frozen **v4** (`release-d3c788c3114a`) + enriched **v5** (`enriched-cb371912e308`) provenance, **E4** AI-assessed precision intervals, and **Phase 2 (`qa-eval-v1`) benchmark results on the 69 kept test questions**:
  - Multi-hop `S4` leads factual accuracy (`0.4273` overall, `0.6466` on 3-hop) vs `S1` SLM alone (`0.1242`), `S2` Vector RAG (`0.0547`), and `S3` GraphRAG (`0.1630`), with `87.0%` automatic faithfulness.
  - Honestly state the tradeoffs: `S2` achieves higher AI-assessed single-abstract citation support (`23/25 = 92.0%` vs `S4`'s `9/25 = 36.0%`) and global pairwise win rate (`80.0%` vs `52.2%`) because abstract chunks carry dense paper-specific prose whereas graph aggregation tools attach paper IDs without abstract text; and all citation/pairwise judgments are AI-assessed with adjudicator C sharing B's model family.
- **Live-Demo Fallback Plan**: If the hosted SLM endpoint is unavailable during Q&A, `Ask` serves the 7 cached scripted demos cleanly (`from_cache=True`, non-500 graceful message for uncached custom prompts).
