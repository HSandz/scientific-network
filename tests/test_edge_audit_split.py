"""Split-with-overlap edge audit (D040, release plan section 2.4) on the invented fixture."""

import csv
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from scientific_network.cli import main
from scientific_network.evaluation.edge_audit import (
    ADJUDICATION_FIELDS,
    SPLIT_FIELDS,
    _assignments,
    _load_quality,
    cohens_kappa,
    prepare_edge_audit_sample,
)

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "tests/fixtures/synthetic_graph.json"
RELEASE_QUALITY = ROOT / "configs/quality-release-v1.yaml"
NODE = shutil.which("node")
CHROME = shutil.which("google-chrome")


def _config(path: Path, *, global_size=10, per_type=2, overlap=4, **audit_overrides) -> Path:
    config = yaml.safe_load(RELEASE_QUALITY.read_text())
    config["audit"].update({"global_sample_size": global_size, "per_type_sample_size": per_type,
                            "overlap_sample_size": overlap, **audit_overrides})
    path.write_text(yaml.safe_dump(config))
    return path


def _prepare(tmp_path, graph=GRAPH, **kwargs):
    config = _config(tmp_path / "quality.yaml", **kwargs)
    sample = tmp_path / "sample.csv"
    summary = prepare_edge_audit_sample(graph, config, sample)
    with sample.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return config, sample, summary, rows


def _write(path: Path, rows: list[dict], fields=SPLIT_FIELDS) -> Path:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def _answer(row: dict, decision="correct", category="", reason="") -> dict:
    return {**row, "decision": decision, "error_category": category, "reason": reason,
            "reviewed_at": "2026-11-09T21:00:00+07:00"}


def _complete(rows, overrides=None) -> list[dict]:
    overrides = overrides or {}
    return [_answer(row, *overrides.get((row["edge_id"], row["reviewer_id"]), ())) for row in rows]


def _score(config, reviews, output, graph=GRAPH, adjudications=None):
    argv = ["score-edge-audit", "--input", str(graph), "--reviews", str(reviews),
            "--config", str(config), "--output", str(output)]
    if adjudications:
        argv += ["--adjudications", str(adjudications)]
    return main(argv)


# --- assignment ---------------------------------------------------------------------------


def test_assignments_are_deterministic_balanced_and_overlap_comes_from_the_global_sample(tmp_path):
    config, _, summary, rows = _prepare(tmp_path)
    _, audit = _load_quality(config)
    by_edge: dict[str, list[dict]] = {}
    for row in rows:
        by_edge.setdefault(row["edge_id"], []).append(row)
    overlap = {edge for edge, group in by_edge.items() if len(group) == 2}
    assert len(overlap) == audit["overlap_sample_size"] == 4
    assert all(by_edge[edge][0]["in_global_sample"] == "true" for edge in overlap)
    assert {r["reviewer_id"] for edge in overlap for r in by_edge[edge]} == {"A", "B"}
    assert all(len(group) == 1 for edge, group in by_edge.items() if edge not in overlap)
    assert all(row["is_overlap"] == str(row["edge_id"] in overlap).lower() for row in rows)
    solo = {"A": 0, "B": 0}
    for edge, group in by_edge.items():
        if edge not in overlap:
            solo[group[0]["reviewer_id"]] += 1
    assert abs(solo["A"] - solo["B"]) <= 1
    assert summary["union_sample_size"] == len(by_edge)
    assert summary["form_rows"] == len(rows) == len(by_edge) + len(overlap)
    assert summary["assigned_rows_per_reviewer"] == {"A": solo["A"] + 4, "B": solo["B"] + 4}
    # replay and seed sensitivity
    sampled = set(by_edge)
    global_ids = sorted(e for e in sampled if by_edge[e][0]["in_global_sample"] == "true")
    assert _assignments(audit, global_ids, sampled) == _assignments(audit, global_ids, sampled)
    reseeded = _assignments({**audit, "random_seed": audit["random_seed"] + 1}, global_ids, sampled)
    assert reseeded != _assignments(audit, global_ids, sampled)


