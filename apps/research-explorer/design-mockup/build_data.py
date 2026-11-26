#!/usr/bin/env python3
"""Extract the real data used by the redesign mockup and inline it into index.html.

Read-only over the repository's analysis outputs; writes only data.json and the
DATA block in index.html inside this folder. Standard library only.

Usage: python3 build_data.py   (run from anywhere)
"""
from __future__ import annotations

import collections
import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TRENDS = ROOT / "reports/final-exam/analysis-v2/trends"
DEMO_CACHE = ROOT / "reports/final-exam/rag-v1/demo-cache.json"
GRAPH = ROOT / "data/processed/enriched-graph-v5/graph.json"
YEARS = ["2021", "2022", "2023", "2024", "2025"]
YEAR_TOTALS = {"2021": 2240, "2022": 1997, "2023": 2217, "2024": 3121, "2025": 4042}

# Thermal-strip selection: subject id -> display name (sentence case, no acronyms in brackets).
STRIP = {
    "method:Q3621696": "Large language models",
    "method:Q114617315": "Diffusion models",
    "method:CLIP": "CLIP",
    "method:Mamba": "Mamba",
    "method:3D Gaussian Splatting": "3D Gaussian splatting",
    "task:Medical Image Segmentation": "Medical image segmentation",
    "task:Visual Question Answering": "Visual question answering",
    "method:contrastive learning": "Contrastive learning",
    "method:graph neural networks": "Graph neural networks",
    "task:text classification": "Text classification",
    "method:graph convolutional network": "Graph convolutional networks",
    "task:image captioning": "Image captioning",
}
LEADERS = ["Large language models", "Diffusion models", "CLIP", "Mamba", "Medical image segmentation"]
ALIASES = {"method:Q3621696": {"llms", "llm", "large language model", "language models", "language model"}}
CLASS_WORD = {"rising": "Rising", "emerging": "Emerging", "stable": "Stable", "declining": "Declining"}


def clean_org(name: str) -> str:
    name = re.sub(r" \((United States|China|United Kingdom)\)$", "", name)
    return name


def nice(name: str) -> str:
    if name.isupper() or any(c.isupper() for c in name[1:3]) or " " not in name and name[:1].isupper():
        return name
    out = name[:1].upper() + name[1:]
    return out


def load_trends():
    rows = {}
    for kind in ["method", "task", "dataset", "topic"]:
        for r in csv.DictReader(open(TRENDS / f"trends-{kind}.csv")):
            rows[r["id"]] = r
            rows[f"{kind}:{r['name']}"] = r
    return rows


