---
name: visual-iteration-report
description: Render a dated product iteration report into a readable HTML daily brief with SVG charts. Use when the user wants a prettier daily report, a printable brief, charted competitor summaries, or a more presentation-friendly artifact from reports/product-iterations.
---

# Visual Iteration Report

Use this skill in the Research Atlas / PaperReading repo when a dated markdown report already exists and the goal is to turn it into a polished brief.

## Source Of Truth

Read these first:

1. `docs/PRODUCT_ITERATION_HARNESS.md`
2. `reports/product-iterations/YYYY-MM-DD.md`
3. `scripts/render_iteration_report.py`

## Workflow

1. Ensure the dated markdown report is complete enough to render.
2. Run:
   `python3 scripts/render_iteration_report.py --date YYYY-MM-DD`
3. Inspect the generated files:
   - `reports/product-iterations/YYYY-MM-DD.html`
   - `reports/product-iterations/YYYY-MM-DD-heatmap.svg`
   - optionally `reports/product-iterations/YYYY-MM-DD-heatmap.png` when `sips` is available
4. If the report reads awkwardly, tighten the markdown source first and rerender.
5. Tell the user where to open the HTML brief and note that it can be printed to PDF from the browser.

## Design Rules

- Prefer one hero summary, one chart, and 3 to 4 compact sections.
- Keep the output printable.
- Use Chinese product-facing wording.
- Do not overdesign the page or turn it into a slide deck.

## Output Expectations

Deliver:

- one readable HTML brief
- one SVG chart
- optionally one PNG preview image
- the source markdown report kept in sync