def test_split_form_carries_reviewer_context_and_an_html_sheet_next_to_it(tmp_path):
    _, sample, summary, rows = _prepare(tmp_path)
    with sample.open(newline="", encoding="utf-8") as stream:
        assert csv.DictReader(stream).fieldnames == SPLIT_FIELDS
    assert all(row["reviewer_id"] in {"A", "B"} and not row["decision"] for row in rows)
    authored = next(row for row in rows if row["relation"] == "AUTHORED")
    assert authored["source_name"] and authored["target_name"]
    assert authored["correct_when"].startswith("The person is on the official byline")
    sheet = sample.with_suffix(".html")
    assert summary["review_sheet"] == str(sheet) and sheet.is_file()
    html = sheet.read_text(encoding="utf-8")
    assert all(row["edge_id"] in html for row in rows)
    # self-contained: outside the embedded data the page references no external resource
    template = re.sub(r'<script id="sheet-data".*?</script>', "", html, flags=re.S)
    assert "http://" not in template and "https://" not in template
    assert "<link" not in template and " src=" not in template


def test_existing_sheet_is_never_overwritten(tmp_path):
    config = _config(tmp_path / "quality.yaml")
    (tmp_path / "sample.html").write_text("keep")
    with pytest.raises(ValueError, match="review sheet already exists"):
        prepare_edge_audit_sample(GRAPH, config, tmp_path / "sample.csv")
    assert (tmp_path / "sample.html").read_text() == "keep"
    assert not (tmp_path / "sample.csv").exists()


def test_design_validation_rejects_malformed_split_settings(tmp_path):
    for overrides, message in (
        ({"review_design": "triple"}, "review_design"),
        ({"reviewer_ids": ["A"]}, "reviewer_ids"),
        ({"reviewer_ids": ["A", "A"]}, "reviewer_ids"),
        ({"overlap_sample_size": 11}, "overlap_sample_size"),
    ):
        config = _config(tmp_path / "bad.yaml", **overrides)
        with pytest.raises(ValueError, match=message):
            _load_quality(config)


# --- scoring ------------------------------------------------------------------------------


def test_split_scoring_end_to_end_with_agreement_adjudication_and_categories(tmp_path, capsys):
    config, sample, _, rows = _prepare(tmp_path)
    overlap = sorted({r["edge_id"] for r in rows if r["is_overlap"] == "true"})
    solo_global = sorted(r["edge_id"] for r in rows
                         if r["is_overlap"] == "false" and r["in_global_sample"] == "true")
    wrong = solo_global[0]
    wrong_row = next(r for r in rows if r["edge_id"] == wrong)
    overrides = {
        (wrong, wrong_row["reviewer_id"]): ("incorrect", "wrong_identity", "merged two people"),
        (overlap[0], "A"): ("correct", "", ""),
        (overlap[0], "B"): ("unverifiable", "unverifiable", "PDF not reachable"),
    }
    reviews = _write(tmp_path / "reviews.csv", _complete(rows, overrides))
    output = tmp_path / "evaluation.json"
    assert _score(config, reviews, output) == 1          # disagreement without adjudication
    assert not output.exists()
    assert "adjudication" in json.loads(capsys.readouterr().err)["message"]

    adjudications = tmp_path / "adjudications.csv"
    first = rows[0]
    _write(adjudications, [{
        "audit_id": first["audit_id"], "method_version": first["method_version"],
        "graph_version": first["graph_version"], "graph_sha256": first["graph_sha256"],
        "quality_config_sha256": first["quality_config_sha256"], "readiness_sha256": "",
        "frame_sha256": first["frame_sha256"], "edge_id": overlap[0], "adjudicator_id": "A+B",
        "decision": "unverifiable", "reason": "agreed it cannot be checked",
        "reviewed_at": "2026-11-10T10:00:00+07:00", "error_category": "unverifiable",
    }], ADJUDICATION_FIELDS + ["error_category"])
    capsys.readouterr()
    assert _score(config, reviews, output, adjudications=adjudications) == 0
    result = json.loads(output.read_text())
    assert result["review_design"] == "split_with_overlap"
    assert result["status"] == "synthetic_protocol_only" and result["course_gate"] is None
    assert result["global"]["total"] == 10
    # overlap edges are drawn from the global sample, so the adjudicated one is counted there
    assert result["global"]["incorrect"] == 1 and result["global"]["unverifiable"] == 1
    assert result["global"]["correct"] == 8
    assert result["global"]["precision"] == 0.8          # unverifiable counts as incorrect
    assert result["agreement"]["edges_reviewed_by_both"] == 4
    assert result["agreement"]["agreed"] == 3 and result["agreement"]["percent"] == 0.75
    assert result["agreement"]["cohens_kappa"] is None or isinstance(result["agreement"]["cohens_kappa"], float)
    assert result["error_categories"]["global_sample"] == {"unverifiable": 1, "wrong_identity": 1}
    counts = result["review_rows_per_reviewer"]
    assert counts["A"] + counts["B"] == len(rows)


