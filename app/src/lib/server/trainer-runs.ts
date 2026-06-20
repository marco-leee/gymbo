import { getDb } from '$lib/services/mongo';
import { v4 as uuidv4 } from 'uuid';

const COLLECTION = 'coached_exercise_runs';
const COACHING_EVENTS = 'coaching_events';
const SAFETY_EVENTS = 'safety_events';

export type ExerciseRunConfig = {
	planned_sets: number;
	target_reps_per_set: number;
	rest_duration_sec: number;
	rest_needed: boolean;
	frame_sample_rate_fps: number;
	voice_repeat_threshold: number;
	exercise_type: string;
};

export type CoachedExerciseRunDoc = {
	_id: string;
	gymbo_session_id: string;
	session_exercise_id: string;
	trainer_id: string;
	client_id: string;
	exercise_type: string;
	status: string;
	config: ExerciseRunConfig;
	merged_observation_state: {
		completed_reps: number;
		total_session_reps: number;
		rep_phase: string;
		in_rep: boolean;
		active_issues: string[];
		recurring_issues: Record<string, number>;
	};
	current_set_number: number;
	completed_sets: number;
	voice_repeat_state: { last_voiced_issue: string | null; repeat_count: number; threshold: number };
	phase: string;
	started_at: Date | null;
	ended_at: Date | null;
	exercise_feedback: string | null;
	created_at: Date;
	updated_at: Date;
};

function defaultConfig(exerciseType: string): ExerciseRunConfig {
	return {
		planned_sets: 3,
		target_reps_per_set: 10,
		rest_duration_sec: 60,
		rest_needed: true,
		frame_sample_rate_fps: 1,
		voice_repeat_threshold: 3,
		exercise_type: exerciseType
	};
}

export function deriveConfigFromSessionExercise(exercise: {
	exercise_key?: string;
	target_sets?: number;
	target_reps?: number;
	rest_seconds?: number;
}): ExerciseRunConfig {
	return {
		planned_sets: exercise.target_sets ?? 3,
		target_reps_per_set: exercise.target_reps ?? 10,
		rest_duration_sec: exercise.rest_seconds ?? 60,
		rest_needed: (exercise.rest_seconds ?? 60) > 0,
		frame_sample_rate_fps: 1,
		voice_repeat_threshold: 3,
		exercise_type: exercise.exercise_key ?? 'overhead_squat'
	};
}

export async function createCoachedExerciseRun(input: {
	gymboSessionId: string;
	sessionExerciseId: string;
	trainerId: string;
	clientId: string;
	exerciseType: string;
	config: ExerciseRunConfig;
}): Promise<CoachedExerciseRunDoc> {
	const db = await getDb();
	const now = new Date();
	const runId = uuidv4();
	const doc: CoachedExerciseRunDoc = {
		_id: runId,
		gymbo_session_id: input.gymboSessionId,
		session_exercise_id: input.sessionExerciseId,
		trainer_id: input.trainerId,
		client_id: input.clientId,
		exercise_type: input.exerciseType,
		status: 'created',
		config: input.config,
		merged_observation_state: {
			completed_reps: 0,
			total_session_reps: 0,
			rep_phase: 'setup',
			in_rep: false,
			active_issues: [],
			recurring_issues: {}
		},
		current_set_number: 1,
		completed_sets: 0,
		voice_repeat_state: { last_voiced_issue: null, repeat_count: 0, threshold: input.config.voice_repeat_threshold },
		phase: 'prepare',
		started_at: null,
		ended_at: null,
		exercise_feedback: null,
		created_at: now,
		updated_at: now
	};
	await db.collection(COLLECTION).insertOne(doc as Record<string, unknown>);
	return doc;
}

export async function getCoachedExerciseRun(runId: string): Promise<CoachedExerciseRunDoc | null> {
	const db = await getDb();
	return db.collection<CoachedExerciseRunDoc>(COLLECTION).findOne({ _id: runId });
}

export async function findActiveRunForExercise(
	gymboSessionId: string,
	sessionExerciseId: string
): Promise<CoachedExerciseRunDoc | null> {
	const db = await getDb();
	return db.collection<CoachedExerciseRunDoc>(COLLECTION).findOne({
		gymbo_session_id: gymboSessionId,
		session_exercise_id: sessionExerciseId,
		status: { $nin: ['ended'] }
	});
}

export async function updateCoachedExerciseRun(
	runId: string,
	patch: Partial<CoachedExerciseRunDoc>
): Promise<CoachedExerciseRunDoc | null> {
	const db = await getDb();
	await db.collection(COLLECTION).updateOne(
		{ _id: runId } as Record<string, unknown>,
		{ $set: { ...patch, updated_at: new Date() } }
	);
	return getCoachedExerciseRun(runId);
}

export async function listCoachingEvents(runId: string, limit = 50, offset = 0) {
	const db = await getDb();
	const coll = db.collection(COACHING_EVENTS);
	const total = await coll.countDocuments({ run_id: runId });
	const events = await coll
		.find({ run_id: runId })
		.sort({ timestamp: 1 })
		.skip(offset)
		.limit(limit)
		.toArray();
	return { events, total };
}

export async function listSafetyEvents(runId: string) {
	const db = await getDb();
	return db.collection(SAFETY_EVENTS).find({ run_id: runId }).sort({ timestamp: 1 }).toArray();
}

export function serializeRun(doc: CoachedExerciseRunDoc) {
	return {
		run_id: doc._id,
		gymbo_session_id: doc.gymbo_session_id,
		session_exercise_id: doc.session_exercise_id,
		status: doc.status,
		exercise_type: doc.exercise_type,
		config: doc.config,
		current_set_number: doc.current_set_number,
		completed_sets: doc.completed_sets,
		merged_observation_state: doc.merged_observation_state,
		started_at: doc.started_at?.toISOString() ?? null,
		ended_at: doc.ended_at?.toISOString() ?? null,
		exercise_feedback: doc.exercise_feedback
	};
}

export { defaultConfig };
