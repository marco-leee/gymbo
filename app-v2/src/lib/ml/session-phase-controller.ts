import type { AnalyserCommand, ExerciseRef } from "./live-session-analyser";
import type { VlmResult, VlmWorkerClient } from "./vlm-worker-client";

export type SessionPhaseProgress = {
	currentIndex: number;
	done: boolean;
};

export type SessionPhaseVlmClient = Pick<
	VlmWorkerClient,
	"init" | "run" | "dispose"
>;

export type SessionPhaseControllerConfig = {
	signal: AbortSignal;
	exercises: readonly ExerciseRef[];
	currentExerciseId?: string | null;
	vlm: SessionPhaseVlmClient;
	vlmIntervalMs: number;
	vlmCaptureSize?: number;
	getSessionInProgress: () => boolean;
	getVideo: () => HTMLVideoElement | null;
	onAnalyserCommand: (command: AnalyserCommand) => void;
	mapVlmToUserExercising: (result: VlmResult) => boolean;
	onUserExercisingChange?: (exercising: boolean) => void;
	onVlmResult?: (result: VlmResult) => void;
	onProgress?: (progress: SessionPhaseProgress) => void;
	onError?: (error: Error) => void;
};

export class SessionPhaseController {
	private intervalId: ReturnType<typeof setInterval> | null = null;
	private currentIndex = 0;
	private readonly readyPromise: Promise<boolean>;
	private readonly captureContext: CanvasRenderingContext2D;
	private readonly vlmCaptureSize: number;
	private disposed = false;

	constructor(private readonly config: SessionPhaseControllerConfig) {
		this.vlmCaptureSize = config.vlmCaptureSize ?? 640;
		this.captureContext = this.createCaptureContext();
		this.currentIndex = this.resolveCurrentIndex();
		console.debug(
			"[SessionPhaseController] init",
			"exercises",
			config.exercises.length,
			"currentIndex",
			this.currentIndex,
		);
		this.emitAnalyserCommand({ kind: "idle" });
		this.emitProgress();
		this.readyPromise = this.config.vlm.init().then(
			() => true,
			(error) => {
				this.reportError(error);
				return false;
			},
		);
		this.intervalId = setInterval(() => {
			void this.runVlmCycle();
		}, this.config.vlmIntervalMs);

		this.config.signal.addEventListener("abort", () => {
			void this.dispose();
		});
	}

	private get currentExercise(): ExerciseRef | null {
		return this.config.exercises[this.currentIndex] ?? null;
	}

	private resolveCurrentIndex() {
		const { currentExerciseId, exercises } = this.config;
		if (!currentExerciseId) {
			return exercises.length > 0 ? 0 : -1;
		}

		const selectedIndex = exercises.findIndex(
			(exercise) => exercise.id === currentExerciseId,
		);
		return selectedIndex >= 0 ? selectedIndex : -1;
	}

	private createCaptureContext() {
		const canvas = document.createElement("canvas");
		canvas.width = this.vlmCaptureSize;
		canvas.height = this.vlmCaptureSize;
		const ctx = canvas.getContext("2d", { willReadFrequently: true });
		if (!ctx) {
			throw new Error("Cannot create session phase VLM capture canvas");
		}

		return ctx;
	}

	private reportError(error: unknown) {
		const normalizedError =
			error instanceof Error ? error : new Error(String(error));
		this.config.onError?.(normalizedError);
	}

	private emitAnalyserCommand(command: AnalyserCommand) {
		console.debug(
			"[SessionPhaseController] emitAnalyserCommand",
			command.kind,
			command.kind === "analyse" ? command.exercise.id : undefined,
		);
		this.config.onAnalyserCommand(command);
	}

	private emitAnalyseCommand() {
		const exercise = this.currentExercise;
		if (!exercise) {
			this.emitAnalyserCommand({ kind: "idle" });
			return;
		}

		this.emitAnalyserCommand({
			kind: "analyse",
			exercise,
		});
	}

	private emitProgress() {
		this.config.onProgress?.({
			currentIndex: this.currentExercise ? this.currentIndex : 0,
			done: this.currentExercise == null,
		});
	}

	private async runVlmCycle() {
		try {
			const ready = await this.readyPromise;
			if (!ready) {
				console.debug(
					"[SessionPhaseController] VLM init not ready, skipping cycle",
				);
				return;
			}
			if (this.config.signal.aborted) {
				return;
			}
			if (!this.config.getSessionInProgress()) {
				return;
			}

			const video = this.config.getVideo();
			if (!this.canCaptureVideo(video)) {
				console.debug(
					"[SessionPhaseController] cannot capture video, skipping VLM frame",
				);
				return;
			}

			this.captureContext.drawImage(
				video,
				0,
				0,
				this.vlmCaptureSize,
				this.vlmCaptureSize,
			);
			const bitmap = await createImageBitmap(this.captureContext.canvas);
			try {
				const result = await this.config.vlm.run(bitmap);
				if (!result) {
					console.debug(
						"[SessionPhaseController] VLM dropped result (inference busy?)",
					);
					return;
				}

				this.config.onVlmResult?.(result);
				console.debug(
					"[SessionPhaseController] VLM",
					result.label,
					"confidence",
					result.confidence,
				);
				if (result.label === "unknown") {
					return;
				}

				const exercising = this.config.mapVlmToUserExercising(result);
				this.config.onUserExercisingChange?.(exercising);
				console.debug(
					"[SessionPhaseController] userExercising",
					exercising,
					"->",
					exercising ? "analyse" : "idle",
				);
				if (exercising) {
					this.emitAnalyseCommand();
				} else {
					this.emitAnalyserCommand({ kind: "idle" });
				}
			} finally {
				bitmap.close();
			}
		} catch (error) {
			this.reportError(error);
		}
	}

	async dispose() {
		if (this.disposed) {
			return;
		}
		this.disposed = true;
		console.debug("[SessionPhaseController] dispose");

		if (this.intervalId) {
			clearInterval(this.intervalId);
			this.intervalId = null;
		}

		await this.config.vlm.dispose();
	}

	private canCaptureVideo(
		video: HTMLVideoElement | null,
	): video is HTMLVideoElement {
		return (
			video != null &&
			video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA &&
			video.videoWidth > 0 &&
			video.videoHeight > 0
		);
	}
}
