# Style Library Cheatsheet

This skill now has two layers:

- a curated Codex playbook for quick choices
- a vendored frontend design library adapted from `ui-ux-pro-max` for deeper search

Use the local query tool first:

```bash
python3 skills/frontend-craft-director/scripts/design_library.py recommend "AI research reading platform"
python3 skills/frontend-craft-director/scripts/design_library.py search "clean editorial dashboard" --domain style
python3 skills/frontend-craft-director/scripts/design_library.py search "accessible chart for trend over time" --domain chart
python3 skills/frontend-craft-director/scripts/design_library.py search "suspense waterfall" --domain react
python3 skills/frontend-craft-director/scripts/design_library.py search "form labels touch targets" --stack react
```

## Start Here

1. Use `recommend` when the product direction is fuzzy.
2. Use `style`, `color`, `typography`, `product`, and `landing` to make visual decisions.
3. Use `ux`, `react`, `web`, `chart`, `icons`, and `--stack` when implementing or reviewing code.

## High-Signal Domains

- `style` (`styles.csv`, 84 rows): visual languages, effects, compatibility, design-system variables
- `color` (`colors.csv`, 161 rows): semantic palettes by product type
- `typography` (`typography.csv`, 73 rows): heading/body pairings and font mood
- `product` (`products.csv`, 161 rows): product-type to style and landing recommendations
- `landing` (`landing.csv`, 34 rows): section order and CTA placement
- `ux` (`ux-guidelines.csv`, 99 rows): accessibility and interaction rules
- `chart` (`charts.csv`, 25 rows): chart selection and a11y fallbacks
- `react` (`react-performance.csv`, 44 rows): frontend performance rules
- `web` (`app-interface.csv`, 30 rows): implementation-level accessibility patterns

## Full Vendor Library

The full imported dataset lives under:

- `vendor/ui-ux-pro-max/data/`
- `vendor/ui-ux-pro-max/data/stacks/`

That includes the higher-volume tables too:

- `google-fonts.csv` for font discovery
- `icons.csv` for icon-system choices
- `ui-reasoning.csv` for product-type decision rules
- `design.csv` and `draft.csv` as raw source material

## Codex Adaptation Rules

- Treat the vendor data as a decision aid, not a mandate.
- Keep using local repo constraints and existing UI patterns as the final source of truth.
- Do not copy Claude-specific command flows or `.claude` packaging into product code.
- Prefer one clear direction over mixing multiple loud styles from the library.
