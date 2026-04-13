# Product Iteration Harness

## Goal

Run a repeatable daily improvement loop for the product:

1. scan competitor products
2. record concise findings
3. pick one bounded improvement
4. implement it if low-risk
5. run regression checks
6. report what changed

This harness exists so product iteration stays explicit, auditable, and small-batch.

## Inputs

- Current repository state
- Existing product invariants in `AGENTS.md`
- Public competitor product pages
- Open product gaps discovered during the scan

## Competitor Set

Prefer official product pages first. Start with:

- Semantic Scholar
- ResearchRabbit
- Litmaps
- Elicit
- SciSpace

You may replace or extend one source when a stronger direct competitor appears.

## Output Contract

Each run should create or update one report under `reports/product-iterations/YYYY-MM-DD.md`.

The report must stay short and include:

1. `Competitor signals`
   3 to 5 bullets, each tied to a named product.
2. `What we can adopt`
   1 to 3 concrete opportunities.
3. `What changed today`
   the bounded implementation, or `No safe code change today`.
4. `Regression`
   exact commands and whether they passed.
5. `Next candidate`
   the next best small improvement.

## Decision Rules

- Prefer one bounded product improvement per run.
- Do not ship broad refactors as part of the daily loop.
- Favor visible user value over internal polish.
- If a competitor idea conflicts with product invariants, note it and skip it.
- If no safe implementation is obvious, still complete the report and regression pass.

## Regression Gates

Before considering a run complete:

- run `python3 -m unittest discover -s tests -p 'test_*.py'`
- run `python3 -m compileall backend frontend tests`
- if frontend structure changed, do one lightweight runtime smoke check against a local server when practical

## Presentation Rules

- User-facing wording must stay product-first.
- Do not expose internal workflow promises in public UI copy.
- Reports should be concise and decision-oriented.

## Automation Notes

The daily automation should:

- prepare today's report file
- scan competitors
- write findings into the report
- apply at most one low-risk improvement
- run regression gates
- leave a short inbox summary with findings and modifications
