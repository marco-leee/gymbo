# Feature: workout-session-phase-controller

> **Full design (architecture, interfaces, mermaid, integration):** [design.md](./design.md).  
> This folder: [doc/features](./). Cursor plan mirror: `session_phase_controller_23f77fbf` in `.cursor/plans/`.

## Summary

A **workout session phase layer** for the run screen: a **SessionPhaseController** that drives an ordered exercise list, classifies the user as exercising or resting (client **VLM in a Web Worker**, Transformers.js + Gemma 4 when wired, placeholder at first), and issues **`idle` / `analyse` + ExerciseRef** commands to a **LiveSessionAnalyser** that runs pose. The controller samples the webcam in the background at ~1s using a hidden internal canvas for VLM; the live analyser draws from the webcam only while pose analysis is commanded. Rep counting and UI phase come from a **per-exercise rep analyzer** (v1: `SquatRepAnalyzer` from today’s `AnalysisStateMachine` logic) with **hooks in the constructor** and a **`createExerciseRepAnalyzer` factory** aligned with the pose engine factory.

## Scope boundaries

- **In scope:** `SessionPhaseController`, `VlmWorkerClient` + `vlm.worker`, `LiveSessionAnalyser`, `IExerciseRepAnalyzer` / `SquatRepAnalyzer` + `createExerciseRepAnalyzer`, single-canvas / `BasePoseEngine` live refactor, wiring on [+page.svelte](../../../app-v2/src/routes/app-v2/sessions/%5Bid%5D/run/+page.svelte), `bun run check`.
- **Out of scope (v1):** Server-side VLM, full list auto-advance / auto-complete session (hooks only), VLM hysteresis, automatic `recordSet` on first “rest” without product rules (page/policy decides).

## Requirements

- [x] Session phase controller: ordered exercise input, VLM on configurable interval, background webcam capture canvas, progress hook stub, `AnalyserCommand` to live analyser, no imports of pose engines or YOLO. v1 run-page wiring currently drives it from the active live target exercise rather than full list auto-progress.
- [x] VLM runs in a dedicated Web Worker; main thread only schedules hidden webcam snapshots and message I/O; single-flight inference on client; `SessionPhaseController` now drives `VlmWorkerClient` from the run page.
- [x] **Unknown VLM label policy** documented and implemented: when `label === "unknown"`, leave `userExercising` unchanged.
- [x] Live analyser: `start` / `stop` / `applyCommand`; `getUserExercising` and `getSessionInProgress` from page; controller emits `idle` when VLM says not exercising and `analyse` when VLM says exercising, so pose inference pauses while the low-rate VLM webcam capture continues in the background.
- [x] `SquatRepAnalyzer` (replaces in-place VLM+pose merge in `AnalysisStateMachine` `tick`): gates `sessionInProgress` and `userExercising` only, **no `vlm` in `step`**; `ExerciseRepAnalyzerHooks` only via **constructor**; `readonly engine` from [SquatPoseEngine](../../../app-v2/src/lib/pose/squat-pose-engine.ts); factory extensible for future `push_up`.
- [x] Run page [+page.svelte](../../../app-v2/src/routes/app-v2/sessions/%5Bid%5D/run/+page.svelte) wires session exercise list/current live target, controller + live analyser lifecycle, and cleanup on destroy.

## Non-goals

- Replacing the entire session UX or set-recording product rules in one go.
- Running full Gemma in the main thread (worker-only for VLM).

## References

- [design.md](./design.md) — technical design
- [PRODUCT_SPEC.md](../../PRODUCT_SPEC.md)
- [PRINCIPLES.md](../../../PRINCIPLES.md) (agent development guide, feature folder)
- [ARCHITECTURE.md](../../../ARCHITECTURE.md)
- [session-flow.md](../session-flow.md)