def test_course_and_project_thresholds_are_reported_separately_for_a_real_graph(tmp_path):
    artifact = json.loads(GRAPH.read_text())
    artifact["is_synthetic"] = False
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps(artifact))
    config, _, _, rows = _prepare(tmp_path, graph=graph)
    reviews = _write(tmp_path / "reviews.csv", _complete(rows))
    output = tmp_path / "evaluation.json"
    assert _score(config, reviews, output, graph=graph) == 1     # project target not met
    result = json.loads(output.read_text())
    assert result["global"]["precision"] == 1.0 and result["global"]["total"] == 10
    assert result["course_gate"] == {"threshold": 0.9, "point_estimate": 1.0, "status": "pass"}
    assert result["global_point_precision_gate"] is True
    assert result["global_wilson_lower_gate"] is False          # 10/10 gives a lower bound near 0.72
    assert result["numeric_gate_status"] == "fail"
    assert result["size_gates"]["status"] == "failed"


@pytest.mark.parametrize("mutation,message", [
    ("drop_row", "frozen reviewer assignment"),
    ("wrong_reviewer", "frozen reviewer assignment"),
    ("unknown_reviewer", "outside audit.reviewer_ids"),
    ("no_category", "error_category"),
    ("category_on_correct", "blank for a correct"),
    ("bad_verdict", "correct, incorrect, or unverifiable"),
])
def test_split_scoring_rejects_malformed_packets(tmp_path, capsys, mutation, message):
    config, _, _, rows = _prepare(tmp_path)
    completed = _complete(rows)
    if mutation == "drop_row":
        completed = completed[1:]
    elif mutation == "wrong_reviewer":
        solo = next(r for r in completed if r["is_overlap"] == "false")
        solo["reviewer_id"] = "B" if solo["reviewer_id"] == "A" else "A"
    elif mutation == "unknown_reviewer":
        completed[0]["reviewer_id"] = "C"
    elif mutation == "no_category":
        completed[0].update(decision="incorrect", reason="x", error_category="")
    elif mutation == "category_on_correct":
        completed[0]["error_category"] = "wrong_topic"
    elif mutation == "bad_verdict":
        completed[0]["decision"] = "maybe"
    reviews = _write(tmp_path / "reviews.csv", completed)
    output = tmp_path / "evaluation.json"
    assert _score(config, reviews, output) == 1
    assert message in json.loads(capsys.readouterr().err)["message"]
    assert not output.exists()


def test_adjudication_for_a_single_reviewer_edge_is_rejected(tmp_path, capsys):
    config, _, _, rows = _prepare(tmp_path)
    reviews = _write(tmp_path / "reviews.csv", _complete(rows))
    solo = next(r for r in rows if r["is_overlap"] == "false")
    adjudications = tmp_path / "adjudications.csv"
    _write(adjudications, [{
        **{k: solo[k] for k in ("audit_id", "method_version", "graph_version", "graph_sha256",
                                  "quality_config_sha256", "frame_sha256", "edge_id")},
        "readiness_sha256": "", "adjudicator_id": "A+B", "decision": "correct", "reason": "x",
        "reviewed_at": "2026-11-10T10:00:00+07:00",
    }], ADJUDICATION_FIELDS)
    assert _score(config, reviews, tmp_path / "evaluation.json", adjudications=adjudications) == 1
    assert "without reviewer disagreement" in json.loads(capsys.readouterr().err)["message"]


def test_a_stricter_double_review_design_is_unchanged_by_the_new_option(tmp_path):
    config = yaml.safe_load((ROOT / "configs/quality.yaml").read_text())
    config["audit"].update(global_sample_size=5, per_type_sample_size=2)
    path = tmp_path / "quality.yaml"
    path.write_text(yaml.safe_dump(config))
    sample = tmp_path / "sample.csv"
    summary = prepare_edge_audit_sample(GRAPH, path, sample)
    assert summary["review_design"] == "double_review" and "review_sheet" not in summary
    assert not sample.with_suffix(".html").exists()


