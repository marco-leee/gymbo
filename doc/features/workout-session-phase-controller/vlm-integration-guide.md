# VLM Integration Guide

Quick reference for using `VlmWorkerClient` in `SessionPhaseController` (Phase 5).

## Basic Usage

```typescript
import { VlmWorkerClient, type VlmResult } from '$lib/ml/vlm-worker-client';

// 1. Initialize
const vlmClient = new VlmWorkerClient();
await vlmClient.init();

// 2. Run inference (e.g. every 1s)
const ctx = getCaptureContext(); // from canvas with video drawn
const bitmap = await createImageBitmap(ctx.canvas);
const result = await vlmClient.run(bitmap);

// 3. Handle result
if (result) {
  // result is VlmResult | null (null if dropped due to single-flight)
  const exercising = mapVlmToUserExercising(result);
  onUserExercisingChange(exercising);
}

// 4. Cleanup
await vlmClient.dispose();
```

## SessionPhaseController Pattern

```typescript
type SessionPhaseControllerConfig = {
  vlm: VlmWorkerClient;
  vlmIntervalMs: number; // e.g. 1000
  getCaptureContext: () => CanvasRenderingContext2D | null;
  mapVlmToUserExercising: (r: VlmResult) => boolean;
  onUserExercisingChange?: (exercising: boolean) => void;
  onVlmResult?: (r: VlmResult) => void;
  signal: AbortSignal;
};

class SessionPhaseController {
  private vlmIntervalId: ReturnType<typeof setInterval> | null = null;

  constructor(private config: SessionPhaseControllerConfig) {
    this.startVlmLoop();
  }

  private startVlmLoop(): void {
    const runVlm = async () => {
      const ctx = this.config.getCaptureContext();
      if (!ctx) return;

      try {
        const bitmap = await createImageBitmap(ctx.canvas);
        const result = await this.config.vlm.run(bitmap);
        
        if (result) {
          this.config.onVlmResult?.(result);
          
          // Unknown label policy: don't change state
          if (result.label !== "unknown") {
            const exercising = this.config.mapVlmToUserExercising(result);
            this.config.onUserExercisingChange?.(exercising);
          }
        }
      } catch (error) {
        console.error('[SessionPhaseController] VLM error:', error);
      }
    };

    // Run immediately, then every interval
    runVlm();
    this.vlmIntervalId = setInterval(runVlm, this.config.vlmIntervalMs);

    // Cleanup on abort
    this.config.signal.addEventListener('abort', () => {
      if (this.vlmIntervalId) {
        clearInterval(this.vlmIntervalId);
        this.vlmIntervalId = null;
      }
    });
  }
}
```

## Unknown Label Policy

From [requirements.md](./requirements.md):

> When `label === "unknown"`, do not change `userExercising` state.

**Rationale:** Prevents spurious state changes from low-confidence or ambiguous frames.

**Implementation:**

```typescript
function mapVlmToUserExercising(result: VlmResult): boolean {
  // Only change state on confident classifications
  if (result.label === "unknown") {
    // Return current state unchanged, or ignore
    return currentUserExercising;
  }
  
  return result.label === "exercising";
}
```

## Single-Flight Behavior

`client.run()` returns `null` if inference is already in progress.

**Handling dropped frames:**

```typescript
const result = await vlmClient.run(bitmap);

if (result === null) {
  console.log('[VLM] Frame dropped (inference in progress)');
  // Don't change state - use previous VLM result
  return;
}

// Process result...
```

**Why single-flight?**
- At 1s intervals, rarely triggers (inference ~200-500ms)
- Prevents queue buildup
- Simple implementation
- Controller can handle dropped frames gracefully

## Capture Context

The controller samples the **same canvas** that `LiveSessionAnalyser` draws to.

**Pattern:**

```typescript
// LiveSessionAnalyser draws video once per analysis frame
analyser.start(); // draws to its own canvas at 5 FPS

// SessionPhaseController samples that canvas at 1s intervals
const ctx = analyser.getCaptureContext(); // or shared canvas
const bitmap = await createImageBitmap(ctx.canvas);
```

**Invariant:** At most **one** `drawImage` from video per analysis frame.

## Error Handling

```typescript
try {
  const bitmap = await createImageBitmap(ctx.canvas);
  const result = await vlmClient.run(bitmap);
  
  if (!result) {
    // Dropped due to single-flight - OK to ignore
    return;
  }
  
  // Process result...
} catch (error) {
  console.error('[VLM] Error:', error);
  
  // Options:
  // 1. Continue with previous state
  // 2. Fall back to "unknown" behavior
  // 3. Disable VLM and rely on pose only
}
```

