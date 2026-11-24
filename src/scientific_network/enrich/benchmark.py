"""QA benchmark question text (specification §6.6), frozen before any system output exists.

Questions are generated from fixed templates and slot values. Slots name v4 entities
(organizations, topics, venues, years) or well-known AI concepts. No v5 graph or model
output was consulted. If a named Method/Task/Dataset ends up without a node in
v5-enriched, that question is dropped and reported, never replaced. Reference answers
are computed later by deterministic Cypher (``reference_status: pending_v5``).
"""

from collections import Counter
import hashlib
import json
from pathlib import Path

BENCHMARK_VERSION = "qa-benchmark-v1"
PREDICATES = {
    "applied_to": "Method -APPLIED_TO-> Task",
    "evaluated_on": "Method|Task -EVALUATED_ON-> Dataset",
    "uses_method": "Paper -USES_METHOD-> Method",
    "addresses_task": "Paper -ADDRESSES_TASK-> Task",
    "uses_dataset": "Paper -USES_DATASET-> Dataset",
    "collab": "Organization -COLLABORATED_WITH- Organization",
    "authored": "Researcher -AUTHORED-> Paper",
    "affiliated": "Researcher -AFFILIATED_WITH-> Organization",
    "has_topic": "Paper -HAS_TOPIC-> Topic",
    "related": "Method|Task -RELATED_TO- Method|Task",
}

