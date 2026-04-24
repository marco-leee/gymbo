import type { SquatFrameAnalysis } from "$lib/pose/types";
import type { VlmResult } from "./exercise-vlm-placeholder";

/** 
 * High-level phase for UI; rep counting uses squat knee angle heuristics.
 * 
 * @deprecated Use RepPhase from $lib/ml/rep instead.
 * This is kept for backward compatibility only.
 */
export type AnalysisPhase = "idle" | "exercising" | "rep_peak" | "rest";

// Re-export new types for backward compatibility
export type { RepPhase } from "./rep/types";

export type AnalysisMachineInput = {
	nowMs: number;
	pose: SquatFrameAnalysis | null;
	vlm: VlmResult;
	/** When false, rep counting is paused (e.g. session not in progress). */
	repCountingEnabled: boolean;
};

export type AnalysisMachineOutput = {
	phase: AnalysisPhase;
	repsInSet: number;
	lastRepAtMs: number | null;
};

const VLM_GATE_CONFIDENCE = 0.35;
const DEPTH_ANGLE = 98;
const TOP_ANGLE = 118;
const MIN_DEPTH_FRAMES = 2;
const MIN_TOP_FRAMES = 2;

/**
 * Combines pose iterations and optional VLM labels.
 * Phase B: when VLM is confident and says `not_exercising`, rep counting is gated off.
 * 
 * @deprecated Use SquatRepAnalyzer from $lib/ml/rep instead.
 * This class will be retired after migration to the new architecture.
 * 
 * Key differences in new approach:
 * - VLM removed from rep analyzer input (gating via userExercising)
 * - Hooks passed via constructor
 * - Readonly engine reference for chart delegation
 */
export class AnalysisStateMachine {
	private depthStreak = 0;
	private topStreak = 0;
	private squatState: "neutral" | "deep" = "neutral";
	private reps = 0;
	private phase: AnalysisPhase = "idle";
	private lastRepAt: number | null = null;
	private repPeakResetPending = false;

	reset(): void {
		this.depthStreak = 0;
		this.topStreak = 0;
		this.squatState = "neutral";
		this.reps = 0;
		this.phase = "idle";
		this.lastRepAt = null;
		this.repPeakResetPending = false;
	}

	tick(input: AnalysisMachineInput): AnalysisMachineOutput {
		const { nowMs, pose, vlm, repCountingEnabled } = input;

		if (this.repPeakResetPending) {
			this.repPeakResetPending = false;
			this.phase = "exercising";
		}

		let vlmAllowsExercise = true;
		if (vlm.label !== "unknown" && vlm.confidence >= VLM_GATE_CONFIDENCE) {
			vlmAllowsExercise = vlm.label !== "not_exercising";
		}

		const angle = pose?.INSIDE_KNEE.angle;
		const poseValid = angle != null;

		if (!repCountingEnabled) {
			this.phase = "rest";
			return {
				phase: this.phase,
				repsInSet: this.reps,
				lastRepAtMs: this.lastRepAt,
			};
		}

		if (!vlmAllowsExercise) {
			this.phase = "idle";
			return {
				phase: this.phase,
				repsInSet: this.reps,
				lastRepAtMs: this.lastRepAt,
			};
		}

		if (!poseValid) {
			this.phase = "idle";
			return {
				phase: this.phase,
				repsInSet: this.reps,
				lastRepAtMs: this.lastRepAt,
			};
		}

		this.phase = "exercising";

		if (angle < DEPTH_ANGLE) {
			this.depthStreak += 1;
			this.topStreak = 0;
			if (this.depthStreak >= MIN_DEPTH_FRAMES) {
				this.squatState = "deep";
			}
		} else if (angle > TOP_ANGLE) {
			this.topStreak += 1;
			this.depthStreak = 0;
			if (this.squatState === "deep" && this.topStreak >= MIN_TOP_FRAMES) {
				this.reps += 1;
				this.lastRepAt = nowMs;
				this.squatState = "neutral";
				this.topStreak = 0;
				this.phase = "rep_peak";
				this.repPeakResetPending = true;
			}
		} else {
			this.depthStreak = 0;
			this.topStreak = 0;
		}

		return {
			phase: this.phase,
			repsInSet: this.reps,
			lastRepAtMs: this.lastRepAt,
		};
	}
}
