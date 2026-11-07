"""Score frame-bound component labels without asserting reviewer independence."""

from collections import defaultdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

import yaml


METHOD_VERSION = "component-evaluation-v1"
COMPONENTS = {
    "researcher_resolution": "binary",
    "organization_resolution": "binary",
    "affiliation_triples": "set",
    "topic_labels": "set",
    "citation_targets": "citation",
}
TARGET_KEYS = {
    "researcher_resolution": "researcher_pairwise",
    "organization_resolution": "organization_resolution",
    "affiliation_triples": "affiliation_triples",
    "topic_labels": "topic_labels",
    "citation_targets": "citation_targets",
}


def _object(value, name: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _nonempty(value, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _read_json(path: Path, name: str) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"{name} is not valid UTF-8 JSON") from exc
    return _object(value, name), raw


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _parse_time(value, name: str) -> datetime:
    text = _nonempty(value, name)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 timestamp with a timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone offset")
    return parsed


def _validate_label(component: str, value, name: str):
    kind = COMPONENTS[component]
    if kind == "binary":
        if type(value) is not bool:
            raise ValueError(f"{name} must be boolean")
        return value
    if kind == "set":
        if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
            raise ValueError(f"{name} must be a list of nonempty strings")
        if len(value) != len(set(value)):
            raise ValueError(f"{name} must not contain duplicate labels")
        return sorted(value)
    if component == "citation_targets":
        value = _object(value, name)
        if type(value.get("is_reference")) is not bool:
            raise ValueError(f"{name}.is_reference must be boolean")
        target = value.get("core_target_id")
        if target is not None and (not isinstance(target, str) or not target.strip()):
            raise ValueError(f"{name}.core_target_id must be null or a nonempty string")
        if not value["is_reference"] and target is not None:
            raise ValueError(f"{name} cannot have a core target when is_reference is false")
        return {"is_reference": value["is_reference"], "core_target_id": target}
    raise ValueError(f"unsupported evaluation component: {component}")


def _validate_frame(frame: dict, is_synthetic: bool) -> tuple[dict[str, dict], dict]:
    if frame.get("schema_version") != "component-evaluation-frame-v1":
        raise ValueError("frame.schema_version must be component-evaluation-frame-v1")
    if frame.get("status") != "frozen":
        raise ValueError("component evaluation requires a frozen annotation frame")
    if type(frame.get("is_synthetic")) is not bool or frame["is_synthetic"] is not is_synthetic:
        raise ValueError("frame.is_synthetic must agree with the requested evaluation scope")
    role = frame.get("sample_role")
    if not isinstance(role, str) or role not in {"development", "test"}:
        raise ValueError("frame.sample_role must be development or test")
    _nonempty(frame.get("frame_id"), "frame.frame_id")
    if is_synthetic and (role != "development" or frame.get("purpose") != "synthetic_protocol_only"):
        raise ValueError("synthetic frames must be development-only and marked synthetic_protocol_only")
    units_value = frame.get("units")
    if not isinstance(units_value, list) or not units_value:
        raise ValueError("frame.units must be a nonempty list")
    units = {}
    for index, raw_unit in enumerate(units_value):
        unit = _object(raw_unit, f"frame.units[{index}]")
        unit_id = _nonempty(unit.get("unit_id"), f"frame.units[{index}].unit_id")
        component = unit.get("component")
        if not isinstance(component, str) or component not in COMPONENTS:
            raise ValueError(f"frame.units[{index}].component is unsupported")
        if unit_id in units:
            raise ValueError(f"frame.units has duplicate unit_id {unit_id!r}")
        stratum = unit.get("stratum")
        if not isinstance(stratum, dict):
            raise ValueError(f"frame.units[{index}].stratum must be an object")
        weight = unit.get("sampling_weight", 1.0)
        if type(weight) not in (int, float) or not math.isfinite(weight) or weight <= 0:
            raise ValueError(f"frame.units[{index}].sampling_weight must be positive and finite")
        units[unit_id] = {
            "unit_id": unit_id,
            "component": component,
            "stratum": stratum,
            "sampling_weight": float(weight),
            "metadata": unit,
        }
    missing_components = sorted(set(COMPONENTS) - {unit["component"] for unit in units.values()})
    if missing_components:
        raise ValueError("frame lacks component units: " + ", ".join(missing_components))
    coverage = _object(frame.get("coverage_frame"), "frame.coverage_frame")
    population_scope = coverage.get("population_scope")
    if not isinstance(population_scope, str) or population_scope not in {"development_sample", "eligible_release_core"}:
        raise ValueError("frame.coverage_frame.population_scope is invalid")
    papers_value = coverage.get("eligible_core_papers")
    positions_value = coverage.get("author_positions")
    if not isinstance(papers_value, list) or not isinstance(positions_value, list):
        raise ValueError("coverage_frame requires eligible_core_papers and author_positions lists")
    papers = {}
    for index, raw_paper in enumerate(papers_value):
        paper = _object(raw_paper, f"coverage_frame.eligible_core_papers[{index}]")
        paper_id = _nonempty(paper.get("paper_id"), f"coverage_frame.eligible_core_papers[{index}].paper_id")
        if paper_id in papers or type(paper.get("abstract_available")) is not bool:
            raise ValueError(f"coverage_frame has a duplicate paper ID or invalid abstract flag: {paper_id}")
        if not isinstance(paper.get("stratum"), dict):
            raise ValueError(f"coverage_frame paper {paper_id} requires a stratum object")
        papers[paper_id] = paper
    if not papers:
        raise ValueError("coverage_frame.eligible_core_papers must not be empty")
    positions = {}
    for index, raw_position in enumerate(positions_value):
        position = _object(raw_position, f"coverage_frame.author_positions[{index}]")
        position_id = _nonempty(position.get("position_id"), f"coverage_frame.author_positions[{index}].position_id")
        paper_id = position.get("paper_id")
        if position_id in positions or paper_id not in papers:
            raise ValueError(f"coverage_frame author position is duplicate or references an unknown paper: {position_id}")
        positions[position_id] = position
    universes = frame.get("label_universes", {})
    if not isinstance(universes, dict):
        raise ValueError("frame.label_universes must be an object")
    topics = universes.get("topic_labels")
    if not isinstance(topics, list) or not topics or any(not isinstance(item, str) or not item for item in topics):
        raise ValueError("frame.label_universes.topic_labels must list the complete frozen topic taxonomy")
    if len(topics) != len(set(topics)):
        raise ValueError("frame.label_universes.topic_labels contains duplicates")
    organizations = universes.get("organization_ids")
    if not isinstance(organizations, list) or any(not isinstance(item, str) or not item for item in organizations):
        raise ValueError("frame.label_universes.organization_ids must list canonical organization IDs")
    if len(organizations) != len(set(organizations)):
        raise ValueError("frame.label_universes.organization_ids contains duplicates")
    pairs = {"researcher_resolution": set(), "organization_resolution": set()}
    topic_papers, author_positions = set(), set()
    reference_ids = set()
    for unit_id, unit in units.items():
        metadata = unit["metadata"]
        component = unit["component"]
        if component in pairs:
            left = _nonempty(metadata.get("left_id"), f"frame unit {unit_id!r}.left_id")
            right = _nonempty(metadata.get("right_id"), f"frame unit {unit_id!r}.right_id")
            if left == right:
                raise ValueError(f"frame unit {unit_id!r} compares an item with itself")
            pair = tuple(sorted((left, right)))
            if pair in pairs[component]:
                raise ValueError(f"frame contains duplicate or reversed {component} pair {pair!r}")
            pairs[component].add(pair)
            pair_type = metadata.get("pair_type")
            if not isinstance(pair_type, str) or pair_type not in {"positive_link_opportunity", "common_name_negative", "other_negative"}:
                raise ValueError(f"frame unit {unit_id!r} requires a declared resolution pair_type")
        elif component == "affiliation_triples":
            position_id = _nonempty(metadata.get("author_position_id"), f"frame unit {unit_id!r}.author_position_id")
            if position_id not in positions or position_id in author_positions:
                raise ValueError(f"frame unit {unit_id!r} must uniquely identify a frozen author position")
            author_positions.add(position_id)
            if metadata.get("complete_label_set") is not True:
                raise ValueError(f"frame unit {unit_id!r} must declare a complete affiliation label set")
        elif component == "topic_labels":
            paper_id = _nonempty(metadata.get("paper_id"), f"frame unit {unit_id!r}.paper_id")
            if paper_id not in papers or paper_id in topic_papers:
                raise ValueError(f"frame unit {unit_id!r} must uniquely identify an eligible paper")
            topic_papers.add(paper_id)
            if metadata.get("complete_label_set") is not True:
                raise ValueError(f"frame unit {unit_id!r} must declare a complete topic label set")
        elif component == "citation_targets":
            source_id = _nonempty(metadata.get("source_paper_id"), f"frame unit {unit_id!r}.source_paper_id")
            reference_id = _nonempty(metadata.get("reference_id"), f"frame unit {unit_id!r}.reference_id")
            if source_id not in papers or reference_id in reference_ids:
                raise ValueError(f"frame unit {unit_id!r} has an unknown source paper or duplicate reference ID")
            reference_ids.add(reference_id)
    return units, {
        "coverage": coverage,
        "papers": papers,
        "positions": positions,
        "topics": set(topics),
        "organizations": set(organizations),
    }


def _validate_predictions(predictions: dict, units: dict[str, dict], frame_sha: str, config_sha: str) -> tuple[dict, dict]:
    if predictions.get("schema_version") != "component-predictions-v1":
        raise ValueError("predictions.schema_version must be component-predictions-v1")
    if predictions.get("frame_sha256") != frame_sha:
        raise ValueError("predictions.frame_sha256 does not match the frozen frame")
    if predictions.get("quality_config_sha256") != config_sha:
        raise ValueError("predictions.quality_config_sha256 does not match the quality config")
    _nonempty(predictions.get("method_version"), "predictions.method_version")
    _parse_time(predictions.get("generated_at"), "predictions.generated_at")
    values = _object(predictions.get("labels"), "predictions.labels")
    expected, actual = set(units), set(values)
    if expected != actual:
        raise ValueError(
            f"predictions.labels must match the frozen unit IDs (missing={len(expected-actual)}, extra={len(actual-expected)})"
        )
    checked = {}
    for unit_id, unit in units.items():
        value = values[unit_id]
        if value is None:
            checked[unit_id] = None
        else:
            checked[unit_id] = _validate_label(unit["component"], value, f"predictions.labels[{unit_id!r}]")
    coverage = _object(predictions.get("coverage"), "predictions.coverage")
    affiliation_ids = coverage.get("accepted_affiliation_position_ids")
    topic_ids = coverage.get("topic_covered_paper_ids")
    if not isinstance(affiliation_ids, list) or any(not isinstance(item, str) for item in affiliation_ids):
        raise ValueError("predictions.coverage.accepted_affiliation_position_ids must be a list of IDs")
    if not isinstance(topic_ids, list) or any(not isinstance(item, str) for item in topic_ids):
        raise ValueError("predictions.coverage.topic_covered_paper_ids must be a list of IDs")
    if len(affiliation_ids) != len(set(affiliation_ids)) or len(topic_ids) != len(set(topic_ids)):
        raise ValueError("prediction coverage ID lists must not contain duplicates")
    return checked, {
        "affiliation_positions": set(affiliation_ids),
        "topic_papers": set(topic_ids),
    }


def _validate_gold(
    gold: dict,
    units: dict[str, dict],
    frame_sha: str,
    predictions_sha: str,
    first_review_time: datetime,
) -> tuple[dict, list[str], int, list[dict]]:
    if gold.get("schema_version") != "component-gold-v1":
        raise ValueError("gold.schema_version must be component-gold-v1")
    if gold.get("frame_sha256") != frame_sha:
        raise ValueError("gold.frame_sha256 does not match the frozen frame")
    if gold.get("predictions_sha256") != predictions_sha:
        raise ValueError("gold.predictions_sha256 does not match the frozen predictions")
    reviewers = gold.get("reviewers")
    if not isinstance(reviewers, list) or len(reviewers) != 2:
        raise ValueError("gold requires exactly two independent reviewer packets")
    reviewer_ids = []
    labels_by_reviewer = []
    expected_ids = set(units)
    for index, reviewer in enumerate(reviewers):
        reviewer = _object(reviewer, f"gold.reviewers[{index}]")
        reviewer_id = _nonempty(reviewer.get("reviewer_id"), f"gold.reviewers[{index}].reviewer_id")
        reviewer_ids.append(reviewer_id)
        labels = _object(reviewer.get("labels"), f"gold.reviewers[{index}].labels")
        if set(labels) != expected_ids:
            raise ValueError(f"reviewer {reviewer_id!r} labels do not match the frozen unit IDs")
        checked = {}
        for unit_id, unit in units.items():
            label = _object(labels[unit_id], f"reviewer {reviewer_id!r} label {unit_id!r}")
            evidence = label.get("evidence_locators")
            if not isinstance(evidence, list) or not evidence or any(not isinstance(item, str) or not item.strip() for item in evidence):
                raise ValueError(f"reviewer {reviewer_id!r} label {unit_id!r} requires evidence locators")
            checked[unit_id] = _validate_label(
                unit["component"], label.get("value"), f"reviewer {reviewer_id!r} label {unit_id!r}"
            )
        labels_by_reviewer.append(checked)
    if len(set(reviewer_ids)) != 2:
        raise ValueError("gold reviewer IDs must be distinct")
    adjudications_value = gold.get("adjudications", [])
    if not isinstance(adjudications_value, list):
        raise ValueError("gold.adjudications must be a list")
    adjudications = {}
    adjudicator_ids = set()
    for index, raw in enumerate(adjudications_value):
        adjudication = _object(raw, f"gold.adjudications[{index}]")
        unit_id = _nonempty(adjudication.get("unit_id"), f"gold.adjudications[{index}].unit_id")
        if unit_id not in units or unit_id in adjudications:
            raise ValueError("adjudication IDs must refer to one frozen unit exactly once")
        adjudicator_id = _nonempty(adjudication.get("adjudicator_id"), f"gold.adjudications[{index}].adjudicator_id")
        if adjudicator_id in reviewer_ids:
            raise ValueError("the adjudicator must be distinct from both reviewers")
        adjudicator_ids.add(adjudicator_id)
        _nonempty(adjudication.get("reason"), f"gold.adjudications[{index}].reason")
        evidence = adjudication.get("evidence_locators")
        if not isinstance(evidence, list) or not evidence or any(not isinstance(item, str) or not item.strip() for item in evidence):
            raise ValueError(f"adjudication {unit_id!r} requires evidence locators")
        adjudications[unit_id] = _validate_label(
            units[unit_id]["component"], adjudication.get("value"), f"adjudication {unit_id!r}"
        )
    resolved = {}
    adjudicated_count = 0
    for unit_id in units:
        first, second = labels_by_reviewer[0][unit_id], labels_by_reviewer[1][unit_id]
        if first == second:
            if unit_id in adjudications:
                raise ValueError(f"agreed unit {unit_id!r} must not have an adjudication")
            resolved[unit_id] = first
        else:
            if unit_id not in adjudications:
                raise ValueError(f"disagreement for unit {unit_id!r} requires a reasoned adjudication")
            resolved[unit_id] = adjudications[unit_id]
            adjudicated_count += 1
    if adjudicated_count != len(adjudications):
        raise ValueError("gold contains an adjudication where reviewers agreed")
    if first_review_time <= _parse_time(gold.get("prediction_frozen_at"), "gold.prediction_frozen_at"):
        raise ValueError("gold must declare review began after predictions were frozen")
    return resolved, reviewer_ids, adjudicated_count, labels_by_reviewer


def _metric(tp: float, fp: float, fn: float) -> dict:
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1_denominator = 2 * tp + fp + fn
    f1 = 2 * tp / f1_denominator if f1_denominator else None
    return {
        "true_positive": round(tp, 8),
        "false_positive": round(fp, 8),
        "false_negative": round(fn, 8),
        "precision": round(precision, 8) if precision is not None else None,
        "recall": round(recall, 8) if recall is not None else None,
        "f1": round(f1, 8) if f1 is not None else None,
    }


def _score_rows(rows: list[tuple], component: str) -> dict:
    kind = COMPONENTS[component]
    abstentions = sum(predicted is None for _, predicted, _ in rows)
    if kind == "binary":
        unweighted = [
            (int(gold is True and predicted is True), int(gold is False and predicted is True),
             int(gold is True and predicted is not True))
            for gold, predicted, _ in rows
        ]
        weighted = [
            ((gold is True and predicted is True) * weight,
             (gold is False and predicted is True) * weight,
             (gold is True and predicted is not True) * weight)
            for gold, predicted, weight in rows
        ]
        result = {
            "unit_count": len(rows),
            "abstentions": abstentions,
            "sample": _metric(*(sum(value[i] for value in unweighted) for i in range(3))),
            "sampling_weighted": _metric(*(math.fsum(value[i] for value in weighted) for i in range(3))),
        }
        result["gold_positive_support"] = sum(gold is True for gold, _, _ in rows)
        return result
    if kind == "set":
        sample = [0.0, 0.0, 0.0]
        weighted = [0.0, 0.0, 0.0]
        for gold, predicted, weight in rows:
            gold_set = set(gold)
            predicted_set = set(predicted or [])
            counts = (len(gold_set & predicted_set), len(predicted_set - gold_set), len(gold_set - predicted_set))
            for index, count in enumerate(counts):
                sample[index] += count
                weighted[index] += count * weight
        result = {
            "unit_count": len(rows),
            "abstentions": abstentions,
            "sample": _metric(*sample),
            "sampling_weighted": _metric(*weighted),
            "gold_positive_support": int(sample[0] + sample[2]),
        }
        return result
    extraction_rows = []
    target_counts = [0.0, 0.0, 0.0]
    weighted_target_counts = [0.0, 0.0, 0.0]
    target_support = 0
    for gold, predicted, weight in rows:
        gold_reference = gold["is_reference"]
        predicted_reference = predicted is not None and predicted["is_reference"]
        extraction_rows.append((gold_reference, predicted_reference, weight))
        gold_target = gold["core_target_id"]
        predicted_target = predicted["core_target_id"] if predicted is not None else None
        tp = gold_target is not None and predicted_target == gold_target
        fp = predicted_target is not None and not tp
        fn = gold_target is not None and not tp
        target_support += int(gold_target is not None)
        target_counts[0] += int(tp)
        target_counts[1] += int(fp)
        target_counts[2] += int(fn)
        weighted_target_counts[0] += int(tp) * weight
        weighted_target_counts[1] += int(fp) * weight
        weighted_target_counts[2] += int(fn) * weight
    extraction = _score_rows(extraction_rows, "researcher_resolution")
    return {
        "unit_count": len(rows),
        "abstentions": abstentions,
        "reference_extraction": extraction,
        "core_target_resolution": {
            "unit_count": len(rows),
            "gold_positive_support": target_support,
            "sample": _metric(*target_counts),
            "sampling_weighted": _metric(*weighted_target_counts),
        },
    }


def _coverage_metrics(frame_parts: dict, prediction_coverage: dict, targets: dict) -> dict:
    coverage = frame_parts["coverage"]
    papers, positions = frame_parts["papers"], frame_parts["positions"]
    if not prediction_coverage["affiliation_positions"] <= set(positions):
        raise ValueError("accepted affiliation coverage contains IDs outside the frozen author-position frame")
    if not prediction_coverage["topic_papers"] <= set(papers):
        raise ValueError("topic coverage contains IDs outside the frozen eligible-paper frame")

    def rate(records, covered, target, group_key):
        numerator = len(covered)
        denominator = len(records)
        value = numerator / denominator if denominator else None
        by_stratum = defaultdict(lambda: [0, 0])
        for record_id, record in records.items():
            stratum = record.get("stratum")
            key = json.dumps(stratum, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            by_stratum[key][1] += 1
            by_stratum[key][0] += int(record_id in covered)
        return {
            "numerator": numerator,
            "denominator": denominator,
            "rate": round(value, 8) if value is not None else None,
            "target": target,
            "passed": value is not None and value >= target,
            "by_stratum": {
                key: {
                    "numerator": counts[0],
                    "denominator": counts[1],
                    "rate": round(counts[0] / counts[1], 8) if counts[1] else None,
                }
                for key, counts in sorted(by_stratum.items())
            },
        }

    abstract_ids = {paper_id for paper_id, paper in papers.items() if paper["abstract_available"]}
    position_records = {
        position_id: {**position, "stratum": papers[position["paper_id"]]["stratum"]}
        for position_id, position in positions.items()
    }
    return {
        "population_scope": coverage["population_scope"],
        "abstracts": rate(papers, abstract_ids, targets["abstracts"], "paper"),
        "author_paper_affiliation_resolution": rate(
            position_records, prediction_coverage["affiliation_positions"],
            targets["author_paper_affiliation_resolution"], "position",
        ),
        "papers_with_supported_topics": rate(
            papers, prediction_coverage["topic_papers"], targets["topics_on_eligible_papers"], "paper",
        ),
    }


def evaluate_components(
    frame_path: Path,
    predictions_path: Path,
    gold_path: Path,
    quality_config_path: Path,
    output_path: Path,
) -> tuple[dict, int]:
    """Score a frozen, double-reviewed component sample and report its limits."""
    protected = {path.resolve() for path in (frame_path, predictions_path, gold_path, quality_config_path)}
    if output_path.resolve() in protected:
        raise ValueError("evaluation output must differ from all input files")
    if output_path.exists() or output_path.is_symlink():
        raise ValueError("evaluation output already exists; use a new versioned path")
    frame, frame_raw = _read_json(frame_path, "frame")
    predictions, _ = _read_json(predictions_path, "predictions")
    gold, _ = _read_json(gold_path, "gold")
    quality_raw = quality_config_path.read_bytes()
    config = yaml.safe_load(quality_raw)
    if not isinstance(config, dict):
        raise ValueError("quality config must be a YAML object")
    targets = config.get("component_precision_targets")
    coverage_targets = config.get("coverage_targets")
    if not isinstance(targets, dict) or not isinstance(coverage_targets, dict):
        raise ValueError("quality config requires component_precision_targets and coverage_targets")
    for key in TARGET_KEYS.values():
        value = targets.get(key)
        if type(value) not in (int, float) or not 0 < value <= 1:
            raise ValueError(f"quality.component_precision_targets.{key} must be between 0 and 1")
    for key in ("abstracts", "author_paper_affiliation_resolution", "topics_on_eligible_papers"):
        value = coverage_targets.get(key)
        if type(value) not in (int, float) or not 0 < value <= 1:
            raise ValueError(f"quality.coverage_targets.{key} must be between 0 and 1")

    synthetic = frame.get("is_synthetic")
    if type(synthetic) is not bool:
        raise ValueError("frame.is_synthetic must be boolean")
    units, frame_parts = _validate_frame(frame, synthetic)
    frame_sha = _sha(frame_raw)
    config_sha = _sha(quality_raw)
    predictions_by_unit, prediction_coverage = _validate_predictions(predictions, units, frame_sha, config_sha)
    generated_at = _parse_time(predictions.get("generated_at"), "predictions.generated_at")
    if not synthetic:
        if frame.get("sample_role") != "test":
            raise ValueError("non-synthetic component evaluation requires a reserved test frame")
        if config.get("status") != "frozen":
            raise ValueError("non-synthetic component evaluation requires a frozen quality config")
        if frame_parts["coverage"].get("population_scope") != "eligible_release_core":
            raise ValueError("non-synthetic coverage evaluation requires the complete eligible release-core denominator")
    gold_by_unit, reviewer_ids, adjudicated, reviewer_labels = _validate_gold(
        gold,
        units,
        frame_sha,
        _sha(predictions_path.read_bytes()),
        _parse_time(gold.get("first_review_started_at"), "gold.first_review_started_at"),
    )
    for unit_id, unit in units.items():
        component = unit["component"]
        for source_name, labels in (("prediction", predictions_by_unit), ("gold", gold_by_unit)):
            value = labels[unit_id]
            if value is None:
                continue
            if component == "topic_labels" and not set(value) <= frame_parts["topics"]:
                raise ValueError(f"{source_name} for {unit_id!r} contains a topic outside the frozen taxonomy")
            if component == "affiliation_triples" and not set(value) <= frame_parts["organizations"]:
                raise ValueError(f"{source_name} for {unit_id!r} contains an organization outside the frozen frame")
            if component == "citation_targets" and value["core_target_id"] is not None and value["core_target_id"] not in frame_parts["papers"]:
                raise ValueError(f"{source_name} for {unit_id!r} targets a paper outside the eligible core frame")
    if _parse_time(gold.get("prediction_frozen_at"), "gold.prediction_frozen_at") != generated_at:
        raise ValueError("gold.prediction_frozen_at must match predictions.generated_at")

    grouped = defaultdict(lambda: defaultdict(list))
    grouped_by_pair_type = defaultdict(lambda: defaultdict(list))
    all_rows = defaultdict(list)
    review_agreement = defaultdict(lambda: {"agreed": 0, "disagreed": 0})
    for unit_id, unit in units.items():
        component = unit["component"]
        row = (gold_by_unit[unit_id], predictions_by_unit[unit_id], unit["sampling_weight"])
        all_rows[component].append(row)
        if reviewer_labels[0][unit_id] == reviewer_labels[1][unit_id]:
            review_agreement[component]["agreed"] += 1
        else:
            review_agreement[component]["disagreed"] += 1
        key = json.dumps(unit["stratum"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        grouped[component][key].append(row)
        if component in {"researcher_resolution", "organization_resolution"}:
            grouped_by_pair_type[component][unit["metadata"]["pair_type"]].append(row)
    component_results = {}
    threshold_checks = {}
    for component, rows in sorted(all_rows.items()):
        if component == "citation_targets":
            metrics = _score_rows(rows, component)
            precision = metrics["core_target_resolution"]["sampling_weighted"]["precision"]
        else:
            metrics = _score_rows(rows, component)
            precision = metrics["sampling_weighted"]["precision"]
        metrics["by_stratum"] = {
            stratum: _score_rows(stratum_rows, component)
            for stratum, stratum_rows in sorted(grouped[component].items())
        }
        if component in grouped_by_pair_type:
            metrics["by_pair_type"] = {
                pair_type: _score_rows(pair_rows, component)
                for pair_type, pair_rows in sorted(grouped_by_pair_type[component].items())
            }
        if component == "topic_labels":
            per_label_rows = defaultdict(list)
            for unit_id, unit in units.items():
                if unit["component"] != component:
                    continue
                gold_set = set(gold_by_unit[unit_id])
                predicted_value = predictions_by_unit[unit_id]
                predicted_set = set(predicted_value or [])
                for label in frame_parts["topics"]:
                    per_label_rows[label].append((
                        label in gold_set,
                        None if predicted_value is None else label in predicted_set,
                        unit["sampling_weight"],
                    ))
            per_label = {}
            macro_values = defaultdict(list)
            for label in sorted(frame_parts["topics"]):
                rows_for_label = per_label_rows[label]
                scored = _score_rows(rows_for_label, "researcher_resolution")
                gold_support = sum(gold is True for gold, _, _ in rows_for_label)
                predicted_support = sum(predicted is True for _, predicted, _ in rows_for_label)
                scored["gold_support"] = gold_support
                scored["predicted_support"] = predicted_support
                per_label[label] = scored
                if gold_support or predicted_support:
                    for metric in ("precision", "recall", "f1"):
                        value = scored["sampling_weighted"][metric]
                        macro_values[metric].append(0.0 if value is None else value)
            metrics["per_label"] = per_label
            metrics["macro_sampling_weighted"] = {
                metric: round(math.fsum(values) / len(values), 8) if values else None
                for metric, values in sorted(macro_values.items())
            }
        agreement = review_agreement[component]
        agreement_total = agreement["agreed"] + agreement["disagreed"]
        metrics["reviewer_agreement"] = {
            "agreed_units": agreement["agreed"],
            "disagreed_units": agreement["disagreed"],
            "exact_unit_agreement_fraction": (
                round(agreement["agreed"] / agreement_total, 8) if agreement_total else None
            ),
            "unit_count": agreement_total,
        }
        target_key = TARGET_KEYS[component]
        threshold_checks[component] = {
            "precision": precision,
            "target": targets[target_key],
            "passed": precision is not None and precision >= targets[target_key],
        }
        component_results[component] = metrics
    coverage_result = _coverage_metrics(frame_parts, prediction_coverage, coverage_targets)
    threshold_checks["coverage"] = {
        key: value["passed"] for key, value in coverage_result.items() if isinstance(value, dict)
    }
    quality_passed = all(
        check["passed"] if isinstance(check, dict) else bool(check)
        for check in threshold_checks.values()
    )
    status = "synthetic_protocol_only" if synthetic else ("component_metrics_pass" if quality_passed else "component_metrics_fail")
    result = {
        "status": status,
        "method_version": METHOD_VERSION,
        "release_status": "ineligible_synthetic" if synthetic else "not_certified",
        "is_synthetic": synthetic,
        "frame_id": frame.get("frame_id"),
        "sample_role": frame["sample_role"],
        "population_scope": frame_parts["coverage"]["population_scope"],
        "hashes": {
            "frame_sha256": frame_sha,
            "predictions_sha256": _sha(predictions_path.read_bytes()),
            "gold_sha256": _sha(gold_path.read_bytes()),
            "quality_config_sha256": config_sha,
        },
        "components": component_results,
        "coverage": coverage_result,
        "threshold_checks": threshold_checks,
        "review": {
            "reviewer_ids": reviewer_ids,
            "adjudicated_unit_count": adjudicated,
            "independence_status": "input_declared_unverified",
            "evidence_locators_status": "input_declared_unverified",
            "prediction_blinding_status": "timestamps_input_declared_not_independently_verified",
            "held_out_membership_status": "input_declared_not_verified" if not synthetic else "synthetic_protocol_only",
        },
        "limitations": [
            "Sampling-weighted metrics trust the frozen frame's supplied inverse inclusion weights.",
            "Reviewer identity, independence, blinding, source locators and label correctness are not software-verified.",
            "A non-synthetic test role is input-declared; held-out membership and cross-year leakage must be verified against the frozen split manifest separately.",
            "A passing component score does not pass the separate final edge audit or certify the release.",
            "Citation recall is bounded by the frozen candidate-reference frame supplied to this evaluator.",
            "Synthetic output validates the protocol only and cannot support a research claim.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return result, int(not synthetic and not quality_passed)
