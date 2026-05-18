export type SessionExerciseType = 'strength' | 'cardio' | 'flexibility' | 'warm_up';

export interface SessionExercise {
	id: string;
	name: string;
	type: SessionExerciseType;
	measurement: 'reps' | 'duration';
	/** When set, matches a curated exercise for server-side pipelines (squat, deadlift, …). Omitted for fully custom rows. */
	exercise_key?: string;
	target_reps?: number;
	target_duration?: number;
	/** Planned load for the block (kg); shown with targets; sets may still override per log. */
	target_weight_kg?: number;
	/** Planned set count goal; omit when unset (no preset rows). */
	target_sets?: number;
	rest_seconds: number;
	order_index: number;
	/** Coaching / reminder text for this exercise block */
	notes?: string;
	sets?: ExerciseSet[];
}

export function exerciseTypeLabel(type: SessionExercise['type']): string {
	switch (type) {
		case 'strength':
			return 'Strength';
		case 'cardio':
			return 'Cardio';
		case 'flexibility':
			return 'Flexibility';
		case 'warm_up':
			return 'Warm up';
		default:
			return String(type);
	}
}

export interface PoseChartPoint {
	frame: number;
	timestampSec: number;
	insideKnee: number;
	outsideHip: number;
}

/** Persisted with set rows (split storage / embedded); aligns with backend VideoMetadata. */
export interface ExerciseSetVideoMetadata {
	camera_view: string;
	duration_sec?: number;
	video_width?: number;
	video_height?: number;
	fps?: number;
	total_frames?: number;
}

export interface ExerciseSet {
	id: string;
	set_number: number;
	actual_reps?: number;
	actual_duration?: number;
	weight_kg?: number;
	rpe?: number;
	video_url?: string;
	video_metadata?: ExerciseSetVideoMetadata;
	pose_chart_data?: PoseChartPoint[];
	video_play_url?: string;
	status: 'pending' | 'completed' | 'processing';
	notes?: string;
}

export interface AnalysisResult {
	id: string;
	overall_score: number;
	rep_count_detected: number;
	processing_status: 'pending' | 'processing' | 'completed' | 'failed';
	started_at?: string;
	completed_at?: string;
}

export interface Session {
	id: string;
	client_id: string;
	trainer_id: string;
	status: 'scheduled' | 'in-progress' | 'completed' | 'cancelled';
	scheduled_at: string;
	notes?: string;
	started_at?: string;
	completed_at?: string;
	created_at: string;
	updated_at: string;
	exercises: SessionExercise[];
	client_name?: string;
}

export interface ListSessionsResponse {
	sessions: Session[];
	total: number;
}

export interface ListSessionsParams {
	client?: string;
	from?: string;
	to?: string;
	status?: string;
	limit?: number;
	offset?: number;
	includePoseChartData?: boolean;
	includeVideoPlayUrl?: boolean;
}

export async function listSessions(params?: ListSessionsParams): Promise<ListSessionsResponse> {
	const searchParams = new URLSearchParams();
	if (params?.client) searchParams.set('client', params.client);
	if (params?.from) searchParams.set('from', params.from);
	if (params?.to) searchParams.set('to', params.to);
	if (params?.status) searchParams.set('status', params.status);
	searchParams.set('limit', String(params?.limit ?? 20));
	searchParams.set('offset', String(params?.offset ?? 0));
	if (params?.includePoseChartData !== undefined) {
		searchParams.set('includePoseChartData', String(params.includePoseChartData));
	}
	if (params?.includeVideoPlayUrl !== undefined) {
		searchParams.set('includeVideoPlayUrl', String(params.includeVideoPlayUrl));
	}

	const response = await fetch(`/api/sessions?${searchParams}`);
	if (!response.ok) {
		throw new Error(`Failed to list sessions: ${response.statusText}`);
	}
	return response.json();
}

export async function getSession(
	id: string,
	fetchFn: typeof fetch = fetch,
	options?: {
		includePoseChartData?: boolean;
		includeVideoPlayUrl?: boolean;
	}
): Promise<Session> {
	const searchParams = new URLSearchParams();
	if (options?.includePoseChartData !== undefined) {
		searchParams.set('includePoseChartData', String(options.includePoseChartData));
	}
	if (options?.includeVideoPlayUrl !== undefined) {
		searchParams.set('includeVideoPlayUrl', String(options.includeVideoPlayUrl));
	}

	const queryString = searchParams.toString();
	const response = await fetchFn(`/api/sessions/${id}${queryString ? `?${queryString}` : ''}`);
	if (!response.ok) {
		throw new Error(`Failed to get session: ${response.statusText}`);
	}
	return response.json();
}

