import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import {
	listSessions,
	createSession,
	CreateSessionSchema,
	generateUUID
} from '$lib/services/mongo';
import { serializeSession } from '$lib/server/sessions';

const ListQuerySchema = z.object({
	client: z.string().optional(),
	from: z.string().datetime().optional(),
	to: z.string().datetime().optional(),
	status: z.enum(['scheduled', 'in-progress', 'completed', 'cancelled']).optional(),
	limit: z.coerce.number().min(1).max(100).default(20),
	offset: z.coerce.number().min(0).default(0)
});

function parseBooleanParam(value: string | null, fallback: boolean): boolean {
	if (value == null) return fallback;
	return value === '1' || value.toLowerCase() === 'true';
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
			const range: Record<string, Date> = {};
			if (query.from) range['$gte'] = new Date(query.from);
			if (query.to) range['$lte'] = new Date(query.to);
			filter['scheduled_at'] = range;
		}

		const sessions = await listSessions(filter);
		const total = sessions.length;
		const paginated = sessions.slice(query.offset, query.offset + query.limit);
		const includePoseChartData = parseBooleanParam(url.searchParams.get('includePoseChartData'), true);
		const includeVideoPlayUrl = parseBooleanParam(url.searchParams.get('includeVideoPlayUrl'), true);

		const serializedSessions = await Promise.allSettled(
			paginated.map((s) =>
				serializeSession(s, {
					includePoseChartData,
					includeVideoPlayUrl
				})
			)
		);

		return json({
			sessions: serializedSessions.flatMap((result, index) => {
				if (result.status === 'fulfilled') return [result.value];
				console.error('Failed to serialize session:', paginated[index]?._id?.toString(), result.reason);
				return [];
			}),
			total
		});
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (isHttpError(err)) throw err;
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

		return json(await serializeSession(newSession), { status: 201 });
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (isHttpError(err)) throw err;
		console.error('Failed to create session:', err);
		throw error(500, 'Failed to create session');
	}
};
