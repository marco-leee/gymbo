import assert from "node:assert/strict";
import { afterEach, beforeEach, describe, test } from "node:test";
import type { SessionExercise } from "$lib/api/sessions";
import type { VlmResult, VlmWorkerClient } from "./vlm-worker-client";
import { SessionPhaseController } from "./session-phase-controller";

type FakeBitmap = ImageBitmap & {
	closeCount: number;
};

type FakeCanvas = HTMLCanvasElement & {
	width: number;
	height: number;
	context: FakeCanvasContext;
};

type FakeCanvasContext = CanvasRenderingContext2D & {
	canvas: FakeCanvas;
	drawCount: number;
	drawSources: unknown[];
};

type FakeTimers = {
	flushInterval: (id?: number) => Promise<void>;
	restore: () => void;
};

type FakeVlmClient = Pick<VlmWorkerClient, "init" | "run" | "dispose"> & {
	initCalls: number;
	runCalls: number;
	disposeCalls: number;
	failInitWith: (error: Error) => void;
	queueResult: (result: VlmResult | null) => void;
};

function createExercise(
	orderIndex: number,
	overrides: Partial<SessionExercise> = {},
): SessionExercise {
	return {
		id: `exercise-${orderIndex}`,
		name: `Exercise ${orderIndex}`,
		type: "strength",
		measurement: "reps",
		target_reps: 10,
		target_sets: 3,
		rest_seconds: 60,
		order_index: orderIndex,
		...overrides,
	};
}

function createFakeVideo(
	overrides: Partial<HTMLVideoElement> = {},
): HTMLVideoElement {
	return {
		readyState: 2,
		videoWidth: 1280,
		videoHeight: 720,
		...overrides,
	} as HTMLVideoElement;
}

function createFakeCanvasContext(): FakeCanvasContext {
	const ctx = {
		canvas: null as unknown as FakeCanvas,
		drawCount: 0,
		drawSources: [],
		drawImage(source: unknown) {
			ctx.drawCount += 1;
			ctx.drawSources.push(source);
		},
	} as unknown as FakeCanvasContext;

	const canvas = {
		width: 0,
		height: 0,
		context: ctx,
		getContext: () => ctx,
	} as unknown as FakeCanvas;
	ctx.canvas = canvas;

	return ctx;
}

function createFakeBitmap(): FakeBitmap {
	return {
		closeCount: 0,
		close() {
			this.closeCount += 1;
		},
	} as FakeBitmap;
}

function createFakeVlmClient(): FakeVlmClient {
	const queuedResults: Array<VlmResult | null> = [];
	let initError: Error | null = null;

	return {
		initCalls: 0,
		runCalls: 0,
		disposeCalls: 0,
		failInitWith(error) {
			initError = error;
		},
		queueResult(result) {
			queuedResults.push(result);
		},
		async init() {
			this.initCalls += 1;
			if (initError) {
				throw initError;
			}
		},
		async run() {
			this.runCalls += 1;
			return queuedResults.shift() ?? null;
		},
		async dispose() {
			this.disposeCalls += 1;
		},
	};
}

function installFakeTimers(): FakeTimers {
	const previousSetInterval = globalThis.setInterval;
	const previousClearInterval = globalThis.clearInterval;
	let nextId = 1;
	const callbacks = new Map<number, () => void | Promise<void>>();

	globalThis.setInterval = ((callback: TimerHandler) => {
		assert.equal(typeof callback, "function");
		const id = nextId++;
		callbacks.set(id, callback as () => void | Promise<void>);
		return id as unknown as ReturnType<typeof setInterval>;
	}) as unknown as typeof setInterval;

	globalThis.clearInterval = ((id: number) => {
		callbacks.delete(Number(id));
	}) as typeof clearInterval;

	return {
		async flushInterval(id) {
			if (id !== undefined) {
				const callback = callbacks.get(id);
				assert.ok(callback, `expected interval ${id} to exist`);
				await callback();
			} else {
				for (const callback of callbacks.values()) {
					await callback();
				}
			}

			await Promise.resolve();
			await Promise.resolve();
		},
		restore() {
			globalThis.setInterval = previousSetInterval;
			globalThis.clearInterval = previousClearInterval;
		},
	};
}

