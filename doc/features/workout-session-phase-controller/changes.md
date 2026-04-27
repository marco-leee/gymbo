# Changes: workout-session-phase-controller

> Shipped code/doc changes for this feature. Update when you merge or release slices.

## 2026-04-24

- Added feature documentation scaffold: [requirements.md](./requirements.md), [plan.md](./plan.md), [log.md](./log.md), [changes.md](./changes.md).
- Added [design.md](./design.md): architecture, layer table, TypeScript contracts, mermaid diagrams, VLM worker sketch, `userExercising` gating, run page integration, out of scope. Linked from [requirements.md](./requirements.md) and [plan.md](./plan.md).
- Added [README.md](./README.md) index for this feature folder.
- Expanded [plan.md](./plan.md) with **Phase 0–7**: implementation focus and **per-phase verification** (checklists, `bun run check`, manual criteria).
- Completed **Phase 3** of the implementation plan: extracted a post-draw live pose seam in [base-pose-engine.ts](../../../app-v2/src/lib/pose/base-pose-engine.ts) so live inference can consume an already-populated canvas while `analyzeLiveVideo()` remains backward compatible.
- Added Phase 3 regression coverage in [pose.test.ts](../../../app-v2/src/lib/pose/pose.test.ts) for `processLiveFrameAfterDraw(...)` and re-ran the existing recorded sampling test.
- Cleared unrelated typecheck blockers encountered during Phase 3 verification in [clients.ts](../../../app-v2/src/lib/api/clients.ts), [+server.ts](../../../app-v2/src/routes/api/sessions/+server.ts), [app.d.ts](../../../app-v2/src/app.d.ts), and [+page.svelte](../../../app-v2/src/routes/app/clients/new/+page.svelte) so `bun run check` is green again.
- Phase 3 automated verification passed: `bun run check` returned 0 errors and `bun test src/lib/pose/pose.test.ts` passed. The manual `run` and `record` route checks were waived for this slice.
- Completed **Phase 4** of the implementation plan: added [live-session-analyser.ts](../../../app-v2/src/lib/ml/live-session-analyser.ts) with owned capture canvas, `idle` / `analyse` command handling, pose-engine + rep-analyzer orchestration, and `getCaptureContext()` for the upcoming controller slice.
- Exposed `analyzeLiveFrameAfterDraw(...)` publicly in [base-pose-engine.ts](../../../app-v2/src/lib/pose/base-pose-engine.ts) so the live analyser can own the single-draw loop while `analyzeLiveVideo()` stays backward compatible.
- Fixed `SquatRepAnalyzer` phase-change hook emission in [squat-rep-analyzer.ts](../../../app-v2/src/lib/ml/rep/squat-rep-analyzer.ts).
- Added Phase 4 automated coverage in [live-session-analyser.test.ts](../../../app-v2/src/lib/ml/live-session-analyser.test.ts), [squat-rep-analyzer.test.ts](../../../app-v2/src/lib/ml/rep/squat-rep-analyzer.test.ts), and extended [pose.test.ts](../../../app-v2/src/lib/pose/pose.test.ts).
- Phase 4 automated verification passed: `bun test src/lib/pose/pose.test.ts src/lib/ml/live-session-analyser.test.ts src/lib/ml/rep/squat-rep-analyzer.test.ts` passed, and `bun run check` returned 0 errors with existing non-blocking Svelte warnings outside this slice.
- Completed **Phase 5** of the implementation plan: added [session-phase-controller.ts](../../../app-v2/src/lib/ml/session-phase-controller.ts) with hidden background webcam capture for VLM, VLM-driven `idle` / `analyse` command emission, unknown-label no-op gating, `AbortSignal` cleanup, and worker disposal.
- Added focused Phase 5 coverage in [session-phase-controller.test.ts](../../../app-v2/src/lib/ml/session-phase-controller.test.ts) for initial idle state, webcam-owned VLM capture, VLM-driven command transitions, dropped-frame handling, and abort cleanup.
- Completed **Phase 6** of the implementation plan: rewired [+page.svelte](../../../app-v2/src/routes/app-v2/sessions/%5Bid%5D/run/+page.svelte) to use [live-session-analyser.ts](../../../app-v2/src/lib/ml/live-session-analyser.ts), [session-phase-controller.ts](../../../app-v2/src/lib/ml/session-phase-controller.ts), and [vlm-worker-client.ts](../../../app-v2/src/lib/ml/vlm-worker-client.ts) instead of [exercise-vlm-placeholder.ts](../../../app-v2/src/lib/ml/exercise-vlm-placeholder.ts) and [analysis-state-machine.ts](../../../app-v2/src/lib/ml/analysis-state-machine.ts) in the live camera loop.
- Updated [session-run-counting-board.svelte](../../../app-v2/src/routes/app-v2/sessions/%5Bid%5D/run/session-run-counting-board.svelte) to use `RepPhase`, keeping the UI on the rep-analyzer type instead of the deprecated state-machine alias.
- Phase 5/6 automated verification passed: `bun test src/lib/ml/session-phase-controller.test.ts`, `bun test src/lib/ml/live-session-analyser.test.ts`, and `bun run check` all passed. Remaining Svelte warnings are pre-existing and outside this feature slice.
- Manual browser verification for live camera cadence, worker teardown, and duplicate-frame checks is still pending.

## 2026-04-25

- Updated [session-phase-controller.ts](../../../app-v2/src/lib/ml/session-phase-controller.ts) so the controller owns the low-rate, non-rendered webcam capture canvas for VLM instead of sampling the live analyser canvas.
- Updated [+page.svelte](../../../app-v2/src/routes/app-v2/sessions/%5Bid%5D/run/+page.svelte) to be webcam-only: removed recorded-video upload state, upload handlers, hidden file input, duration preview video, saved video preview, and recorded set analysis chart from the run page.
- The live run flow now keeps VLM capture as a background process: VLM `not_exercising` emits `idle` and pauses pose inference; VLM `exercising` emits `analyse` for the current exercise and resumes pose analysis.
- Automated verification passed: `bun test src/lib/ml/session-phase-controller.test.ts src/lib/ml/live-session-analyser.test.ts` and `bun run check`. Remaining Svelte warnings are pre-existing and outside this slice.
