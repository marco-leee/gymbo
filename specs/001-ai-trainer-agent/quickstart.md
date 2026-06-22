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
# Listens on TRAINER_WS_PORT (default 10001)
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

## 6. Testing Guide

Copy-paste checklist for validating the AI Live Trainer Agent locally. Run layers **bottom-up**: automated tests → worker smoke → full E2E → live UI.

### Prerequisites

1. **MongoDB** running:

   ```bash
   just init
   # or: docker compose up -d
   ```

2. **Backend deps** synced once:

   ```bash
   cd backend && uv sync
   ```

3. **Env vars** (see section 7). Minimum for dry-run testing:

   | Variable | Where | Value |
   |----------|-------|-------|
   | `MONGODB_URI` or `MONGO_URI` | `backend/src/.env` | `mongodb://gymbo:gymbo@localhost:27017/gymbo?authSource=admin` |
   | `TRAINER_DRY_RUN` | shell when starting worker | `1` (no OpenRouter) |
   | `TRAINER_WORKER_URL` | `app/.env` (optional) | `http://localhost:10001` |
   | `VITE_TRAINER_WS_URL` | `app/.env` (optional) | `http://localhost:10001` |

   Live VLM additionally requires `OPENROUTER_API_KEY` in `backend/src/.env`.

4. **Auth session**: log in at `http://localhost:5173` as a trainer before REST or live-page tests.

### Three-terminal layout (E2E / UI)

| Terminal | Command | Purpose |
|----------|---------|---------|
| 1 | `just init` (once) | MongoDB |
| 2 | `cd backend && TRAINER_DRY_RUN=1 uv run python src/trainer_fastapi_main.py` | Trainer worker (WS + internal API) |
| 3 | `cd app && bun run dev` | SvelteKit REST proxy + live UI |

---

### 6.1 Unit tests (fast, no MongoDB)

Domain policy tests — voice dedup and rep merging:

```bash
cd backend
uv run pytest tests/unit/agent/domain/ -v
```

Expected: all tests pass (`test_voice_dedup.py`, `test_observation_merger.py`).

---

### 6.2 Integration tests (dry-run graph)

Set-loop and rep-accuracy benchmarks using in-process graph runners (no live WS):

```bash
cd backend
uv run pytest tests/integration/trainer/ -v
```

Expected: `test_set_loop.py`, `test_rep_accuracy.py` pass. Dry-run VLM uses fixtures from `backend/src/tmp/vlm-state/processed/` when present; otherwise deterministic mock phases.

Run a single file:

```bash
uv run pytest tests/integration/trainer/test_rep_accuracy.py -v
```

---

### 6.3 Offline session graph smoke (no API, no worker)

Validate LangGraph session orchestration in-process:

```bash
cd backend
uv run python src/langchain-flow.py --dry-run
```

Expected: stdout lines like `[trainer:phase_message]`, `[trainer:state]` as the graph walks prepare → setup → sets.

> **Note**: The legacy `--video` / `--state-dir` flags from early POC docs are deprecated. Live frames go through the WS worker; offline dev uses `--dry-run` above.

---

### 6.4 Trainer worker dry-run smoke (no OpenRouter)

**Start worker:**

```bash
cd backend
TRAINER_DRY_RUN=1 uv run python src/trainer_fastapi_main.py
```

**Health checks** (second terminal):

```bash
curl -s http://localhost:10001/health
# {"status":"ok"}

curl -s http://localhost:10001/stats
# {"active_runs":0}
```

Worker logs should show `dry_run=True` and listen on port `10001` (`TRAINER_WS_PORT`).

**Direct internal API** (after a run exists in MongoDB — see 6.6):

```bash
curl -X POST http://localhost:10001/internal/runs/{run_id}/start
curl -X POST http://localhost:10001/internal/runs/{run_id}/end
```

---

### 6.5 Trainer worker live VLM (optional)

Requires `OPENROUTER_API_KEY` in `backend/src/.env`. **Do not** set `TRAINER_DRY_RUN`.

```bash
cd backend
uv run python src/trainer_fastapi_main.py
```

Or offline video CLI with real VLM:

```bash
cd backend
uv run python src/langchain-flow.py
```

Verify OpenRouter connectivity before E2E; use dry-run (6.4) when iterating on WS/REST wiring.

---

### 6.6 Full E2E: REST → start → WebSocket → frames

Uses SvelteKit REST (MongoDB + auth) and Python worker (graph + WS). Matches production control plane.

#### Step 0 — Prepare session data

