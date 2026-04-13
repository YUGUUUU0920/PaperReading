---
name: research-product-iteration
description: Create concise competitor research, product iteration reports, and one bounded improvement for the Research Atlas paper-reading product. Use when the user asks for competitor analysis, recurring product iteration, daily improvement loops, or report-driven feature refinement for this repo.
---

# Research Product Iteration

Use this skill for the Research Atlas / PaperReading repo when the task is to:

- scan paper-reading or literature-discovery competitors
- summarize what is worth learning
- write a short dated iteration report
- choose at most one safe product improvement
- implement it and run regressions

## Source Of Truth

Read these first:

1. `AGENTS.md`
2. `docs/PRODUCT_ITERATION_HARNESS.md`
3. `docs/AI_HARNESS.md`
4. the latest file under `reports/product-iterations/`

Use `scripts/prepare_iteration_report.py --date YYYY-MM-DD` to seed the report file when needed.

For competitor pages and what to inspect on each, see [references/official-competitors.md](references/official-competitors.md).

## Workflow

1. Prepare context
   Read the harness docs and latest report so the next change stays incremental.
2. Scan competitors
   Prefer official product pages first. Extract 3 to 5 product signals, not a long market memo.
3. Write the dated report
   Follow the contract in `docs/PRODUCT_ITERATION_HARNESS.md`.
4. Pick one bounded change
   Favor visible user value over infrastructure polish. Skip implementation if no low-risk change is obvious.
5. Run regressions
   Always run:
   `python3 -m unittest discover -s tests -p 'test_*.py'`
   `python3 -m compileall backend frontend tests scripts`
   If frontend structure changed, do one lightweight local smoke check when practical.
6. Report back briefly
   Tell the user what competitors signaled, what changed, and what should be next.

## Decision Rules

- Keep the report concise and decision-oriented.
- Do not expose internal workflow promises in the public UI.
- Avoid broad refactors inside the daily loop.
- Prefer one user-facing improvement per run.
- If a competitor idea conflicts with repo invariants, record it and skip it.

## Output Expectations

Deliver:

- one short dated report in `reports/product-iterations/`
- at most one bounded code change
- regression results
- a concise summary for the user
