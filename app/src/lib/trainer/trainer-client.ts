import { io, type Socket } from 'socket.io-client';
import { VoicePlaybackQueue } from './voice-playback';

export type TrainerState = {
	runId: string;
	status: string;
	phase: string;
	currentSet?: {
		set_number: number;
		target_reps: number;
		completed_reps: number;
	};
	merged_state?: {
		rep_phase: string;
		in_rep: boolean;
		active_issues: string[];
		completed_reps: number;
	};
};

export type TrainerClientOptions = {
	wsUrl: string;
	runId: string;
	gymboSessionId: string;
	sessionExerciseId: string;
	clientId: string;
	exerciseType?: string;
	onState?: (state: TrainerState) => void;
	onPhaseMessage?: (payload: { phase: string; message: string; metadata?: Record<string, unknown> }) => void;
	onEmergency?: (payload: { description: string; source: string }) => void;
	onConnectionChange?: (connected: boolean) => void;
};

export class TrainerClient {
	private socket: Socket | null = null;
	private pingTimer: ReturnType<typeof setInterval> | null = null;
	private missedPongs = 0;
	readonly voiceQueue = new VoicePlaybackQueue();

	constructor(private options: TrainerClientOptions) {}

	connect(): void {
		this.socket = io(`${this.options.wsUrl}/trainer`, {
			transports: ['websocket'],
			withCredentials: true
		});

		this.socket.on('connect', () => {
			this.missedPongs = 0;
			this.options.onConnectionChange?.(true);
			this.register();
			this.startPing();
		});

		this.socket.on('disconnect', () => {
			this.options.onConnectionChange?.(false);
			this.stopPing();
		});

		this.socket.on('trainer:state', (data: Record<string, unknown>) => {
			this.options.onState?.({
				runId: String(data.run_id ?? ''),
				status: String(data.status ?? ''),
				phase: String(data.phase ?? ''),
				currentSet: data.current_set as TrainerState['currentSet'],
				merged_state: data.merged_state as TrainerState['merged_state']
			});
		});

		this.socket.on('trainer:phase_message', (data) => {
			this.options.onPhaseMessage?.(data);
		});

		this.socket.on('trainer:voice_cue', (data: { cue_id: string; message: string; focus_issue?: string }) => {
			this.voiceQueue.enqueue({
				cueId: data.cue_id,
				message: data.message,
				focusIssue: data.focus_issue
			});
		});

		this.socket.on('trainer:emergency', (data) => {
			this.options.onEmergency?.({ description: data.description, source: data.source });
		});

		this.socket.on('trainer:pong', () => {
			this.missedPongs = 0;
		});

		this.socket.on('trainer:error', (data) => {
			console.error('trainer:error', data);
		});
	}

	private register(): void {
		this.socket?.emit('trainer:register', {
			run_id: this.options.runId,
			gymbo_session_id: this.options.gymboSessionId,
			session_exercise_id: this.options.sessionExerciseId,
			client_id: this.options.clientId,
			exercise_type: this.options.exerciseType ?? 'overhead_squat',
			config: { frame_sample_rate_fps: 1 }
		});
	}

	sendFrame(payload: {
		jpegBase64: string;
		seq: number;
		timestampSec: number;
		width: number;
		height: number;
	}): void {
		this.socket?.emit('trainer:frame', {
			meta: {
				run_id: this.options.runId,
				seq: payload.seq,
				timestamp_sec: payload.timestampSec,
				dimensions: { width: payload.width, height: payload.height, format: 'jpeg' }
			},
			frame: payload.jpegBase64
		});
	}

	sendControl(action: 'resume' | 'end' | 'end_set' | 'end_rest' | 'emergency_ack'): void {
		this.socket?.emit('trainer:control', { run_id: this.options.runId, action });
	}

	disconnect(): void {
		this.socket?.emit('trainer:unregister', { run_id: this.options.runId });
		this.stopPing();
		this.voiceQueue.clear();
		this.socket?.disconnect();
		this.socket = null;
	}

	private startPing(): void {
		this.stopPing();
		this.pingTimer = setInterval(() => {
			if (!this.socket?.connected) return;
			this.socket.emit('trainer:ping', { run_id: this.options.runId });
			this.missedPongs += 1;
			if (this.missedPongs >= 3) {
				this.options.onConnectionChange?.(false);
			}
		}, 15000);
	}

	private stopPing(): void {
		if (this.pingTimer) {
			clearInterval(this.pingTimer);
			this.pingTimer = null;
		}
	}
}