1. Start worker (6.4) and frontend (`cd app && bun run dev`).
2. Create a Gymbo session with at least one rep-based exercise (e.g. overhead squat) via `/app/sessions/new`.
3. Open the session detail page or `GET /api/sessions/{id}` and note:
   - `gymbo_session_id` → session `id`
   - `session_exercise_id` → first exercise `_id` (Mongo ObjectId string)
4. Copy auth cookie from browser DevTools → Application → Cookies (needed for `curl`).

#### Step 1 — Create exercise run (REST)

```bash
curl -s -X POST http://localhost:5173/api/trainer/exercise-runs \
  -H "Content-Type: application/json" \
  -H "Cookie: <paste-session-cookie>" \
  -d '{
    "gymbo_session_id": "<session-uuid>",
    "session_exercise_id": "<exercise-object-id>"
  }'
```

Expected `201`: `{ "run_id": "...", "status": "created", "ws_url": "/trainer", "config": { ... } }`.

Config defaults come from the planned `SessionExercise` (`target_sets`, `target_reps`, `rest_seconds`).

#### Step 2 — Start agent graph

```bash
curl -s -X POST http://localhost:5173/api/trainer/exercise-runs/{run_id}/start \
  -H "Cookie: <paste-session-cookie>"
```

Expected `200`: `{ "run_id": "...", "status": "preparing" }`. SvelteKit proxies to `POST /internal/runs/{run_id}/start` on the worker.

#### Step 3 — Connect WebSocket and send frames

Use the live page (6.7) or a Socket.IO client. Manual sequence:

1. Connect to `http://localhost:10001` namespace `/trainer` (Socket.IO, not raw WS).
2. Emit `trainer:register`:

   ```json
   {
     "run_id": "<run_id>",
     "gymbo_session_id": "<session-uuid>",
     "session_exercise_id": "<exercise-object-id>",
     "client_id": "<client-uuid>",
     "exercise_type": "overhead_squat",
     "camera_view": "LEFT"
   }
   ```

3. Receive `trainer:registered`, then `trainer:phase_message` (prepare/setup).
4. Emit `trainer:frame` at ~1 fps — base64 JPEG in `frame`, increment `meta.seq`:

   ```json
   {
     "meta": {
       "run_id": "<run_id>",
       "seq": 1,
       "timestamp_sec": 0.0,
       "dimensions": { "width": 640, "height": 480, "format": "jpeg" }
     },
     "frame": "<base64-jpeg>"
   }
   ```

5. Observe server events:
   - `trainer:state` — reps, phase, active issues
   - `trainer:voice_cue` — async coaching (dry-run emits on fixture cadence)
   - `trainer:phase_message` — set announce, rest, feedback
6. End run: emit `trainer:control` `{ "run_id": "...", "action": "end" }` or REST:

   ```bash
   curl -X POST http://localhost:5173/api/trainer/exercise-runs/{run_id}/end \
     -H "Cookie: <paste-session-cookie>"
   ```

#### Step 4 — Verify persisted logs (optional)

```bash
curl -s "http://localhost:5173/api/trainer/exercise-runs/{run_id}/coaching-events?limit=10" \
  -H "Cookie: <paste-session-cookie>"

curl -s "http://localhost:5173/api/trainer/exercise-runs/{run_id}/safety-events" \
  -H "Cookie: <paste-session-cookie>"
```

---

### 6.7 Frontend live page (manual)

Fastest path for full UX validation.

1. Start MongoDB, trainer worker (`TRAINER_DRY_RUN=1`), and `bun run dev`.
2. Log in as trainer.
3. Open `/app/sessions/{session_id}/live` for a session with planned exercises.
4. Click **Start live coaching**.
5. Allow camera permission when prompted.
6. Confirm UI updates:
   - **Connection** badge → `Live`
   - **Phase** → prepare → setup → set in progress
   - **Reps** increment during dry-run fixture cycles
   - **Phase message** text appears under stats
7. If emergency banner appears, test **Resume** and **End run**.
8. Click **End exercise**; confirm run ends cleanly (camera stops, no WS errors in console).

Optional: set `VITE_TRAINER_WS_URL=http://localhost:10001` in `app/.env` if the worker is not on localhost.

Multi-exercise: after ending exercise A, reposition camera and start again — flow advances to the next `SessionExercise`.

---

### 6.8 Success criteria checklist

Use during 6.6 or 6.7. Tick each item manually.

