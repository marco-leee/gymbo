# Changes: async-video-processing

> Chronological log of shipped code/doc changes for this feature.

## 2026-04-28

- Added feature documentation scaffold under `doc/features/async-video-processing/` (requirements, plan, decision log, this file).
- Documented **Protocol + DTO layer boundaries** (strategy/model agnostic) in feature `plan.md`, `requirements.md`, `log.md`, and layer-by-layer cursor plan.
- Documented processor persistence as **Python `pymongo`** + `MONGO_URI` (not internal HTTP).
- Consolidated full implementation spec (Phase 0, job JSON, Protocol table, per-layer detail, verification, risks) into [plan.md](./plan.md).
- Phase 0 orchestration: **SvelteKit `LPUSH`** → Redis list; **Python worker `BRPOP`** loop (optional HTTP enqueue for curl only).
- Implemented: **`ai/pipeline`** contracts (`ProcessingResultRepo`, `MongoSessionSetRepo`), **`worker_phase0`**, root **`docker-compose.yaml`** (**`redis`**, **`worker`**, same stack as **mongo**/minio) + **`ai/Dockerfile.worker`**; **`app-v2`** `REDIS_URL`, **`enqueueVideoJobIfConfigured`**, PUT enqueue after **`updateSetInExercise`**; Bun test **`video-job-queue.test.ts`**.