def test_cohens_kappa_matches_the_textbook_example_and_is_undefined_without_variation():
    pairs = ([("correct", "correct")] * 20 + [("correct", "incorrect")] * 5
             + [("incorrect", "correct")] * 10 + [("incorrect", "incorrect")] * 15)
    assert cohens_kappa(pairs) == pytest.approx(0.4)
    assert cohens_kappa([("correct", "correct"), ("incorrect", "incorrect")]) == pytest.approx(1.0)
    assert cohens_kappa([("correct", "correct")] * 50) is None
    assert cohens_kappa([]) is None


# --- the HTML sheet -----------------------------------------------------------------------


def _sheet_parts(sheet: Path) -> tuple[str, dict]:
    html = sheet.read_text(encoding="utf-8")
    data = json.loads(re.search(r'<script id="sheet-data" type="application/json">(.*?)</script>', html, re.S)[1])
    return html, data


def test_hostile_text_cannot_break_out_of_the_embedded_data(tmp_path):
    artifact = json.loads(GRAPH.read_text())
    hostile = '</script><img src=x onerror=alert(1)>'
    next(n for n in artifact["nodes"] if n["id"] == "paper:p1")["name"] = hostile
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps(artifact))
    _, sample, _, rows = _prepare(tmp_path, graph=graph, global_size=27, per_type=2, overlap=2)
    html, data = _sheet_parts(sample.with_suffix(".html"))
    assert "</script><img" not in html
    assert any(hostile in row["context"]["also_show"] + row["context"]["source_name"] + row["context"]["target_name"]
               for row in data["rows"])


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_exported_csv_from_the_sheet_scores_cleanly(tmp_path):
    config, sample, _, rows = _prepare(tmp_path)
    html_path = sample.with_suffix(".html")
    driver = tmp_path / "export.js"
    driver.write_text(
        "const fs=require('fs');const html=fs.readFileSync(process.argv[2],'utf8');"
        "const logic=/<script id=\"logic\">([\\s\\S]*?)<\\/script>/.exec(html)[1];"
        "const data=JSON.parse(/<script id=\"sheet-data\" type=\"application\\/json\">([\\s\\S]*?)<\\/script>/.exec(html)[1]);"
        "eval(logic);const answers=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));"
        "const built=buildCsv(data.fields,data.rows,answers,process.argv[4]);"
        "process.stdout.write(JSON.stringify({csv:built.csv,exported:built.exported,iso:isoLocal(new Date(Date.UTC(2026,10,8,0,0,0)))}));"
    )
    wrong = next(r for r in rows if r["is_overlap"] == "false" and r["in_global_sample"] == "true")
    packets = []
    for reviewer in ("A", "B"):
        answers = {}
        for row in rows:
            if row["reviewer_id"] != reviewer:
                continue
            answer = {"decision": "correct", "category": "", "reason": "", "at": "2026-11-09T21:00:00+07:00"}
            if row["edge_id"] == wrong["edge_id"]:
                answer.update(decision="incorrect", category="wrong_topic", reason='says "NLP", but it is, vision\nonly')
            answers[f"{reviewer}|{row['edge_id']}"] = answer
        answers_path = tmp_path / f"answers-{reviewer}.json"
        answers_path.write_text(json.dumps(answers))
        done = subprocess.run([NODE, str(driver), str(html_path), str(answers_path), reviewer],
                              capture_output=True, text=True, timeout=60, env={"TZ": "Asia/Bangkok", "PATH": ""})
        assert done.returncode == 0, done.stderr
        out = json.loads(done.stdout)
        assert out["iso"] == "2026-11-08T07:00:00+07:00"
        assert out["exported"] == sum(1 for r in rows if r["reviewer_id"] == reviewer)
        packet = tmp_path / f"export-{reviewer}.csv"
        packet.write_text(out["csv"], encoding="utf-8")
        packets.append(packet)
    with packets[0].open(newline="", encoding="utf-8") as a, packets[1].open(newline="", encoding="utf-8") as b:
        merged = list(csv.DictReader(a)) + list(csv.DictReader(b))
    reviews = _write(tmp_path / "reviews.csv", merged)
    output = tmp_path / "evaluation.json"
    assert _score(config, reviews, output) == 0
    result = json.loads(output.read_text())
    assert result["global"]["incorrect"] == 1 and result["global"]["total"] == 10
    assert result["error_categories"]["global_sample"] == {"wrong_topic": 1}
    wrong_rows = [r for r in merged if r["edge_id"] == wrong["edge_id"]]
    assert wrong_rows[0]["reason"] == 'says "NLP", but it is, vision\nonly'      # quoting survives the CSV round trip


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_incomplete_answers_are_not_exported(tmp_path):
    _, sample, _, rows = _prepare(tmp_path)
    driver = tmp_path / "export.js"
    driver.write_text(
        "const fs=require('fs');const html=fs.readFileSync(process.argv[2],'utf8');"
        "eval(/<script id=\"logic\">([\\s\\S]*?)<\\/script>/.exec(html)[1]);"
        "const data=JSON.parse(/<script id=\"sheet-data\" type=\"application\\/json\">([\\s\\S]*?)<\\/script>/.exec(html)[1]);"
        "const a=JSON.parse(process.argv[3]);const built=buildCsv(data.fields,data.rows,a,'A');"
        "process.stdout.write(String(built.exported));"
    )
    mine = [r for r in rows if r["reviewer_id"] == "A"]
    answers = {
        f"A|{mine[0]['edge_id']}": {"decision": "correct", "at": "2026-11-09T21:00:00+07:00"},
        f"A|{mine[1]['edge_id']}": {"decision": "incorrect", "category": "wrong_topic", "reason": "  ", "at": "x"},
        f"A|{mine[2]['edge_id']}": {"decision": "incorrect", "category": "", "reason": "no category", "at": "x"},
    }
    done = subprocess.run([NODE, str(driver), str(sample.with_suffix('.html')), json.dumps(answers)],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    assert done.stdout == "1"


@pytest.mark.skipif(CHROME is None, reason="google-chrome is not installed")
def test_sheet_renders_assigned_cards_in_a_real_browser(tmp_path):
    _, sample, _, rows = _prepare(tmp_path)
    sheet = sample.with_suffix(".html")
    command = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=3000",
               f"--user-data-dir={tmp_path / 'profile'}", "--dump-dom", f"{sheet.as_uri()}#reviewer=B"]
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        pytest.skip("headless Chrome did not finish")
    if done.returncode != 0 or "<html" not in done.stdout:
        pytest.skip(f"headless Chrome unavailable: {done.stderr[-200:]}")
    expected = sum(1 for r in rows if r["reviewer_id"] == "B")
    assert done.stdout.count('<article class="card"') == expected
    assert f"0 of {expected} complete" in done.stdout
    assert 'class="empty"' not in done.stdout       # the "choose your reviewer" prompt was replaced by cards


