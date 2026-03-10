import type { PageLoad } from './$types';
import { getSession, type Session } from '$lib/api/sessions';
import { getClient, type Client } from '$lib/api/clients';

export interface SessionPageData {
	session: Session;
	client: Client | null;
}

export const load: PageLoad = async ({ params }): Promise<SessionPageData> => {
	const session = await getSession(params.id);
	
	let client: Client | null = null;
	try {
		client = await getClient(session.client_id);
	} catch {
		// Client might not exist or be deleted
		client = null;
	}

	return {
		session,
		client
	};
};
