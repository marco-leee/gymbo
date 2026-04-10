import { SquatPoseEngine } from "./squat-pose-engine";
import type { PoseEngineDeps, PoseEngineExerciseKey } from "./types";

export class UnsupportedPoseEngineError extends Error {
	constructor(exerciseKey: string) {
		super(`Pose analysis is not available for "${exerciseKey}" yet`);
		this.name = "UnsupportedPoseEngineError";
	}
}

export function createExercisePoseEngine(
	exerciseKey: PoseEngineExerciseKey,
	deps: PoseEngineDeps,
) {
	switch (exerciseKey) {
		case "squat":
			return new SquatPoseEngine(deps);
		default:
			throw new UnsupportedPoseEngineError(exerciseKey);
	}
}
