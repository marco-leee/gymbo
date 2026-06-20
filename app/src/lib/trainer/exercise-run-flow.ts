import { TrainerClient } from './trainer-client';
import { FrameLoop } from './frame-loop';

export type SessionExercisePlan = {
	id: string;
	exercise_key: string;
	target_sets: number;
	target_reps: number;
	rest_seconds: number;
	name?: string;
};

export type ExerciseRunFlowOptions = {
	sessionId: string;
	clientId: string;
	wsUrl: string;
	exercises: SessionExercisePlan[];
	onStateChange?: (state: unknown) => void;
	onEmergency?: (payload: { description: string; source: string }) => void;
};

export class ExerciseRunFlow {
	private currentIndex = 0;
	private client: TrainerClient | null = null;
	private frameLoop = new FrameLoop();
	private completedExerciseIds: string[] = [];

	constructor(private options: ExerciseRunFlowOptions) {}

	get currentExercise(): SessionExercisePlan | undefined {
		return this.options.exercises[this.currentIndex];
	}

	get completedExercises(): string[] {
		return [...this.completedExerciseIds];
	}

	async startCurrentExercise(): Promise<{ runId: string } | null> {
		const exercise = this.currentExercise;
		if (!exercise) return null;

		const res = await fetch('/api/trainer/exercise-runs', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				gymbo_session_id: this.options.sessionId,
				session_exercise_id: exercise.id
			})
		});
		if (!res.ok) throw new Error('Failed to create exercise run');
		const { run_id: runId } = await res.json();

		const startRes = await fetch(`/api/trainer/exercise-runs/${runId}/start`, { method: 'POST' });
		if (!startRes.ok) throw new Error('Failed to start exercise run');

		this.client = new TrainerClient({
			wsUrl: this.options.wsUrl,
			runId,
			gymboSessionId: this.options.sessionId,
			sessionExerciseId: exercise.id,
			clientId: this.options.clientId,
			exerciseType: exercise.exercise_key,
			onState: (state) => this.options.onStateChange?.(state),
			onEmergency: (payload) => this.options.onEmergency?.(payload)
		});
		this.client.connect();
		return { runId };
	}

	startCamera(video: HTMLVideoElement, canvas: HTMLCanvasElement, fps = 1): void {
		if (!this.client) return;
		this.frameLoop.start({
			video,
			canvas,
			fps,
			onFrame: ({ jpegBase64, seq, timestampSec }) => {
				this.client?.sendFrame({
					jpegBase64,
					seq,
					timestampSec,
					width: canvas.width,
					height: canvas.height
				});
			}
		});
	}

	stopCamera(): void {
		this.frameLoop.stop();
	}

	async endCurrentRun(): Promise<void> {
		this.stopCamera();
		if (this.client) {
			this.client.sendControl('end');
			this.client.disconnect();
			this.client = null;
		}
		const exercise = this.currentExercise;
		if (exercise) {
			this.completedExerciseIds.push(exercise.id);
		}
	}

	async advanceToNextExercise(): Promise<boolean> {
		await this.endCurrentRun();
		if (this.currentIndex + 1 >= this.options.exercises.length) {
			return false;
		}
		this.currentIndex += 1;
		return true;
	}

	resume(): void {
		this.client?.sendControl('resume');
	}

	sendEmergencyAck(): void {
		this.client?.sendControl('emergency_ack');
	}
}
