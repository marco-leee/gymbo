# Decision log: workout-session-phase-controller

> Newest entries at the bottom.

| Date       | Decision | Rationale |
| ---------- | -------- | --------- |
| 2026-04-24 | Feature folder created from [doc/features/template](../template) with `requirements`, `plan`, `log`, `changes`. | Per [PRINCIPLES.md](../../../PRINCIPLES.md) agent dev guide. |
| 2026-04-24 | VLM in dedicated worker; `SessionPhaseController` does not import pose engines. | Decoupling and main-thread jank. |
| 2026-04-24 | `AnalysisStateMachine` refactored to `SquatRepAnalyzer` with ctor hooks and `createExerciseRepAnalyzer` for extensibility. | Not a generic lifecycle FSM; per-exercise rep reducers. |
| 2026-04-24 | Authored [design.md](./design.md) as canonical technical design in `doc/features`. | Single place for interfaces, data flow, and diagrams; `requirements` stays the checklist. |
| 2026-04-24 | [plan.md](./plan.md) drafted Phases 0–7 with per-phase verification. | Shippable slices; re-run `bun run check` after major phases. |
| 2026-04-24 | Switched Gemma 4 worker prompt generation to `apply_chat_template()` with image-first multimodal content. | The handwritten prompt omitted Gemma 4's required image placeholder tokens, causing `tokens: 0, features: 256` during inference. |
| 2026-04-24 | Extracted a post-draw live pose seam in `BasePoseEngine` and kept `analyzeLiveVideo()` as a compatibility wrapper. | Phase 3 needs a single `drawImage()` owner per throttled live frame while preserving the recorded upload path until `LiveSessionAnalyser` takes over in Phase 4. |
| 2026-04-24 | Fixed unrelated typecheck blockers in client/session API typing while verifying Phase 3. | `bun run check` was failing outside the pose slice, so the verification pass now points back to real Phase 3 regressions instead of stale import and typing errors. |
| 2026-04-24 | Implemented `LiveSessionAnalyser` with an owned capture canvas, `idle`/`analyse` command handling, and frame-by-frame rep gating tests. | Phase 4 now has the orchestration layer that Phase 5 can drive without re-embedding pose and rep logic in the run page. |
| 2026-04-24 | Implemented `SessionPhaseController` with tested VLM cadence, unknown-label gating, and abort disposal. | Phase 5 now exists as a standalone controller that only coordinates `VlmWorkerClient`, analyser commands, and page-level `userExercising` state. |
| 2026-04-24 | Wired the run page to `LiveSessionAnalyser` + `SessionPhaseController` for the current live target exercise instead of the legacy in-loop VLM/state-machine path. | Keeps timeline selection behavior intact for v1 while removing duplicate frame grabs and preserving the controller/analyser boundary. |
| 2026-04-25 | Moved VLM capture ownership into `SessionPhaseController` as a hidden, low-rate webcam canvas. | If VLM sampled the analyser canvas, then pausing pose would also stop fresh VLM frames; controller-owned capture lets VLM wake the analyser back up. |
| 2026-04-25 | Removed recorded-video upload from the run page. | The run experience is now webcam-only: VLM decides exercising/resting from live frames, and pose analysis follows the current exercise only when VLM emits `analyse`. |
