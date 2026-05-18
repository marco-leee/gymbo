# Decision log: async-video-processing

> Append-only style: newest decisions at the bottom.

| Date       | Decision | Rationale |
| ---------- | -------- | --------- |
| 2026-04-28 | Perception v1 is **pose-only**; segmentation, pointmap, and fusion are **placeholder functions** with stable interfaces. | Ship end-to-end async flow and chart data quickly; avoid loading unused `safetensors` and multi-head inference until needed. |
| 2026-04-28 | Python processor is **out-of-Worker**; CF Queue/Worker only **orchestrates** (enqueue + delegate). | Sapiens needs PyTorch, large weights, and long CPU/GPU work unsuitable for standard Worker isolates. |
| 2026-04-28 | Persistence: processor writes with **`pymongo`** + `MONGO_URI`; mirror `updateSetInExercise` field paths in Python. Supersedes earlier “internal HTTP API first” idea. | Fewer moving parts; `MONGO_URI` only in trusted processor env; keep schema parity with app manually. |
| 2026-04-28 | **Phase 0** includes the **output layer**: **pymongo** update on session/set, exercised with **stub** `pose_chart_data` before input/perception layers. | Proves queue → processor → DB early; later layers reuse the same `ProcessingResultRepo`. |
| 2026-04-28 | **Layer boundaries** are **`typing.Protocol` + DTOs**; Sapiens, R2/OpenCV, and pymongo are **adapters** only. Orchestrator is strategy- and model-provider-agnostic; tests use fake pose and fake `ProcessingResultRepo`. | Standardised inter-layer APIs. |
| 2026-04-28 | Full technical specification consolidated into [plan.md](./plan.md) under `doc/features/async-video-processing/`. | Single repo location for implementers (queue, contracts, Phase 0, layers, risks). |
| 2026-04-28 | **Phase 0 producer:** SvelteKit **`LPUSH`** job JSON to Redis **after** Mongo update; **Python worker** **`BRPOP`** on startup/loop. Optional HTTP `/enqueue` for testing only. | Matches simple local pattern; avoids extra HTTP hop on PUT. |
| 2026-04-28 | **Enqueue fail-open:** if **`REDIS_URL`** is unset, skip LPUSH; Redis errors are logged and do not fail the client PUT. **`MongoSessionSetRepo`** matches nested sets only while **`status`** is **`processing`** (idempotent once **`completed`**). | Reliability + duplicate jobs after completion. |
| 2026-04-28 | **Stub chart for Phase 0:** one synthetic **`PoseChartPoint`** (`frame=0`, `timestampSec=0`, inside/outside angles `0`) via **`stub_pose_chart_points()`** until biomechanics exists. | Validates pymongo vs `PoseChartPointSchema`. |