| ID | Criterion | How to verify |
|----|-----------|---------------|
| **SC-001** | Preparation/setup guidance within 10s of start | After `start`, first `trainer:phase_message` (prepare/setup) arrives ≤10s |
| **SC-002** | Voice cue within 3s of voice-out event | `trainer:voice_cue` appears ≤3s after state shows new issue (browser TTS or console log) |
| **SC-003** | Rep count accuracy ≥90% vs manual count | Automated: `test_rep_accuracy.py`. Manual: compare UI rep counter to your count over a full set |
| **SC-004** | Emergency stop halts observation within 2s | Trigger unsafe severity (live VLM) or simulate pause; frames ignored, status `paused` ≤2s |
| **SC-005** | End feedback includes reps, top issues, improvement, next focus | After `end`, check `exercise_feedback` in GET run response or final `trainer:phase_message` |
| **SC-006** | Repeated issues below threshold (default 3) not spoken | Same issue 1–2 times → no cue; 3rd → `trainer:voice_cue` with `trigger: repeat_threshold` |
| **SC-007** | Frame processing continues during voice playback | While cue plays, `trainer:state` still updates; rep counter keeps moving |

Section 5 above is a shorter smoke-test summary of the same flow.

---

### 6.9 Active-only frames and status sync (iteration 2)

Verify transport lifecycle fixes (plan.md § Iteration 2):

1. Start worker + live page; open DevTools → WS.
2. Click **Start live coaching** — during first ~4s (prepare/setup):
   - **No** `trainer:frame` events in WS log (camera preview may still run locally).
   - After `trainer:register`, expect **`trainer:state`** snapshot immediately (not only `trainer:registered`).
   - Live UI **Phase** / **Status** should update (not stuck on `preparing`).
3. When `trainer:state` shows `status: "active"`:
   - `trainer:frame` events appear at ~1 fps.
4. Between sets (if rest configured): frames stop when `status: "resting"`; resume when back to `active`.
5. `GET /api/trainer/exercise-runs/{run_id}` — status should advance past `preparing` during the run (Python persists transitions).

---

## 7. Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENROUTER_API_KEY` | — | VLM API access (not needed when `TRAINER_DRY_RUN=1`) |
| `OPENROUTER_MODEL` | nemotron free tier | VLM model |
| `MONGODB_URI` / `MONGO_URI` | from app env | Session + run persistence |
| `TRAINER_DRY_RUN` | off | `1`/`true` → fixture VLM + mock pose (no OpenRouter) |
| `TRAINER_WS_PORT` | 10001 | Trainer Socket.IO port |
| `TRAINER_WORKER_URL` | `http://localhost:10001` | Python worker base URL (SvelteKit server-side proxy for graph lifecycle) |
| `VITE_TRAINER_WS_URL` | `http://localhost:10001` | Browser Socket.IO URL (live page) |
| `TRAINER_MAX_PENDING_FRAMES` | 4 | Frame backpressure |

---

## 8. Troubleshooting

| Symptom | Fix |
|---------|-----|
| No VLM response | Check `OPENROUTER_API_KEY`; use `TRAINER_DRY_RUN=1` first (section 6.4) |
| `503 AGENT_UNAVAILABLE` on start | Trainer worker not running — start `trainer_fastapi_main.py`; check `TRAINER_WORKER_URL` |
| `401` / `403` on REST | Log in as trainer; copy fresh session cookie for `curl` |
| `404 Exercise not found` | `session_exercise_id` must match exercise `_id` from session API, not order index |
| `409 Exercise already has an active run` | `POST .../end` on existing run or restart worker to clear in-memory registry |
| Frames ignored | Confirm run status is `active`/`preparing`; check `trainer:register` ack; not `paused` |
| `RUN_NOT_FOUND` on WS register | Call REST `start` first so run loads from MongoDB into worker registry |
| Voice cues spam | Verify `voice_repeat_threshold` in config (default 3) |
| Rep count stuck | Rep completion is VLM-only — check `rep_completed` in dry-run fixtures or live VLM JSON |
| Session stuck paused | POST `/api/trainer/exercise-runs/{run_id}/resume` or `/end` |
| Live page WS fails | Set `VITE_TRAINER_WS_URL=http://localhost:10001`; check CORS (`TRAINER_WS_CORS=*` default) |
| Unit/integration tests fail | Run from `backend/` with `uv run pytest`; ensure `uv sync` completed |
| Mongo connection errors | `just init`; match `MONGODB_URI` between app and backend `.env` |

---

## Next Step

Run `/speckit-tasks` to generate implementation tasks from this plan.
