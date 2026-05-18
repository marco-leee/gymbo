# Feature: async-video-processing

> Async pipeline: after a set video is uploaded to R2, a job is queued and a Python processor runs layered analysis, then writes results to Mongo.

**Detailed design:** everything below is expanded in [plan.md](./plan.md) (job schema, Protocols, Phase 0, per-layer notes, verification, risks).

## Summary

Trainers or clients upload a short MP4 per set; the app stores the object in R2 and marks the set `processing`. A worker (queue + processor) downloads the video, runs perception (pose first; other branches stubbed), derives biomechanics (e.g. joint angles into `pose_chart_data`), and updates the set to `completed` (or records failure). Layers are **Protocol + DTO** boundaries so pose provider, frame source, biomechanics strategy, and **result repository** can be swapped.

## Upstream flow (today’s app)

1. Client calls `POST /api/media/sign` → presigned PUT + **`r2_key`** ([`sign/+server.ts`](../../../app-v2/src/routes/api/media/sign/+server.ts)).
2. Client PUTs MP4 to R2.
3. Client updates set with **`video_url: key`** → server sets **`processing`** when previously `pending` ([`sets/[setId]/+server.ts`](../../../app-v2/src/routes/api/sessions/[id]/exercises/[exerciseId]/sets/[setId]/+server.ts)).

**Target:** step 3 also **LPUSH**es job JSON to **Redis** (after Mongo succeeds) — body §4.1 in [plan.md](./plan.md); **Python worker** **BRPOP**s the same list.

## Scope boundaries

- **In scope:** Job contract; **Phase 0** — **Redis LIST** (SvelteKit **`LPUSH`** after set update; **Python worker** **`BRPOP`** in Docker); **Protocol/DTO** boundaries; input, perception, biomechanics strategy, feedback stub, **`ProcessingResultRepo`**. **Cloudflare Queues** deferred.
- **Out of scope:** Rich coaching copy, full segmentation/pointmap/fusion models (future swap-in), real-time WebSocket analysis (separate flow in [`doc/README.md`](../../README.md)).

## Requirements

- [ ] On set `video_url` commit (after Mongo success), server **`LPUSH`**es job JSON to **Redis** (`REDIS_URL`, shared list key with worker) — see [plan.md §4.2](./plan.md).
- [ ] **Phase 0:** Dockerized **Python worker** **`BRPOP`**s that list and writes via **`MongoSessionSetRepo`**. Optional **`POST /enqueue`** (Bearer) only for manual injection.
- [ ] Processor downloads the object from R2 via S3-compatible API using server-side credentials.
- [ ] Input layer exposes a **`FrameSource`** (or equivalent Protocol) producing **`NormalizedFrame`** DTOs (`frame_index`, `timestamp_sec`, …) without exposing R2/S3 types to downstream layers.
- [ ] Perception: **`PoseEstimator`** implementation runs **Sapiens** pose (backbone + `PoseHeatmapHead`, UDP decode) today; seg, pointmap, and fusion are no-op / null **provider** implementations behind the same Protocols.
- [ ] Biomechanism is a **`BiomechanicsStrategy`** implementation mapping perception DTOs to chart fields compatible with `PoseChartPointSchema` (`insideKnee`, `outsideHip`, etc.) — see [`mongo.ts`](../../../app-v2/src/lib/services/mongo.ts).
- [ ] Processor pipeline layers communicate only through **`typing.Protocol`** and **DTOs** (no vendor types at boundaries); orchestrator composes concrete adapters from config.
- [ ] Output persistence implements **`ProcessingResultRepo`**; v1 **`MongoSessionSetRepo`** (`pymongo`, same paths/shapes as app `updateSetInExercise`): `pose_chart_data`, `status: completed` on success; sensible error surfacing on failure.
- [ ] Optional **`POST /enqueue`** (if implemented for ops/curl) uses **Bearer**; unauthenticated public enqueue is not allowed. Main path is **SvelteKit → Redis** only.

## Non-goals

- Loading seg / pointmap checkpoints or multi-head forward for unused heads in v1.
- UX for job progress bar or partial results streaming (can follow later).

## References

- [requirements template](../template/requirements.md)
- [product spec](../../PRODUCT_SPEC.md)
- [doc/README.md](../../README.md) (async processing bullets)
- [exercise.md](../exercise.md)
- [PRINCIPLES.md](../../../PRINCIPLES.md)
- [ARCHITECTURE.md](../../../ARCHITECTURE.md)
- [Detailed plan](./plan.md)
- [app-v2 wrangler R2](../../../app-v2/wrangler.jsonc)
- [app-v2 media sign](../../../app-v2/src/routes/api/media/sign/+server.ts)
- [app-v2 set update](../../../app-v2/src/routes/api/sessions/[id]/exercises/[exerciseId]/sets/[setId]/+server.ts)
- [ai/__main__.py](../../../ai/__main__.py)
