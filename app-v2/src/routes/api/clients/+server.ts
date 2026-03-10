import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import {
	listClients,
	createClient,
	CreateClientSchema,
	type ClientDoc,
} from '$lib/services/models/client';
import { generateUUID } from '$lib/services/mongo';
import { ObjectId } from 'mongodb';

const ListQuerySchema = z.object({
	search: z.string().optional().default(''),
	limit: z.coerce.number().min(1).max(100).default(20),
	offset: z.coerce.number().min(0).default(0)
});

function serializeClient(client: { _id: ObjectId } & ClientDoc) {
	return {
		id: client._id.toString(),
		user_id: client.user_id,
		email: client.user.email,
		full_name: client.user.full_name,
		first_name: client.user.first_name,
		last_name: client.user.last_name,
		gender: client.gender,
		height_cm: client.height_cm,
		weight_kg: client.weight_kg,
		created_at: client.created_at,
		updated_at: client.updated_at
	};
}

export const GET: RequestHandler = async ({ url }) => {
	try {
		const query = ListQuerySchema.parse({
			search: url.searchParams.get('search') ?? undefined,
			limit: url.searchParams.get('limit') ?? undefined,
			offset: url.searchParams.get('offset') ?? undefined
		});

		const filter: Record<string, unknown> = { deleted_at: null };

		if (query.search) {
			filter['$or'] = [
				{ 'user.email': { $regex: query.search, $options: 'i' } },
				{ 'user.full_name': { $regex: query.search, $options: 'i' } }
			];
		}

		const clients = await listClients(filter);
		const total = clients.length;
		const paginated = clients.slice(query.offset, query.offset + query.limit);

		console.log(clients)

		return json({
			clients: paginated.map(serializeClient),
			total
		});
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		console.error('Failed to list clients:', err);
		throw error(500, 'Failed to list clients');
	}
};

export const POST: RequestHandler = async ({ request }) => {
	try {
		const body = await request.json();
		const validated = CreateClientSchema.parse(body);

		const now = new Date();
		const clientData: Omit<ClientDoc, 'created_at' | 'updated_at'> = {
			user_id: generateUUID(),
			gender: validated.gender,
			height_cm: validated.height_cm,
			weight_kg: validated.weight_kg,
			user: {
				email: validated.email,
				full_name: validated.full_name,
				first_name: validated.first_name,
				last_name: validated.last_name,
				created_at: now,
				updated_at: now,
				deleted_at: null
			}
		};

		const newClient = await createClient(clientData);

		return json(serializeClient(newClient), { status: 201 });
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (err instanceof Error && err.message.includes('duplicate')) {
			throw error(409, 'Client with this email already exists');
		}
		console.error('Failed to create client:', err);
		throw error(500, 'Failed to create client');
	}
};
