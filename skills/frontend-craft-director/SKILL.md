---
name: frontend-craft-director
description: Plan, build, review, and refine polished frontend interfaces with clear visual direction, strong information hierarchy, accessible interactions, responsive layouts, intentional motion, and data-backed style choices. Use when designing pages, cleaning up cluttered UIs, refactoring components, choosing tokens or typography, or reviewing frontend code for UX and visual quality.
---

# Frontend Craft Director

Use this skill when the task changes how an interface looks, feels, reads, or behaves.

This skill now includes:
- a curated Codex guide in [references/style-library-cheatsheet.md](references/style-library-cheatsheet.md)
- a vendored frontend design library in [vendor/ui-ux-pro-max/data](vendor/ui-ux-pro-max/data)
- a Codex-native query tool in [scripts/design_library.py](scripts/design_library.py)

The vendor data is adapted from `nextlevelbuilder/ui-ux-pro-max-skill` under MIT. Keep the workflow here Codex-native rather than copying Claude-specific packaging or command conventions.

This skill is for:
- new pages, dashboards, landing pages, flows, or component systems
- cluttered or visually noisy UIs that need stronger hierarchy
- frontend refactors where the structure is fine but the presentation is weak
- UI reviews covering usability, accessibility, responsiveness, and polish
- choosing or tightening color, typography, spacing, motion, and state patterns

This skill is not for:
- backend-only work
- API design without interface impact
- infra or build issues unrelated to user experience

## Core Principles

1. Start from the product task, not decoration.
2. Choose one visual direction and stay consistent.
3. Reduce before adding. Remove competing surfaces, labels, and controls first.
4. Make hierarchy obvious with layout, spacing, contrast, and type scale.
5. Treat interaction states as part of the design, not cleanup.
6. Motion should explain change, not simply add activity.
7. Accessibility and responsiveness are release criteria, not optional polish.
8. In an existing product, preserve the established system unless the user wants a redesign.

## Workflow

### 1. Read the Local Interface Context

Before editing, inspect the files that actually define the UI:
- page entrypoints
- component files
- CSS, Tailwind config, tokens, theme files
- layout wrappers, navigation, and shared primitives
- screenshots or rendered pages when available

Also determine:
- framework and styling approach
- whether the repo already has a design system
- whether the task is a refresh, cleanup, or net-new design

### 2. Diagnose the Experience

Summarize the real problem in concrete terms:
- too many competing sections
- weak CTA hierarchy
- cramped spacing
- unclear grouping
- inconsistent card treatments
- no visual rhythm
- poor mobile behavior
- missing hover, focus, loading, empty, or error states

If the UI feels “messy,” identify:
- what should be primary
- what can be secondary
- what can be removed entirely

### 3. Pick a Visual Direction

Read [references/visual-directions.md](references/visual-directions.md) and choose one direction that matches the product and audience.

When the direction is unclear, query the local style library first:

```bash
python3 skills/frontend-craft-director/scripts/design_library.py recommend "research reading platform"
python3 skills/frontend-craft-director/scripts/design_library.py search "clean editorial dashboard" --domain style
python3 skills/frontend-craft-director/scripts/design_library.py search "accessible table and form labels" --domain ux
python3 skills/frontend-craft-director/scripts/design_library.py search "suspense waterfall" --domain react
```

Use [references/style-library-cheatsheet.md](references/style-library-cheatsheet.md) to decide which domain to search.

Do not mix multiple strong aesthetics unless the user explicitly wants a high-contrast editorial or experimental treatment.

Once chosen, align:
- typography
- spacing density
- surface depth
- border radius
- color intensity
- motion style

### 4. Plan the Interface

For each page or component, decide:
- primary user task
- primary CTA
- section order
- what information is visible by default
- what becomes supporting metadata

Prefer:
- one dominant headline or entry point
- 2 to 4 key signals near the top
- consistent card and panel logic
- repeatable layout patterns over one-off visual tricks

### 5. Implement with Craft

While editing:
- prefer semantic tokens or existing variables over hardcoded values
- use one spacing scale consistently
- keep type sizes and weights purposeful
- make empty/loading/error/disabled states explicit
- ensure all clickable controls look clickable
- ensure keyboard focus is visible
- ensure mobile layouts work without horizontal scroll

When working in React or modern frontend stacks:
- follow existing component boundaries
- avoid adding unnecessary abstraction for simple presentational work
- preserve the repo’s established patterns unless the task is a redesign
- use `design_library.py search ... --stack <stack>` when stack-specific guidance is likely to matter

### 6. Review Against Quality Gates

Read [references/frontend-review-checklist.md](references/frontend-review-checklist.md) and verify:
- hierarchy
- density
- responsiveness
- interaction states
- accessibility
- motion
- performance-sensitive presentation choices

If asked for a review, prioritize findings that change behavior, clarity, or usability over stylistic preference.

## Decision Rules

- If the interface feels overcrowded, remove one whole layer of UI before refining details.
- If two elements both look primary, one of them is wrong.
- If copy is doing the work that layout should do, improve the layout.
- If every card looks special, none of them are special.
- If motion is noticeable before it is useful, reduce it.
- If mobile requires precision tapping or side-scrolling, the design is not ready.
- If the design system is weak, establish a small consistent token set before polishing components.

## Validation

Before finishing, check:
- desktop and mobile layouts both read cleanly
- primary CTA is unmistakable
- hover, focus, active, disabled, loading, and empty states exist where needed
- text contrast and focus visibility are acceptable
- animations are subtle and meaningful
- no obvious spacing or radius drift across similar components
- any style-library guidance used still fits the repo’s actual product and constraints

## Output Expectations

Good outcomes from this skill usually include:
- a clear visual direction
- fewer competing elements
- stronger information hierarchy
- cleaner responsive behavior
- more polished component states
- concise explanation of what changed and why
- when useful, a quick note about which local design-library domains informed the decision
