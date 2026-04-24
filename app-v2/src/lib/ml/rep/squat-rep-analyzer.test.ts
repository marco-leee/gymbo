import assert from "node:assert/strict";
import { describe, test } from "node:test";
import { SquatRepAnalyzer } from "./squat-rep-analyzer";

function createAnalysis(angle: number) {
	return {
		INSIDE_KNEE: {
			idxToCoordinates: {},
			angle,
			rotationAngle: 0,
			comment: null,
		},
		OUTSIDE_HIP: {
			idxToCoordinates: {},
			angle,
			rotationAngle: 0,
			comment: null,
		},
	};
}

describe("SquatRepAnalyzer", () => {
	test("emits phase transitions when the phase changes", () => {
		const transitions: Array<[string, string]> = [];
		const analyzer = new SquatRepAnalyzer(
			{
				onOutput() {},
				onPhaseChange(prev, next) {
					transitions.push([prev, next]);
				},
			},
			{} as never,
		);

		analyzer.step({
			nowMs: 10,
			sessionInProgress: true,
			userExercising: true,
			analysis: createAnalysis(130),
		});

		analyzer.step({
			nowMs: 20,
			sessionInProgress: true,
			userExercising: false,
			analysis: createAnalysis(130),
		});

		assert.deepEqual(transitions, [
			["idle", "exercising"],
			["exercising", "idle"],
		]);
	});
});
