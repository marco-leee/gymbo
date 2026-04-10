import type { PoseEngineExerciseKey } from "./types";

export function resolveExercisePoseEngineKey(exercise: {
	name?: string | null;
}): PoseEngineExerciseKey | null {
	const normalizedName = exercise.name?.trim().toLowerCase() ?? "";

	if (normalizedName.includes("squat")) {
		return "squat";
	}

	if (
		normalizedName.includes("push up") ||
		normalizedName.includes("push-up") ||
		normalizedName.includes("pushup")
	) {
		return "push_up";
	}

	return null;
}
