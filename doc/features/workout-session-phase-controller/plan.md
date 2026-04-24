# Plan: workout-session-phase-controller

> **Full design details:** [design.md](./design.md) (source of truth in this repo).  
> Optional mirror: `.cursor/plans/session_phase_controller_23f77fbf.plan.md`. This file is the short **execution** checklist; keep it in sync with shipped work and `design.md`.

## Approach

- **Controller:** `SessionPhaseController` — list + `VlmWorkerClient` + `onAnalyserCommand` / `onUserExercisingChange`; `getCaptureContext` from the live analyser; **no** `BasePoseEngine` or YOLO.
- **Workers:** new `vlm.worker` (placeholder infer); existing YOLO path unchanged, called only from the live analyser.
- **Live analyser:** `LiveSessionAnalyser` — own shared canvas, `createExercisePoseEngine` + `createExerciseRepAnalyzer`, optional thin orchestration hooks; rep UI via **ctor hooks** on `SquatRepAnalyzer`.
- **Refactor** [BasePoseEngine.analyzeLiveVideo](../../../app-v2/src/lib/pose/base-pose-engine.ts) so a single `drawImage` per frame (e.g. `processLiveFrameAfterDraw` or external pre-draw) — analyser or shared frame source owns the draw.
- **Retire** monolithic [AnalysisStateMachine](../../../app-v2/src/lib/ml/analysis-state-machine.ts) after `SquatRepAnalyzer` and type aliases (e.g. `RepPhase`).

## Phased implementation and verification

Each phase should end green on **its** verification before stacking the next. Re-run `bun run check` in `app-v2` at least after Phases 2, 4, 5, and 6, or on every push.

---

### Phase 0 — Feature docs (optional bootstrap)

- **Implement:** [requirements.md](./requirements.md), [design.md](./design.md), this file, [log.md](./log.md), [changes.md](./changes.md), [README.md](./README.md).
- **Verify:** All links in `design.md` resolve; [requirements.md](./requirements.md) checkboxes still reflect “not done” for code work.

---

### Phase 1 — VLM Web Worker and client

- **Implement:** `app-v2/src/lib/workers/vlm.worker.ts` (placeholder: echo or fixed `VlmResult`), `VlmWorkerClient` in `app-v2/src/lib/ml/vlm-worker-client.ts`: `init`, `dispose`, `run(ImageBitmap)` with **transferable** bitmap, request ids, **single-flight** (ignore or coalesce if previous run in flight), message types for `error` / `ready`.
- **Verify:**
  - [ ] `bun run check` in `app-v2` passes.
  - [ ] From a one-off or unit-style script / dev route if needed: post a small bitmap, receive stub `VlmResult` in main thread, no uncaught errors.
  - [ ] Worker throws no DOM APIs; Vite builds the worker chunk without errors.
  - [ ] (Manual) In DevTools: heavy inference, when added later, is not on main thread (placeholder is trivial today).

---

### Phase 2 — Exercise rep analyzer (squat) and retire `AnalysisStateMachine` usage in live path

- **Implement:** `IExerciseRepAnalyzer`, `ExerciseRepAnalyzerHooks`, `RepGate`, `SquatRepAnalyzer` (logic migrated from [analysis-state-machine.ts](../../../app-v2/src/lib/ml/analysis-state-machine.ts): remove **VLM** from input; use `sessionInProgress` + `userExercising` in `step`). `createExerciseRepAnalyzer` mirroring the pose [factory](../../../app-v2/src/lib/pose/exercise-pose-engine-factory.ts). Export `SquatRepOutput` / `RepPhase` as needed. Keep or re-export a thin `AnalysisStateMachine` alias for imports until the run page is migrated.
- **Verify:**
  - [ ] `bun run check` passes.
  - [ ] With a **synthetic** `step` sequence in a test (if you add one) or manual log: `userExercising` false flips to idle-style phase and does not count reps; when true and valid angles, reps increment as before.
  - [ ] `SquatRepAnalyzer` constructor receives `SquatPoseEngine` ref; `chart` delegation to `engine.chartPointFromIteration` still works for callers that use it.

---

### Phase 3 — Base live loop: single `drawImage` and pose after draw