export async function createSession(data: {
	client_id: string;
	scheduled_at: string;
	notes?: string;
	exercises: Omit<SessionExercise, 'id'>[];
}): Promise<Session> {
	const response = await fetch('/api/sessions', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		const error = await response.text();
		throw new Error(`Failed to create session: ${error}`);
	}
	return response.json();
}

export async function addSessionExercise(
	sessionId: string,
	data: {
		name: string;
		type: SessionExercise['type'];
		measurement: SessionExercise['measurement'];
		exercise_key?: string;
		target_reps?: number;
		target_duration?: number;
		target_weight_kg?: number;
		target_sets?: number;
		rest_seconds: number;
		notes?: string;
	}
): Promise<Session> {
	const response = await fetch(`/api/sessions/${sessionId}/exercises`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		const detail = await response.text();
		throw new Error(detail || `Failed to add exercise: ${response.statusText}`);
	}
	return response.json();
}

export async function deleteSessionExercise(sessionId: string, exerciseId: string): Promise<Session> {
	const response = await fetch(`/api/sessions/${sessionId}/exercises/${exerciseId}`, {
		method: 'DELETE'
	});
	if (!response.ok) {
		const detail = await response.text();
		throw new Error(detail || `Failed to remove exercise: ${response.statusText}`);
	}
	return response.json();
}

/** Set or clear exercise coaching notes (`null` clears on server). */
export async function updateSessionExerciseNotes(
	sessionId: string,
	exerciseId: string,
	notes: string | null
): Promise<Session> {
	const response = await fetch(`/api/sessions/${sessionId}/exercises/${exerciseId}`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ notes })
	});
	if (!response.ok) {
		const detail = await response.text();
		throw new Error(detail || `Failed to update exercise: ${response.statusText}`);
	}
	return response.json();
}

export async function updateSession(
	id: string,
	data: { scheduled_at?: string; notes?: string }
): Promise<Session> {
	const response = await fetch(`/api/sessions/${id}`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		throw new Error(`Failed to update session: ${response.statusText}`);
	}
	return response.json();
}

export async function deleteSession(id: string): Promise<void> {
	const response = await fetch(`/api/sessions/${id}`, {
		method: 'DELETE'
	});
	if (!response.ok) {
		throw new Error(`Failed to delete session: ${response.statusText}`);
	}
}

export async function startSession(id: string): Promise<Session> {
	const response = await fetch(`/api/sessions/${id}/start`, {
		method: 'POST'
	});
	if (!response.ok) {
		throw new Error(`Failed to start session: ${response.statusText}`);
	}
	return response.json();
}

export async function completeSession(id: string): Promise<Session> {
	const response = await fetch(`/api/sessions/${id}/complete`, {
		method: 'POST'
	});
	if (!response.ok) {
		throw new Error(`Failed to complete session: ${response.statusText}`);
	}
	return response.json();
}

// Set Management API

export async function addSet(sessionId: string, exerciseId: string): Promise<Session> {
	const response = await fetch(`/api/sessions/${sessionId}/exercises/${exerciseId}/sets`, {
		method: 'POST'
	});
	if (!response.ok) {
		throw new Error(`Failed to add set: ${response.statusText}`);
	}
	return response.json();
}

export async function recordSet(
	sessionId: string,
	exerciseId: string,
	setId: string,
	data: {
		actual_reps?: number;
		actual_duration?: number;
		weight_kg?: number;
		rpe?: number;
		video_url?: string;
		video_metadata?: ExerciseSetVideoMetadata;
		pose_chart_data?: PoseChartPoint[];
		status?: 'pending' | 'completed' | 'processing';
		notes?: string;
	}
): Promise<Session> {
	const response = await fetch(`/api/sessions/${sessionId}/exercises/${exerciseId}/sets/${setId}`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		throw new Error(`Failed to record set: ${response.statusText}`);
	}
	return response.json();
}

export async function deleteSet(
	sessionId: string,
	exerciseId: string,
	setId: string
): Promise<Session> {
	const response = await fetch(`/api/sessions/${sessionId}/exercises/${exerciseId}/sets/${setId}`, {
		method: 'DELETE'
	});
	if (!response.ok) {
		throw new Error(`Failed to delete set: ${response.statusText}`);
	}
	return response.json();
}
