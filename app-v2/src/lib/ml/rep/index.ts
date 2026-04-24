/**
 * Exercise rep analyzer exports.
 * 
 * Main entry point for rep counting logic.
 */

export { createExerciseRepAnalyzer, UnsupportedRepAnalyzerError } from "./exercise-rep-analyzer-factory";
export { SquatRepAnalyzer, type SquatRepOutput } from "./squat-rep-analyzer";
export type {
	ExerciseRepAnalyzerHooks,
	IExerciseRepAnalyzer,
	RepGate,
	RepPhase,
} from "./types";