def test_single_reviewer_has_no_overlap_and_exports_score(tmp_path):
    config, sample, summary, rows = _prepare(
        tmp_path, review_design="single_reviewer", independent_reviewers=1,
        reviewer_ids=["A"], overlap=0, per_type=5,
    )
    assert summary["review_design"] == "single_reviewer"
    assert summary["overlap_sample_size"] == 0
    assert summary["form_rows"] == summary["union_sample_size"]
    assert {r["reviewer_id"] for r in rows} == {"A"}
    assert {r["is_overlap"] for r in rows} == {"false"}
    html, data = _sheet_parts(sample.with_suffix('.html'))
    assert data["meta"]["reviewer_ids"] == ["A"]
    reviews = _write(tmp_path / "done.csv", _complete(rows))
    assert _score(config, reviews, tmp_path / "result.json") == 0
    result = json.loads((tmp_path / "result.json").read_text())
    assert result["audit_completion"] == "complete"
    assert result["agreement"]["edges_reviewed_by_both"] == 0
    assert result["agreement"]["percent"] is None and result["agreement"]["cohens_kappa"] is None
    assert "unavailable" in result["agreement"]["availability"]


def test_partial_scores_actual_global_denominator_missingness_and_only_returned_overlap(tmp_path):
    config, _, summary, rows = _prepare(tmp_path)
    complete = _complete(rows)
    overlap_ids = sorted({r["edge_id"] for r in rows if r["is_overlap"] == "true"})
    solo = next(r for r in rows if r["in_global_sample"] == "true" and r["is_overlap"] == "false")
    # One global edge absent entirely; one overlap edge reviewed by just A.
    completed = [r for r in complete if r["edge_id"] != solo["edge_id"]
                 and not (r["edge_id"] == overlap_ids[0] and r["reviewer_id"] == "B")]
    next(r for r in completed if r["edge_id"] == overlap_ids[0]).update(
        decision="unverifiable", error_category="unverifiable", reason='Cannot verify "tên", source\nmissing')
    reviews = _write(tmp_path / "partial.csv", completed)
    strict = tmp_path / "strict.json"
    assert _score(config, reviews, strict) == 1 and not strict.exists()
    result_path = tmp_path / "partial.json"
    assert main(["score-edge-audit", "--input", str(GRAPH), "--config", str(config),
                 "--reviews", str(reviews), "--allow-partial", "--output", str(result_path)]) == 0
    result = json.loads(result_path.read_text())
    assert result["audit_completion"] == "partial"
    assert result["global"]["planned_total"] == 10 and result["global"]["total"] == 9
    assert result["global"]["unverifiable"] == 1
    assert result["global"]["precision"] == pytest.approx(8 / 9)
    assert result["completion"]["missing_assignment_count"] == 2
    assert result["completion"]["planned_assignments"] == summary["form_rows"]
    assert result["completion"]["overlap_completed"] == result["agreement"]["edges_reviewed_by_both"] == 3
    assert result["completion"]["overlap_planned"] == 4
    assert sum(x["global_reviewed"] for x in result["completion"]["relation_coverage"].values()) == 9
    assert any("nonresponse" in s for s in result["limitations"])


