.PHONY: setup test schema validate services

setup:
	uv sync --locked --group dev

test:
	uv run pytest

schema:
	uv run research-network schema

validate:
	uv run research-network validate --input tests/fixtures/synthetic_graph.json --output reports/runs/synthetic-validation.json

services:
	docker compose up -d neo4j
