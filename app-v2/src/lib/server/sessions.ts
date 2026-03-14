import type { ObjectId } from 'mongodb';
import type { SessionDoc } from '$lib/services/mongo';
import { getPresignedPlayUrl } from '$lib/server/storage';

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
						pose_chart_data?: {
							frame: number;
							timestampSec: number;
							insideKnee: number;
							outsideHip: number;
						}[];
						video_play_url?: string;
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
						status: set.status,
						notes: set.notes
					};
					if (includePoseChartData) {
						setObj.pose_chart_data = set.pose_chart_data;
					}
					if (includeVideoPlayUrl && set.video_url) {
						try {
							setObj.video_play_url = await getPresignedPlayUrl(set.video_url);
						} catch {
							// omit video_play_url on error
						}
					}
					return setObj;
				})
			)
		}))
	);

	return {
		id: session._id.toString(),
		client_id: session.client_id,
		trainer_id: session.trainer_id,
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
