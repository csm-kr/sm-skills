# Alignment And Readability Evaluation Rubric

Use this reference after the first rendered PDF/contact sheet and before final delivery.
It is platform-neutral and applies to Codex and Claude. If a multi-agent/subagent
tool is available and the user allows agent review, run a dedicated visual-alignment
reviewer. If no agent tool is available, perform the same review manually and record
the result in the build notes.

## Evidence Baseline

Use these external readability baselines when choosing font sizes:

- NDRN accessibility guidance: body text minimum is 24 pt for PowerPoint.
- UD2024 presentation guidance: heading 1 minimum 32 pt, heading 2 minimum 28 pt,
  text minimum 24 pt.
- High Point University accessibility guidance: body text minimum 24 pt and headings
  minimum 32 pt.
- WCAG 2.2 target-size guidance: interactive or dot-like target elements should be at
  least 24 by 24 CSS px when they function as selectable/visually target-like items.

Deck rule derived from those sources:

- Title/H1: normally 48-72 pt.
- Section/H2: normally 36-52 pt, never below 32 pt.
- For large-room/projector or strict accessibility delivery: body and main bullets
  normally 24-30 pt, never below 24 pt.
- For normal 1280x720 reveal HTML decks: body and main bullets normally 28-30 CSS px,
  hard floor 26 CSS px, card body 24-26 CSS px. This is the user's aesthetic default
  because forcing all body text to 32px makes slides look heavy.
- Use 20-22 CSS px only for short supporting labels, never for primary reading text.
- Source notes/fine print: avoid when possible; if used, keep 11-14 pt and visually
  separate from primary content, or 15-16 CSS px in normal HTML decks.
- Korean text needs more air than English: line-height >= 1.45 for headings/labels and
  >= 1.5 for body text.

## Required Alignment Agent Pass

After first render:

1. Render a contact sheet and full-size PNGs for any visually dense slide.
2. Ask a dedicated reviewer agent to inspect only alignment, visibility, and polish.
3. Provide the agent with the contact sheet plus full-size PNGs of the cover, final
   slide, and any diagram/table/checklist slide.
4. Ask for findings in three sections only:
   - severity-ordered issues
   - rubric improvements
   - final recheck checklist
5. Do not let the reviewer edit files unless explicitly assigned a disjoint write scope.

If no agent is available, do the same pass manually and record:

```text
alignment-review-mode: manual
reviewed-artifacts: contact sheet, slide PNGs
result: pass/fail with issues fixed
```

## 100 Point Rubric

Failing any hard gate below requires another render before delivery.

### A. Readability And Scale - 25 pts

- 10 pts: H1/H2/body sizes meet the active delivery profile above.
- 5 pts: Korean body lines have enough line-height and do not feel cramped.
- 5 pts: source notes and labels are legible without competing with main content.
- 5 pts: no important text is visually smaller than nearby decorative numbers/icons.

Hard fail: body text below the active delivery profile floor, or any Korean body
paragraph looks cramped at full-slide view. Also fail if a normal HTML deck looks
visually heavy because ordinary body text was forced to 32px+ everywhere.

### B. Grid And Edge Alignment - 20 pts

- 5 pts: repeated headers, footers, and page numbers sit on the same coordinates.
- 5 pts: cards in the same row/column share matching x/y/width/height.
- 5 pts: left edges of related text blocks align to a visible grid.
- 5 pts: visual centers match the intended optical center, not only the mathematical
  center.

Hard fail: a row of bullets, dots, labels, or cards appears unintentionally staggered.

### C. Diagram And Marker Accuracy - 20 pts

- 8 pts: dots/pins/number badges sit exactly on their intended path or anchor point.
- 4 pts: labels belong to the nearest visual element by proximity and alignment.
- 4 pts: visual markers have consistent size, stroke, and internal centering.
- 4 pts: arrow/path/line endpoints visually land on the target, not beside it.

Hard fail: map pins, numbered steps, or checklist dots visibly miss their targets.

### D. Spacing, Collision, And Safe Area - 15 pts

- 5 pts: no text touches card borders, icons, dots, or neighboring text.
- 4 pts: bottom content clears the footer zone by at least 0.42 in in paged decks.
- 3 pts: card padding is large enough for Korean ascenders/descenders and line breaks.
- 3 pts: empty space feels intentional and balanced across the slide.

Hard fail: text baseline touches a border, dot, icon, or footer.

### E. Visual Rhythm And Polish - 10 pts

- 4 pts: contact sheet has clear layout variation without breaking the system.
- 3 pts: first and final slides feel intentionally related.
- 3 pts: color and contrast prioritize legibility over decoration.

### F. Delivery Evidence - 10 pts

- 3 pts: PDF page count is correct.
- 2 pts: every page is 16:9.
- 2 pts: contact sheet is generated and inspected.
- 2 pts: selected full-size pages are inspected after changes.
- 1 pt: build notes record the review mode and fixes.

## Rebuild Rule

When the alignment score is below 90/100, or any hard fail is found:

1. Fix layout in source HTML/CSS.
2. Regenerate HTML/PDF.
3. Regenerate contact sheet and selected page PNGs.
4. Run the alignment reviewer again or repeat manual review.
5. Deliver only after no hard fails remain.
