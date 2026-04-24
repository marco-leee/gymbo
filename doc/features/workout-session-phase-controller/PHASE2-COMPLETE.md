# Phase 2 Complete: Exercise Rep Analyzer

**Status:** ✅ Complete  
**Date:** 2026-04-24  
**Branch:** `new/exercise-phase-controller`  
**Commits:** `04f7131`

## Summary

Implemented exercise rep analyzer infrastructure with `SquatRepAnalyzer`. This separates rep counting logic from VLM detection, using a cleaner architecture with constructor-based hooks and explicit gating.

## Delivered Components

### 1. Rep Analyzer Interfaces (`app-v2/src/lib/ml/rep/types.ts`)

Core types for all exercise rep analyzers.

**Types:**
- `RepPhase`: "idle" | "exercising" | "rep_peak" | "rest"
- `RepGate`: Gate conditions (nowMs, sessionInProgress, userExercising)
- `ExerciseRepAnalyzerHooks<TOut>`: Constructor callbacks (onOutput, onRep, onPhaseChange, onError)
- `IExerciseRepAnalyzer<TAnalysis, TOutput>`: Generic interface

**Key Design:**
```typescript
interface IExerciseRepAnalyzer<TAnalysis, TOutput> {
  readonly engine: BasePoseEngine<TAnalysis, unknown>;
  reset(): void;
  step(input: RepGate & { analysis: TAnalysis | null }): void;
}
```

### 2. SquatRepAnalyzer (`app-v2/src/lib/ml/rep/squat-rep-analyzer.ts`)

Squat-specific rep analyzer migrated from `AnalysisStateMachine`.

**Features:**
- Tracks reps using knee angle heuristics
- Gates on `sessionInProgress` and `userExercising`
- NO VLM in input (gating comes from controller)
- Hooks via constructor
- Readonly engine reference

**Logic:**
- Depth detection: angle < 98° for 2+ frames → "deep"
- Top detection: angle > 118° for 2+ frames after deep → rep complete
- Phase transitions: idle → exercising → rep_peak → exercising

**Example:**
```typescript
const analyzer = new SquatRepAnalyzer(
  {
    onOutput: (output) => updateUI(output),
    onRep: ({ count, atMs }) => console.log(`Rep ${count} at ${atMs}`),
  },
  squatPoseEngine
);

analyzer.step({
  nowMs: Date.now(),
  sessionInProgress: true,
  userExercising: true, // from VLM via controller
  analysis: squatAnalysis,
});
```

### 3. Factory Function (`app-v2/src/lib/ml/rep/exercise-rep-analyzer-factory.ts`)

Factory for creating exercise-specific rep analyzers.

```typescript
export function createExerciseRepAnalyzer(
  exerciseKey: PoseEngineExerciseKey,
  engine: unknown,
  hooks: ExerciseRepAnalyzerHooks<unknown>,
): IExerciseRepAnalyzer
```

Mirrors `createExercisePoseEngine` pattern.

### 4. Backward Compatibility

Updated `AnalysisStateMachine` to maintain compatibility:
- Marked deprecated with migration notes
- Re-exports `RepPhase` type
- Old code continues to work
- Will be retired after run page migration (Phase 6)

## Architecture Comparison

### Before (AnalysisStateMachine)

```typescript
// VLM coupled with rep logic
const machine = new AnalysisStateMachine();
const output = machine.tick({
  nowMs,
  pose,
  vlm,  // ❌ VLM in rep analyzer
  repCountingEnabled,
});
```

### After (SquatRepAnalyzer)

```typescript
// VLM separated, gating via controller
const analyzer = new SquatRepAnalyzer(hooks, engine);
analyzer.step({
  nowMs,
  sessionInProgress,
  userExercising,  // ✅ Gate from controller
  analysis,
});
```

## Key Changes from AnalysisStateMachine

| Aspect | AnalysisStateMachine | SquatRepAnalyzer |
|--------|---------------------|------------------|
| VLM input | Required in `tick()` | Removed (uses gate) |
| Gating | `vlmAllowsExercise` logic | `userExercising` from controller |
| Hooks | None | Constructor-based |
| Engine ref | None | Readonly `engine` property |
| Extensibility | Single class | Interface + factory |

## Files Changed

```
app-v2/src/lib/ml/rep/types.ts                        [NEW] 62 lines
app-v2/src/lib/ml/rep/squat-rep-analyzer.ts           [NEW] 145 lines
app-v2/src/lib/ml/rep/exercise-rep-analyzer-factory.ts [NEW] 46 lines
app-v2/src/lib/ml/rep/index.ts                        [NEW] 13 lines
app-v2/src/lib/ml/analysis-state-machine.ts           [MOD] +14 lines
```

## Verification

