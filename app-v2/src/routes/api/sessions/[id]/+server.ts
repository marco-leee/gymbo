import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import {
	getSessionById,
	updateSession,
	softDeleteSession,
	UpdateSessionSchema,
	type SessionDoc
} from '$lib/services/mongo';
import { ObjectId } from 'mongodb';

const IdParamSchema = z.string().refine(val => ObjectId.isValid(val), {
	message: 'Invalid session ID'
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

export const GET: RequestHandler = async ({ params }) => {
	try {
		const id = IdParamSchema.parse(params.id);

		const session = await getSessionById(id);

		if (!session || session.deleted_at) {
			throw error(404, 'Session not found');
		}

		return json(serializeSession(session));
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (err instanceof Error && 'status' in err) throw err;
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

		return json(serializeSession(updated));
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (err instanceof Error && 'status' in err) throw err;
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
		if (err instanceof Error && 'status' in err) throw err;
		console.error('Failed to delete session:', err);
		throw error(500, 'Failed to delete session');
	}
};
