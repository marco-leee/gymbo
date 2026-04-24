/**
 * Factory for creating exercise-specific rep analyzers.
 * 
 * Mirrors the pattern of createExercisePoseEngine.
 */

import type { PoseEngineExerciseKey } from "$lib/pose/types";
import type { SquatPoseEngine } from "$lib/pose/squat-pose-engine";
import { SquatRepAnalyzer, type SquatRepOutput } from "./squat-rep-analyzer";
import type { ExerciseRepAnalyzerHooks, IExerciseRepAnalyzer } from "./types";

export class UnsupportedRepAnalyzerError extends Error {
	constructor(exerciseKey: string) {
		super(`Rep analyzer is not available for "${exerciseKey}" yet`);
		this.name = "UnsupportedRepAnalyzerError";
	}
}

/**
 * Create a rep analyzer for a given exercise.
 * 
 * @param exerciseKey - Exercise type (e.g. "squat")
 * @param engine - Pose engine instance (must match exercise type)
 * @param hooks - Hooks for rep events (onOutput, onRep, etc.)
 * @returns Rep analyzer instance
 * 
 * @example
 * ```ts
 * const engine = createExercisePoseEngine("squat", deps);
 * const analyzer = createExerciseRepAnalyzer("squat", engine, {
 *   onOutput: (output) => console.log(output),
 *   onRep: (event) => console.log("Rep!", event.count),
 * });
 * ```
 */
export function createExerciseRepAnalyzer(
	exerciseKey: PoseEngineExerciseKey,
	engine: unknown,
	hooks: ExerciseRepAnalyzerHooks<unknown>,
): IExerciseRepAnalyzer {
	switch (exerciseKey) {
		case "squat":
			return new SquatRepAnalyzer(
				hooks as ExerciseRepAnalyzerHooks<SquatRepOutput>,
				engine as SquatPoseEngine,
			);
		default:
			throw new UnsupportedRepAnalyzerError(exerciseKey);
	}
}