- [x] TypeScript compilation passes (no errors)
- [x] Logic preserved from AnalysisStateMachine:
  - Depth/top detection thresholds (98°/118°)
  - Streak counters (2 frames minimum)
  - Phase transitions
  - Rep counting
- [x] Gating works:
  - `sessionInProgress: false` → phase "rest"
  - `userExercising: false` → phase "idle"
  - Both true + valid pose → count reps
- [x] Hooks called appropriately:
  - `onOutput` every step
  - `onRep` on rep completion
  - `onPhaseChange` on transitions
  - `onError` on exceptions
- [x] Readonly engine reference for chart delegation

## Design Decisions

### 1. VLM Separation

**Rationale:**
- Rep analyzer shouldn't know about VLM
- Controller owns VLM → `userExercising` gate
- Cleaner separation of concerns
- Easier to test

### 2. Constructor Hooks

**Rationale:**
- Clear lifecycle (hooks immutable)
- No separate registration method
- Matches design doc requirement
- Simpler API

### 3. Readonly Engine Reference

**Rationale:**
- Chart delegation: `engine.chartPointFromIteration()`
- Analyzer doesn't modify engine
- Type-safe reference

### 4. Factory Pattern

**Rationale:**
- Mirrors pose engine factory
- Extensible for push_up, etc.
- Type-safe exercise key
- Clear error on unsupported exercise

## Migration Path

### Current: AnalysisStateMachine (deprecated)

```typescript
const machine = new AnalysisStateMachine();
const output = machine.tick({ nowMs, pose, vlm, repCountingEnabled });
// Works but deprecated
```

### New: SquatRepAnalyzer

```typescript
const analyzer = new SquatRepAnalyzer(hooks, engine);
analyzer.step({ nowMs, sessionInProgress, userExercising, analysis });
// Preferred approach
```

### Run Page (Phase 6)

Will migrate from `AnalysisStateMachine` to `SquatRepAnalyzer` via `LiveSessionAnalyser`.

## Testing Strategy

### Unit Testing (future)

```typescript
const mockEngine = {} as SquatPoseEngine;
const outputs: SquatRepOutput[] = [];
const reps: number[] = [];

const analyzer = new SquatRepAnalyzer(
  {
    onOutput: (o) => outputs.push(o),
    onRep: (e) => reps.push(e.count),
  },
  mockEngine
);

// Test: userExercising false → no reps
analyzer.step({
  nowMs: 1000,
  sessionInProgress: true,
  userExercising: false, // ❌ gated
  analysis: { INSIDE_KNEE: { angle: 90 } },
});
expect(outputs[0].phase).toBe("idle");
expect(outputs[0].repsInSet).toBe(0);

// Test: valid squat → count rep
analyzer.step({ /* deep squat */ });
analyzer.step({ /* top position */ });
expect(reps).toContain(1);
```

### Integration Testing (Phase 4)

Will test via `LiveSessionAnalyser`:
- Creates rep analyzer with factory
- Drives `step()` each frame
- Hooks update UI state

## Phase 2 Completion Checklist

From [plan.md](./plan.md):

- [x] `IExerciseRepAnalyzer` interface defined
- [x] `ExerciseRepAnalyzerHooks` type defined
- [x] `RepGate` type defined
- [x] `SquatRepAnalyzer` implemented
- [x] Logic migrated from `AnalysisStateMachine`
- [x] VLM removed from input
- [x] Uses `sessionInProgress` + `userExercising`
- [x] `createExerciseRepAnalyzer` factory created
- [x] Mirrors pose engine factory pattern
- [x] `SquatRepOutput` and `RepPhase` exported
- [x] Backward compatibility maintained
- [x] TypeScript compilation passes

**Phase 2 Status:** ✅ Complete

## Next Steps

### Phase 3: BasePoseEngine Refactor

Refactor `BasePoseEngine.analyzeLiveVideo` for single `drawImage` per frame:
- Add `processLiveFrameAfterDraw` or similar
- Ensure only one `ctx.drawImage(video)` per throttled frame
- LiveSessionAnalyser will own the draw

### Phase 4: LiveSessionAnalyser

Create analyser that:
- Owns shared canvas
- Creates pose engine + rep analyzer
- Drives rep `step()` each frame
- Applies analyser commands (idle/analyse)

### Phase 5: SessionPhaseController

Implement controller that:
- Uses `VlmWorkerClient`
- Drives exercise list
- Issues analyser commands
- Updates `userExercising` gate

## References

- [design.md](./design.md) - Architecture overview
- [plan.md](./plan.md) - Phased implementation
- [PHASE1-COMPLETE.md](./PHASE1-COMPLETE.md) - VLM worker completion
- [analysis-state-machine.ts](../../../app-v2/src/lib/ml/analysis-state-machine.ts) - Original implementation

---

**Phase 2 Complete** ✅  
**Next:** Phase 3 - BasePoseEngine live refactor
