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
