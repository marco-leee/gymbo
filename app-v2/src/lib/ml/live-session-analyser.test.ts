import assert from "node:assert/strict";
import { afterEach, beforeEach, describe, test } from "node:test";
import type { SessionExercise } from "$lib/api/sessions";
import type { PoseDetection, PoseEngineDeps } from "$lib/pose/types";
import type { createPoseEngineRuntime } from "$lib/pose/pose-runtime";
import {
	createLiveSessionAnalyser,
	type AnalyserCommand,
} from "./live-session-analyser";

type FakeCanvasContext = CanvasRenderingContext2D & {
	canvas: HTMLCanvasElement;
	drawCount: number;
};

type RafController = {
	flushFrame: () => Promise<void>;
	restore: () => void;
};

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

function createFakeCanvasContext(size: number): FakeCanvasContext {
	const canvas = {
		width: size,
		height: size,
		getContext: () => ctx,
	} as unknown as HTMLCanvasElement;

	const ctx = {
		canvas,
		drawCount: 0,
		drawImage: () => {
			ctx.drawCount += 1;
		},
		getImageData() {
			return {
				data: new Uint8ClampedArray(size * size * 4),
			} as ImageData;
		},
	} as unknown as FakeCanvasContext;

	return ctx;
}

function installFakeBrowserGlobals(ctx: FakeCanvasContext): () => void {
	const previousDocument = globalThis.document;
	const previousMediaElement = globalThis.HTMLMediaElement;

	globalThis.document = {
		createElement(tagName: string) {
			if (tagName !== "canvas") {
				throw new Error(`Unexpected element request: ${tagName}`);
			}

			return ctx.canvas;
		},
	} as Document;

	globalThis.HTMLMediaElement = {
		HAVE_CURRENT_DATA: 2,
	} as typeof HTMLMediaElement;

	return () => {
		globalThis.document = previousDocument;
		globalThis.HTMLMediaElement = previousMediaElement;
	};
}

function installRafController(): RafController {
	const previousRaf = globalThis.requestAnimationFrame;
	const previousPerformance = globalThis.performance;
	const queue: FrameRequestCallback[] = [];
	let nowMs = 0;

	globalThis.requestAnimationFrame = ((callback: FrameRequestCallback) => {
		queue.push(callback);
		return queue.length;
	}) as typeof requestAnimationFrame;

	Object.defineProperty(globalThis, "performance", {
		configurable: true,
		value: {
			now: () => nowMs,
		} as Performance,
	});

	return {
		async flushFrame() {
			const callback = queue.shift();
			assert.ok(callback, "expected a queued animation frame");
			nowMs += 100;
			callback(nowMs);
			await Promise.resolve();
			await Promise.resolve();
			await new Promise<void>((resolve) => setTimeout(resolve, 0));
		},
		restore() {
			globalThis.requestAnimationFrame = previousRaf;
			Object.defineProperty(globalThis, "performance", {
				configurable: true,
				value: previousPerformance,
			});
		},
	};
}

function createPoseRuntime(
	ctx: FakeCanvasContext,
): ReturnType<typeof createPoseEngineRuntime> {
	return {
		modelInputSize: Number(ctx.canvas.width) || 640,
		analysisFps: 5,
		videoSeekEpsilonSec: 0.001,
		createVideoSource: async () => {
			throw new Error("uploaded video path is not used in this test");
		},
		createCanvasContext: () => ctx,
		createModelInput: () => new Float32Array([1]) as Float32Array<ArrayBuffer>,
		ensureWorkerReady: async () => ({}) as Worker,
		runPoseInference: async () => createPoseWithConfidence(),
		dispose() {},
	} as unknown as ReturnType<typeof createPoseEngineRuntime>;
}

function createExercise(overrides: Partial<SessionExercise> = {}): SessionExercise {
	return {
		id: "exercise-1",
		name: "Air Squat",
		type: "strength",
		measurement: "reps",
		target_sets: 3,
		rest_seconds: 60,
		order_index: 0,
		...overrides,
	};
}

describe("createLiveSessionAnalyser", () => {
	let restoreBrowserGlobals: (() => void) | null = null;
	let raf: RafController | null = null;

	beforeEach(() => {
		const ctx = createFakeCanvasContext(640);
		restoreBrowserGlobals = installFakeBrowserGlobals(ctx);
		raf = installRafController();
	});

	afterEach(() => {
		raf?.restore();
		restoreBrowserGlobals?.();
		raf = null;
		restoreBrowserGlobals = null;
	});

	test("exposes capture context and stays idle until analyse is commanded", async () => {
		const ctx = createFakeCanvasContext(640);
		restoreBrowserGlobals?.();
		restoreBrowserGlobals = installFakeBrowserGlobals(ctx);

		const errors: Error[] = [];
		const outputs: string[] = [];
		const analyser = createLiveSessionAnalyser({
			getVideo: () =>
				({
					readyState: 2,
					videoWidth: 1280,
					videoHeight: 720,
					currentTime: 1,
				}) as HTMLVideoElement,
			poseRuntime: createPoseRuntime(ctx),
			modelInputSize: 640,
			targetFps: 30,
			getSessionInProgress: () => true,
			getUserExercising: () => true,
			orchestrationHooks: {
				onError: (error) => errors.push(error),
			},
			signal: new AbortController().signal,
			createRepHooks: () => ({
				onOutput: (output) => outputs.push(output.phase),
			}),
		});

		assert.equal(analyser.getCaptureContext(), ctx);

		analyser.start();
		await raf?.flushFrame();
		assert.deepEqual(outputs, []);
		assert.equal(ctx.drawCount, 0);

		const command: AnalyserCommand = {
			kind: "analyse",
			exercise: createExercise(),
		};
		analyser.applyCommand(command);
		await raf?.flushFrame();

		assert.deepEqual(errors, []);
		assert.deepEqual(outputs, ["exercising"]);
		assert.equal(ctx.drawCount, 1);
	});

	test("re-reads user exercising gate on every analysed frame", async () => {
		const ctx = createFakeCanvasContext(640);
		restoreBrowserGlobals?.();
		restoreBrowserGlobals = installFakeBrowserGlobals(ctx);

		let userExercising = false;
		const errors: Error[] = [];
		const outputs: string[] = [];
		const analyser = createLiveSessionAnalyser({
			getVideo: () =>
				({
					readyState: 2,
					videoWidth: 1280,
					videoHeight: 720,
					currentTime: 1,
				}) as HTMLVideoElement,
			poseRuntime: createPoseRuntime(ctx),
			modelInputSize: 640,
			targetFps: 30,
			getSessionInProgress: () => true,
			getUserExercising: () => userExercising,
			orchestrationHooks: {
				onError: (error) => errors.push(error),
			},
			signal: new AbortController().signal,
			createRepHooks: () => ({
				onOutput: (output) => outputs.push(output.phase),
			}),
		});

		analyser.applyCommand({
			kind: "analyse",
			exercise: createExercise(),
		});
		analyser.start();

		await raf?.flushFrame();
		userExercising = true;
		await raf?.flushFrame();

		assert.deepEqual(errors, []);
		assert.deepEqual(outputs, ["idle", "exercising"]);
	});
});
