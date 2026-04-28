import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import { ObjectId } from 'mongodb';
import {
	getSessionById,
	UpdateSessionExercisePayloadSchema,
	updateExerciseNotesInSession,
	deleteExerciseFromSession
} from '$lib/services/mongo';
import { serializeSession } from '$lib/server/sessions';

const SessionIdSchema = z.string().refine((val) => ObjectId.isValid(val), {
	message: 'Invalid session ID'
});

const ExerciseIdSchema = z.string().refine((val) => ObjectId.isValid(val), {
	message: 'Invalid exercise ID'
});

function parseBooleanParam(value: string | null, fallback: boolean): boolean {
	if (value == null) return fallback;
	return value === '1' || value.toLowerCase() === 'true';
}

function sessionHasVideos(s: NonNullable<Awaited<ReturnType<typeof getSessionById>>>): boolean {
	return s.exercises.some((ex) => ex.sets?.some((set) => set.video_url));
}

export const PUT: RequestHandler = async ({ params, request, url }) => {
	try {
		const sessionId = SessionIdSchema.parse(params.id);
		const exerciseId = ExerciseIdSchema.parse(params.exerciseId);

		const existing = await getSessionById(sessionId);
		if (!existing || existing.deleted_at) {
			throw error(404, 'Session not found');
		}

		if (existing.status === 'completed' || existing.status === 'cancelled') {
			throw error(400, 'Cannot update a completed or cancelled session');
		}

		if (sessionHasVideos(existing)) {
			throw error(400, 'Cannot update session with uploaded videos');
		}

		const exOid = new ObjectId(exerciseId);
		const hasExercise = existing.exercises.some((ex) => ex._id?.equals(exOid));
		if (!hasExercise) {
			throw error(404, 'Exercise not found');
		}

		const body = await request.json();
		const validated = UpdateSessionExercisePayloadSchema.parse(body);

		const updated = await updateExerciseNotesInSession(sessionId, exerciseId, validated.notes);

		if (!updated) {
			throw error(500, 'Failed to update exercise');
		}

		return json(
			await serializeSession(updated, {
				includePoseChartData: parseBooleanParam(url.searchParams.get('includePoseChartData'), true),
				includeVideoPlayUrl: parseBooleanParam(url.searchParams.get('includeVideoPlayUrl'), false)
			})
		);
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map((e) => e.message).join(', '));
		}
		if (isHttpError(err)) throw err;
		console.error('Failed to update session exercise:', err);
		throw error(500, 'Failed to update exercise');
	}
};

export const DELETE: RequestHandler = async ({ params, url }) => {
	try {
		const sessionId = SessionIdSchema.parse(params.id);
		const exerciseId = ExerciseIdSchema.parse(params.exerciseId);

		const existing = await getSessionById(sessionId);
		if (!existing || existing.deleted_at) {
			throw error(404, 'Session not found');
		}

		if (existing.status === 'completed' || existing.status === 'cancelled') {
			throw error(400, 'Cannot update a completed or cancelled session');
		}

		if (sessionHasVideos(existing)) {
			throw error(400, 'Cannot update session with uploaded videos');
		}

		const outcome = await deleteExerciseFromSession(sessionId, exerciseId);

		if (!outcome.ok) {
			if (outcome.reason === 'sets_not_pending') {
				throw error(
					409,
					'Cannot delete this exercise until every set is still pending'
				);
			}
			throw error(404, 'Exercise not found');
		}

		return json(
			await serializeSession(outcome.session, {
				includePoseChartData: parseBooleanParam(url.searchParams.get('includePoseChartData'), true),
				includeVideoPlayUrl: parseBooleanParam(url.searchParams.get('includeVideoPlayUrl'), false)
			})
		);
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map((e) => e.message).join(', '));
		}
		if (isHttpError(err)) throw err;
		console.error('Failed to delete session exercise:', err);
		throw error(500, 'Failed to delete exercise');
	}
};