## Lifecycle

```typescript
// Initialization (once at session start)
const vlmClient = new VlmWorkerClient();
await vlmClient.init(); // loads model, can take 30-60s first time

// Usage (repeated)
// ... interval loop with run() ...

// Cleanup (session end or page navigate)
await vlmClient.dispose(); // terminates worker
```

## State Tracking

```typescript
console.log(vlmClient.isReady);     // true after init()
console.log(vlmClient.isInferring); // true during run()
```

Use `isReady` to gate inference calls:

```typescript
if (!vlmClient.isReady) {
  console.warn('[VLM] Not ready, skipping inference');
  return;
}
```

## Performance

| Operation | Duration | Notes |
|-----------|----------|-------|
| `init()` | 30-60s | First load, cached thereafter |
| `init()` (cached) | ~2-5s | Model in browser cache |
| `run()` | 200-500ms | Per frame, WebGPU |
| `run()` (dropped) | <1ms | Single-flight logic |
| `dispose()` | <100ms | Cleanup |

**Main thread impact:** 0ms (all inference in worker)

## Testing

See test page at `/dev/vlm-test` for interactive testing:

```bash
npm run dev
# Navigate to http://localhost:5173/dev/vlm-test
```

## Placeholder vs Real Model

**Phase 1A (current):** Placeholder always returns `"unknown"`

```typescript
// Placeholder behavior:
const result = await client.run(bitmap);
// result = { label: "unknown", confidence: 0.0 }
```

**Phase 1B (Gemma 4):** Real model returns exercise detection

```typescript
// Real model behavior:
const result = await client.run(bitmap);
// result = { label: "exercising", confidence: 0.85 }
// OR
// result = { label: "not_exercising", confidence: 0.92 }
```

**API identical** - no code changes needed for upgrade.

## Integration Checklist

For SessionPhaseController (Phase 5):

- [ ] Create `VlmWorkerClient` instance
- [ ] Call `init()` during controller setup
- [ ] Set up interval timer (1s)
- [ ] Get capture context from shared canvas
- [ ] Create `ImageBitmap` per interval
- [ ] Call `client.run(bitmap)`
- [ ] Handle `null` return (dropped frames)
- [ ] Implement unknown label policy
- [ ] Map result to `userExercising` state
- [ ] Call `dispose()` on abort signal
- [ ] Clear interval timer on cleanup

## Example: Complete Integration

```typescript
import { VlmWorkerClient, type VlmResult } from '$lib/ml/vlm-worker-client';

async function setupSessionPhaseController(
  signal: AbortSignal,
  getCaptureContext: () => CanvasRenderingContext2D | null,
  onUserExercisingChange: (exercising: boolean) => void
) {
  // Initialize VLM
  const vlm = new VlmWorkerClient();
  await vlm.init();
  console.log('[Session] VLM ready');

  let currentUserExercising = false;

  // VLM loop
  const runVlmInference = async () => {
    if (!vlm.isReady) return;

    const ctx = getCaptureContext();
    if (!ctx) return;

    try {
      const bitmap = await createImageBitmap(ctx.canvas);
      const result = await vlm.run(bitmap);

      if (!result) {
        // Dropped, keep current state
        return;
      }

      // Unknown policy: don't change state
      if (result.label === "unknown") {
        return;
      }

      // Update state
      const exercising = result.label === "exercising";
      if (exercising !== currentUserExercising) {
        currentUserExercising = exercising;
        onUserExercisingChange(exercising);
      }
    } catch (error) {
      console.error('[Session] VLM error:', error);
    }
  };

  // Start interval
  const intervalId = setInterval(runVlmInference, 1000);

  // Cleanup
  signal.addEventListener('abort', async () => {
    clearInterval(intervalId);
    await vlm.dispose();
    console.log('[Session] VLM disposed');
  });
}
```

## See Also

- [vlm-implementation-plan.md](./vlm-implementation-plan.md) - Implementation details
- [design.md](./design.md) - Architecture overview
- [PHASE1-COMPLETE.md](./PHASE1-COMPLETE.md) - Phase 1 summary
- Test page: `/dev/vlm-test`

---

**Status:** VLM client ready for integration (Phase 1A complete)  
**Next:** Implement SessionPhaseController (Phase 5)
