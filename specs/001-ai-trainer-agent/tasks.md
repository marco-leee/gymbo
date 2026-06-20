# Tasks: AI Live Trainer Agent

**Input**: Design documents from `/specs/001-ai-trainer-agent/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, modular-architecture.md, quickstart.md

**Organization**: Tasks grouped by user story to enable independent implementation and testing. MVP = User Story 1 (Live Set Coaching).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1–US5) for story-phase tasks only

## Path Conventions

- Backend: `backend/src/`
- Frontend: `app/src/`
- Tests: `backend/tests/`
- Feature docs: `specs/001-ai-trainer-agent/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and module scaffolding

- [X] T001 Create backend agent module directory tree per modular-architecture.md in `backend/src/agent/` (app, domain, pipeline, graphs, exercises, infra)
- [X] T002 Add LangGraph, langchain-openai, and trainer agent dependencies to `backend/pyproject.toml` and run `uv sync`
- [X] T003 Create feature change log at `specs/001-ai-trainer-agent/log.md` per Constitution Principle IX (speckit path)
- [X] T004 [P] Create frontend trainer module directory `app/src/lib/trainer/` with barrel export `app/src/lib/trainer/index.ts`
- [X] T005 [P] Fix and verify trainer env vars in `specs/001-ai-trainer-agent/quickstart.md` section 7 (`TRAINER_WS_PORT`, `TRAINER_WORKER_URL`, `TRAINER_MAX_PENDING_FRAMES`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST complete before any user story work

**⚠️ CRITICAL**: No user story work until this phase is complete

- [X] T006 Create Pydantic domain models and migrate `VLMFrameResult` from `backend/src/langchain-flow.py` into `backend/src/agent/domain/models.py` (`MergedObservationState`, `VoiceOutEvent`, `ExerciseRunConfig`, `CoachedExerciseRun`)
- [X] T007 [P] Define pipeline port protocols (`PosePort`, `VLMPort`, `CueGeneratorPort`) in `backend/src/agent/pipeline/ports.py`
- [X] T008 [P] Implement OpenRouter LLM client factory in `backend/src/agent/infra/llm_factory.py`
- [X] T009 [P] Implement testable clock abstraction in `backend/src/agent/infra/clock.py`
- [X] T010 Implement MongoDB run repository for `coached_exercise_runs`, `coaching_events`, and `safety_events` in `backend/src/agent/infra/run_repository.py`
- [X] T011 [P] Add MongoDB collection constants and indexes for `coached_exercise_runs`, `coaching_events`, and `safety_events` in `backend/src/database/mongodb/collections.py`
- [X] T012 [P] Create Pydantic WS wire models for all `trainer:*` events in `backend/src/models/trainer_ws_protocol.py`
- [X] T013 Implement per-run composition root in `backend/src/agent/app/run_context.py` (frame buffer ref, voice queue, dedup state, graph task handles)
- [X] T014 Implement in-memory `RunRegistry` in `backend/src/agent/app/run_registry.py`
- [X] T015 Implement `RunEventPublisher` for `trainer:state`, `trainer:voice_cue`, `trainer:phase_message`, `trainer:emergency` in `backend/src/agent/app/event_publisher.py`
- [X] T016 Create graph factory skeleton with dry-run vs live adapter wiring in `backend/src/agent/graphs/factory.py`
- [X] T017 Create trainer ASGI entry point mounting Socket.IO and internal control routes in `backend/src/trainer_fastapi_main.py`
- [X] T018 [P] Create exercise profile registry in `backend/src/agent/exercises/registry.py`
- [X] T019 Implement Python internal control API (`POST /internal/runs/{run_id}/start|resume|end|pause`) delegating to `RunController` in `backend/src/trainer_api.py`
- [X] T020 [P] Implement SvelteKit server-side worker client calling `TRAINER_WORKER_URL` in `app/src/lib/server/trainer-worker.ts`

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 — Live Set Coaching (Priority: P1) 🎯 MVP

**Goal**: Per-frame observation loop—frame ingest, preprocess, pose, VLM analysis, state merge, rep completion—without blocking on voice playback

**Independent Test**: Run one set with live camera or fixture frames via `/trainer` WS. Verify frame buffer updates, observe-only merges, voice-out events emit when needed, rep completion from VLM state, set returns to orchestrator.

### Implementation for User Story 1

- [X] T021 [P] [US1] Implement ring frame buffer in `backend/src/agent/pipeline/frame_buffer.py`
- [X] T022 [P] [US1] Implement JPEG decode and frame preprocessor in `backend/src/agent/pipeline/preprocessor.py`
- [X] T023 [P] [US1] Implement rolling frame history for VLM context in `backend/src/agent/pipeline/frame_history.py`
- [X] T024 [P] [US1] Implement MediaPipe pose adapter wrapping `backend/src/estimator/mediapipe.py` in `backend/src/agent/pipeline/pose/mediapipe_adapter.py`
- [X] T025 [P] [US1] Implement dry-run pose adapter in `backend/src/agent/pipeline/pose/dry_run_adapter.py`
- [X] T026 [P] [US1] Migrate OpenRouter VLM adapter from `backend/src/langchain-flow.py` into `backend/src/agent/pipeline/vlm/openrouter_adapter.py`
- [X] T027 [P] [US1] Implement dry-run VLM adapter using fixtures from `backend/src/tmp/vlm-state/processed/` in `backend/src/agent/pipeline/vlm/dry_run_adapter.py`
- [X] T028 [US1] Implement observation merger (rep increment on `rep_completed`, issue tracking) in `backend/src/agent/domain/observation_merger.py`
- [X] T029 [US1] Implement rep completion policy in `backend/src/agent/domain/rep_completion.py`
- [X] T030 [US1] Implement set subgraph LangGraph in `backend/src/agent/graphs/set_loop.py` with pass-through `safety_check` stub (replaced in US3 T050); nodes: grab_frame → preprocess_pose → vlm_analyze → observe/emit_voice → safety_check → check_reps_complete
- [X] T031 [US1] Wire set subgraph into graph factory in `backend/src/agent/graphs/factory.py`
- [X] T032 [US1] Implement Socket.IO `/trainer` handlers for `trainer:register`, `trainer:frame`, `trainer:ping`, `trainer:unregister` (v1 WS auth via session cookie; no `ws_token` required) in `backend/src/trainer_socket_namespace.py`
- [X] T033 [US1] Connect frame ingest to `RunContext.frame_buffer` in `backend/src/trainer_socket_namespace.py`
- [X] T034 [US1] Implement minimal `RunController.start_set_loop()` to run set subgraph against active run in `backend/src/agent/app/run_controller.py`
- [X] T035 [US1] Emit `trainer:state` snapshots on observation cycles via `backend/src/agent/app/event_publisher.py`
- [X] T036 [P] [US1] Implement camera frame loop with configurable fps (default 1) in `app/src/lib/trainer/frame-loop.ts`
- [X] T037 [P] [US1] Implement Socket.IO trainer client (register, send frames, receive state) in `app/src/lib/trainer/trainer-client.ts`
- [X] T038 [US1] Handle empty frame buffer and stall edge cases in `backend/src/agent/graphs/set_loop.py` (skip cycle, no stale cues)

**Checkpoint**: User Story 1 independently testable via WS + frame loop or dry-run fixtures

---

## Phase 4: User Story 2 — Async Voice Coaching (Priority: P1)

**Goal**: Independent VoiceOut subgraph consumes events asynchronously with repeat-issue deduplication; set loop never waits for cue generation or playback

**Independent Test**: Trigger multiple voice-out events for the same issue during a set. Verify threshold dedup (default 3), new issues speak immediately, coaching events logged, set loop continues in parallel.

### Implementation for User Story 2

- [X] T039 [US2] Implement voice dedup policy in `backend/src/agent/domain/voice_dedup.py`
- [X] T040 [US2] Implement coaching cue generator port in `backend/src/agent/pipeline/cue_generator.py`
- [X] T041 [US2] Implement VoiceOut subgraph in `backend/src/agent/graphs/voice_out.py` (consume_event → dedup_check → generate_cue → log_coaching)
- [X] T042 [US2] Add voice-out `asyncio.Queue` consumer background task to `backend/src/agent/app/run_context.py`
- [X] T043 [US2] Wire set subgraph `emit_voice` node to `put_nowait` on voice queue in `backend/src/agent/graphs/set_loop.py`
- [X] T044 [US2] Implement bounded queue backpressure (maxsize 20, coalesce by focus_issue) in `backend/src/agent/app/run_context.py`
- [X] T045 [US2] Emit `trainer:voice_cue` events from VoiceOut subgraph via `backend/src/agent/app/event_publisher.py`
- [X] T046 [US2] Persist coaching events to MongoDB on speak in `backend/src/agent/infra/run_repository.py`
- [X] T047 [US2] Implement client voice playback queue with no-interrupt policy in `app/src/lib/trainer/voice-playback.ts`
- [X] T048 [US2] Integrate voice playback with trainer client events in `app/src/lib/trainer/trainer-client.ts`

**Checkpoint**: User Stories 1 and 2 work together; voice does not block set observation

---

## Phase 5: User Story 3 — Safety and Emergency Stop (Priority: P2)

**Goal**: Set-level unsafe checks and global safety monitor pause coaching; trainer can resume or end

**Independent Test**: Simulate unsafe VLM severity or global safety trigger during active set. Verify emergency halt within 2s, session paused, resume/end controls work.

### Implementation for User Story 3

- [X] T049 [US3] Implement set-level and global safety evaluator in `backend/src/agent/domain/safety_evaluator.py`
- [X] T050 [US3] Replace set subgraph pass-through stub with real safety check and emergency return in `backend/src/agent/graphs/set_loop.py`
- [X] T051 [US3] Implement global safety monitor interrupt in `backend/src/agent/app/run_controller.py`
- [X] T052 [US3] Implement `RunController.pause()`, `RunController.resume()`, and `RunController.end()` for emergency lifecycle in `backend/src/agent/app/run_controller.py`
- [X] T053 [US3] Handle `trainer:control` actions `resume`, `end`, `end_set`, `emergency_ack` in `backend/src/trainer_socket_namespace.py`
- [X] T054 [US3] Emit `trainer:emergency` events via `backend/src/agent/app/event_publisher.py`
- [X] T055 [US3] Persist safety events to MongoDB in `backend/src/agent/infra/run_repository.py`
- [X] T056 [US3] Pause frame processing when run status is `paused` in `backend/src/trainer_socket_namespace.py`
- [X] T057 [US3] Wire `trainer:unregister` to teardown `RunContext` and stop graph tasks in `backend/src/trainer_socket_namespace.py`

**Checkpoint**: Emergency stop pauses coaching; trainer resume/end restores or ends run

---

## Phase 6: User Story 4 — Rest Between Sets (Priority: P3)

**Goal**: Rest subgraph runs timer and during-rest activities between sets when more sets remain

**Independent Test**: Complete one set with rest configured, verify timer starts, during-rest messages sent, early end via `end_rest`, return to session orchestration (validated end-to-end after US5 session graph).

### Implementation for User Story 4

- [X] T058 [US4] Implement rest subgraph in `backend/src/agent/graphs/rest.py` (start_timer → during_rest_tick → check_timer_done)
- [X] T059 [US4] Wire rest timer to `infra/clock.py` in `backend/src/agent/graphs/rest.py`
- [X] T060 [US4] Emit during-rest `trainer:phase_message` events in `backend/src/agent/app/event_publisher.py`
- [X] T061 [US4] Handle `trainer:control` action `end_rest` in `backend/src/trainer_socket_namespace.py`

**Checkpoint**: Rest subgraph unit-testable; session-graph integration in US5 T063

---

## Phase 7: User Story 5 — Session Open and Close (Priority: P4)

**Goal**: Full Coached Exercise Run orchestration—prepare → setup → set loop with rest → per-exercise feedback → run complete; REST API and live UI for multi-exercise Gymbo Session flow

**Independent Test**: Run full single-exercise session (3 sets with rest) from REST create/start through WS to end. Verify prep within 10s, set announcements, overall feedback (SC-005 fields), session complete messaging. Multi-exercise: end run A, start run B for next `SessionExercise`.

### Implementation for User Story 5

- [X] T062 [P] [US5] Implement overhead squat exercise profile (VLM prompt, issue taxonomy, prep/setup copy) in `backend/src/agent/exercises/overhead_squat.py`
- [X] T063 [US5] Implement session graph in `backend/src/agent/graphs/session.py` including rest subgraph invocation (prepare → setup → announce_set → call set subgraph → decide_rest → call rest subgraph → decide_more_sets → exercise_feedback)
- [X] T064 [US5] Implement exercise feedback builder producing SC-005 fields (total reps, top recurring issues, one observed improvement, one next-session focus) in `backend/src/agent/domain/exercise_feedback.py`
- [X] T065 [US5] Complete `RunController` lifecycle (create, start, end, teardown) in `backend/src/agent/app/run_controller.py`
- [X] T066 [US5] Implement REST `POST /api/trainer/exercise-runs` in `app/src/routes/api/trainer/exercise-runs/+server.ts`
- [X] T067 [US5] Implement REST `GET /api/trainer/exercise-runs/[run_id]/+server.ts` in `app/src/routes/api/trainer/exercise-runs/[run_id]/+server.ts`
- [X] T068 [US5] Implement REST `POST /api/trainer/exercise-runs/[run_id]/start/+server.ts` proxying to Python `POST /internal/runs/{run_id}/start` in `app/src/routes/api/trainer/exercise-runs/[run_id]/start/+server.ts`
- [X] T069 [US5] Implement REST `PATCH /api/trainer/exercise-runs/[run_id]/config/+server.ts` in `app/src/routes/api/trainer/exercise-runs/[run_id]/config/+server.ts`
- [X] T070 [US5] Implement REST `POST /api/trainer/exercise-runs/[run_id]/resume/+server.ts` proxying to Python internal API in `app/src/routes/api/trainer/exercise-runs/[run_id]/resume/+server.ts`
- [X] T071 [US5] Implement REST `POST /api/trainer/exercise-runs/[run_id]/end/+server.ts` proxying to Python internal API in `app/src/routes/api/trainer/exercise-runs/[run_id]/end/+server.ts`
- [X] T072 [P] [US5] Implement REST `GET /api/trainer/exercise-runs/[run_id]/coaching-events/+server.ts` in `app/src/routes/api/trainer/exercise-runs/[run_id]/coaching-events/+server.ts`
- [X] T073 [P] [US5] Implement REST `GET /api/trainer/exercise-runs/[run_id]/safety-events/+server.ts` in `app/src/routes/api/trainer/exercise-runs/[run_id]/safety-events/+server.ts`
- [X] T074 [US5] Derive `ExerciseRunConfig` from `SessionExercise` and proxy graph lifecycle via `trainer-worker.ts` in `app/src/lib/server/trainer-runs.ts`
- [X] T075 [US5] Implement multi-exercise run flow (pick next exercise, start/end runs) in `app/src/lib/trainer/exercise-run-flow.ts`
- [X] T076 [US5] Implement live run UI state store in `app/src/lib/trainer/live-state.svelte.ts`
- [X] T077 [US5] Create live coaching page with TailwindCSS layout (camera, reps, phase, controls) at `app/src/routes/app/sessions/[id]/live/+page.svelte`
- [X] T078 [US5] Emit prepare/setup/set_announce/feedback/session_complete `trainer:phase_message` events from session graph via `backend/src/agent/app/event_publisher.py`
- [X] T079 [US5] Implement reconnect/disconnect UX (missed pong, WS drop, trainer notification) in `app/src/lib/trainer/trainer-client.ts` and `app/src/routes/app/sessions/[id]/live/+page.svelte`
- [X] T080 [US5] Refactor `backend/src/langchain-flow.py` into thin CLI calling `backend/src/agent/graphs/factory.py` for offline video dev

**Checkpoint**: Full single-exercise session and multi-exercise UX loop complete

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validation, integration tests, and documentation

- [X] T081 [P] Add integration test suite replaying fixture frames through `/trainer` in `backend/tests/integration/trainer/test_set_loop.py`
- [X] T082 [P] Add unit tests for voice dedup threshold behavior in `backend/tests/unit/agent/domain/test_voice_dedup.py`
- [X] T083 [P] Add unit tests for observation merger rep counting in `backend/tests/unit/agent/domain/test_observation_merger.py`
- [X] T084 [P] Add rep-count accuracy benchmark for SC-003 (fixture sets vs expected counts) in `backend/tests/integration/trainer/test_rep_accuracy.py`
- [X] T085 Run quickstart.md smoke test checklist (SC-001, SC-002, SC-003, SC-004, SC-005, SC-006, SC-007) and document results in `specs/001-ai-trainer-agent/log.md`
- [X] T086 [P] Append implementation milestones to `specs/001-ai-trainer-agent/log.md` per Constitution Principle IX

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depends on | Blocks |
|-------|------------|--------|
| Setup (1) | — | Foundational |
| Foundational (2) | Setup | All user stories |
| US1 (3) | Foundational (incl. T019–T020) | US2 |
| US2 (4) | US1 emit path | — |
| US3 (5) | US1 set loop (T030 stub → T050) | — |
| US4 (6) | US1 set complete | US5 T063 (rest wiring) |
| US5 (7) | US1–US4 subgraphs + T019–T020 | Polish |
| Polish (8) | Desired stories complete | — |

### User Story Dependencies

| Story | Priority | Depends on | Independently testable after |
|-------|----------|------------|------------------------------|
| US1 Live Set Coaching | P1 | Foundational | Phase 3 checkpoint |
| US2 Async Voice Coaching | P1 | US1 emit path | Phase 4 checkpoint |
| US3 Safety & Emergency | P2 | US1 set loop | Phase 5 checkpoint |
| US4 Rest Between Sets | P3 | US1 | Phase 6 checkpoint (subgraph only); full flow after US5 |
| US5 Session Open/Close | P4 | US1–US4 + control plane | Phase 7 checkpoint |

### Within Each User Story

- T019–T020 (control plane) before US5 REST start/resume/end proxies
- Pipeline adapters before graph nodes that call them
- Domain policies before graph nodes that invoke them
- T063 session graph after T058 rest subgraph exists

---

## Parallel Execution Examples

### Phase 2 (Foundational)

```bash
T007 pipeline/ports.py
T008 infra/llm_factory.py
T009 infra/clock.py
T012 models/trainer_ws_protocol.py
T018 exercises/registry.py
T020 app/src/lib/server/trainer-worker.ts
```

### Phase 3 (User Story 1)

```bash
T021 frame_buffer.py
T022 preprocessor.py
T024 pose/mediapipe_adapter.py
T026 vlm/openrouter_adapter.py
T036 frame-loop.ts
T037 trainer-client.ts
```

### Phase 7 (User Story 5)

```bash
T062 exercises/overhead_squat.py
T072 coaching-events/+server.ts
T073 safety-events/+server.ts
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**CRITICAL**, incl. T019–T020)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Dry-run set loop + WS frame ingest
5. Demo live set observation before voice polish

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → live set coaching (MVP)
3. US2 → spoken cues without blocking observation
4. US3 → safety pause/resume/end
5. US4 → rest subgraph
6. US5 → full session UX + REST proxies + live page
7. Polish → SC-003 benchmark + smoke tests

### Suggested MVP Scope

**User Story 1** (T001–T038): Core frame-based observation and rep tracking. Voice (US2) follows immediately after MVP validation.

---

## Task Summary

| Metric | Count |
|--------|-------|
| **Total tasks** | 86 |
| Setup | 5 |
| Foundational | 15 |
| US1 (P1) | 18 |
| US2 (P1) | 10 |
| US3 (P2) | 9 |
| US4 (P3) | 4 |
| US5 (P4) | 19 |
| Polish | 6 |

### Independent Test Criteria

| Story | How to verify |
|-------|---------------|
| US1 | One set via `/trainer` WS; frame pipeline, state merge, rep completion from VLM |
| US2 | Repeated voice-out events; dedup threshold 3; set loop unblocked |
| US3 | Unsafe trigger → pause within 2s; resume/end/end_set via WS + REST |
| US4 | Rest subgraph timer + `end_rest`; full loop after US5 |
| US5 | Full 3-set session via REST proxy → Python → WS; SC-005 feedback fields |

### Format Validation

All 86 tasks use checklist format: `- [X] T### [P?] [US?] Description with file path`
