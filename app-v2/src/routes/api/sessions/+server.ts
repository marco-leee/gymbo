import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import {
	listSessions,
	createSession,
	CreateSessionSchema,
	type SessionDoc,
	generateUUID
} from '$lib/services/mongo';
import { ObjectId } from 'mongodb';

const ListQuerySchema = z.object({
	client: z.string().optional(),
	from: z.string().datetime().optional(),
	to: z.string().datetime().optional(),
	status: z.enum(['scheduled', 'in-progress', 'completed', 'cancelled']).optional(),
	limit: z.coerce.number().min(1).max(100).default(20),
	offset: z.coerce.number().min(0).default(0)
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

export const GET: RequestHandler = async ({ url }) => {
	try {
		const query = ListQuerySchema.parse({
			client: url.searchParams.get('client') ?? undefined,
			from: url.searchParams.get('from') ?? undefined,
			to: url.searchParams.get('to') ?? undefined,
			status: url.searchParams.get('status') ?? undefined,
			limit: url.searchParams.get('limit') ?? undefined,
			offset: url.searchParams.get('offset') ?? undefined
		});

		const filter: Record<string, unknown> = { deleted_at: null };

		if (query.client) {
			filter['client_id'] = query.client;
		}

		if (query.status) {
			filter['status'] = query.status;
		}

		if (query.from || query.to) {
			filter['scheduled_at'] = {};
			if (query.from) filter['scheduled_at']['$gte'] = new Date(query.from);
			if (query.to) filter['scheduled_at']['$lte'] = new Date(query.to);
		}

		const sessions = await listSessions(filter);
		const total = sessions.length;
		const paginated = sessions.slice(query.offset, query.offset + query.limit);

		return json({
			sessions: paginated.map(serializeSession),
			total
		});
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		console.error('Failed to list sessions:', err);
		throw error(500, 'Failed to list sessions');
	}
};

export const POST: RequestHandler = async ({ request, locals }) => {
	try {
		const body = await request.json();
		const validated = CreateSessionSchema.parse(body);

		// TODO: Get trainer_id from authenticated user context
		// For now, using a placeholder - should come from locals.user.id or similar
		const trainerId = locals?.user?.id ?? generateUUID();

		const now = new Date();
		const sessionData = {
			client_id: validated.client_id,
			trainer_id: trainerId,
			status: 'scheduled' as const,
			scheduled_at: new Date(validated.scheduled_at),
			notes: validated.notes,
			exercises: validated.exercises.map((ex, idx) => ({
				...ex,
				order_index: ex.order_index ?? idx,
				sets: []
			})),
			created_at: now,
			updated_at: now
		};

		const newSession = await createSession(sessionData);

		return json(serializeSession(newSession), { status: 201 });
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		console.error('Failed to create session:', err);
		throw error(500, 'Failed to create session');
	}
};
