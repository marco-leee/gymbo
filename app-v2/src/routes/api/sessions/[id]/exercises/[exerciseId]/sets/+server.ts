import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import { addSetToExercise } from '$lib/services/mongo';
import { ObjectId } from 'mongodb';
import { serializeSession } from '$lib/server/sessions';
import { isValidObjectIdParam } from '$lib/services/object-id';
import { assertSessionOwned, getTrainerId, requireTrainer } from '$lib/server/trainer-auth';

const IdParamSchema = z.object({
	id: z.string().refine(val => ObjectId.isValid(val), {
		message: 'Invalid session ID'
	}),
	exerciseId: z.string().refine(val => isValidObjectIdParam(val), {
		message: 'Invalid exercise ID'
	})
});

export const POST: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const { id, exerciseId } = IdParamSchema.parse(event.params);

		const existing = await assertSessionOwned(getTrainerId(event), id);

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

		return json(await serializeSession(session));
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (isHttpError(err)) throw err;
		console.error('Failed to add set:', err);
		throw error(500, 'Failed to add set');
	}
};
