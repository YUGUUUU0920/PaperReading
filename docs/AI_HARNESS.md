# AI Harness

## Design Principles

- Ask models for explicit fields instead of free-form prose blobs.
- Keep output schemas stable so the UI can rely on predictable sections.
- Validate model output before storing it.
- Preserve deterministic fallbacks so the product still works without model output.

## Summary Contract

The summary pipeline expects these fields:

- `problem`
- `method`
- `findings`
- `scenarios`
- `verdict`
- `tags`

These fields are defined in `backend/app/ai/contracts.py` and parsed in `backend/app/ai/harness.py`.

## Execution Path

1. `PaperService` prepares paper metadata and tags.
2. `SummaryService` builds candidate tags and calls the harness.
3. `SummaryHarness` creates structured messages for the model.
4. The response is parsed as JSON and validated field by field.
5. If the model path fails, `SummaryService` produces a deterministic Chinese briefing.

## Editing Guidance

- Put new prompt instructions in `backend/app/ai/harness.py`, not in route handlers.
- If you add fields, update both the contract and the parser.
- Prefer concise Chinese tags that can be reused across list, detail, and recommendation modules.
