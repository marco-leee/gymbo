/**
 * Squat rep analyzer.
 * 
 * Migrated from AnalysisStateMachine, but:
 * - VLM removed from input (uses userExercising gate instead)
 * - Hooks passed via constructor
 * - Readonly reference to engine for chart delegation
 */

import type { SquatPoseEngine } from "$lib/pose/squat-pose-engine";
import type { SquatFrameAnalysis } from "$lib/pose/types";
import type {
	ExerciseRepAnalyzerHooks,
	IExerciseRepAnalyzer,
	RepGate,
	RepPhase,
} from "./types";

/** Output from squat rep analyzer. */
export type SquatRepOutput = {
	phase: RepPhase;
	repsInSet: number;
	lastRepAtMs: number | null;
};

// Squat detection constants (from AnalysisStateMachine)
const DEPTH_ANGLE = 98;
const TOP_ANGLE = 118;
const MIN_DEPTH_FRAMES = 2;
const MIN_TOP_FRAMES = 2;

/**
 * Squat rep analyzer.
 * 
 * Tracks squat reps using knee angle heuristics.
 * Gates counting based on sessionInProgress and userExercising.
 * 
 * Does NOT use VLM directly - userExercising comes from controller.
 */
export class SquatRepAnalyzer implements IExerciseRepAnalyzer<SquatFrameAnalysis, SquatRepOutput> {
	private depthStreak = 0;
	private topStreak = 0;
	private squatState: "neutral" | "deep" = "neutral";
	private reps = 0;
	private phase: RepPhase = "idle";
	private lastRepAt: number | null = null;
	private repPeakResetPending = false;

	constructor(
		private readonly hooks: ExerciseRepAnalyzerHooks<SquatRepOutput>,
		readonly engine: SquatPoseEngine,
	) {}

	reset(): void {
		this.depthStreak = 0;
		this.topStreak = 0;
		this.squatState = "neutral";
		this.reps = 0;
		this.phase = "idle";
		this.lastRepAt = null;
		this.repPeakResetPending = false;
	}

	step(input: RepGate & { analysis: SquatFrameAnalysis | null }): void {
		const { nowMs, sessionInProgress, userExercising, analysis } = input;

		try {
			// Handle rep peak reset from previous frame
			if (this.repPeakResetPending) {
				this.repPeakResetPending = false;
				this.phase = "exercising";
			}

			const angle = analysis?.INSIDE_KNEE.angle;
			const poseValid = angle != null;

			// Gate 1: Session not in progress (paused)
			if (!sessionInProgress) {
				this.phase = "rest";
				this.emitOutput(nowMs);
				return;
			}

			// Gate 2: User not exercising (from VLM via controller)
			if (!userExercising) {
				this.phase = "idle";
				this.emitOutput(nowMs);
				return;
			}

			// Gate 3: Pose not valid
			if (!poseValid) {
				this.phase = "idle";
				this.emitOutput(nowMs);
				return;
			}

			// Pose is valid and user is exercising - count reps
			this.phase = "exercising";

			// Squat depth detection
			if (angle < DEPTH_ANGLE) {
				this.depthStreak += 1;
				this.topStreak = 0;
				if (this.depthStreak >= MIN_DEPTH_FRAMES) {
					this.squatState = "deep";
				}
			}
			// Squat top position detection
			else if (angle > TOP_ANGLE) {
				this.topStreak += 1;
				this.depthStreak = 0;

				// Rep completed: went from deep to top
				if (this.squatState === "deep" && this.topStreak >= MIN_TOP_FRAMES) {
					this.reps += 1;
					this.lastRepAt = nowMs;
					this.squatState = "neutral";
					this.topStreak = 0;
					this.phase = "rep_peak";
					this.repPeakResetPending = true;

					// Emit rep event
					this.hooks.onRep?.({ count: this.reps, atMs: nowMs });
				}
			}
			// In between angles
			else {
				this.depthStreak = 0;
				this.topStreak = 0;
			}

			this.emitOutput(nowMs);
		} catch (error) {
			this.hooks.onError?.(error instanceof Error ? error : new Error(String(error)));
		}
	}

	private emitOutput(nowMs: number): void {
		const output: SquatRepOutput = {
			phase: this.phase,
			repsInSet: this.reps,
			lastRepAtMs: this.lastRepAt,
		};

		// Check for phase change
		const prevPhase = this.phase;
		if (prevPhase !== this.phase) {
			this.hooks.onPhaseChange?.(prevPhase, this.phase);
		}

		this.hooks.onOutput(output);
	}
}
