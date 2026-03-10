import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import {
	getSessionById,
	updateSetInExercise,
	deleteSetFromExercise,
	type SessionDoc
} from '$lib/services/mongo';
import { ObjectId } from 'mongodb';

const IdParamSchema = z.object({
	id: z.string().refine(val => ObjectId.isValid(val), {
		message: 'Invalid session ID'
	}),
	exerciseId: z.string().refine(val => ObjectId.isValid(val), {
		message: 'Invalid exercise ID'
	}),
	setId: z.string().refine(val => ObjectId.isValid(val), {
		message: 'Invalid set ID'
	})
});

const UpdateSetSchema = z.object({
	actual_reps: z.number().int().nonnegative().optional(),
	actual_duration: z.number().int().nonnegative().optional(),
	weight_kg: z.number().nonnegative().optional(),
	rpe: z.number().int().min(1).max(10).optional(),
	video_url: z.string().optional(),
	status: z.enum(['pending', 'completed', 'processing']).optional(),
	notes: z.string().optional()
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

export const PUT: RequestHandler = async ({ params, request }) => {
	try {
		const { id, exerciseId, setId } = IdParamSchema.parse(params);
		const body = await request.json();
		const validated = UpdateSetSchema.parse(body);

		const existing = await getSessionById(id);
		if (!existing || existing.deleted_at) {
			throw error(404, 'Session not found');
		}

		// Check if exercise and set exist
		const exercise = existing.exercises.find(ex => ex._id?.toString() === exerciseId);
		if (!exercise) {
			throw error(404, 'Exercise not found in session');
		}

		const set = exercise.sets?.find(s => s._id?.toString() === setId);
		if (!set) {
			throw error(404, 'Set not found in exercise');
		}

		// Only allow updates if session is not completed or cancelled
		if (existing.status === 'cancelled') {
			throw error(400, 'Cannot update sets in a cancelled session');
		}

		// If video_url is being set and status is pending, change to processing
		const updateData: Parameters<typeof updateSetInExercise>[3] = { ...validated };
		if (validated.video_url && set.status === 'pending') {
			updateData.status = 'processing';
		}

		const session = await updateSetInExercise(id, exerciseId, setId, updateData);

		if (!session) {
			throw error(500, 'Failed to update set');
		}

		return json(serializeSession(session));
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (err instanceof Error && 'status' in err) throw err;
		console.error('Failed to update set:', err);
		throw error(500, 'Failed to update set');
	}
};

export const DELETE: RequestHandler = async ({ params }) => {
	try {
		const { id, exerciseId, setId } = IdParamSchema.parse(params);

		const existing = await getSessionById(id);
		if (!existing || existing.deleted_at) {
			throw error(404, 'Session not found');
		}

		// Check if set exists
		const exercise = existing.exercises.find(ex => ex._id?.toString() === exerciseId);
		if (!exercise) {
			throw error(404, 'Exercise not found in session');
		}

		const set = exercise.sets?.find(s => s._id?.toString() === setId);
		if (!set) {
			throw error(404, 'Set not found in exercise');
		}

		// Only allow deletion if session is not completed or cancelled
		if (existing.status === 'completed' || existing.status === 'cancelled') {
			throw error(400, 'Cannot delete sets from a completed or cancelled session');
		}

		// Cannot delete if video is uploaded
		if (set.video_url) {
			throw error(400, 'Cannot delete a set with uploaded video');
		}

		const session = await deleteSetFromExercise(id, exerciseId, setId);

		if (!session) {
			throw error(500, 'Failed to delete set');
		}

		return json(serializeSession(session));
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (err instanceof Error && 'status' in err) throw err;
		console.error('Failed to delete set:', err);
		throw error(500, 'Failed to delete set');
	}
};
