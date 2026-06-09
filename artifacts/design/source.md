# Design Source Reference

## Artifact
`artifacts/dashboard/index.html` — Interactive dashboard for the Abandono Acadêmico Casa Grande project (Fase 4).

## DESIGN.md Used
`spec/design-direction.md` — Design Direction document specifying:
- Dark theme (#1a1a2e background, #00d2ff accent, #ff6b6b alerts)
- Data-first, ornament-second principle
- Interactive simulation as understanding tool
- Responsive layout with CSS grid/flexbox
- Sans-serif typography (system stack)

## Design Decisions
- **Palette:** #1a1a2e (bg), #16213e (cards), #0f3460 (accent surfaces), #00d2ff (positive), #ff6b6b (alerts), #ffd93d (warnings), #6bcb77 (ok)
- **Typography:** Segoe UI / system-ui fallback, no external font loading
- **Layout:** CSS Grid with responsive auto-fit, max-width 1280px container
- **Charts:** CSS-only histograms (no charting library), SVG ring for risk gauge
- **Simulation:** Vanilla JS logistic function with domain-calibrated coefficients
- **Interactivity:** range input sliders with real-time probability recalculation

## Model Data Sources
- Metrics: Accuracy=0.665, F1=0.152 (from ADR-001 / task spec)
- Feature importances: domain-informed estimates based on RandomForest baseline
- Coefficients: simplified logistic approximation for simulation (not the actual RF model)
- Target distribution: ~75% non-abandoned, ~25% SUSPENDED (from classification report)
