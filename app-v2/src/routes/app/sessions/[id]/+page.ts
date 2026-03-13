import type { PageLoad } from './$types';
import { getSession, type Session } from '$lib/api/sessions';
import { getClient, type Client } from '$lib/api/clients';

export interface SessionPageData {
	session: Session;
	client: Client | null;
}

export const load: PageLoad = async ({ params, fetch }): Promise<SessionPageData> => {
	const session = await getSession(params.id, fetch, {
		includePoseChartData: false,
		includeVideoPlayUrl: false
	});

	let client: Client | null = null;
	try {
		client = await getClient(session.client_id, fetch);
	} catch {
		// Client might not exist or be deleted
		client = null;
	}

	return {
		session,
		client
	};
};
