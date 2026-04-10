# Paper Reading Agent Guide

## Product Goal

Paper Reading is a public-facing AI research assistant for discovering, reading, and comparing top-conference papers.

## Source Of Truth

1. `README.md`
   Public product overview and deployment instructions.
2. `docs/ARCHITECTURE.md`
   System boundaries, request flow, and extension points.
3. `docs/AI_HARNESS.md`
   Summary contract, structured output rules, and fallback strategy.
4. `docs/DATA_SOURCES.md`
   Official conference sources and supported years.
5. `backend/app/ai/`
   AI harness contracts, prompt builders, and output validators.
6. `backend/app/services/`
   Product logic for search, enrichment, summaries, tags, and recommendations.
7. `frontend/src/`
   User-facing copy and interaction layer.

## Directory Map

- `backend/app/ai/`
  Structured AI contracts and harness logic. Keep prompts, schema validation, and rendering rules here.
- `backend/app/integrations/sources/`
  Official conference source adapters. Prefer structured metadata when a site exposes it.
- `backend/app/services/summary_service.py`
  Summary generation orchestration. Do not place raw prompt strings directly in route handlers.
- `backend/app/services/tag_service.py`
  Chinese tag taxonomy and deterministic tag generation.
- `backend/app/services/enrichment_service.py`
  External metadata enrichment such as citations and topic signals.
- `frontend/src/components/`
  Product copy should be user-facing only. Do not expose internal workflow promises, hidden constraints, or engineering shortcuts.

## Product Invariants

- User-facing copy must describe value, not internal implementation details.
- Every summary path should produce the same section structure.
- AI outputs should be validated before they are rendered.
- Paper tags must prefer clear Chinese concepts over raw source taxonomy.
- External enrichment should degrade gracefully when upstream APIs fail.

## AI Harness Rules

- Ask models for structured fields, not free-form blobs.
- Validate required sections before storing summaries.
- Keep a deterministic fallback so the product remains usable without model output.
- Preserve a small, explicit tag vocabulary so downstream UI remains stable.

## Safe Changes

- It is safe to add new tags, new official sources, and new recommendation signals if they remain optional and degrade gracefully.
- It is not safe to expose internal instructions or hidden product assumptions in the public UI.
