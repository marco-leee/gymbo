import type { ObjectId } from 'mongodb';
import type { SessionDoc } from '$lib/services/mongo';
import { getPresignedPlayUrl } from '$lib/server/storage';

export type SessionForSerialization = { _id: ObjectId } & SessionDoc;

export async function serializeSession(session: SessionForSerialization) {
	const exercises = await Promise.all(
		session.exercises.map(async (ex) => ({
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
				(ex.sets ?? []).map(async (set) => {
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
						pose_chart_data: set.pose_chart_data,
						status: set.status,
						notes: set.notes
					};
					if (set.video_url) {
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
		scheduled_at: session.scheduled_at.toISOString(),
		notes: session.notes,
		started_at: session.started_at?.toISOString(),
		completed_at: session.completed_at?.toISOString(),
		created_at: session.created_at.toISOString(),
		updated_at: session.updated_at.toISOString(),
		exercises
	};
}
