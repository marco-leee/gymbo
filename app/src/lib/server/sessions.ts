import type { ObjectId } from 'mongodb';
import type { SessionDoc } from '$lib/services/mongo';
import { getPresignedPlayUrl } from '$lib/server/storage';
import { objectIdToString } from '$lib/services/object-id';

export type SessionForSerialization = { _id: ObjectId } & SessionDoc;

type SerializeSessionOptions = {
	includePoseChartData?: boolean;
	includeVideoPlayUrl?: boolean;
};

function serializeDate(value: unknown): string | undefined {
	if (value == null) return undefined;
	const date = value instanceof Date ? value : new Date(value as string | number);
	return Number.isNaN(date.getTime()) ? undefined : date.toISOString();
}

export async function serializeSession(
	session: SessionForSerialization,
	options: SerializeSessionOptions = {}
) {
	const includePoseChartData = options.includePoseChartData ?? true;
	const includeVideoPlayUrl = options.includeVideoPlayUrl ?? true;
	const exercisesSource = Array.isArray(session.exercises) ? session.exercises : [];
	const exercises = await Promise.all(
		exercisesSource.map(async (ex) => ({
			id: ex._id?.toString(),
			name: ex.name,
			type: ex.type,
			measurement: ex.measurement,
			target_reps: ex.target_reps,
			target_duration: ex.target_duration,
			target_sets: ex.target_sets,
			rest_seconds: ex.rest_seconds,
			order_index: ex.order_index,
			notes: ex.notes,
			exercise_key: ex.exercise_key,
			target_weight_kg: ex.target_weight_kg,
			sets: await Promise.all(
				(Array.isArray(ex.sets) ? ex.sets : []).map(async (set) => {
					const setObj: {
						id: string | undefined;
						set_number: number;
						actual_reps?: number;
						actual_duration?: number;
						weight_kg?: number;
						rpe?: number;
						video_url?: string;
						processed_video_url?: string;
						video_metadata?: Record<string, unknown>;
						pose_chart_data?: import('$lib/pose/pose-chart-types').PoseChartPoint[];
						video_play_url?: string;
						processed_video_play_url?: string;
						status: string;
						notes?: string;
					} = {
						id: set._id?.toString(),
						set_number: set.set_number,
						actual_reps: set.actual_reps,
						actual_duration: set.actual_duration,
						weight_kg: set.weight_kg,
						rpe: set.rpe,
						video_url: set.video_url,
						processed_video_url: set.processed_video_url,
						status: set.status,
						notes: set.notes
					};
					if (set.video_metadata != null && typeof set.video_metadata === 'object') {
						setObj.video_metadata = set.video_metadata as Record<string, unknown>;
					}
					if (includePoseChartData) {
						setObj.pose_chart_data = set.pose_chart_data;
					}
					if (includeVideoPlayUrl && set.video_url) {
						if (/^https?:\/\//i.test(set.video_url)) {
							setObj.video_play_url = set.video_url;
						} else {
							try {
								setObj.video_play_url = await getPresignedPlayUrl(set.video_url);
							} catch {
								// omit video_play_url on error
							}
						}
					}
					if (includeVideoPlayUrl && set.processed_video_url) {
						if (/^https?:\/\//i.test(set.processed_video_url)) {
							setObj.processed_video_play_url = set.processed_video_url;
						} else {
							try {
								setObj.processed_video_play_url = await getPresignedPlayUrl(
									set.processed_video_url
								);
							} catch {
								// omit processed_video_play_url on error
							}
						}
					}
					return setObj;
				})
			)
		}))
	);

	return {
		id: session._id.toString(),
		client_id: objectIdToString(session.client_id),
		trainer_id: objectIdToString(session.trainer_id),
		status: session.status,
		scheduled_at: serializeDate(session.scheduled_at) ?? new Date(0).toISOString(),
		notes: session.notes,
		started_at: serializeDate(session.started_at),
		completed_at: serializeDate(session.completed_at),
		created_at: serializeDate(session.created_at) ?? new Date(0).toISOString(),
		updated_at: serializeDate(session.updated_at) ?? new Date(0).toISOString(),
		exercises
	};
}
