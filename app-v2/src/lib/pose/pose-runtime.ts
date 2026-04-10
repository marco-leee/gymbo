import { getPoseModelData } from "$lib/services/model-cache";
import YoloWorker from "$lib/workers/yolo.worker?worker";
import type { PoseDetection, PoseEngineDeps, PoseVideoSource } from "./types";

type PoseWorkerMessage =
	| { type: "ready" }
	| {
			type: "result";
			id: number;
			inputName: string;
			outputNames: string[];
			pose: PoseDetection | null;
	  }
	| {
			type: "error";
			id?: number;
			message: string;
	  };

export class PoseWorkerInitError extends Error {}
export class PoseInferenceError extends Error {}
export class VideoDecodeError extends Error {}

function createModelInputFromCanvas(
	ctx: CanvasRenderingContext2D,
	modelInputSize: number,
) {
	const imageData = ctx.getImageData(0, 0, modelInputSize, modelInputSize).data;
	const channelSize = modelInputSize * modelInputSize;
	const input = new Float32Array(channelSize * 3);

	for (let pixelIdx = 0; pixelIdx < channelSize; pixelIdx++) {
		const rgbaIdx = pixelIdx * 4;
		input[pixelIdx] = imageData[rgbaIdx] / 255;
		input[channelSize + pixelIdx] = imageData[rgbaIdx + 1] / 255;
		input[channelSize * 2 + pixelIdx] = imageData[rgbaIdx + 2] / 255;
	}

	return input;
}

async function createBrowserVideoSource(file: File): Promise<PoseVideoSource> {
	const blobUrl = URL.createObjectURL(file);
	const video = document.createElement("video");
	video.muted = true;
	video.playsInline = true;
	video.preload = "auto";

	try {
		await new Promise<void>((resolve, reject) => {
			video.onloadeddata = () => resolve();
			video.onerror = () => reject(new VideoDecodeError("Cannot decode uploaded video"));
			video.src = blobUrl;
			video.load();
		});
	} catch (error) {
		video.pause();
		video.removeAttribute("src");
		video.load();
		URL.revokeObjectURL(blobUrl);
		throw error;
	}

	return {
		get duration() {
			return video.duration;
		},
		get videoWidth() {
			return video.videoWidth;
		},
		get videoHeight() {
			return video.videoHeight;
		},
		get currentTime() {
			return video.currentTime;
		},
		async seekTo(timestampSec: number) {
			const safeDuration = Number.isFinite(video.duration) ? video.duration : 0;
			const epsilonSec = 0.001;
			const targetTime = safeDuration > 0
				? Math.max(0, Math.min(timestampSec, safeDuration - epsilonSec))
				: 0;

			if (Math.abs(video.currentTime - targetTime) <= epsilonSec) {
				await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
				return;
			}

			await new Promise<void>((resolve, reject) => {
				const handleSeeked = () => {
					cleanup();
					resolve();
				};
				const handleError = () => {
					cleanup();
					reject(new VideoDecodeError("Video seek failed"));
				};
				const cleanup = () => {
					video.removeEventListener("seeked", handleSeeked);
					video.removeEventListener("error", handleError);
				};

				video.addEventListener("seeked", handleSeeked);
				video.addEventListener("error", handleError);
				video.currentTime = targetTime;
			});
		},
		drawFrame(ctx, modelInputSize) {
			ctx.drawImage(video, 0, 0, modelInputSize, modelInputSize);
		},
		dispose() {
			video.pause();
			video.removeAttribute("src");
			video.load();
			URL.revokeObjectURL(blobUrl);
		},
	};
}