# (template_id, hops_class, traversals, intent, answer_type, judged, chain, text, slot_rows)
TEMPLATES = [
    # --- single hop -------------------------------------------------------
    ("T1a", "1", 1, "lookup", "set", "set_f1", ["applied_to"], "Which tasks is {method} applied to?",
     {"test": [("transformer",), ("graph neural network",), ("diffusion model",)],
      "development": [("convolutional neural network",)]}),
    ("T1b", "1", 1, "lookup", "set", "set_f1", ["evaluated_on"], "Which datasets is {method} evaluated on?",
     {"test": [("large language model",), ("contrastive learning",), ("graph convolutional network",)],
      "development": [("variational autoencoder",)]}),
    ("T1c", "1", 1, "count", "number", "exact", ["uses_method"], "How many papers in the corpus use {method}?",
     {"test": [("knowledge distillation",), ("generative adversarial network",), ("attention mechanism",)],
      "development": [("Q-learning",)]}),
    ("T1d", "1", 1, "count", "number", "exact", ["addresses_task"], "How many papers address {task}?",
     {"test": [("image classification",), ("object detection",), ("question answering",)],
      "development": [("text classification",)]}),
    ("T1e", "1", 1, "ranking", "ranked_list", "set_f1", ["collab"],
     "Which five organizations does {org} collaborate with most often, by number of joint papers?",
     {"test": [("Tsinghua University",), ("National University of Singapore",), ("University of Oxford",)],
      "development": [("Fudan University",)]}),
    ("T1f", "1", 1, "lookup", "set", "set_f1", ["evaluated_on"], "Which datasets are used to evaluate work on {task}?",
     {"test": [("node classification",), ("link prediction",)], "development": []}),
    ("T1g", "1", 1, "first_year", "year", "exact", ["uses_dataset"],
     "In which year did the first paper that uses {dataset} appear?",
     {"test": [("Cora",), ("Atari",)], "development": []}),
    ("T1h", "1", 1, "lookup", "set", "set_f1", ["related"], "Which methods are related to {method}?",
     {"test": [("proximal policy optimization",)], "development": []}),
    # --- two hops ---------------------------------------------------------
    ("T2a", "2", 2, "lookup", "set", "set_f1", ["uses_method", "uses_dataset"],
     "Which datasets are used in papers that apply {method}?",
     {"test": [("transformer",), ("diffusion model",), ("graph neural network",)],
      "development": [("BERT",)]}),
    ("T2b", "2", 2, "lookup", "set", "set_f1", ["addresses_task", "has_topic"],
     "Which topics do papers addressing {task} belong to?",
     {"test": [("machine translation",), ("image segmentation",), ("recommendation",)],
      "development": [("anomaly detection",)]}),
    ("T2c", "2", 2, "lookup", "set", "set_f1", ["evaluated_on", "applied_to"],
     "Which methods are applied to tasks that are evaluated on {dataset}?",
     {"test": [("ImageNet",), ("COCO",), ("GLUE",)], "development": [("CIFAR-100",)]}),
    ("T2d", "2", 2, "lookup", "set", "set_f1", ["collab", "collab"],
     "Which organizations collaborate with the collaborators of {org}, excluding {org} and its direct collaborators?",
     {"test": [("Zhejiang University",), ("Carnegie Mellon University",), ("Alibaba Group (China)",)],
      "development": [("Huawei Technologies (China)",)]}),
    ("T2e", "2", 2, "ranking", "ranked_list", "set_f1", ["uses_method", "authored"],
     "Which ten researchers authored the most papers that use {method}?",
     {"test": [("large language model",), ("contrastive learning",), ("proximal policy optimization",)],
      "development": [("prompt tuning",)]}),
    ("T2f", "2", 2, "lookup", "set", "set_f1", ["has_topic", "uses_dataset"],
     "Which datasets are used in {topic} papers published in {year}?",
     {"test": [("Computer vision", "2023"), ("Graph machine learning", "2024"),
               ("Natural language processing and language models", "2025")],
      "development": [("Robotics and embodied AI", "2022")]}),
    ("T2g", "2", 2, "ranking", "ranked_list", "set_f1", ["has_topic", "uses_method"],
     "Which five methods are used by the most {topic} papers?",
     {"test": [("Reinforcement learning",), ("Generative modeling",), ("Multimodal learning",)],
      "development": []}),
    ("T2h", "2", 2, "lookup", "set", "set_f1", ["uses_method", "addresses_task"],
     "Which tasks are addressed in {venue} {year} papers that use {method}?",
     {"test": [("IJCAI", "2023", "transformer"), ("AAAI", "2024", "graph neural network")],
      "development": []}),
    ("T2i", "2", 2, "ranking", "ranked_list", "set_f1", ["uses_dataset", "has_topic"],
     "Which three topics are most associated with papers that use {dataset}?",
     {"test": [("MNIST",), ("Atari",)], "development": []}),
    # --- three or more hops -----------------------------------------------
    ("T3a", "3", 3, "ranking", "ranked_list", "set_f1", ["uses_method", "authored", "affiliated"],
     "Which five organizations authored the most papers that use {method}?",
     {"test": [("transformer",), ("graph neural network",), ("diffusion model",), ("large language model",)],
      "development": [("convolutional neural network",)]}),
    ("T3b", "3", 3, "ranking", "ranked_list", "set_f1", ["addresses_task", "authored", "affiliated"],
     "Which five organizations published the most papers addressing {task} in {year}?",
     {"test": [("object detection", "2022"), ("node classification", "2023"),
               ("question answering", "2024"), ("sentiment analysis", "2021")],
      "development": [("summarization", "2023")]}),
    ("T3c", "3", 4, "lookup", "set", "set_f1", ["collab", "affiliated", "authored", "uses_method"],
     "Which organizations that collaborate with {org} also published papers that use {method}?",
     {"test": [("Tsinghua University", "transformer"), ("Microsoft (United States)", "large language model"),
               ("Google (United States)", "attention mechanism"),
               ("Massachusetts Institute of Technology", "generative adversarial network")],
      "development": [("Monash University", "Q-learning")]}),
    ("T3d", "3", 4, "lookup", "set", "set_f1", ["affiliated", "authored", "uses_method", "uses_dataset"],
     "Which datasets are used in papers from {org} that apply {method}?",
     {"test": [("Alibaba Group (China)", "transformer"), ("Tencent (China)", "graph neural network"),
               ("Peking University", "diffusion model")],
      "development": [("Fudan University", "variational autoencoder")]}),
    ("T3e", "3", 3, "lookup", "set", "set_f1", ["applied_to", "addresses_task", "uses_dataset"],
     "Which datasets are used in papers that address tasks to which {method} is applied?",
     {"test": [("transformer",), ("diffusion model",), ("graph neural network",),
               ("knowledge distillation",), ("contrastive learning",)],
      "development": [("BERT",)]}),
    # --- global and trend questions (no single reference answer) ----------
    ("G1", "global", None, "global_summary", "narrative", "pairwise_ai", ["community_reports"],
     "What were the main research directions in {year} across AAAI and IJCAI?",
     {"test": [("2021",), ("2022",), ("2023",), ("2024",), ("2025",)], "development": []}),
    ("G2", "global", None, "trend", "narrative", "pairwise_ai", ["trend"],
     "Which methods grew fastest as a share of each year's papers between 2021 and 2025?",
     {"test": [()], "development": []}),
    ("G3", "global", None, "trend", "narrative", "pairwise_ai", ["trend"],
     "Which tasks declined most as a share of each year's papers between 2021 and 2025?",
     {"test": [()], "development": []}),
    ("G4", "global", None, "trend", "narrative", "pairwise_ai", ["trend"],
     "Which datasets became more common between 2021 and 2025, and in which topics?",
     {"test": [()], "development": []}),
    ("G5", "global", None, "trend", "narrative", "pairwise_ai", ["trend", "collab"],
     "Which organizations moved into large language models after 2022, and who do they collaborate with?",
     {"test": [()], "development": []}),
    ("G6", "global", None, "global_summary", "narrative", "pairwise_ai", ["community_reports"],
     "Which research communities work on reinforcement learning, and who are their hubs and bridges?",
     {"test": [()], "development": []}),
    ("G7", "global", None, "comparison", "narrative", "pairwise_ai", ["trend"],
     "How do the method portfolios of AAAI and IJCAI papers differ?",
     {"test": [()], "development": []}),
    ("G8", "global", None, "trend", "narrative", "pairwise_ai", ["trend"],
     "Which topics are emerging in 2025 that were rare in 2021?",
     {"test": [()], "development": []}),
    ("G9", "global", None, "trend", "narrative", "pairwise_ai", ["trend", "evaluated_on"],
     "What datasets do the fastest-growing tasks of 2025 use, and which groups published on them first?",
     {"test": [()], "development": []}),
    ("G10", "global", None, "trend", "narrative", "pairwise_ai", ["trend", "collab"],
     "How has collaboration between organizations in China and the United States changed from 2021 to 2025?",
     {"test": [()], "development": []}),
    ("G11", "global", None, "global_summary", "narrative", "pairwise_ai", ["community_reports"],
     "Which communities of researchers connect multi-agent systems and reinforcement learning?",
     {"test": [()], "development": []}),
]
# Development-only global questions (templates reused with other wording).
DEVELOPMENT_GLOBAL = [
    ("G13", "What were the main research directions at IJCAI in 2022?", "global_summary"),
    ("G14", "Which topics gained the most papers between 2022 and 2024?", "trend"),
    ("G15", "Which organizations lead research on trustworthy machine learning, and who do they collaborate with?", "global_summary"),
    ("G16", "What methods characterize graph machine learning papers in 2023 compared with 2021?", "comparison"),
]
SLOT_NAMES = {"G1": ("year",), "T2h": ("venue", "year", "method"), "T2f": ("topic", "year"), "T3b": ("task", "year"),
              "T3c": ("org", "method"), "T3d": ("org", "method")}
