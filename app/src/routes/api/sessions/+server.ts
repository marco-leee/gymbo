import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import { listSessions, createSession, CreateSessionSchema } from '$lib/services/mongo';
import { serializeSession } from '$lib/server/sessions';
import { parseObjectId } from '$lib/services/object-id';
import {
	assertClientOwned,
	getTrainerId,
	requireTrainer,
	trainerSessionFilter
} from '$lib/server/trainer-auth';

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

export const GET: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const trainerId = getTrainerId(event);

		const query = ListQuerySchema.parse({
			client: event.url.searchParams.get('client') ?? undefined,
			from: event.url.searchParams.get('from') ?? undefined,
			to: event.url.searchParams.get('to') ?? undefined,
			status: event.url.searchParams.get('status') ?? undefined,
			limit: event.url.searchParams.get('limit') ?? undefined,
			offset: event.url.searchParams.get('offset') ?? undefined
		});

		if (query.client) {
			await assertClientOwned(trainerId, query.client);
		}

		const filter: Record<string, unknown> = { ...trainerSessionFilter(trainerId) };

		if (query.client) {
			filter['client_id'] = parseObjectId(query.client);
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
		const includePoseChartData = parseBooleanParam(
			event.url.searchParams.get('includePoseChartData'),
			true
		);
		const includeVideoPlayUrl = parseBooleanParam(
			event.url.searchParams.get('includeVideoPlayUrl'),
			true
		);

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

export const POST: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const trainerId = getTrainerId(event);

		const body = await event.request.json();
		const validated = CreateSessionSchema.parse(body);

		await assertClientOwned(trainerId, validated.client_id);

		const now = new Date();
		const sessionData = {
			client_id: parseObjectId(validated.client_id),
			trainer_id: parseObjectId(trainerId),
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
