import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getPresignedPlayUrl } from '$lib/server/storage';

export const GET: RequestHandler = async ({ url }) => {
	try {
		const key = url.searchParams.get('key');
		if (!key) {
			throw error(400, 'Missing media key');
		}

		const play_url = await getPresignedPlayUrl(key);
		return json({ play_url });
	} catch (err) {
		if (err instanceof Error && 'status' in err) throw err;
		console.error('Failed to sign media playback:', err);
		throw error(500, 'Failed to sign media playback');
	}
};
