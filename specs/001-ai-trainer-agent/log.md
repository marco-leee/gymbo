# Change Log: AI Live Trainer Agent

## 2026-06-20 — Implementation plan created

- Added `plan.md`, `research.md`, `data-model.md`, `quickstart.md`
- Added contracts: `contracts/trainer-ws.md`, `contracts/trainer-rest.md`
- Branch: `001-ai-trainer-agent`

## 2026-06-20 — Voice-out queue: in-memory default

- Changed voice-out queue from Redis to in-process `asyncio.Queue` per session
- Redis deferred until multi-worker / cross-process split is needed
- Updated: `plan.md`, `research.md`, `data-model.md`, `quickstart.md`

## 2026-06-20 — Multi-exercise session vs single-exercise graph

- Clarified: Gymbo Session may plan multiple exercises; agent graph runs one exercise at a time
- UX: camera up → complete all sets/reps for exercise → next exercise until session done
- Renamed scope to **Coached Exercise Run** in data model and REST/WS contracts
- Updated: `plan.md`, `research.md`, `data-model.md`, `contracts/*`, `quickstart.md`

## 2026-06-20 — Modular architecture decomposition

- Added `modular-architecture.md` — seven layers, module catalog, ports, file tree, POC migration map
- Updated `plan.md` with modular summary and phase→module matrix
- Updated `research.md` section 12

## 2026-06-20 — Implementation tasks generated

- Added `tasks.md` (86 tasks across 8 phases, organized by user story)

## 2026-06-20 — Spec analysis remediation

- **Control plane**: SvelteKit REST + MongoDB; Python internal HTTP for graph lifecycle; WS direct to Python (`plan.md`, `tasks.md` T019–T020, T074)
- **WS contract**: All `trainer:control` actions covered; `trainer:unregister` added; `ws_token` deferred in v1 (`contracts/trainer-ws.md`)
- **Terminology**: Spec aligned to **Coached Exercise Run** + multi-exercise Gymbo Session (`spec.md`)
- **SC-003/SC-005**: Rep-accuracy benchmark task (T084); exercise feedback fields explicit in T064
- **US4/US5 ordering**: Rest integration moved into session graph task (T063); removed premature stub task
- **MongoDB**: `safety_events` indexes in T011
- **Quickstart**: Fixed `TRAINER_WS_PORT`; added `TRAINER_WORKER_URL`
- **Pose overlay**: Deferred to post-v1 in plan Complexity Tracking
- **Log path**: Speckit convention `specs/001-ai-trainer-agent/log.md` (Principle IX)
