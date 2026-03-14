import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import {
	getSessionById,
	updateSetInExercise,
	deleteSetFromExercise
} from '$lib/services/mongo';
import { ObjectId } from 'mongodb';
import { serializeSession } from '$lib/server/sessions';

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
	pose_chart_data: z.array(z.object({
		frame: z.number().int().nonnegative(),
		timestampSec: z.number().nonnegative(),
		insideKnee: z.number(),
		outsideHip: z.number()
	})).optional(),
	status: z.enum(['pending', 'completed', 'processing']).optional(),
	notes: z.string().optional()
});

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

		return json(await serializeSession(session));
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (isHttpError(err)) throw err;
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

		return json(await serializeSession(session));
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (isHttpError(err)) throw err;
		console.error('Failed to delete set:', err);
		throw error(500, 'Failed to delete set');
	}
};
