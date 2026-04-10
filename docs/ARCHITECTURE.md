# Architecture Map

## Goal

Paper Reading is a public-facing assistant for discovering, triaging, and reading top AI conference papers.

## Request Flow

1. `frontend/src/`
   Search, detail, and library pages render the product UI.
2. `backend/app/presentation/`
   HTTP routes expose bootstrap, search, paper detail, summarize, and library APIs.
3. `backend/app/services/`
   Search orchestration, source hydration, enrichment, tags, and summary generation.
4. `backend/app/integrations/sources/`
   Official conference adapters for ACL, NeurIPS, ICLR, and ICML.
5. `backend/app/repositories/sqlite.py`
   Stores papers, dataset status, summaries, and enrichment metadata.

## Core Modules

- `backend/app/services/paper_service.py`
  Entry point for search, detail, related papers, and serialization.
- `backend/app/services/summary_service.py`
  Summary orchestration with structured model output and deterministic fallback.
- `backend/app/services/enrichment_service.py`
  Citation, open access, and topic enrichment via external scholarly metadata.
- `backend/app/services/tag_service.py`
  Stable Chinese tag taxonomy for UI chips and recommendations.
- `backend/app/ai/`
  JSON contract for summaries and harness helpers for prompt building and validation.

## Product Boundaries

- User-facing copy should describe user value, not implementation shortcuts.
- External enrichment must be optional and cacheable.
- Official conference sources remain the primary paper corpus.
- The UI can display signals such as citations or code links, but should degrade gracefully if a source lacks them.
