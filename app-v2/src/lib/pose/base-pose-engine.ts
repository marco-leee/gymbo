import type {
	PoseEngineDeps,
	PoseEngineIteration,
	PoseFrame,
	VideoAnalysisInput,
} from "./types";

function getSampleTimes(durationSec: number, analysisFps: number, epsilonSec: number) {
	if (!Number.isFinite(durationSec) || durationSec <= 0) {
		return [0];
	}

	const intervalSec = 1 / analysisFps;
	const times: number[] = [0];
	for (let timestampSec = intervalSec; timestampSec < durationSec; timestampSec += intervalSec) {
		times.push(timestampSec);
	}

	const lastFrameTime = Math.max(0, durationSec - epsilonSec);
	if (Math.abs(times[times.length - 1] - lastFrameTime) > epsilonSec) {
		times.push(lastFrameTime);
	}

	return times;
}

function createCanvasContext(modelInputSize: number) {
	const canvas = document.createElement("canvas");
	canvas.width = modelInputSize;
	canvas.height = modelInputSize;
	const ctx = canvas.getContext("2d", { willReadFrequently: true });
	if (!ctx) {
		throw new Error("Cannot create video canvas");
	}

	return ctx;
}

export abstract class BasePoseEngine<TAnalysis, TChartPoint> {
	constructor(protected deps: PoseEngineDeps) {}

	async *analyzeVideo(
		input: VideoAnalysisInput,
	): AsyncGenerator<PoseEngineIteration<TAnalysis>, void, void> {
		const video = await this.deps.createVideoSource(input.file);
		const ctx =
			this.deps.createCanvasContext?.(this.deps.modelInputSize) ??
			createCanvasContext(this.deps.modelInputSize);

		try {
			const worker = await this.deps.ensureWorkerReady();
			const sampleTimes = getSampleTimes(
				video.duration,
				this.deps.analysisFps,
				this.deps.videoSeekEpsilonSec,
			);

			for (const [frameIndex, timestampSec] of sampleTimes.entries()) {
				await video.seekTo(timestampSec);
				video.drawFrame(ctx, this.deps.modelInputSize);
				const inputTensor = this.deps.createModelInput(
					ctx,
					this.deps.modelInputSize,
				);
				const pose = await this.deps.runPoseInference(worker, inputTensor);
				const frame: PoseFrame = {
					frameIndex,
					timestampSec: video.currentTime,
					sourceWidth: video.videoWidth,
					sourceHeight: video.videoHeight,
					pose,
				};
				const analysis = this.analyzeFrame(frame);
				const iteration = {
					...frame,
					analysis,
				};
				this.logIteration?.(iteration);
				yield iteration;
			}
		} finally {
			video.dispose();
		}
	}

	chartPointFromIteration?(
		_iteration: PoseEngineIteration<TAnalysis>,
	): TChartPoint | null;

	protected logIteration?(_iteration: PoseEngineIteration<TAnalysis>): void;

	protected abstract analyzeFrame(frame: PoseFrame): TAnalysis | null;
}

export { getSampleTimes };