def main() -> None:
    trends = load_trends()
    strip_rows = []
    max_slope = 0.0
    for key, disp in STRIP.items():
        r = trends[key]
        max_slope = max(max_slope, abs(float(r["slope_of_share"])))
    for key, disp in STRIP.items():
        r = trends[key]
        slope = float(r["slope_of_share"])
        t = (abs(slope) / max_slope) ** 0.5 * (1 if slope > 0 else -1)
        if r["class"] == "stable":
            t = max(-0.18, min(0.18, t))
        strip_rows.append({
            "id": r["id"], "name": disp, "raw_name": r["name"], "kind": r["kind"],
            "class": r["class"], "label": CLASS_WORD[r["class"]], "t": round(t, 3),
            "total": int(r["total_papers"]),
            "papers": [int(r[f"papers_{y}"]) for y in YEARS],
            "share": [round(float(r[f"share_{y}"]) * 100, 3) for y in YEARS],
            "p": round(float(r["slope_p_value"]), 3),
        })
    strip_rows.sort(key=lambda x: -x["t"])
    by_id = {s["id"]: s for s in strip_rows}

    # Organisation specialisation (relative concentration) per subject.
    gi = collections.defaultdict(list)
    for r in csv.DictReader(open(TRENDS / "group-interest.csv")):
        if not r["group"].startswith("organization:"):
            continue
        m = re.match(r"organization:(.*) \((organization:I\d+)\)$", r["group"])
        gi[r["subject"]].append({
            "name": clean_org(m.group(1)), "id": m.group(2),
            "papers": int(r["group_papers_in_subject"]), "group_papers": int(r["group_papers"]),
            "spec": round(float(r["rca"]), 2),
            "growth": round(float(r["growth_late_minus_early"]) * 100, 2),
        })

    def leading(subject_id, min_papers=3, n=8):
        rows = [x for x in gi.get(subject_id, []) if x["papers"] >= min_papers]
        if len(rows) < 3:
            rows = [x for x in gi.get(subject_id, []) if x["papers"] >= 2]
        rows.sort(key=lambda x: (-x["spec"], -x["papers"]))
        return rows[:n]

    # Paper-level graph facts for every strip subject.
    print("loading graph ...")
    g = json.load(open(GRAPH))
    nodes = {n["id"]: n for n in g["nodes"]}
    subj_ids = set(by_id)
    subj_papers = collections.defaultdict(set)
    paper_ents = collections.defaultdict(set)
    authors = collections.defaultdict(set)
    cited_by = collections.Counter()
    for e in g["edges"]:
        rel = e["relation"]
        if rel in ("USES_METHOD", "ADDRESSES_TASK", "USES_DATASET"):
            paper_ents[e["source_id"]].add(e["target_id"])
            if e["target_id"] in subj_ids:
                subj_papers[e["target_id"]].add(e["source_id"])
        elif rel == "AUTHORED":
            authors[e["target_id"]].add(e["source_id"])
        elif rel == "CITES":
            cited_by[e["target_id"]] += 1

    def paper_info(pid):
        n = nodes.get(pid)
        if not n:
            return None
        venue = pid.split(":")[1].upper()
        auths = [nodes[a]["name"] for a in sorted(authors.get(pid, ()))][:3]
        return {"id": pid, "title": n["name"], "year": n["properties"].get("year"), "venue": venue,
                "authors": auths, "n_authors": len(authors.get(pid, ())), "cited": cited_by.get(pid, 0),
                "url": n["properties"].get("official_url")}

    topics = {}
    for sid, s in by_id.items():
        papers = subj_papers[sid]
        co = collections.Counter()
        for p in papers:
            for ent in paper_ents[p]:
                if ent != sid:
                    co[ent] += 1
        related = {"Method": [], "Task": [], "Dataset": []}
        for ent, c in co.most_common():
            lab = nodes[ent]["label"]
            if nodes[ent]["name"].lower() in ALIASES.get(sid, ()):
                continue
            if lab in related and len(related[lab]) < 6 and c >= 2:
                related[lab].append({"name": nice(nodes[ent]["name"]), "papers": c})
        rcount = collections.Counter()
        for p in papers:
            for a in authors.get(p, ()):
                rcount[a] += 1
        researchers = [{"name": nodes[a]["name"], "papers": c} for a, c in rcount.most_common(10) if c >= 5]
        top = sorted(papers, key=lambda p: (-cited_by.get(p, 0), -(nodes[p]["properties"].get("year") or 0), p))[:5]
        topics[sid] = {
            "orgs": leading(sid),
            "researchers": researchers,
            "max_researcher_papers": rcount.most_common(1)[0][1] if rcount else 0,
            "related": related,
            "top_papers": [paper_info(p) for p in top],
            "graph_papers": len(papers),
        }

    leaders = []
    for disp in LEADERS:
        s = next(x for x in strip_rows if x["name"] == disp)
        leaders.append({"id": s["id"], "name": disp, "class": s["class"], "t": s["t"],
                        "orgs": leading(s["id"], n=3)})

    # Ask demos.
    cache = json.load(open(DEMO_CACHE))
    demos_out = []
    for idx in (0, 1, 2, 4):
        demos_out.append(build_demo(cache["demos"][idx], paper_info, nodes))

    data = {
        "years": YEARS, "year_totals": YEAR_TOTALS,
        "strip": strip_rows, "topics": topics, "leaders": leaders,
        "demos": demos_out, "demo_model": cache["model"], "demo_generated_at": cache["generated_at"],
        "trend_note": json.load(open(TRENDS / "trends-summary.json"))["classification_note"],
    }
    (HERE / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    html_path = HERE / "index.html"
    if html_path.exists():
        html = html_path.read_text()
        blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        new = re.sub(r"(<script id=\"data\" type=\"application/json\">).*?(</script>)",
                     lambda m: m.group(1) + blob + m.group(2), html, count=1, flags=re.S)
        html_path.write_text(new)
        print("inlined data into index.html", len(blob), "bytes")


# ---------------------------------------------------------------------------
# Demo conversion: plain-language plan steps, footnoted answer, trimmed evidence.

PLAIN_FIELDS = [
    (r"papers after cutoff", "papers after 2022"),
    (r"share_delta", "share change"),
    (r"post_total >= 10, post_subject >= 2", "at least 10 papers after 2022, two of them on the subject"),
    (r"threshold: ", ""),
    (r"\(CAGR 2021-2025\)", "(2021 to 2025)"),
    (r"by lift", "by specialisation"),
    (r"personalized PageRank lift", "specialisation"),
    (r"for the topic 'Causal inference'", "in causal inference"),
    (r"'Causal inference'", "causal inference"),
    (r"Large Language Models \(LLMs\)", "Large language models"),
    (r"large-language-model", "large language model"),
]


def pct_points(x: float) -> str:
    return f"+{x * 100:.1f} points" if x >= 0 else f"{x * 100:.1f} points"


def rewrite_line(line: str) -> str:
    line = re.sub(r"^[-*] ", "", line).replace("Name: ", "")
    line = re.sub(r"share change (-?\d+\.\d+)", lambda m: "share change " + pct_points(float(m.group(1))), line)
    line = re.sub(r"(\d+\.\d{5,}) CAGR", lambda m: f"share up {float(m.group(1)) * 100:.0f}% a year", line)
    line = re.sub(r"with a CAGR of (\d+\.\d+)", lambda m: f"growing {float(m.group(1)) * 100:.0f}% a year", line)
    line = re.sub(r"lift (\d+\.\d+)", lambda m: f"specialisation {float(m.group(1)):.1f}×", line)
    line = re.sub(r"subject papers (\d+), total papers (\d+)", r"\1 of its \2 papers on the topic", line)
    for pat, rep in PLAIN_FIELDS:
        line = re.sub(pat, rep, line)
    return line


def step_text(demo_id: str, step: dict) -> tuple[str, str]:
    a = step.get("args", {})
    t = step["tool"]
    if demo_id.startswith("demo-01") and t == "neighbors":
        return "Find organizations that co-authored with Tsinghua University", f"{step['row_count']} collaborators found"
    if demo_id.startswith("demo-01") and t == "aggregate":
        return ("Compare each collaborator's share of language-model papers up to 2022 and after",
                "37 organizations had enough papers; 15 grew the most")
    if t == "trend":
        return "Rank methods by how fast their share of papers grew, 2021 to 2025", f"{step['row_count']} methods are rising"
    if t == "neighbors":
        tgt = a.get("filters", {}).get("target_labels", ["entities"])[0].lower() + "s"
        return f"Find {tgt} that appear in the same papers as diffusion models", f"{step['row_count']} {tgt} found"
    if t == "rank":
        return "Rank organizations by how concentrated their work is on causal inference", f"{step['row_count']} organizations ranked"
    return t, f"{step['row_count']} rows"


def build_demo(dm: dict, paper_info, nodes) -> dict:
    r = dm["result"]
    did = dm["demo_id"]
    steps = r["steps"]
    # Understanding step from the parser/linker output (real).
    # demo-05's linker also matched the word "lift" to a method; the mockup hides that spurious match.
    linked = [{"text": x["text"], "name": x.get("name"), "type": x["entity_type"]} for x in r.get("linked", [])
              if x["text"].lower() != "lift"]
    plan = []
    recog = ", ".join(f"{x['name'] or x['text']} ({x['type'].lower()})" for x in linked) or "the subject and the question type"
    after = r.get("parsed", {}).get("after_year")
    plan.append({"text": "Read the question and find the names it mentions",
                 "result": "Recognised " + recog.replace("Large Language Models (LLMs)", "large language models")
                 + (f", after {after}" if after else "")})
    for s in steps:
        txt, res = step_text(did, s)
        plan.append({"text": txt, "result": res, "step": s["step"]})
    plan.append({"text": "Write the answer and check every number against the results",
                 "result": "All numbers matched" if r.get("faithfulness_passed") else "Some numbers did not match"})

    # Rows per step (trim to plain columns).
    tables = []
    for s in steps:
        rows = s["rows"]
        if s["tool"] == "neighbors" and did.startswith("demo-01"):
            rows = sorted(rows, key=lambda x: -x["support_count"])
            tables.append({"step": s["step"], "title": "Tsinghua University's collaborators",
                           "columns": ["Organization", "Sector", "Country", "Shared papers"],
                           "rows": [[x["neighbor_name"], x.get("neighbor_sector") or "", x.get("neighbor_country_code") or "", x["support_count"]] for x in rows]})
        elif s["tool"] == "aggregate":
            tables.append({"step": s["step"], "title": "Share of language-model papers, up to 2022 and after",
                           "columns": ["Organization", "Up to 2022", "After 2022", "Share after", "Change"],
                           "rows": [[x["entity_name"], x["pre_papers"], x["post_papers"], x["post_gt_2022_share"], x["share_delta"]] for x in rows],
                           "pre": [x["pre_le_2022_share"] for x in rows],
                           "formats": ["text", "text", "text", "pct", "pp"]})
        elif s["tool"] == "trend":
            tables.append({"step": s["step"], "title": "Rising methods",
                           "columns": ["Method", "Papers", "Share 2021", "Share 2025", "Growth a year"],
                           "rows": [[nice(x["name"]).replace("Large Language Models (LLMs)", "Large language models"), x["total_papers"], x["share_by_year"]["2021"], x["share_by_year"]["2025"], x["cagr_of_share_2021_2025"]] for x in rows],
                           "formats": ["text", "int", "pct", "pct", "pct0"],
                           "series": [{"name": nice(x["name"]).replace("Large Language Models (LLMs)", "Large language models"),
                                       "share": [x["share_by_year"][y] * 100 for y in YEARS]} for x in rows]})
        elif s["tool"] == "neighbors":
            lab = s["args"]["filters"]["target_labels"][0]
            seen = {}
            for x in rows:
                nm = x["neighbor_name"]
                if nm not in seen or x["support_count"] > seen[nm]["support_count"]:
                    seen[nm] = x
            rr = sorted(seen.values(), key=lambda x: -x["support_count"])
            tables.append({"step": s["step"], "title": f"{lab}s used with diffusion models",
                           "kind": lab,
                           "columns": [lab, "Shared papers", "Link"],
                           "rows": [[nice(x["neighbor_name"]), x["support_count"], "stated in a paper" if x["relation"] == "APPLIED_TO" else "same paper"] for x in rr]})
        elif s["tool"] == "rank":
            tables.append({"step": s["step"], "title": "Organizations most specialised in causal inference",
                           "columns": ["Organization", "Specialisation", "Papers on the topic", "All papers"],
                           "rows": [[clean_org(x["name"]), x["lift"], x["subject_papers"], x["total_papers"]] for x in rows],
                           "formats": ["text", "x", "int", "int"]})

    # Footnoted answer.
    row_papers = {}
    for s in steps:
        for x in s["rows"]:
            nm = x.get("entity_name") or x.get("neighbor_name") or x.get("name")
            pids = x.get("paper_ids") or x.get("support_paper_ids") or []
            if nm and pids and nm not in row_papers:
                row_papers[nm] = pids
    footnotes = []

    def add_fn(label, pids, step):
        footnotes.append({"n": len(footnotes) + 1, "label": label, "papers": pids, "step": step})
        return len(footnotes)

    blocks = []
    text = r["answer"]
    for para in [p for p in text.split("\n") if p.strip()]:
        is_li = bool(re.match(r"^\s*[-*] ", para))
        line = rewrite_line(para.strip())
        segs = []
        # bracketed step references -> footnotes
        parts = re.split(r"\s?\[step (\d+)\]", line)
        for i, part in enumerate(parts):
            if i % 2 == 0:
                if part:
                    segs.append(part)
            else:
                st = int(part)
                segs.append({"fn": add_fn(f"Step {st}: {plan[st]['text'].lower()}", [], st)})
        if is_li:
            name = re.split(r":", line, maxsplit=1)[0].strip()
            pids = row_papers.get(name)
            if pids:
                segs.append({"fn": add_fn(name, pids, None)})
        blocks.append({"type": "li" if is_li else "p", "segs": segs})
    # Demo-03: footnote each named task/dataset that has shared papers.
    if did.startswith("demo-03"):
        blocks = []
        for para in [p for p in text.split("\n") if p.strip()]:
            segs = []
            pattern = re.compile(r"(" + "|".join(re.escape(n) for n in sorted(row_papers, key=len, reverse=True)) + r")( \(\d+ shared papers\))?")
            pos = 0
            for m in pattern.finditer(para):
                segs.append(para[pos:m.end()])
                if m.group(2):
                    segs.append({"fn": add_fn(m.group(1), row_papers[m.group(1)], None)})
                pos = m.end()
            segs.append(para[pos:])
            blocks.append({"type": "p", "segs": segs})

    cited = []
    for f in footnotes:
        for p in f["papers"]:
            if p not in cited:
                cited.append(p)
    result_ids = []
    for rp in r.get("result_papers") or []:
        for p in rp["paper_ids"]:
            if p not in result_ids:
                result_ids.append(p)
    papers = {p: paper_info(p) for p in set(cited) | set(result_ids[:40])}

    # Subgraph (trim, readable labels).
    sg_nodes, sg_edges = [], []
    if did.startswith("demo-01"):
        center = "organization:I99065089"
        agg = next(t for t in tables if t.get("formats") and t["columns"][0] == "Organization" and "Change" in t["columns"])
        agg_names = {row[0]: row for row in agg["rows"]}
        nb = sorted(steps[0]["rows"], key=lambda x: -x["support_count"])
        keep = [x for x in nb if x["neighbor_name"] in agg_names] + [x for x in nb if x["neighbor_name"] not in agg_names][:20]
        sg_nodes.append({"id": center, "name": "Tsinghua University", "label": "Organization", "hop": 0})
        for x in keep:
            grew = x["neighbor_name"] in agg_names
            sg_nodes.append({"id": x["neighbor_id"], "name": clean_org(x["neighbor_name"]), "label": "Organization", "hop": 1,
                             "highlight": grew, "delta": agg_names[x["neighbor_name"]][4] if grew else None})
            sg_edges.append({"source": x["neighbor_id"], "target": center, "hop": 1, "weight": x["support_count"], "label": f"{x['support_count']} shared papers"})
        # The cache keeps 50 of step 1's 100 rows; collaborators that only appear in step 2's input are added
        # without a shared-paper weight.
        present = {n["id"] for n in sg_nodes}
        for x in steps[1]["rows"]:
            if x["entity_id"] not in present:
                sg_nodes.append({"id": x["entity_id"], "name": clean_org(x["entity_name"]), "label": "Organization", "hop": 1,
                                 "highlight": True, "delta": x["share_delta"]})
                sg_edges.append({"source": x["entity_id"], "target": center, "hop": 1, "weight": 1, "label": "collaborator"})
        llm = "method:Q3621696"
        sg_nodes.append({"id": llm, "name": "Large language models", "label": "Method", "hop": 2})
        for x in steps[1]["rows"]:
            sg_edges.append({"source": x["entity_id"], "target": llm, "hop": 2, "weight": x["post_gt_2022_subject_papers"], "label": f"{x['post_gt_2022_subject_papers']} papers after 2022"})
    elif r.get("subgraph_nodes"):
        for n in r["subgraph_nodes"]:
            sg_nodes.append({"id": n["id"], "name": nice(n["name"]), "label": n["label"], "hop": 0 if n["id"] == "method:Q114617315" else n.get("hop") or 1})
        ids = {n["id"] for n in sg_nodes}
        for e in r["subgraph_edges"]:
            if e["source"] in ids and e["target"] in ids:
                sg_edges.append({"source": e["source"], "target": e["target"], "hop": e.get("hop") or 1, "weight": e.get("support_count") or 1,
                                 "label": f"{e.get('support_count') or 1} shared papers"})

    titles = {"demo-01": "Tsinghua's collaborators and language models",
              "demo-02": "Fastest-growing methods",
              "demo-03": "What diffusion models are used for",
              "demo-05": "Who specialises in causal inference"}
    chart = {"demo-01": "slope", "demo-02": "lines", "demo-03": "bars", "demo-05": "bars"}[did[:7]]
    follow = {
        "demo-01": ["Which Tsinghua collaborators lost share?", "Show the papers behind Chinese University of Hong Kong", "Compare with Peking University's collaborators"],
        "demo-02": ["Who leads large language model research?", "Which methods are cooling down?", "Show diffusion models over time"],
        "demo-03": ["Which organizations publish most on diffusion models?", "How did image editing change over time?", "Compare with GANs"],
        "demo-05": ["How has causal inference changed since 2021?", "Show Columbia University's causal inference papers", "Which researchers connect these groups?"],
    }[did[:7]]
    return {
        "id": did, "title": titles[did[:7]], "question": dm["question"], "mode": r.get("mode"),
        "latency": dm["total_latency_s"], "plan": plan, "blocks": blocks, "footnotes": footnotes,
        "tables": tables, "papers": papers, "cited": cited, "result_ids": result_ids,
        "result_count": len(result_ids), "nodes": sg_nodes, "edges": sg_edges, "chart": chart,
        "checked": bool(r.get("faithfulness_passed")), "follow": follow,
        "raw_answer": r["answer"],
    }


if __name__ == "__main__":
    main()