DEFAULT_SLOT = {"T1a": "method", "T1b": "method", "T1c": "method", "T1d": "task", "T1e": "org", "T1f": "task",
                "T1g": "dataset", "T1h": "method", "T2a": "method", "T2b": "task", "T2c": "dataset", "T2d": "org",
                "T2e": "method", "T2g": "topic", "T2i": "dataset", "T3a": "method", "T3e": "method"}
SPLIT_COUNTS = {
    "test": {"1": 20, "2": 25, "3": 20, "global": 15},
    "development": {"1": 5, "2": 6, "3": 5, "global": 4},
}


def build_questions() -> list[dict]:
    questions: list[dict] = []
    counters = {"test": 0, "development": 0}

    def add(split, template_id, hops, traversals, intent, answer_type, judged, chain, text, slots):
        counters[split] += 1
        questions.append({
            "question_id": f"qa-v1-{'t' if split == 'test' else 'd'}{counters[split]:03d}",
            "split": split, "template_id": template_id, "hops": hops, "traversals": traversals,
            "intent": intent, "answer_type": answer_type, "judged": judged,
            "relation_chain": [PREDICATES.get(step, step) for step in chain],
            "text": text, "slots": slots, "reference_status": "pending_v5",
            "missing_entity_rule": "drop_and_report_never_replace",
        })

    for split in ("test", "development"):
        for template_id, hops, traversals, intent, answer_type, judged, chain, text, rows in TEMPLATES:
            names = SLOT_NAMES.get(template_id) or ((DEFAULT_SLOT[template_id],) if template_id in DEFAULT_SLOT else ())
            for values in rows[split]:
                slots = dict(zip(names, values))
                add(split, template_id, hops, traversals, intent, answer_type, judged, chain, text.format(**slots), slots)
    for template_id, text, intent in DEVELOPMENT_GLOBAL:
        add("development", template_id, "global", None, intent, "narrative", "pairwise_ai",
            ["trend" if intent == "trend" else "community_reports"], text, {})
    return questions


