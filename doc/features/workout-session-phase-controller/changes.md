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