export function createPoseEngineRuntime(
	options?: Partial<
		Pick<
			PoseEngineDeps,
			"modelInputSize" | "analysisFps" | "videoSeekEpsilonSec"
		>
	>,
) {
	let worker: Worker | null = null;
	let workerReadyPromise: Promise<void> | null = null;
	let workerBootPromise: Promise<void> | null = null;
	let resolveWorkerReady: (() => void) | null = null;
	let rejectWorkerReady: ((reason?: unknown) => void) | null = null;
	let nextPoseRequestId = 1;
	const pendingPoseRequests = new Map<
		number,
		{
			resolve: (
				value: Extract<PoseWorkerMessage, { type: "result" }>,
			) => void;
			reject: (reason?: unknown) => void;
		}
	>();

	function resetWorkerReadyPromise() {
		workerReadyPromise = new Promise<void>((resolve, reject) => {
			resolveWorkerReady = resolve;
			rejectWorkerReady = reject;
		});
	}

	function rejectPendingPoseRequests(reason: unknown) {
		for (const pending of pendingPoseRequests.values()) {
			pending.reject(reason);
		}
		pendingPoseRequests.clear();
	}

	function destroyWorker(reason = new Error("Pose worker destroyed")) {
		rejectWorkerReady?.(reason);
		rejectWorkerReady = null;
		resolveWorkerReady = null;
		rejectPendingPoseRequests(reason);
		if (worker) {
			worker.postMessage({ type: "dispose" });
			worker.terminate();
			worker = null;
		}
		workerReadyPromise = null;
		workerBootPromise = null;
	}

	function handleWorkerMessage(event: MessageEvent<PoseWorkerMessage>) {
		const message = event.data;
		if (message.type === "ready") {
			resolveWorkerReady?.();
			resolveWorkerReady = null;
			rejectWorkerReady = null;
			return;
		}

		if (message.type === "error") {
			if (message.id != null) {
				const pending = pendingPoseRequests.get(message.id);
				if (pending) {
					pendingPoseRequests.delete(message.id);
					pending.reject(new PoseInferenceError(message.message));
					return;
				}
			}

			destroyWorker(new PoseInferenceError(message.message));
			console.error("Pose worker error", message.message);
			return;
		}

		const pending = pendingPoseRequests.get(message.id);
		if (!pending) return;

		pendingPoseRequests.delete(message.id);
		pending.resolve(message);
	}

	async function createWorker() {
		if (worker) return;
		if (workerBootPromise) {
			await workerBootPromise;
			return;
		}

		resetWorkerReadyPromise();
		workerBootPromise = (async () => {
			const modelData = await getPoseModelData();
			const nextWorker = new YoloWorker();
			nextWorker.onmessage = handleWorkerMessage;
			nextWorker.onerror = (event) => {
				const error = new PoseWorkerInitError(
					event.message || "Pose worker crashed",
				);
				destroyWorker(error);
				console.error("Pose worker crashed", error);
			};
			worker = nextWorker;
			nextWorker.postMessage({ type: "init", modelData }, [modelData]);
			await workerReadyPromise;
		})()
			.catch((error) => {
				destroyWorker(
					error instanceof Error
						? error
						: new PoseWorkerInitError("Pose worker failed"),
				);
				throw error;
			})
			.finally(() => {
				workerBootPromise = null;
			});

		await workerBootPromise;
	}

	async function ensureWorkerReady() {
		await createWorker();
		if (!worker || !workerReadyPromise) {
			throw new PoseWorkerInitError("Pose worker was not created");
		}

		await workerReadyPromise;
		return worker;
	}

	async function runPoseInference(
		activeWorker: Worker,
		input: Float32Array,
	): Promise<PoseDetection | null> {
		const requestId = nextPoseRequestId++;
		const result = await new Promise<Extract<PoseWorkerMessage, { type: "result" }>>(
			(resolve, reject) => {
				pendingPoseRequests.set(requestId, { resolve, reject });
				activeWorker.postMessage(
					{
						type: "run",
						id: requestId,
						input: {
							data: input.buffer,
							dims: [1, 3, runtime.modelInputSize, runtime.modelInputSize],
							type: "float32",
						},
					},
					[input.buffer],
				);
			},
		);

		return result.pose;
	}

	const runtime = {
		modelInputSize: options?.modelInputSize ?? 640,
		analysisFps: options?.analysisFps ?? 5,
		videoSeekEpsilonSec: options?.videoSeekEpsilonSec ?? 0.001,
		createVideoSource: createBrowserVideoSource,
		createModelInput: createModelInputFromCanvas,
		ensureWorkerReady,
		runPoseInference,
		dispose: destroyWorker,
	};

	return runtime;
}
