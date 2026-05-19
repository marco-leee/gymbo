import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import {
	UpdateClientSchema,
	type ClientDoc,
	updateClient,
	softDeleteClient
} from '$lib/services/models/client';
import { ObjectId } from 'mongodb';
import { assertClientOwned, getTrainerId, requireTrainer } from '$lib/server/trainer-auth';

const IdParamSchema = z.string().refine(val => ObjectId.isValid(val), {
	message: 'Invalid client ID'
});

function serializeClient(client: { _id: ObjectId } & ClientDoc) {
	return {
		id: client._id.toString(),
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

export const GET: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const id = IdParamSchema.parse(event.params.id);

		const client = await assertClientOwned(getTrainerId(event), id);

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

export const PUT: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const trainerId = getTrainerId(event);
		const id = IdParamSchema.parse(event.params.id);
		const body = await event.request.json();
		const validated = UpdateClientSchema.parse(body);

		const existing = await assertClientOwned(trainerId, id);

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

export const DELETE: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const id = IdParamSchema.parse(event.params.id);

		await assertClientOwned(getTrainerId(event), id);

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
