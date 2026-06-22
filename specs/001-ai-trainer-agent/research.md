# Research: AI Live Trainer Agent

**Feature**: `001-ai-trainer-agent` | **Date**: 2026-06-20

## 1. Agent Orchestration Framework

**Decision**: LangGraph with four compiled subgraphs (Session, Set, VoiceOut, Rest) invoked from a top-level Session Graph.

**Rationale**:
- Existing POC (`backend/src/langchain-flow.py`) already uses LangGraph `StateGraph` for sample → VLM → observe/voice_out loop with proven structured VLM output via OpenRouter.
- LangGraph supports subgraph composition (`add_node` with compiled subgraph), conditional edges, and interrupt/resume—needed for emergency pause (FR-008, FR-009).
- Async voice consumption maps cleanly to a separate compiled graph fed by an in-process `asyncio.Queue`, keeping the set loop non-blocking (FR-024).

**Alternatives considered**:
- **Celery task chain**: Rejected—harder to express conditional rep-loop routing and in-session state merges; adds ops overhead without benefit at v1 scale.
- **Single monolithic LangGraph**: Rejected—voice-out would either block set loop or require manual threading; violates SC-007.
- **Custom asyncio state machine**: Rejected—reimplements LangGraph features; POC already on LangGraph.

---

## 2. VLM Provider and Pose Pipeline

**Decision**: OpenRouter (via `langchain-openai` `ChatOpenAI`) for VLM form analysis; MediaPipe for server-side pose derivation on each received frame; optional YOLO overlay data from client for display only (not rep counting).

**Rationale**:
- POC uses OpenRouter with structured `VLMFrameResult` output (action, rep_phase, rep_completed, severity, focus_issue).
- Spec requires pose before form analysis (FR-016) and rep count from VLM state only (FR-022)—MediaPipe on server satisfies preprocess without client-side rep heuristics.
- Existing `estimator/mediapipe.py` and YOLO pipeline can be reused for pose landmarks fed into VLM context JSON.

**Alternatives considered**:
- **Client-only pose + server rules engine**: Rejected—spec explicitly excludes pose-based rep heuristics for rep completion.
- **GPT-4o direct (no OpenRouter)**: Rejected—OpenRouter already configured in POC; supports model switching without code changes.
- **On-device VLM**: Rejected—entire agent graph must run server-side (FR-013).

---

## 3. Client–Server Transport

**Decision**: Socket.IO namespace `/trainer` on the same FastAPI/uvicorn process pattern as `yolo_fastapi_main.py`. Client sends `trainer:frame` events; server pushes `trainer:event` (voice cue, state update, emergency, session phase).

**Rationale**:
- Existing infrastructure: FastAPI + python-socketio + `StreamRegistry` pattern handles live frame ingest with backpressure (`YOLO_MAX_PENDING_FRAMES`).
- Mobile browsers need reliable reconnect; Socket.IO provides this out of the box.
- Binary frame payloads with metadata (seq, timestamp, dimensions) mirror proven `YoloFrameIncoming` shape.

**Alternatives considered**:
- **WebRTC data channel**: Rejected—higher implementation cost; frame rate is low (1 fps); Socket.IO sufficient.
- **REST polling for frames**: Rejected—inefficient for continuous streaming; poor mobile battery profile.
- **gRPC bidi stream**: Rejected—not used elsewhere in codebase; Socket.IO pattern already deployed.

---

## 4. Frame Buffer Strategy

**Decision**: Server-side per-session ring buffer (latest N frames, default N=3) in memory; set loop always processes the most recent frame. Stale frames discarded when client cadence exceeds server processing time.

**Rationale**:
- Spec: "process the latest frame received" (FR-015); "does not block set loop on client playback" (edge case).
- At 1 fps default, memory footprint is negligible (~3 JPEG frames).
- Matches edge case: camera stall → skip/retry without stale cues.

**Alternatives considered**:
- **Process every frame in order**: Rejected—creates backlog when VLM latency > frame interval; violates real-time coaching intent.
- **Redis frame store**: Rejected—unnecessary for v1 at 1 fps; in-memory per session is simpler (KISS).

---

## 5. Voice-Out Async Queue and Deduplication

**Decision**: In-process `asyncio.Queue` per active session, owned by the single trainer worker process. Set subgraph `put_nowait`s voice-out events; a background asyncio task (VoiceOut consumer) drains the queue. Deduplication state (`last_voiced_issue`, `repeat_count`) lives alongside the queue in session-scoped memory, persisted to MongoDB on each speak/skip.

**Rationale**:
- Spec requires independent consumption (FR-025) and non-blocking set loop (FR-024)—async queue + consumer task satisfies both without external infra.
- Matches existing deployment pattern: `yolo_fastapi_main.py` runs one uvicorn process with in-memory `StreamRegistry`.
- Voice events are ephemeral and low-volume at 1 fps; process restart ends the live session anyway, so cross-process durability adds little value for v1.
- Repeat threshold default 3 (FR-038) matches POC coaching chatter minimization in VLM system prompt.
- KISS / YAGNI: no Redis dependency for live coaching until scaling demands it.

**Alternatives considered**:
- **Redis list (`LPUSH`/`BRPOP`)**: Deferred—use when Set and VoiceOut run on separate workers or multiple uvicorn processes need shared queue access. Redis remains in the stack for async video jobs, not live trainer v1.
- **Coalesce in set loop**: Rejected—dedup logic belongs in VoiceOut subgraph per spec diagram.
- **Synchronous voice in set loop**: Rejected—blocks observation cycles (violates SC-007).

---

## 6. Voice Playback on Client

**Decision**: Client-side `VoicePlaybackQueue` using Web Speech API (`speechSynthesis`) for v1, with server-sent cue text. Queue appends new/threshold-met cues; skips duplicates below threshold per server decision (FR-031, FR-032).

**Rationale**:
- Server generates cue text; client owns playback timing—matches hybrid split.
- Queue semantics satisfy "play after current cue finishes without interrupting" (FR-032).
- No additional TTS service required for v1 (YAGNI).

**Alternatives considered**:
- **Server-side TTS stream**: Rejected—adds latency and audio streaming complexity; defer unless Web Speech quality insufficient.
- **Pre-recorded cue library**: Rejected—spec requires fresh cue generation (FR-027).

---

## 7. Session Persistence

**Decision**: MongoDB documents for coached sessions, extending existing session models in `app/src/lib/services/mongo.ts` / `backend/src/database/mongodb/`. Store merged observation state, coaching events, config, and status transitions.

**Rationale**:
- Gymbo already uses MongoDB for sessions, sets, and media metadata.
- Coached session entity from spec maps to an extension of existing session schema with `mode: "live_trainer"` discriminator.

**Alternatives considered**:
- **PostgreSQL**: Rejected—not current stack for session data.
- **Ephemeral-only sessions**: Rejected—overall feedback and coaching event log require persistence (FR-006, FR-027).

---

## 8. Safety Monitor

**Decision**: Two-tier safety: (1) set-level check after each observation cycle using VLM `severity: critical` or dedicated safety classifier node; (2) global monitor as a parallel LangGraph interrupt that sets session status to `paused`.

**Rationale**:
- Spec distinguishes set-level unsafe → emergency return (FR-021) vs global → pause all coaching (FR-008).
- VLM already outputs severity levels in POC `VLMFrameResult`.
- LangGraph `interrupt()` supports trainer resume/end (FR-009).

**Alternatives considered**:
- **Separate safety microservice**: Rejected—YAGNI; safety is a node + interrupt in existing graph.
- **Client-side safety only**: Rejected—server must enforce (FR-036).

---

## 9. Frontend Live Session UI

**Decision**: New route `app/sessions/[id]/live` with components in `app/src/lib/trainer/`. Reuse existing session API for config; new trainer WS client for runtime.

**Rationale**:
- Constitution requires SvelteKit + Tailwind + bun.
- Existing record flow (`record/+page.svelte`) handles post-hoc video upload—not live coaching; separate route avoids conflating UX.
- Pose overlay can reuse `app/src/lib/pose/` rendering while server drives coaching logic.

**Alternatives considered**:
- **Extend record page**: Rejected—different interaction model (live vs upload); would violate KISS for page complexity.
- **Streamlit frontend**: Rejected—constitution mandates SvelteKit.

---

## 10. Testing Strategy

**Decision**:
- **Unit**: Graph node functions with `--dry-run` mock VLM (existing POC pattern).
- **Integration**: Pre-recorded frame fixture sequences replayed through `/trainer` namespace; assert state JSON snapshots in `tmp/vlm-state/`.
- **E2E**: Manual smoke via quickstart.md with test video stream simulating client frame loop.

**Rationale**: POC already validates graph wiring with `--dry-run`. Frame fixtures from `backend/src/tmp/vlm-state/processed/` provide regression baselines.

**Alternatives considered**:
- **Live camera CI**: Rejected—flaky; use recorded fixtures instead.

---

## 11. Multi-Exercise Session Planning vs Single-Exercise Graph

**Decision**: The LangGraph agent (Session → Set → VoiceOut → Rest subgraphs) runs **one Coached Exercise Run at a time**, scoped to a single `SessionExercise` from the trainer's pre-planned Gymbo Session. Multi-exercise workouts are a **UX sequencing concern** outside the graph: complete one exercise run, then start the next.

**Rationale**:
- Camera setup, equipment, and viewing angle differ per movement—trainer repositions between exercises.
- Each exercise has its own sets, reps, and rest (`target_sets`, `target_reps`, `rest_seconds` on `SessionExercise`).
- Observation state, VLM context, and voice dedup reset naturally per exercise block.
- Matches existing Gymbo session model: `Session.exercises[]` already supports multi-exercise planning.
- KISS: one graph instance, one frame loop, one exercise type per run—no cross-exercise state in the agent.

**UX flow**:
1. Trainer plans session with multiple exercises (existing session UI).
2. For exercise 1: set up camera → start Coached Exercise Run → monitor until all sets/reps done → per-exercise feedback.
3. Reposition for exercise 2 → new run with that exercise's plan.
4. Repeat until all `SessionExercise` blocks complete → Gymbo Session marked complete.

**Alternatives considered**:
- **Single graph for entire multi-exercise session**: Rejected—camera teardown/reposition breaks continuous frame loop; VLM prompts and rep logic are exercise-specific; would conflate unrelated merged state.
- **Parallel graphs per exercise**: Rejected—one camera stream, one athlete; YAGNI.

---

## 12. Modular Layer Decomposition

**Decision**: Seven-layer module split documented in [modular-architecture.md](./modular-architecture.md): Presentation → Transport → Application → Orchestration (LangGraph) → Domain + Pipeline → Infrastructure.

**Rationale**:
- Constitution Principle VII (Modularize) and V (DRY): POC functions map to single modules; graphs stay thin.
- Domain layer (merger, dedup, safety, rep completion) unit-testable without LangGraph or network.
- Pipeline ports (`PosePort`, `VLMPort`, `CueGeneratorPort`) allow dry-run adapters for CI and offline dev.
- `RunContext` composition root isolates per-exercise-run state (frame buffer, voice queue, dedup).
- Exercise plugins decouple movement-specific prompts from graph structure.

**Alternatives considered**:
- **Monolithic `agent/` with fat graph nodes**: Rejected—untestable business logic embedded in LangGraph; duplicates POC patterns.
- **Microservices per subgraph**: Rejected—YAGNI; single process with in-memory queue sufficient for v1.
- **Separate npm/Python packages**: Rejected—premature; monorepo modules with import boundaries sufficient.

---

## Resolved Clarifications

All Technical Context items resolved. No remaining `NEEDS CLARIFICATION` flags.

| Topic | Resolution |
|-------|------------|
| Orchestrator runtime | Server-side LangGraph (FR-013) |
| Frame loop owner | Client at 1 fps default (FR-010–012) |
| Rep completion | VLM merged state only (FR-022) |
| Voice dedup threshold | Default 3 (FR-038) |
| Emergency stop behavior | Pause; trainer resume or end (FR-008) |
| Overlapping voice playback | Skip dupes; queue new/threshold-met (FR-031–032) |
| Multi-exercise session | Graph runs one exercise at a time; UX loops exercise runs within planned Gymbo Session |
| Module decomposition | Seven layers; see modular-architecture.md |
| Frame send gating (v1.1) | Client and server accept/send frames only when `status === active` |
| Status sync on register (v1.1) | `trainer:state` snapshot immediately after `trainer:register` |
| Mid-run status persistence (v1.1) | Python worker writes status/phase to Mongo on each transition |
| LangGraph migration (v1.2) | Replace `*Runner` asyncio loops with four compiled `StateGraph` subgraphs; `MemorySaver` for pause/resume |

