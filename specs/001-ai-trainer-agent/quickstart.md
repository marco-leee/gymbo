# Quickstart: AI Live Trainer Agent

**Feature**: `001-ai-trainer-agent` | **Branch**: `001-ai-trainer-agent`

## Prerequisites

- bun (frontend)
- uv + Python 3.12 (backend)
- MongoDB running (`just init` or docker compose)
- `OPENROUTER_API_KEY` in `backend/src/.env`

---

## 1. Backend: POC Graph (existing)

Validate LangGraph wiring without API calls:

```bash
cd backend
uv sync
uv run python src/langchain-flow.py --video src/test.mp4 --dry-run --state-dir src/tmp/vlm-state/test
```

Expected: JSON snapshots in `src/tmp/vlm-state/test/` for each graph step.

---

## 2. Backend: Live VLM on Video File

Full VLM pipeline against test video:

```bash
cd backend
uv run python src/langchain-flow.py --video src/test.mp4 --state-dir src/tmp/vlm-state/live
```

Requires `OPENROUTER_API_KEY` in `backend/src/.env`.

---

## 3. Backend: Trainer Agent (after implementation)

Start trainer ASGI server:

```bash
cd backend
uv run python src/trainer_fastapi_main.py
# Listens on YOLO_WS_PORT (default 10001)
```

Health check:

```bash
curl http://localhost:10001/health
```

---

## 4. Frontend: Live Session UI (after implementation)

```bash
cd app
bun install
bun run dev
```

Navigate to `/app/sessions/{id}/live` for an started coached session.

---

## 5. Smoke Test: Full Live Flow

### A. Start exercise run (REST)

```bash
curl -X POST http://localhost:5173/api/trainer/exercise-runs \
  -H "Content-Type: application/json" \
  -H "Cookie: <auth-cookie>" \
  -d '{
    "gymbo_session_id": "<session-uuid>",
    "session_exercise_id": "<exercise-uuid>"
  }'
```

Config (`target_sets`, `target_reps`, `rest_seconds`) is read from the planned `SessionExercise`. Use `config_overrides` only when needed.

### B. Start agent graph for this exercise

```bash
curl -X POST http://localhost:5173/api/trainer/exercise-runs/{run_id}/start \
  -H "Cookie: <auth-cookie>"
```

### C. Connect WebSocket (one exercise at a time)

Use browser devtools or a Socket.IO client:

1. Connect to `ws://localhost:10001/trainer`
2. Emit `trainer:register` with `run_id` and `session_exercise_id`
3. Emit `trainer:frame` at 1 fps from camera or test JPEG loop
4. Observe `trainer:state`, `trainer:voice_cue`, `trainer:phase_message` events
5. When exercise complete, `trainer:control` action `end` or wait for natural completion
6. Reposition camera → repeat B–C for next `SessionExercise` in the Gymbo Session

### D. Verify success criteria

| ID | Check |
|----|-------|
| SC-001 | Preparation message within 10s of start |
| SC-002 | Voice cue within 3s of voice-out event |
| SC-004 | Emergency stop halts observation within 2s |
| SC-006 | Repeated issues below threshold not spoken |
| SC-007 | Frame events continue while cue plays |

---

## 6. Integration Tests

```bash
cd backend
uv run pytest tests/integration/trainer/ -v
```

Tests use `--dry-run` graph mode and fixture frames from `src/tmp/vlm-state/processed/`.

---

## 7. Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENROUTER_API_KEY` | — | VLM API access |
| `OPENROUTER_MODEL` | nemotron free tier | VLM model |
| `MONGODB_URI` | from app env | Session persistence |
| `TRAINER_WS_PORT` | 10001 | Trainer Socket.IO port |
| `TRAINER_MAX_PENDING_FRAMES` | 4 | Frame backpressure |

---

## 8. Troubleshooting

| Symptom | Fix |
|---------|-----|
| No VLM response | Check `OPENROUTER_API_KEY`; try `--dry-run` first |
| Frames ignored | Confirm run status is `active`; check `trainer:register` ack |
| Voice cues spam | Verify `voice_repeat_threshold` in config (default 3) |
| Rep count stuck | Rep completion is VLM-only—check `rep_completed` in state JSON |
| Session stuck paused | Trainer must POST `/resume` or `/end` on the **exercise run** |

---

## Next Step

Run `/speckit-tasks` to generate implementation tasks from this plan.
