import type { PageLoad } from './$types';
import { getSession, type Session } from '$lib/api/sessions';

export interface LiveCoachingPageData {
	session: Session;
	trainerWsUrl: string;
}

export const load: PageLoad = async ({ params, fetch }): Promise<LiveCoachingPageData> => {
	const session = await getSession(params.id, fetch, { includeVideoPlayUrl: false });
	const trainerWsUrl =
		typeof import.meta !== 'undefined' && import.meta.env?.VITE_TRAINER_WS_URL
			? String(import.meta.env.VITE_TRAINER_WS_URL)
			: 'http://localhost:10001';
	return { session, trainerWsUrl };
};