def validate_questions(questions: list[dict]) -> None:
    ids = [q["question_id"] for q in questions]
    texts = [q["text"] for q in questions]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate question_id")
    if len(set(texts)) != len(texts):
        raise ValueError("duplicate question text")
    for split, expected in SPLIT_COUNTS.items():
        got = Counter(q["hops"] for q in questions if q["split"] == split)
        if dict(got) != expected:
            raise ValueError(f"{split} hop counts {dict(got)} differ from {expected}")
    if any("{" in text or "}" in text for text in texts):
        raise ValueError("unfilled template slot")


def freeze_benchmark(output_dir: Path, *, source_files: list[Path] | None = None) -> dict:
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError(f"refusing to overwrite existing benchmark: {output_dir}")
    questions = build_questions()
    validate_questions(questions)
    output_dir.mkdir(parents=True)
    lines = [json.dumps(q, sort_keys=True, ensure_ascii=False) for q in questions]
    questions_path = output_dir / "questions.jsonl"
    questions_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    template_source = Path(__file__).read_bytes()
    receipt = {
        "benchmark_version": BENCHMARK_VERSION,
        "counts": {split: dict(sorted(Counter(str(q["hops"]) for q in questions if q["split"] == split).items()))
                   for split in SPLIT_COUNTS},
        "intents": dict(sorted(Counter(q["intent"] for q in questions if q["split"] == "test").items())),
        "questions_sha256": hashlib.sha256(questions_path.read_bytes()).hexdigest(),
        "generator_sha256": hashlib.sha256(template_source).hexdigest(),
        "reference_answers": "pending_v5; computed by deterministic Cypher after v5-enriched is loaded, "
                             "before any system is tuned or run on the test questions",
        "written_without": "any v5 graph, extraction output or language-model output",
        "slot_sources": "v4 organizations and topics; well-known AI concepts; entities absent from v5 are dropped and reported",
        "hop_definition": "hops is the minimum number of edge traversals the reference query needs: 1, 2, or 3 (three or more, "
                          "with the exact count in traversals); global questions have no traversal count",
        "judging": {"set_f1": "set F1 against the Cypher reference", "exact": "exact match",
                    "pairwise_ai": "global questions, pairwise judged by the AI evaluator, labelled AI-assessed"},
    }
    (output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt
