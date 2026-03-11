import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getModelDownload } from '$lib/server/storage';

export const GET: RequestHandler = async () => {
	try {
		const model = await getModelDownload();
		return json(model, {
			headers: {
				'cache-control': 'no-store'
			}
		});
	} catch (err) {
		console.error('Failed to sign model download:', err);
		throw error(500, 'Failed to sign model download');
	}
};