@pytest.mark.parametrize("mutation", ["duplicate", "foreign", "wrong_hash", "wrong_reviewer", "blank", "bad_csv", "naive_time"])
def test_partial_opt_in_keeps_invalid_reviews_fatal(tmp_path, mutation):
    config, _, _, rows = _prepare(tmp_path)
    completed = _complete(rows)
    solo = next(r for r in completed if r["is_overlap"] == "false")
    if mutation == "duplicate":
        completed.append(completed[0].copy())
    elif mutation == "foreign":
        completed[0]["edge_id"] = "edge:foreign"
    elif mutation == "wrong_hash":
        completed[0]["frame_sha256"] = "0" * 64
    elif mutation == "wrong_reviewer":
        solo["reviewer_id"] = "B" if solo["reviewer_id"] == "A" else "A"
    elif mutation == "blank":
        completed[0]["decision"] = ""
    elif mutation == "naive_time":
        completed[0]["reviewed_at"] = "2026-11-10T01:00:00"
    reviews = _write(tmp_path / "reviews.csv", completed)
    if mutation == "bad_csv":
        with reviews.open('a') as stream:
            stream.write('broken,row\n')
    output = tmp_path / "result.json"
    assert main(["score-edge-audit", "--input", str(GRAPH), "--config", str(config),
                 "--reviews", str(reviews), "--allow-partial", "--output", str(output)]) == 1
    assert not output.exists()


def test_partial_still_requires_adjudication_of_returned_conflicts(tmp_path):
    config, _, _, rows = _prepare(tmp_path)
    complete = _complete(rows)
    shared = next(r for r in complete if r["is_overlap"] == "true")
    shared.update(decision="incorrect", error_category="wrong_identity", reason="Conflict")
    # Partial because a different single-review edge is missing.
    solo = next(r for r in complete if r["is_overlap"] == "false")
    reviews = _write(tmp_path / "reviews.csv", [r for r in complete if r is not solo])
    output = tmp_path / "result.json"
    assert main(["score-edge-audit", "--input", str(GRAPH), "--config", str(config),
                 "--reviews", str(reviews), "--allow-partial", "--output", str(output)]) == 1
    assert not output.exists()
    adjudication = _write(tmp_path / "adjudicate.csv", [{
        **{k: shared[k] for k in ADJUDICATION_FIELDS if k in shared},
        "adjudicator_id": "A+B", "decision": "unverifiable", "reason": "Joint review unresolved",
        "reviewed_at": "2026-11-10T10:00:00+07:00",
    }], ADJUDICATION_FIELDS)
    assert main(["score-edge-audit", "--input", str(GRAPH), "--config", str(config),
                 "--reviews", str(reviews), "--allow-partial", "--adjudications", str(adjudication),
                 "--output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert result["agreement"]["agreed"] == 3
    assert result["global"]["unverifiable"] == 1


def test_multiple_exports_are_combined_as_csv_rows_by_cli(tmp_path):
    config, _, _, rows = _prepare(tmp_path)
    completed = _complete(rows)
    paths = [_write(tmp_path / f"{r}.csv", [x for x in completed if x["reviewer_id"] == r]) for r in ("A", "B")]
    output = tmp_path / "result.json"
    assert main(["score-edge-audit", "--input", str(GRAPH), "--config", str(config),
                 "--reviews", *map(str, paths), "--output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert result["audit_completion"] == "complete" and len(result["review_packets"]) == 2
