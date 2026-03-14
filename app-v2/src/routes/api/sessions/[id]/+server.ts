import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import {
	getSessionById,
	updateSession,
	softDeleteSession,
	UpdateSessionSchema
} from '$lib/services/mongo';
import { ObjectId } from 'mongodb';
import { serializeSession } from '$lib/server/sessions';

const IdParamSchema = z.string().refine(val => ObjectId.isValid(val), {
	message: 'Invalid session ID'
});

function parseBooleanParam(value: string | null, fallback: boolean): boolean {
	if (value == null) return fallback;
	return value === '1' || value.toLowerCase() === 'true';
}

export const GET: RequestHandler = async ({ params, url }) => {
	try {
		const id = IdParamSchema.parse(params.id);

		const session = await getSessionById(id);

		if (!session || session.deleted_at) {
			throw error(404, 'Session not found');
		}

		return json(
			await serializeSession(session, {
				includePoseChartData: parseBooleanParam(url.searchParams.get('includePoseChartData'), true),
				includeVideoPlayUrl: parseBooleanParam(url.searchParams.get('includeVideoPlayUrl'), true)
			})
		);
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (isHttpError(err)) throw err;
		console.error('Failed to get session:', err);
		throw error(500, 'Failed to get session');
	}
};

export const PUT: RequestHandler = async ({ params, request }) => {
	try {
		const id = IdParamSchema.parse(params.id);
		const body = await request.json();
		const validated = UpdateSessionSchema.parse(body);

		const existing = await getSessionById(id);
		if (!existing || existing.deleted_at) {
			throw error(404, 'Session not found');
		}

		// Only allow updates if session hasn't started or been completed
		if (existing.status === 'completed' || existing.status === 'cancelled') {
			throw error(400, 'Cannot update a completed or cancelled session');
		}

		// Check if there are any videos uploaded (sets with video_url)
		const hasVideos = existing.exercises.some(ex =>
			ex.sets?.some(set => set.video_url)
		);
		if (hasVideos) {
			throw error(400, 'Cannot update session with uploaded videos');
		}

		const updateData: Parameters<typeof updateSession>[1] = {};
		if (validated.scheduled_at !== undefined) {
			updateData.scheduled_at = new Date(validated.scheduled_at);
		}
		if (validated.notes !== undefined) updateData.notes = validated.notes;

		const updated = await updateSession(id, updateData);

		if (!updated) {
			throw error(500, 'Failed to update session');
		}

		return json(await serializeSession(updated));
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (isHttpError(err)) throw err;
		console.error('Failed to update session:', err);
		throw error(500, 'Failed to update session');
	}
};

export const DELETE: RequestHandler = async ({ params }) => {
	try {
		const id = IdParamSchema.parse(params.id);

		const existing = await getSessionById(id);
		if (!existing || existing.deleted_at) {
			throw error(404, 'Session not found');
		}

		// Check if there are any videos uploaded
		const hasVideos = existing.exercises.some(ex =>
			ex.sets?.some(set => set.video_url)
		);
		if (hasVideos) {
			throw error(400, 'Cannot delete session with uploaded videos');
		}

		const success = await softDeleteSession(id);

		if (!success) {
			throw error(500, 'Failed to delete session');
		}

		return json({ success: true });
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (isHttpError(err)) throw err;
		console.error('Failed to delete session:', err);
		throw error(500, 'Failed to delete session');
	}
};
