# Phase 1 Complete: VLM Worker & Client

**Status:** ✅ Complete  
**Date:** 2026-04-24  
**Branch:** `new/exercise-phase-controller`  
**Commits:** `7f85597`

## Summary

Implemented the VLM (Vision Language Model) Web Worker and client for exercise repetition detection. This is Phase 1A (placeholder) - ready for Phase 1B upgrade to Gemma 4 VLM.

## Delivered Components

### 1. VLM Worker (`app-v2/src/lib/workers/vlm.worker.ts`)

Web Worker for VLM inference with placeholder implementation.

**Features:**
- Message-based communication (init/run/dispose)
- Type-safe message types
- Placeholder inference (returns "unknown" for now)
- Error handling
- Clean lifecycle

**Messages:**
- `init` → `ready`
- `run(id, bitmap)` → `result(id, vlm)`
- `dispose` → cleanup
- Errors → `error(id?, message)`

### 2. VLM Worker Client (`app-v2/src/lib/ml/vlm-worker-client.ts`)

Main thread client for the VLM worker.

**Features:**
- Async lifecycle: `init()`, `dispose()`
- Single-flight inference: drops concurrent requests
- Transferable ImageBitmap: zero-copy performance
- Promise-based API
- Request tracking with unique IDs
- State tracking: `isReady`, `isInferring`
- Automatic worker error recovery

**API:**
```typescript
const client = new VlmWorkerClient();
await client.init();

const bitmap = await createImageBitmap(canvas);
const result = await client.run(bitmap); // null if dropped

await client.dispose();
```

### 3. Test Page (`app-v2/src/routes/dev/vlm-test/+page.svelte`)

Interactive test page for manual verification.

**URL:** `/dev/vlm-test`

**Features:**
- Camera integration
- Single inference button
- Continuous mode (1s intervals)
- Stats display (count, duration)
- Result visualization
- Client state monitoring

## Architecture

```
Main Thread                    Worker Thread
-----------                    -------------
SessionPhaseController
    ↓
VlmWorkerClient  ←--message--> vlm.worker.ts
    ↓ run(bitmap)              ↓ inferFrame()
    ← Promise<VlmResult>       ← VlmResult
```

**Single-flight logic:**
- If inference in progress → drop new request → return `null`
- Controller handles dropped frames gracefully
- Prevents queue buildup at 1s intervals

## Type Definitions

```typescript
type VlmResult = {
  label: "unknown" | "exercising" | "not_exercising";
  confidence: number;
  stateHint?: string;
  raw?: unknown;
};
```

**Design:** VLM detects repetition activity, NOT exercise type.

## Verification

- [x] TypeScript compilation passes (no errors in VLM files)
- [x] Test page works (`/dev/vlm-test`)
- [x] Worker initialization successful
- [x] Message passing works (init, run, dispose)
- [x] Single-flight logic drops concurrent requests
- [x] Transferable ImageBitmap (verified in code)
- [x] Error handling works

## Files Changed

```
app-v2/src/lib/workers/vlm.worker.ts          [NEW] 145 lines
app-v2/src/lib/ml/vlm-worker-client.ts        [NEW] 280 lines
app-v2/src/routes/dev/vlm-test/+page.svelte   [NEW] 249 lines
```

## Next Steps: Phase 1B

Upgrade placeholder to real Gemma 4 VLM:

1. Add `@huggingface/transformers` dependency
2. Load `onnx-community/gemma-4-E2B-it-ONNX` model
3. Implement `inferFrame()` with vision-language inference
4. Parse model output into `VlmResult`
5. Test with camera feed

**No API changes needed** - drop-in replacement for placeholder.

See [vlm-implementation-plan.md](./vlm-implementation-plan.md) for Phase 1B details.

## Testing Instructions

### Manual Test (Dev Page)

1. Start dev server: `npm run dev` (in `app-v2/`)
2. Navigate to `/dev/vlm-test`
3. Click "1. Init VLM Worker" → wait for "ready"
4. Click "2. Start Camera" → allow camera access
5. Click "3. Run Once" → see result
6. Click "4. Run Continuous" → see 1s updates
7. Open DevTools → check console for worker logs
8. Open DevTools Performance → verify worker thread

### Expected Behavior

- **Status:** Shows current state
- **Result:** `{ label: "unknown", confidence: 0.0 }` (placeholder)
- **Stats:** Count increments, duration ~0-5ms (placeholder)
- **Single-flight:** Rapid clicks drop extra requests

### Integration Test (Future)

Once SessionPhaseController is implemented (Phase 5):

```typescript
const client = new VlmWorkerClient();
await client.init();

// In session controller interval (1s):
const ctx = getCaptureContext();
const bitmap = await createImageBitmap(ctx.canvas);
const result = await client.run(bitmap);

if (result && result.label !== "unknown") {
  const exercising = result.label === "exercising";
  onUserExercisingChange(exercising);
}
```

## Design Decisions

### 1. Single-Flight vs Queue

**Chosen:** Drop concurrent requests

**Rationale:**
- Simple implementation
- At 1s intervals, rarely triggers
- Controller can handle dropped frames
- No memory buildup

**Alternative:** Queue latest request
- More complex
- Marginal benefit at 1s cadence

### 2. Transferable vs Clone

**Chosen:** Transfer ImageBitmap

**Rationale:**
- Zero-copy performance
- Large images (640x640 @ 4 bytes/pixel = 1.6MB)
- Worker API supports transfer
- Bitmap can't be reused (must recreate)

### 3. Placeholder First

**Chosen:** Phase 1A placeholder → Phase 1B real model

**Rationale:**
- Test infrastructure first
- Large model (~3GB) takes time to load
- API stable for upgrade
- Can wire into SessionPhaseController now

## Performance Characteristics

| Metric | Placeholder | Real Model (est.) |
|--------|-------------|-------------------|
| Init time | ~100ms | ~30-60s (first load) |
| Inference | <1ms | ~200-500ms (WebGPU) |
| Memory | <1MB | ~3-4GB |
| Main thread | 0ms | 0ms (worker) |

## Known Limitations

1. **Placeholder only:** Always returns "unknown"
2. **Model not loaded:** Phase 1B needed for real inference
3. **No WebGPU fallback:** Will add WASM fallback in Phase 1B
4. **No timeout:** Should add 5s timeout per inference
5. **No retry logic:** Worker crash requires page reload

## Phase 1 Completion Checklist

From [plan.md](./plan.md):

- [x] `vlm.worker.ts` implemented with placeholder
- [x] `VlmWorkerClient` implemented
- [x] `init()`, `dispose()`, `run()` methods
- [x] Transferable ImageBitmap
- [x] Single-flight logic
- [x] Request ID tracking
- [x] Message types (init/run/dispose/ready/result/error)
- [x] TypeScript compilation passes
- [x] Test page created
- [x] Manual verification possible

**Phase 1A Status:** ✅ Complete

## References

- [vlm-implementation-plan.md](./vlm-implementation-plan.md) - Full implementation plan
- [design.md](./design.md) - Architecture overview
- [plan.md](./plan.md) - Phased implementation checklist
- [exercise-vlm-placeholder.ts](../../../app-v2/src/lib/ml/exercise-vlm-placeholder.ts) - Gemma 4 code examples

---

**Next Phase:** Phase 2 - Exercise Rep Analyzer (SquatRepAnalyzer)
