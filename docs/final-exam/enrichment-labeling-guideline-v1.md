# Enrichment reference-label guideline v1

Frozen on 2026-11-24 **before** any extractor or language model ran on a development
paper. It defines the AI-assessed reference labels for the 100 development papers
(`data/manifests/enrichment-splits-v1/development.jsonl`) used in the K1 model
comparison and in threshold tuning. Labels are written by the project agent
(Claude Sonnet 5.5, Claude Code), a different model family from every extractor and
language-model candidate. They are **AI-assessed, not human annotations**.

## What is labelled

The text is the paper title and abstract. Each label is a string that appears in
that text (case-insensitive, copied as written). Types:

- **Method** — a model, algorithm, architecture or technique that the paper
  proposes, uses or directly compares against. Named systems ("GraphMix", "PPO") and
  established generic techniques ("transformer", "graph neural network",
  "contrastive learning") both count. Not a method: bare generic words ("model",
  "approach", "framework", "method", "algorithm", "network", "technique"), metrics,
  losses stated only as a number, datasets, or the paper's own result.
- **Task** — a recognisable research problem the paper addresses
  ("image segmentation", "link prediction", "multi-agent path finding"). Not a
  task: whole fields ("machine learning", "artificial intelligence", "deep
  learning"), vague goals ("improve performance"), and application domains stated
  without a problem ("healthcare") unless a problem is named.
- **Dataset** — a named dataset, benchmark, corpus or standard environment suite
  used for training or evaluation ("ImageNet", "MuJoCo", "GLUE"). Not a dataset:
  generic phrases ("real-world datasets", "public benchmarks", "our dataset" without
  a name). A newly released dataset that the paper names counts.

Keep each entity once per paper (the longest natural surface form). Prefer the head
phrase with its modifiers ("offline reinforcement learning", not "reinforcement
learning" when the longer form is what the text says); do not label both.

## Relations

Only two relation types are labelled, both between labelled entities and supported by
a single sentence of the text:

- `APPLIED_TO` — Method → Task: the method is applied to, or proposed for, the task.
- `EVALUATED_ON` — Method or Task → Dataset: the method (or task) is evaluated or
  benchmarked on the dataset.

Paper-to-entity edges are not labelled separately: every labelled Method, Task and
Dataset is a mention, and a paper-level edge exists wherever a mention is verified.

## Matching rule used for scoring (fixed now)

Entity strings are normalised (lowercase, hyphens and punctuation to spaces, articles
dropped, trailing plural "s" removed on each token). A predicted entity matches a
reference entity of the same type when the normalised token sets have Jaccard
similarity ≥ 0.5, one-to-one, greedy by similarity. **Lenient F1 is the primary
figure** because boundary choices are subjective; strict F1 (identical normalised
strings) is reported next to it. A relation matches when both endpoints match
(lenient) and the relation type is equal.

## Limits

One labeller, no inter-annotator check; labels carry the labeller's errors and
boundary preferences, and the model comparison inherits them. They are reference
labels for choosing a model and tuning on development data, not gold labels.
