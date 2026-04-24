import type { SessionExercise } from "$lib/api/sessions";
import {
	createExerciseRepAnalyzer,
	UnsupportedRepAnalyzerError,
	type ExerciseRepAnalyzerHooks,
	type IExerciseRepAnalyzer,
	type SquatRepOutput,
} from "$lib/ml/rep";
import { BasePoseEngine } from "$lib/pose/base-pose-engine";
import {
	createExercisePoseEngine,
	UnsupportedPoseEngineError,
} from "$lib/pose/exercise-pose-engine-factory";
import { resolveExercisePoseEngineKey } from "$lib/pose/exercise-key";
import type { createPoseEngineRuntime } from "$lib/pose/pose-runtime";
import type { PoseEngineIteration } from "$lib/pose/types";

export type ExerciseRef = SessionExercise;

export type AnalyserCommand =
	| { kind: "idle" }
	| { kind: "analyse"; exercise: ExerciseRef };

export type LiveSessionAnalyserConfig = {
	getVideo: () => HTMLVideoElement | null;
	poseRuntime: ReturnType<typeof createPoseEngineRuntime>;
	modelInputSize: number;
	targetFps: number;
	getSessionInProgress: () => boolean;
	getUserExercising: () => boolean;
	orchestrationHooks?: {
		onAnalysisFrame?: (event: {
			exercise: ExerciseRef;
			iteration: PoseEngineIteration<unknown>;
			captureContext: CanvasRenderingContext2D;
		}) => void;
		onError?: (error: Error) => void;
	};
	signal: AbortSignal;
	createRepHooks: (
		exercise: ExerciseRef | null,
	) => ExerciseRepAnalyzerHooks<SquatRepOutput>;
};

export interface LiveSessionAnalyser {
	applyCommand(cmd: AnalyserCommand): void;
	start(): void;
	stop(): void;
	resetForExerciseChange(): void;
	getCaptureContext(): CanvasRenderingContext2D;
}

type ActiveAnalyserState = {
	exercise: ExerciseRef;
	engine: BasePoseEngine<unknown, unknown>;
	repAnalyzer: IExerciseRepAnalyzer;
};

function createCaptureContext(modelInputSize: number) {
	const canvas = document.createElement("canvas");
	canvas.width = modelInputSize;
	canvas.height = modelInputSize;

	const ctx = canvas.getContext("2d", { willReadFrequently: true });
	if (!ctx) {
		throw new Error("Cannot create live analyser capture canvas");
	}

	return ctx;
}

function normalizeError(error: unknown) {
	return error instanceof Error ? error : new Error(String(error));
}

export function createLiveSessionAnalyser(
	config: LiveSessionAnalyserConfig,
): LiveSessionAnalyser {
	const captureContext = createCaptureContext(config.modelInputSize);
	let currentCommand: AnalyserCommand = { kind: "idle" };
	let activeState: ActiveAnalyserState | null = null;
	let started = false;
	let loopRunning = false;
	let frameIndex = 0;
	let lastProcessMs = 0;

	function reportError(error: unknown) {
		config.orchestrationHooks?.onError?.(normalizeError(error));
	}

	function clearActiveState() {
		activeState = null;
		frameIndex = 0;
		lastProcessMs = 0;
	}

	function buildActiveState(exercise: ExerciseRef) {
		const exerciseKey = resolveExercisePoseEngineKey(exercise);
		if (!exerciseKey) {
			throw new Error(`Pose analysis is not available for exercise "${exercise.name}"`);
		}

		const engine = createExercisePoseEngine(
			exerciseKey,
			config.poseRuntime,
		) as BasePoseEngine<unknown, unknown>;
		const repAnalyzer = createExerciseRepAnalyzer(
			exerciseKey,
			engine,
			config.createRepHooks(exercise) as ExerciseRepAnalyzerHooks<unknown>,
		);

		activeState = {
			exercise,
			engine,
			repAnalyzer,
		};
		frameIndex = 0;
		lastProcessMs = 0;
	}

	async function runLoop() {
		loopRunning = true;

		try {
			while (started && !config.signal.aborted) {
				await new Promise<void>((resolve) => {
					requestAnimationFrame(() => resolve());
				});

				if (!started || config.signal.aborted) {
					break;
				}

				if (currentCommand.kind !== "analyse" || !activeState) {
					continue;
				}

				const video = config.getVideo();
				if (!video) {
					continue;
				}

				if (video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
					continue;
				}

				if (video.videoWidth === 0 || video.videoHeight === 0) {
					continue;
				}

				const nowMs = performance.now();
				const minIntervalMs = 1000 / Math.max(1, config.targetFps);
				if (nowMs - lastProcessMs < minIntervalMs) {
					continue;
				}
				lastProcessMs = nowMs;

				try {
					captureContext.drawImage(
						video,
						0,
						0,
						config.modelInputSize,
						config.modelInputSize,
					);

					const worker = await config.poseRuntime.ensureWorkerReady();
					const iteration = await activeState.engine.analyzeLiveFrameAfterDraw(worker, {
						frameIndex,
						timestampSec: Number.isFinite(video.currentTime)
							? video.currentTime
							: nowMs / 1000,
						sourceWidth: video.videoWidth,
						sourceHeight: video.videoHeight,
						ctx: captureContext,
					});

					activeState.repAnalyzer.step({
						nowMs,
						sessionInProgress: config.getSessionInProgress(),
						userExercising: config.getUserExercising(),
						analysis: iteration.analysis,
					});

					config.orchestrationHooks?.onAnalysisFrame?.({
						exercise: activeState.exercise,
						iteration,
						captureContext,
					});

					frameIndex += 1;
				} catch (error) {
					reportError(error);
				}
			}
		} finally {
			loopRunning = false;
		}
	}

	return {
		applyCommand(cmd) {
			currentCommand = cmd;

			if (cmd.kind === "idle") {
				clearActiveState();
				return;
			}

			try {
				const nextExerciseId = cmd.exercise.id;
				const currentExerciseId = activeState?.exercise.id;
				if (nextExerciseId !== currentExerciseId) {
					clearActiveState();
					buildActiveState(cmd.exercise);
					return;
				}

				if (!activeState) {
					buildActiveState(cmd.exercise);
				}
			} catch (error) {
				if (
					error instanceof UnsupportedPoseEngineError ||
					error instanceof UnsupportedRepAnalyzerError ||
					error instanceof Error
				) {
					reportError(error);
					clearActiveState();
					return;
				}

				throw error;
			}
		},

		start() {
			if (started || config.signal.aborted) {
				return;
			}

			started = true;
			if (!loopRunning) {
				void runLoop();
			}
		},

		stop() {
			started = false;
		},

		resetForExerciseChange() {
			frameIndex = 0;
			lastProcessMs = 0;
			activeState?.repAnalyzer.reset();
		},

		getCaptureContext() {
			return captureContext;
		},
	};
}
