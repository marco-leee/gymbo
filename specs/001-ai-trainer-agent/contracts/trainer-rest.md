# Contract: Trainer REST API

**Feature**: `001-ai-trainer-agent` | **Base path**: `/api/trainer`

All endpoints require authenticated trainer session (existing Gymbo auth via `hooks.server.ts`).

**Scope**: Endpoints operate on **Coached Exercise Runs** (one exercise block). The parent **Gymbo Session** (`/api/sessions/{id}`) holds the multi-exercise plan; each run targets one `SessionExercise`.

**Control plane**: SvelteKit handles public REST and MongoDB. `POST .../start`, `POST .../resume`, and `POST .../end` proxy to the Python trainer worker internal API (`POST /internal/runs/{run_id}/start|resume|end`) which runs `RunController` and LangGraph. See [plan.md](../plan.md) § Control Plane.

---

## POST `/api/trainer/exercise-runs`

Start a Coached Exercise Run for one planned exercise in a Gymbo Session.

**Request body**:

```json
{
  "gymbo_session_id": "uuid",
  "session_exercise_id": "uuid",
  "config_overrides": {
    "frame_sample_rate_fps": 1.0,
    "voice_repeat_threshold": 3
  }
}
```

Config defaults are derived from the `SessionExercise` row (`target_sets`, `target_reps`, `rest_seconds`, `exercise_key`). Overrides apply only to this run.

**Response** `201`:

```json
{
  "run_id": "uuid",
  "gymbo_session_id": "uuid",
  "session_exercise_id": "uuid",
  "status": "created",
  "config": { "...": "ExerciseRunConfig" },
  "ws_url": "/trainer"
}
```

**Validation errors** `400`: invalid config; `404`: session or exercise not found; `409`: exercise already has an active run

---

## GET `/api/trainer/exercise-runs/{run_id}`

Get Coached Exercise Run snapshot.

**Response** `200**:

```json
{
  "run_id": "uuid",
  "gymbo_session_id": "uuid",
  "session_exercise_id": "uuid",
  "status": "active",
  "exercise_type": "overhead_squat",
  "config": { "...": "ExerciseRunConfig" },
  "current_set_number": 2,
  "completed_sets": 1,
  "merged_observation_state": {
    "completed_reps": 0,
    "active_issues": []
  },
  "started_at": "2026-06-20T12:00:00Z",
  "ended_at": null
}
```

**Errors**: `404` run not found; `403` not owner

---

## POST `/api/trainer/exercise-runs/{run_id}/start`

Start the agent graph (prepare → setup) for this exercise run. Idempotent if already started.

**Response** `200`:

```json
{
  "run_id": "uuid",
  "status": "preparing"
}
```

v1: WS auth uses the same session cookie as REST; `ws_token` is optional and not emitted in v1.

---

## PATCH `/api/trainer/exercise-runs/{run_id}/config`

Update run config before first set begins.

**Request body** (partial):

```json
{
  "frame_sample_rate_fps": 2.0,
  "voice_repeat_threshold": 4
}
```

**Response** `200`: updated run snapshot

**Errors**: `409` if set already in progress

---

## POST `/api/trainer/exercise-runs/{run_id}/resume`

Resume after global emergency pause within this exercise run.

**Response** `200**:

```json
{
  "run_id": "uuid",
  "status": "active"
}
```

**Errors**: `409` if not in `paused` status

---

## POST `/api/trainer/exercise-runs/{run_id}/end`

End this exercise run. Triggers per-exercise feedback → run complete. Does not end the Gymbo Session; trainer may start the next exercise run.

**Response** `200**:

```json
{
  "run_id": "uuid",
  "status": "ended",
  "exercise_feedback": "..."
}
```

---

## GET `/api/trainer/exercise-runs/{run_id}/coaching-events`

Paginated coaching event log for this run.

**Query**: `?limit=50&offset=0`

**Response** `200**:

```json
{
  "events": [
    {
      "id": "uuid",
      "message": "Keep chest up.",
      "focus_issue": "forward lean",
      "severity": "moderate",
      "set_number": 1,
      "timestamp": "2026-06-20T12:01:00Z"
    }
  ],
  "total": 12
}
```

---

## GET `/api/trainer/exercise-runs/{run_id}/safety-events`

Safety audit log for this run.

**Response** `200**:

```json
{
  "events": [
    {
      "id": "uuid",
      "source": "set_check",
      "severity": "critical",
      "description": "...",
      "timestamp": "..."
    }
  ]
}
```

---

## Integration with Existing Session API

| Layer | API | Scope |
|-------|-----|-------|
| Workout plan | `GET /api/sessions/{id}` | Multi-exercise Gymbo Session |
| Live coaching | `/api/trainer/exercise-runs/*` | One exercise at a time |

Coached Exercise Runs link to existing entities:

| Field | Mapping |
|-------|---------|
| `gymbo_session_id` | `Session._id` |
| `session_exercise_id` | `Session.exercises[].id` |
| `config.planned_sets` | `SessionExercise.target_sets` |
| `config.target_reps_per_set` | `SessionExercise.target_reps` |
| `config.rest_duration_sec` | `SessionExercise.rest_seconds` |

**Frontend route** `app/sessions/[id]/live` loads the Gymbo Session plan, lets the trainer pick or advance to the next exercise, and starts a run for the selected `session_exercise_id`.

**Multi-exercise flow**: After `POST .../end` on run A, trainer repositions camera and `POST /api/trainer/exercise-runs` for exercise B. Gymbo Session completes via existing `POST /api/sessions/{id}/complete` when all exercises are done.

---

## Deprecated aliases (avoid in new code)

| Legacy path | Replacement |
|-------------|-------------|
| `POST /api/trainer/sessions` | `POST /api/trainer/exercise-runs` |
| `GET /api/trainer/sessions/{id}` | `GET /api/trainer/exercise-runs/{run_id}` |

---

## Error Envelope

All errors use consistent shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "target_reps_per_set must be >= 1"
  }
}
```

| HTTP | Code | When |
|------|------|------|
| 400 | `VALIDATION_ERROR` | Invalid request body |
| 401 | `UNAUTHORIZED` | Missing/invalid auth |
| 403 | `FORBIDDEN` | Not session owner |
| 404 | `NOT_FOUND` | Session not found |
| 409 | `CONFLICT` | Invalid state transition |
| 503 | `AGENT_UNAVAILABLE` | Graph worker not running |
