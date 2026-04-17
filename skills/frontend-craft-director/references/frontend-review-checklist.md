# Frontend Review Checklist

Use this as the final pass before shipping or when reviewing an existing UI.

## Hierarchy

- Is the primary action obvious within a few seconds?
- Is there one dominant headline or entry point?
- Are supporting signals visually subordinate to the main task?
- Are repeated card and panel patterns consistent?

## Density

- Can any toolbar, stat row, chip row, or section be removed?
- Is too much information visible before the user asks for it?
- Do multiple badges, pills, and labels compete for attention?

## Layout

- Does the page have a clear reading path?
- Are related controls grouped together?
- Is spacing consistent between equivalent elements?
- Does mobile avoid horizontal scroll and cramped tap targets?

## States

- Hover state
- Focus state
- Active/selected state
- Disabled state
- Loading state
- Empty state
- Error state

If any relevant state is missing, the UI is unfinished.

## Accessibility

- Visible keyboard focus
- Reasonable color contrast
- Labels for icon-only or ambiguous controls
- No information conveyed by color alone
- Motion remains usable with reduced-motion preferences

## Motion

- Does animation explain a change in state or hierarchy?
- Are durations short and consistent?
- Are transforms and opacity preferred over layout-shifting motion?
- Would the UI feel cleaner if one animation were removed?

## Performance-Sensitive Presentation

- Are large images necessary and properly constrained?
- Are heavy decorative effects used sparingly?
- Are above-the-fold sections doing too much work?
- Is there unnecessary visual churn on first load?

## Delivery Standard

Ship only when the UI feels:
- clearer
- calmer
- more intentional
- easier to scan
- easier to use on mobile
