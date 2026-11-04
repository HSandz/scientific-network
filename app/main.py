"""Optional local artifact preview; the evidence-backed demo remains planned."""

import json
from pathlib import Path

from pydantic import ValidationError
import streamlit as st

from scientific_network.contracts import GraphArtifact
from scientific_network.graph.validate import graph_counts, validate_graph

st.set_page_config(page_title="AI Research Network", layout="wide")
st.title("AI Research Network")
st.caption("NeurIPS 2023 main track + ICML 2023 · local artifact preview")
upload = st.file_uploader("Open a graph artifact", type=["json"])
fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/synthetic_graph.json"
try:
    graph = GraphArtifact.model_validate_json(upload.getvalue() if upload else fixture.read_bytes())
except (OSError, ValidationError) as exc:
    st.error(str(exc))
    st.stop()

if graph.is_synthetic:
    st.warning("Invented example for testing. These are not collected researchers, publications or results.")
st.write(f"Graph version: `{graph.graph_version}`")
st.info("Structural checks do not measure accuracy. Independent audit, recall and coverage are not available in this preview.")
errors = validate_graph(graph)
if errors:
    st.error("Artifact failed structural validation.")
    st.json(errors)
    st.stop()
counts = graph_counts(graph)
left, right = st.columns(2)
left.subheader("Nodes by label")
left.dataframe([{"label": key, "count": value} for key, value in counts["nodes_by_label"].items()], hide_index=True)
right.subheader("Relationships")
right.dataframe([{"relation": key, "count": value} for key, value in counts["edges_by_relation"].items()], hide_index=True)
st.subheader("Evidence records")
st.json(json.loads(graph.model_dump_json())["evidence"], expanded=False)
st.caption("Planned: entity search, bounded network neighborhoods, source inspection, topic portfolios and measured quality summaries.")
