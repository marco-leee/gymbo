import type { TrainerState } from './trainer-client';

export class LiveRunState {
	runId = $state<string | null>(null);
	status = $state('idle');
	phase = $state('');
	completedReps = $state(0);
	targetReps = $state(0);
	setNumber = $state(1);
	activeIssues = $state<string[]>([]);
	connected = $state(false);
	emergencyMessage = $state<string | null>(null);
	phaseMessage = $state<string | null>(null);

	applyTrainerState(state: TrainerState): void {
		this.runId = state.runId;
		this.status = state.status;
		this.phase = state.phase;
		if (state.currentSet) {
			this.setNumber = state.currentSet.set_number;
			this.targetReps = state.currentSet.target_reps;
			this.completedReps = state.currentSet.completed_reps;
		}
		if (state.merged_state) {
			this.activeIssues = state.merged_state.active_issues ?? [];
			if (state.merged_state.completed_reps != null) {
				this.completedReps = state.merged_state.completed_reps;
			}
		}
	}

	setConnection(connected: boolean): void {
		this.connected = connected;
	}

	setEmergency(message: string): void {
		this.emergencyMessage = message;
	}

	clearEmergency(): void {
		this.emergencyMessage = null;
	}

	setPhaseMessage(message: string): void {
		this.phaseMessage = message;
	}
}
