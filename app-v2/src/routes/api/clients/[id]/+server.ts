import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import {
	UpdateClientSchema,
	type ClientDoc,
	getClientById,
	updateClient,
	softDeleteClient
} from '$lib/services/models/client';
import { ObjectId } from 'mongodb';

const IdParamSchema = z.string().refine(val => ObjectId.isValid(val), {
	message: 'Invalid client ID'
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

export const GET: RequestHandler = async ({ params }) => {
	try {
		const id = IdParamSchema.parse(params.id);

		const client = await getClientById(id);

		if (!client || client.deleted_at) {
			throw error(404, 'Client not found');
		}

		return json(serializeClient(client));
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (err instanceof Error && 'status' in err) throw err;
		console.error('Failed to get client:', err);
		throw error(500, 'Failed to get client');
	}
};

export const PUT: RequestHandler = async ({ params, request }) => {
	try {
		const id = IdParamSchema.parse(params.id);
		const body = await request.json();
		const validated = UpdateClientSchema.parse(body);

		const existing = await getClientById(id);
		if (!existing || existing.deleted_at) {
			throw error(404, 'Client not found');
		}

		const updateData: Parameters<typeof updateClient>[1] = {};
		if (validated.gender !== undefined) updateData.gender = validated.gender;
		if (validated.height_cm !== undefined) updateData.height_cm = validated.height_cm;
		if (validated.weight_kg !== undefined) updateData.weight_kg = validated.weight_kg;
		if (validated.user) updateData.user = { ...existing.user, ...validated.user };

		const updated = await updateClient(id, updateData);

		if (!updated) {
			throw error(500, 'Failed to update client');
		}

		return json(serializeClient(updated));
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (err instanceof Error && 'status' in err) throw err;
		console.error('Failed to update client:', err);
		throw error(500, 'Failed to update client');
	}
};

export const DELETE: RequestHandler = async ({ params }) => {
	try {
		const id = IdParamSchema.parse(params.id);

		const existing = await getClientById(id);
		if (!existing || existing.deleted_at) {
			throw error(404, 'Client not found');
		}

		const success = await softDeleteClient(id);

		if (!success) {
			throw error(500, 'Failed to delete client');
		}

		return json({ success: true });
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map(e => e.message).join(', '));
		}
		if (err instanceof Error && 'status' in err) throw err;
		console.error('Failed to delete client:', err);
		throw error(500, 'Failed to delete client');
	}
};
