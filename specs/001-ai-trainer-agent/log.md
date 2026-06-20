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
