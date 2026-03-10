import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import {
	getSessionById,
	addSetToExercise,
	type SessionDoc
} from '$lib/services/mongo';
import { ObjectId } from 'mongodb';

const IdParamSchema = z.object({
	id: z.string().refine(val => ObjectId.isValid(val), {
		message: 'Invalid session ID'
	}),
	exerciseId: z.string().refine(val => ObjectId.isValid(val), {
		message: 'Invalid exercise ID'
	})
});

function serializeSession(session: { _id: ObjectId } & SessionDoc) {
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
		exercises: session.exercises.map(ex => ({
			id: ex._id?.toString(),
			name: ex.name,
			type: ex.type,
			measurement: ex.measurement,
			target_reps: ex.target_reps,
			target_duration: ex.target_duration,
			target_sets: ex.target_sets,
			rest_seconds: ex.rest_seconds,
			order_index: ex.order_index,
			sets: ex.sets?.map(set => ({
				id: set._id?.toString(),
				set_number: set.set_number,
				actual_reps: set.actual_reps,
				actual_duration: set.actual_duration,
				weight_kg: set.weight_kg,
				rpe: set.rpe,
				video_url: set.video_url,
				status: set.status,
				notes: set.notes
			})) ?? []
		}))
	};
}

export const POST: RequestHandler = async ({ params }) => {
	try {
		const { id, exerciseId } = IdParamSchema.parse(params);

		const existing = await getSessionById(id);
		if (!existing || existing.deleted_at) {
			throw error(404, 'Session not found');
		}

		// Check if exercise exists
		const exercise = existing.exercises.find(ex => ex._id?.toString() === exerciseId);
		if (!exercise) {
			throw error(404, 'Exercise not found in session');
		}

		// Only allow adding sets if session is in-progress or scheduled
		if (existing.status === 'completed' || existing.status === 'cancelled') {
			throw error(400, 'Cannot add sets to a completed or cancelled session');
		}

		const session = await addSetToExercise(id, exerciseId);

		if (!session) {
			throw error(500, 'Failed to add set');
		}

		return json(serializeSession(session));
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (err instanceof Error && 'status' in err) throw err;
		console.error('Failed to add set:', err);
		throw error(500, 'Failed to add set');
	}
};
