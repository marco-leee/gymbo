/**
 * Exercise rep analyzer types.
 * 
 * Rep analyzers track repetition counting and UI phase per exercise,
 * separate from VLM detection and pose analysis.
 */

import type { BasePoseEngine } from "$lib/pose/base-pose-engine";

/** High-level phase for UI; used by rep analyzers. */
export type RepPhase = "idle" | "exercising" | "rep_peak" | "rest";

/**
 * Gate conditions for rep counting.
 * 
 * Rep analyzers use these to determine if counting should proceed,
 * WITHOUT knowing about VLM directly.
 */
export type RepGate = {
	/** Current timestamp in milliseconds. */
	nowMs: number;
	/** Session is in progress (not paused by user). */
	sessionInProgress: boolean;
	/** User is exercising (from VLM or other gating mechanism). */
	userExercising: boolean;
};

/**
 * Hooks for rep analyzer events.
 * 
 * Rep analyzers call these from their constructor,
 * NOT from a separate registration method.
 */
export type ExerciseRepAnalyzerHooks<TOut> = {
	/** Called on every step with current output. */
	onOutput: (output: TOut) => void;
	/** Called when a rep is completed. */
	onRep?: (event: { count: number; atMs: number }) => void;
	/** Called when phase changes. */
	onPhaseChange?: (prev: RepPhase, next: RepPhase) => void;
	/** Called on analysis errors. */
	onError?: (error: Error) => void;
};

/**
 * Generic exercise rep analyzer interface.
 * 
 * All exercise-specific rep analyzers implement this.
 */
export interface IExerciseRepAnalyzer<TAnalysis = unknown, TOutput = unknown> {
	/** Reference to the pose engine (for chart delegation). */
	readonly engine: BasePoseEngine<TAnalysis, unknown>;

	/** Reset internal state (e.g. on exercise change). */
	reset(): void;

	/**
	 * Process one frame of analysis.
	 * 
	 * @param input - Gate conditions and pose analysis result
	 */
	step(input: RepGate & { analysis: TAnalysis | null }): void;
}
