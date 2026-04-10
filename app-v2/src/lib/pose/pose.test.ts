import assert from "node:assert/strict";
import { describe, test } from "node:test";
import { resolveExercisePoseEngineKey } from "./exercise-key";
import {
	createExercisePoseEngine,
	UnsupportedPoseEngineError,
} from "./exercise-pose-engine-factory";
import { BasePoseEngine } from "./base-pose-engine";
import {
	calculateSquatInterestPoints,
	classifySquatAngle,
	type PoseDetection,
	type PoseEngineDeps,
	type PoseFrame,
} from "./types";

function createPoseWithConfidence(confidence = 1): PoseDetection {
	const keypoints = Array.from({ length: 17 }, () => ({
		x: 0,
		y: 0,
		confidence,
	}));

	keypoints[6] = { x: 100, y: 100, confidence };
	keypoints[12] = { x: 100, y: 200, confidence };
	keypoints[14] = { x: 200, y: 200, confidence };
	keypoints[16] = { x: 200, y: 300, confidence };

	return {
		confidence,
		classId: 0,
		box: {
			x: 0,
			y: 0,
			width: 300,
			height: 300,
		},
		keypoints,
	};
}

function createTestDeps(): PoseEngineDeps {
	let currentTime = 0;

	return {
		modelInputSize: 2,
		analysisFps: 2,
		videoSeekEpsilonSec: 0.001,
		createVideoSource: async () => ({
			duration: 1.1,
			videoWidth: 1920,
			videoHeight: 1080,
			get currentTime() {
				return currentTime;
			},
			async seekTo(time: number) {
				currentTime = time;
			},
			drawFrame() {},
			dispose() {},
		}),
		createCanvasContext: () => ({}) as CanvasRenderingContext2D,
		createModelInput: () => new Float32Array([0]),
		ensureWorkerReady: async () => ({}) as Worker,
		runPoseInference: async () => createPoseWithConfidence(),
	};
}

describe("resolveExercisePoseEngineKey", () => {
	test("maps squat-like exercise names to squat", () => {
		assert.equal(resolveExercisePoseEngineKey({ name: "Barbell Squat" }), "squat");
	});

	test("maps push-up exercise names to push_up", () => {
		assert.equal(resolveExercisePoseEngineKey({ name: "Push Up" }), "push_up");
	});

	test("returns null for unsupported exercise names", () => {
		assert.equal(resolveExercisePoseEngineKey({ name: "Cycling" }), null);
	});
});

describe("createExercisePoseEngine", () => {
	test("creates a squat engine for the squat key", () => {
		const engine = createExercisePoseEngine("squat", createTestDeps());
		assert.equal(engine.constructor.name, "SquatPoseEngine");
	});

	test("throws for unsupported engines", () => {
		assert.throws(
			() => createExercisePoseEngine("push_up", createTestDeps()),
			UnsupportedPoseEngineError,
		);
	});
});

describe("squat helpers", () => {
	test("classifies squat angles with the existing thresholds", () => {
		assert.equal(classifySquatAngle(95), "GOOD");
		assert.equal(classifySquatAngle(80), "TOO LOW");
		assert.equal(classifySquatAngle(135), "LOWER");
		assert.equal(classifySquatAngle(175), null);
	});

	test("returns squat interest points for confident keypoints", () => {
		const squatPoints = calculateSquatInterestPoints(createPoseWithConfidence(), {
			modelInputSize: 640,
			poseConfidenceThreshold: 0.25,
			sourceWidth: 640,
			sourceHeight: 640,
		});

		assert.notEqual(squatPoints, null);
		assert.equal(squatPoints?.INSIDE_KNEE.angle, 90);
		assert.equal(squatPoints?.OUTSIDE_HIP.angle, 270);
	});

	test("returns null when required keypoints are below threshold", () => {
		assert.equal(
			calculateSquatInterestPoints(createPoseWithConfidence(0.1), {
				modelInputSize: 640,
				poseConfidenceThreshold: 0.25,
				sourceWidth: 640,
				sourceHeight: 640,
			}),
			null,
		);
	});
});

describe("BasePoseEngine", () => {
	test("streams frame iterations in sampling order", async () => {
		class TestEngine extends BasePoseEngine<string, never> {
			protected analyzeFrame(frame: PoseFrame): string | null {
				return frame.pose ? `frame-${frame.frameIndex}` : null;
			}
		}

		const seenInputs: number[] = [];
		let currentTime = 0;
		const engine = new TestEngine({
			...createTestDeps(),
			createVideoSource: async () => ({
				duration: 1.1,
				videoWidth: 1920,
				videoHeight: 1080,
				get currentTime() {
					return currentTime;
				},
				async seekTo(time: number) {
					currentTime = time;
				},
				drawFrame() {},
				dispose() {},
			}),
			createModelInput: () => {
				const next = seenInputs.length;
				seenInputs.push(next);
				return new Float32Array([next]);
			},
			runPoseInference: async (_worker, input) => ({
				...createPoseWithConfidence(),
				classId: input[0] ?? 0,
			}),
		});

		const iterations: Array<{ frame: number; timestampSec: number }> = [];

		for await (const iteration of engine.analyzeVideo({
			file: new File(["video"], "demo.mp4", { type: "video/mp4" }),
		})) {
			iterations.push({
				frame: iteration.frameIndex,
				timestampSec: Number(iteration.timestampSec.toFixed(3)),
			});
		}

		assert.deepEqual(iterations, [
			{ frame: 0, timestampSec: 0 },
			{ frame: 1, timestampSec: 0.5 },
			{ frame: 2, timestampSec: 1 },
			{ frame: 3, timestampSec: 1.099 },
		]);
	});
});
