# Feature: workout-session-phase-controller

> **Full design (architecture, interfaces, mermaid, integration):** [design.md](./design.md).  
> This folder: [doc/features](./). Cursor plan mirror: `session_phase_controller_23f77fbf` in `.cursor/plans/`.

## Summary

A **workout session phase layer** for the run screen: a **SessionPhaseController** that drives an ordered exercise list, classifies the user as exercising or resting (client **VLM in a Web Worker**, Transformers.js + Gemma 4 when wired, placeholder at first), and issues **`idle` / `analyse` + ExerciseRef** commands to a **LiveSessionAnalyser** that runs pose. **No duplicate `drawImage`** from the camera: one shared capture surface, pose at analysis FPS, VLM at ~1s. Rep counting and UI phase come from a **per-exercise rep analyzer** (v1: `SquatRepAnalyzer` from today’s `AnalysisStateMachine` logic) with **hooks in the constructor** and a **`createExerciseRepAnalyzer` factory** aligned with the pose engine factory.

## Scope boundaries

- **In scope:** `SessionPhaseController`, `VlmWorkerClient` + `vlm.worker`, `LiveSessionAnalyser`, `IExerciseRepAnalyzer` / `SquatRepAnalyzer` + `createExerciseRepAnalyzer`, single-canvas / `BasePoseEngine` live refactor, wiring on [+page.svelte](../../../app-v2/src/routes/app-v2/sessions/%5Bid%5D/run/+page.svelte), `bun run check`.
- **Out of scope (v1):** Server-side VLM, full list auto-advance / auto-complete session (hooks only), VLM hysteresis, automatic `recordSet` on first “rest” without product rules (page/policy decides).

## Requirements

- [ ] Session phase controller: ordered exercise list, VLM on configurable interval, progress hooks (policy TBD), `AnalyserCommand` to live analyser, no imports of pose engines or YOLO.
- [ ] VLM runs in a dedicated Web Worker; main thread only schedules snapshots and message I/O; single-flight inference on client; placeholder `VlmResult` until model wired.
- [ ] **Unknown VLM label policy** documented: e.g. do not flip `userExercising` on `unknown` (or explicit alternative).
- [ ] Live analyser: `start` / `stop` / `applyCommand`; `getUserExercising` and `getSessionInProgress` from page; one shared canvas: analyser does pose loop; controller samples same canvas for VLM; at most one `drawImage` from `<video>` per analysis frame.
- [x] `SquatRepAnalyzer` (replaces in-place VLM+pose merge in `AnalysisStateMachine` `tick`): gates `sessionInProgress` and `userExercising` only, **no `vlm` in `step`**; `ExerciseRepAnalyzerHooks` only via **constructor**; `readonly engine` from [SquatPoseEngine](../../../app-v2/src/lib/pose/squat-pose-engine.ts); factory extensible for future `push_up`.
- [ ] Run page [+page.svelte](../../../app-v2/src/routes/app-v2/sessions/%5Bid%5D/run/+page.svelte) wires session exercise list, controller + live analyser lifecycle, cleanup on destroy.

## Non-goals

- Replacing the entire session UX or set-recording product rules in one go.
- Running full Gemma in the main thread (worker-only for VLM).

## References

- [design.md](./design.md) — technical design
- [PRODUCT_SPEC.md](../../PRODUCT_SPEC.md)
- [PRINCIPLES.md](../../../PRINCIPLES.md) (agent development guide, feature folder)
- [ARCHITECTURE.md](../../../ARCHITECTURE.md)
- [session-flow.md](../session-flow.md)