describe("SessionPhaseController", () => {
	let timers: FakeTimers;
	let createImageBitmapCalls: HTMLCanvasElement[];
	let createdBitmaps: FakeBitmap[];
	let createdCanvasContexts: FakeCanvasContext[];
	let previousCreateImageBitmap: typeof globalThis.createImageBitmap | undefined;
	let previousDocument: typeof globalThis.document | undefined;
	let previousMediaElement: typeof globalThis.HTMLMediaElement | undefined;
	let previousConsoleDebug: typeof console.debug;

	beforeEach(() => {
		previousConsoleDebug = console.debug;
		console.debug = () => {};
		timers = installFakeTimers();
		createImageBitmapCalls = [];
		createdBitmaps = [];
		createdCanvasContexts = [];
		previousCreateImageBitmap = globalThis.createImageBitmap;
		previousDocument = globalThis.document;
		previousMediaElement = globalThis.HTMLMediaElement;

		globalThis.createImageBitmap = (async (source: CanvasImageSource) => {
			createImageBitmapCalls.push(source as HTMLCanvasElement);
			const bitmap = createFakeBitmap();
			createdBitmaps.push(bitmap);
			return bitmap;
		}) as typeof createImageBitmap;

		globalThis.document = {
			createElement(tagName: string) {
				assert.equal(tagName, "canvas");
				const ctx = createFakeCanvasContext();
				createdCanvasContexts.push(ctx);
				return ctx.canvas;
			},
		} as Document;

		globalThis.HTMLMediaElement = {
			HAVE_CURRENT_DATA: 2,
		} as typeof HTMLMediaElement;
	});

	afterEach(() => {
		console.debug = previousConsoleDebug;
		timers.restore();
		if (previousCreateImageBitmap) {
			globalThis.createImageBitmap = previousCreateImageBitmap;
		} else {
			delete (globalThis as { createImageBitmap?: typeof createImageBitmap })
				.createImageBitmap;
		}

		if (previousDocument) {
			globalThis.document = previousDocument;
		} else {
			delete (globalThis as { document?: Document }).document;
		}

		if (previousMediaElement) {
			globalThis.HTMLMediaElement = previousMediaElement;
		} else {
			delete (globalThis as { HTMLMediaElement?: typeof HTMLMediaElement })
				.HTMLMediaElement;
		}
	});

	test("starts idle until VLM says the user is exercising", () => {
		const exercise = createExercise(0);
		const analyserCommands: unknown[] = [];

		new SessionPhaseController({
			signal: new AbortController().signal,
			exercises: [exercise],
			vlm: createFakeVlmClient(),
			vlmIntervalMs: 1000,
			getSessionInProgress: () => true,
			getVideo: () => createFakeVideo(),
			onAnalyserCommand: (command) => analyserCommands.push(command),
			mapVlmToUserExercising: (result) => result.label === "exercising",
		});

		assert.deepEqual(analyserCommands, [{ kind: "idle" }]);
	});

	test("captures webcam frames on a background canvas for VLM", async () => {
		const exercise = createExercise(0);
		const video = createFakeVideo();
		const vlm = createFakeVlmClient();
		vlm.queueResult({ label: "unknown", confidence: 0.4 });

		new SessionPhaseController({
			signal: new AbortController().signal,
			exercises: [exercise],
			vlm,
			vlmIntervalMs: 1000,
			getSessionInProgress: () => true,
			getVideo: () => video,
			onAnalyserCommand: () => {},
			mapVlmToUserExercising: (result) => result.label === "exercising",
		});

		await timers.flushInterval();

		const captureContext = createdCanvasContexts[0];
		assert.ok(captureContext, "expected an internal capture canvas");
		assert.equal(captureContext.canvas.width, 640);
		assert.equal(captureContext.canvas.height, 640);
		assert.equal(captureContext.drawCount, 1);
		assert.deepEqual(captureContext.drawSources, [video]);
		assert.deepEqual(createImageBitmapCalls, [captureContext.canvas]);
		assert.equal(vlm.runCalls, 1);
		assert.equal(createdBitmaps[0]?.closeCount, 1);
	});

	test("emits analyse and updates userExercising when VLM says exercising", async () => {
		const exercise = createExercise(0);
		const analyserCommands: unknown[] = [];
		const userExercisingChanges: boolean[] = [];
		const vlmResults: VlmResult[] = [];
		const vlm = createFakeVlmClient();
		vlm.queueResult({ label: "exercising", confidence: 0.91 });

		new SessionPhaseController({
			signal: new AbortController().signal,
			exercises: [exercise],
			vlm,
			vlmIntervalMs: 1000,
			getSessionInProgress: () => true,
			getVideo: () => createFakeVideo(),
			onAnalyserCommand: (command) => analyserCommands.push(command),
			mapVlmToUserExercising: (result) => result.label === "exercising",
			onUserExercisingChange: (value) => userExercisingChanges.push(value),
			onVlmResult: (result) => vlmResults.push(result),
		});

		await timers.flushInterval();

		assert.equal(vlm.initCalls, 1);
		assert.deepEqual(vlmResults, [{ label: "exercising", confidence: 0.91 }]);
		assert.deepEqual(userExercisingChanges, [true]);
		assert.deepEqual(analyserCommands, [
			{ kind: "idle" },
			{ kind: "analyse", exercise },
		]);
	});

	test("emits idle and updates userExercising when VLM says not exercising", async () => {
		const exercise = createExercise(0);
		const analyserCommands: unknown[] = [];
		const userExercisingChanges: boolean[] = [];
		const vlm = createFakeVlmClient();
		vlm.queueResult({ label: "not_exercising", confidence: 0.88 });

		new SessionPhaseController({
			signal: new AbortController().signal,
			exercises: [exercise],
			vlm,
			vlmIntervalMs: 1000,
			getSessionInProgress: () => true,
			getVideo: () => createFakeVideo(),
			onAnalyserCommand: (command) => analyserCommands.push(command),
			mapVlmToUserExercising: (result) => result.label === "exercising",
			onUserExercisingChange: (value) => userExercisingChanges.push(value),
		});

		await timers.flushInterval();

		assert.deepEqual(userExercisingChanges, [false]);
		assert.deepEqual(analyserCommands, [{ kind: "idle" }, { kind: "idle" }]);
	});

	test("selects the configured current exercise from the ordered list", async () => {
		const firstExercise = createExercise(0);
		const secondExercise = createExercise(1);
		const analyserCommands: unknown[] = [];
		const progressEvents: Array<{ currentIndex: number; done: boolean }> = [];
		const vlm = createFakeVlmClient();
		vlm.queueResult({ label: "exercising", confidence: 0.91 });

		new SessionPhaseController({
			signal: new AbortController().signal,
			exercises: [firstExercise, secondExercise],
			currentExerciseId: secondExercise.id,
			vlm,
			vlmIntervalMs: 1000,
			getSessionInProgress: () => true,
			getVideo: () => createFakeVideo(),
			onAnalyserCommand: (command) => analyserCommands.push(command),
			mapVlmToUserExercising: (result) => result.label === "exercising",
			onProgress: (progress) => progressEvents.push(progress),
		});

		await timers.flushInterval();

		assert.deepEqual(analyserCommands, [
			{ kind: "idle" },
			{
				kind: "analyse",
				exercise: secondExercise,
			},
		]);
		assert.deepEqual(progressEvents, [{ currentIndex: 1, done: false }]);
	});

	test("keeps userExercising unchanged when VLM returns unknown or a dropped frame", async () => {
		const exercise = createExercise(0);
		const analyserCommands: unknown[] = [];
		const userExercisingChanges: boolean[] = [];
		const vlm = createFakeVlmClient();
		vlm.queueResult({ label: "unknown", confidence: 0.4 });
		vlm.queueResult(null);

		new SessionPhaseController({
			signal: new AbortController().signal,
			exercises: [exercise],
			vlm,
			vlmIntervalMs: 1000,
			getSessionInProgress: () => true,
			getVideo: () => createFakeVideo(),
			onAnalyserCommand: (command) => analyserCommands.push(command),
			mapVlmToUserExercising: (result) => result.label === "exercising",
			onUserExercisingChange: (value) => userExercisingChanges.push(value),
		});

		await timers.flushInterval();
		await timers.flushInterval();

		assert.deepEqual(analyserCommands, [{ kind: "idle" }]);
		assert.deepEqual(userExercisingChanges, []);
		assert.equal(vlm.runCalls, 2);
	});

	test("cleans up the interval and disposes the worker on abort", async () => {
		const exercise = createExercise(0);
		const abortController = new AbortController();
		const vlm = createFakeVlmClient();
		vlm.queueResult({ label: "not_exercising", confidence: 0.88 });

		new SessionPhaseController({
			signal: abortController.signal,
			exercises: [exercise],
			vlm,
			vlmIntervalMs: 1000,
			getSessionInProgress: () => true,
			getVideo: () => createFakeVideo(),
			onAnalyserCommand: () => {},
			mapVlmToUserExercising: (result) => result.label === "exercising",
		});

		abortController.abort();
		await Promise.resolve();
		await timers.flushInterval();

		assert.equal(vlm.disposeCalls, 1);
		assert.equal(vlm.runCalls, 0);
	});

	test("reports init failures without running interval work", async () => {
		const errors: Error[] = [];
		const vlm = createFakeVlmClient();
		vlm.failInitWith(new Error("init failed"));

		new SessionPhaseController({
			signal: new AbortController().signal,
			exercises: [createExercise(0)],
			vlm,
			vlmIntervalMs: 1000,
			getSessionInProgress: () => true,
			getVideo: () => createFakeVideo(),
			onAnalyserCommand: () => {},
			mapVlmToUserExercising: (result) => result.label === "exercising",
			onError: (error) => errors.push(error),
		});

		await timers.flushInterval();

		assert.equal(vlm.runCalls, 0);
		assert.deepEqual(errors.map((error) => error.message), ["init failed"]);
	});
});
