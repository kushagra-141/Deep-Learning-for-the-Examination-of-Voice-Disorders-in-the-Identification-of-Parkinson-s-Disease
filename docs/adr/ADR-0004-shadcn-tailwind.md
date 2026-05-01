# ADR-0004: shadcn/ui + Tailwind over MUI/Chakra

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

The frontend needs a component library for accessible, polished UI primitives (buttons, modals, tooltips, selects, sliders). The options are: a full-featured component library (MUI, Chakra UI), or a "copy-paste" approach with a design primitive layer.

## Decision

We will use **shadcn/ui** (built on Radix UI primitives + Tailwind CSS). Components are copied into `frontend/src/components/ui/` and owned by the project rather than imported from a package.

## Consequences

- **Good:** Full control over component code — no runtime CSS-in-JS overhead, no vendor lock-in.
- **Good:** Radix UI provides best-in-class accessibility (focus trapping, keyboard nav, screen reader announcements) out of the box.
- **Good:** Tailwind's tree-shaking eliminates unused styles in the production bundle.
- **Bad:** Components are copied into the repo; upstream updates are not automatic (must be pulled manually).
- **Risks:** Larger `src/components/ui/` directory to maintain.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| Material UI (MUI) | Runtime CSS-in-JS has a performance cost; difficult to customize tokens |
| Chakra UI | Runtime CSS-in-JS; Emotion dependency |
| Headless UI | Less comprehensive than Radix (missing several needed primitives) |

## References

- `00_MASTER_PLAN.md §0.6`
- `03_FRONTEND_LLD.md §Design System`
