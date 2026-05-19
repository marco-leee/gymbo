import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import { ObjectId } from 'mongodb';
import {
	getSessionById,
	SessionExercisePayloadSchema,
	addExerciseToSession
} from '$lib/services/mongo';
import { serializeSession } from '$lib/server/sessions';
import { assertSessionOwned, getTrainerId, requireTrainer } from '$lib/server/trainer-auth';

const IdParamSchema = z.string().refine(val => ObjectId.isValid(val), {
	message: 'Invalid session ID'
});

function parseBooleanParam(value: string | null, fallback: boolean): boolean {
	if (value == null) return fallback;
	return value === '1' || value.toLowerCase() === 'true';
}

function sessionHasVideos(s: NonNullable<Awaited<ReturnType<typeof getSessionById>>>): boolean {
	return s.exercises.some(ex => ex.sets?.some(set => set.video_url));
}

export const POST: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const sessionId = IdParamSchema.parse(event.params.id);
		const body = await event.request.json();
		const validated = SessionExercisePayloadSchema.parse(body);

		const existing = await assertSessionOwned(getTrainerId(event), sessionId);

		if (existing.status === 'completed' || existing.status === 'cancelled') {
			throw error(400, 'Cannot update a completed or cancelled session');
		}

		if (sessionHasVideos(existing)) {
			throw error(400, 'Cannot update session with uploaded videos');
		}

		const updated = await addExerciseToSession(sessionId, validated);

		if (!updated) {
			throw error(500, 'Failed to add exercise');
		}

		return json(
			await serializeSession(updated, {
				includePoseChartData: parseBooleanParam(
					event.url.searchParams.get('includePoseChartData'),
					true
				),
				includeVideoPlayUrl: parseBooleanParam(
					event.url.searchParams.get('includeVideoPlayUrl'),
					false
				)
			}),
			{ status: 201 }
		);
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (isHttpError(err)) throw err;
		console.error('Failed to add session exercise:', err);
		throw error(500, 'Failed to add exercise');
	}
};