---

## 14. LangGraph migration (iteration 3)

**Decision**: Replace imperative `SessionRunner`, `SetLoopRunner`, `RestRunner`, and `VoiceOutHandler` with four compiled LangGraph subgraphs. Top-level session graph invokes set and rest subgraphs as nodes; voice graph runs as a background drain loop on the existing `asyncio.Queue`.

**Rationale**:
- Original POC (`797df4d`) validated `StateGraph` for sample → VLM → observe/voice_out routing with structured output.
- Research §1 already chose LangGraph for subgraph composition, conditional edges, and `interrupt()` — first implementation diverged to custom asyncio loops for speed of delivery.
- Domain and pipeline modules are already graph-ready (pure functions + ports); only orchestration layer needs rewriting.
- LangGraph `interrupt()` + `MemorySaver` maps directly to emergency pause/resume (FR-008, FR-009) without manual `ctx.paused` polling in every loop.
- Cyclic set subgraph replaces `while True` + `asyncio.sleep` with explicit conditional edges — easier to test node-by-node and visualize.

**Graph compilation pattern**:

```python
# set_loop.py (sketch)
builder = StateGraph(TrainerGraphState)
builder.add_node("grab_frame", grab_frame)
# ... nodes delegate to domain/pipeline ...
builder.add_conditional_edges("safety_check", route_after_safety, {...})
builder.add_conditional_edges("check_reps_complete", route_reps, {"continue": "wait_cycle", "done": END})
set_graph = builder.compile()

# session.py — invoke subgraph as node
session_builder.add_node("run_set", set_graph)
```

**State split**:
- `TrainerGraphState` (TypedDict): checkpointable run progress — status, phase, set counters, merged observation dict, control flags.
- `RunContext`: non-checkpointable I/O — frame buffer, voice queue, socket sid, repeat state. Passed via `config["configurable"]["run_context"]`.

**Voice async pattern**:
- `emit_voice` node calls `ctx.enqueue_voice(event)` (side effect, non-blocking).
- Background task: `while event := await queue.get(): await voice_graph.ainvoke({"event": event, ...})`.
- Preserves FR-024/FR-025/SC-007 without embedding voice generation in set graph.

**Pause/resume**:
- `MemorySaver` checkpointer keyed by `thread_id=run_id`.
- Set-level or global emergency triggers `interrupt()` at next safe node (after `safety_check` or session decision node).
- `RunController.resume()` sends `Command(resume=True)` to continue from checkpoint.

**Alternatives considered**:
- **Keep custom runners, add LangGraph later**: Rejected — dual paths violate DRY; plan and spec already mandate LangGraph.
- **Single monolithic graph (POC style)**: Rejected — cannot model async voice + session/rest phases cleanly (research §1).
- **LangGraph `Send` for voice fan-out**: Rejected — overkill for single consumer queue at v1 scale.
- **Redis checkpointer**: Deferred — single worker; in-memory `MemorySaver` sufficient until multi-process.

**Testing**:
- Unit-test node wrappers with mock `RunContext` in configurable.
- Integration: `session_graph.ainvoke(..., {"configurable": {"dry_run": True}})` with fixture frames pushed to buffer.
- CLI: `langchain-flow.py` calls `build_session_graph().ainvoke()` instead of `SessionRunner.run()`.

---

## 13. Live transport lifecycle (iteration 2)

**Decision**: Gate client frame send and server frame accept to `status === active` only; emit `trainer:state` snapshot immediately after `trainer:register`; persist run status transitions from Python session graph to MongoDB.

**Rationale**:
- First implementation started session graph on `POST start` before WS connected; `publish_state` dropped events when `ctx.sid` was null — clients missed prepare→setup→active transitions.
- SvelteKit patched Mongo to `preparing` on start but worker did not persist later transitions — REST appeared stuck.
- Frames during prepare/setup filled buffer without set loop consuming them.

**Alternatives considered**:
- **Connect WS before start**: Correct ordering but requires API/UX reorder; deferred.
- **Periodic state heartbeat during prepare**: Extra complexity; register snapshot sufficient for v1.1.
- **Stop camera during prepare**: Worse UX for “frame your camera” prep message.
