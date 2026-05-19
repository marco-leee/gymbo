import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getPresignedPlayUrl } from '$lib/server/storage';
import {
	assertSessionOwned,
	getTrainerId,
	parseSessionIdFromMediaKey,
	requireTrainer
} from '$lib/server/trainer-auth';

export const GET: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const trainerId = getTrainerId(event);

		const key = event.url.searchParams.get('key');
		if (!key) {
			throw error(400, 'Missing media key');
		}

		const sessionId = parseSessionIdFromMediaKey(key);
		if (!sessionId) {
			throw error(400, 'Invalid media key');
		}
		await assertSessionOwned(trainerId, sessionId);

		const play_url = await getPresignedPlayUrl(key);
		return json({ play_url });
	} catch (err) {
		if (isHttpError(err)) throw err;
		console.error('Failed to sign media playback:', err);
		throw error(500, 'Failed to sign media playback');
	}
};
