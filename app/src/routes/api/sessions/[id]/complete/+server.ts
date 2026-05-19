import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import { completeSession } from '$lib/services/mongo';
import { ObjectId } from 'mongodb';
import { serializeSession } from '$lib/server/sessions';
import { assertSessionOwned, getTrainerId, requireTrainer } from '$lib/server/trainer-auth';

const IdParamSchema = z.string().refine(val => ObjectId.isValid(val), {
	message: 'Invalid session ID'
});

export const POST: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const id = IdParamSchema.parse(event.params.id);

		const existing = await assertSessionOwned(getTrainerId(event), id);

		if (existing.status !== 'in-progress') {
			throw error(400, `Cannot complete a session with status: ${existing.status}. Session must be in-progress.`);
		}

		const session = await completeSession(id);

		if (!session) {
			throw error(500, 'Failed to complete session');
		}

		return json(await serializeSession(session));
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (isHttpError(err)) throw err;
		console.error('Failed to complete session:', err);
		throw error(500, 'Failed to complete session');
	}
};
