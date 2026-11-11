# V5 quality and isolated identity candidate

[Baseline report](baseline-audit.md),[machine census](baseline-audit.json),
[ranked issues](issue-inventory.csv),[identity evidence](identity-error-analysis.md).
Original source/graph data stay ignored;restore permitted original bytes rather
than reacquiring a new API snapshot. No external collection in this work.

```bash
uv sync --locked --group dev --extra analysis --extra report
uv run python -m scientific_network.quality.identity_audit \
  --works data/interim/release-v1/works.jsonl \
  --graph data/processed/release-graph-v4/graph.json \
  --freeze reports/release-v4/content-freeze-v4.json \
  --cache-dir data/raw/openalex-release-v1 \
  --output-dir reports/runs/manual-quality-v5 \
  --detail-dir reports/runs/manual-quality-v5-details
uv run pytest
```

Use unused directories every time. JSON includes venue/year strata,input hashes
and reason categories. Record-level source diagnostics stay in ignored run storage.
Source equality and graph size do not establish semantic accuracy.
