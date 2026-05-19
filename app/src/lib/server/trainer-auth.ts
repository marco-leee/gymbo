import { error, type RequestEvent } from '@sveltejs/kit';
import type { AuthSession } from '$lib/auth';
import { getClientById } from '$lib/services/models/client';
import { trainerObjectId } from '$lib/services/models/trainer';
import { getSessionById } from '$lib/services/mongo';
import { objectIdsEqual } from '$lib/services/object-id';
import type { Filter } from 'mongodb';
import type { ClientDoc } from '$lib/services/models/client';
import type { StoredSessionDoc } from '$lib/services/mongo';

export type TrainerUser = NonNullable<AuthSession['user']>;

export function requireTrainer(event: RequestEvent): TrainerUser {
	const user = event.locals.user;
	if (!user) {
		error(401, 'Unauthorized');
	}
	return user;
}

export function getTrainerId(event: RequestEvent): string {
	const trainerId = event.locals.trainerId;
	if (!trainerId) {
		error(401, 'Unauthorized');
	}
	return trainerId;
}

export function trainerClientFilter(trainerIdHex: string): Filter<ClientDoc> {
	return { deleted_at: null, trainer_id: trainerObjectId(trainerIdHex) };
}

export function trainerSessionFilter(
	trainerIdHex: string,
	extra: Filter<StoredSessionDoc> = {}
): Filter<StoredSessionDoc> {
	return { deleted_at: null, trainer_id: trainerObjectId(trainerIdHex), ...extra };
}

export async function assertClientOwned(trainerIdHex: string, clientIdHex: string) {
	const client = await getClientById(clientIdHex);
	if (!client || client.deleted_at || !objectIdsEqual(client.trainer_id, trainerIdHex)) {
		error(404, 'Client not found');
	}
	return client;
}

export async function assertSessionOwned(trainerIdHex: string, sessionIdHex: string) {
	const session = await getSessionById(sessionIdHex);
	if (!session || session.deleted_at || !objectIdsEqual(session.trainer_id, trainerIdHex)) {
		error(404, 'Session not found');
	}
	return session;
}

/** Extract session id from R2 key `session/{sessionId}/...` */
export function parseSessionIdFromMediaKey(key: string): string | null {
	const match = /^session\/([^/]+)\//.exec(key);
	return match?.[1] ?? null;
}