- **Implement:** Refactor [base-pose-engine.ts](../../../app-v2/src/lib/pose/base-pose-engine.ts) so live inference can use **`ctx` already filled** (e.g. `processLiveFrameAfterDraw` or `analyzeLiveVideo` with `preDraw: false` + `drawImage` only in one outer loop). The invariant is: **at most one** `drawImage(video, …)` per throttled frame on the model input canvas.
- **Verify:**
  - [ ] `bun run check` passes.
  - [ ] **Recorded** video analysis path (upload flow) still works if it used `analyzeVideo` (no regression).
  - [ ] (Manual) If the run page is still on the old call path: live chart still populates for squat; after Phase 4, re-verify with the new analyser.

---

### Phase 4 — `LiveSessionAnalyser`

- **Implement:** `LiveSessionAnalyser` module: `start` / `stop` / `applyCommand`, own capture canvas, call `createExercisePoseEngine` + `createExerciseRepAnalyzer` on `analyse` + `ExerciseRef`, drive rep `step` each frame, optional `orchestrationHooks` only for raw frame / errors; `createRepHooks` or equivalent from config; `resetForExerciseChange`.
- **Verify:**
  - [ ] `bun run check` passes.
  - [ ] (Manual) Temporary wiring (dev-only buttons or a minimal test route) can start/stop: when `analyse` + squat, `onOutput` from rep hooks fires; when `idle`, loop stops or does not run pose.
  - [ ] Gating: `getUserExercising` return value changes are reflected in rep output (mock getter in a test or manual log).

---

### Phase 5 — `SessionPhaseController`

- **Implement:** `SessionPhaseController` with exercise list, `VlmWorkerClient` on interval, `getCaptureContext`, `onAnalyserCommand`, `onUserExercisingChange` / `mapVlmToUserExercising`, `AbortSignal` cleanup, optional `onProgress` stub.
- **Verify:**
  - [ ] `bun run check` passes.
  - [ ] (Manual) With video + shared canvas: ~1s cadence to worker, `onVlmResult` or equivalent updates gating, `onAnalyserCommand` receives `idle` / `analyse` transitions according to a minimal v1 list rule.
  - [ ] Stopping the controller (abort) clears timers and disposes the VLM path without worker leaks in DevTools (best-effort check).

---

### Phase 6 — Run page integration and cleanup

- **Implement:** [+page.svelte](../../../app-v2/src/routes/app-v2/sessions/%5Bid%5D/run/+page.svelte): build `ExerciseRef[]`, plumb `userExercising` state, `SessionPhaseController` + `LiveSessionAnalyser` lifecycle, remove in-loop [ExerciseVlmPlaceholder](../../../app-v2/src/lib/ml/exercise-vlm-placeholder.ts) from the live rAF path, delete or narrow dead imports. **Unknown VLM label policy** applied (see [requirements.md](./requirements.md)). Remove `AnalysisStateMachine` from run page in favour of `SquatRepAnalyzer` via the live analyser.
- **Verify:**
  - [ ] `bun run check` passes.
  - [ ] (Manual) Start session, start camera, in-progress: scoreboard and live chart behaviour match expectations for squat; rest / idle from VLM policy does not spuriously reset reps (per your chosen unknown rule).
  - [ ] No duplicate `drawImage` from the same video element for the same frame for pose and VLM snapshot (one compositor, two consumers).
  - [ ] Teardown: navigate away, camera off, no runaway rAF, workers disposed.

---

### Phase 7 — Final product verification (end of feature slice)

- **Verify (full checklist):**
  - [ ] `bun run check` in `app-v2`.
  - [ ] [requirements.md](./requirements.md) checkboxes for implemented items are **checked**; document any deferred items in [changes.md](./changes.md) and [log.md](./log.md).
  - [ ] All design invariants in [design.md](./design.md) re-read: controller has no pose imports; VLM in worker; rep hooks via `SquatRepAnalyzer` constructor.

## Legacy: single list of work items (summary)

1. VLM worker + client  
2. Rep analyzer + factory + migrate from `AnalysisStateMachine`  
3. Base pose live draw refactor  
4. `LiveSessionAnalyser`  
5. `SessionPhaseController`  
6. Run page + cleanup  
7. Full verification

## Risks / notes

- Worker bundling for Transformers.js in Vite may need extra config when Gemma is added.
- List progress and `recordSet` behaviour stay product-defined; do not entangle in the rep analyzer’s constructor hooks only — page composes.
