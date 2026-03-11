import type { PageLoad } from './$types';
import { getSession, type Session } from '$lib/api/sessions';
import { getClient, type Client } from '$lib/api/clients';

export interface SessionEditPageData {
	session: Session;
	client: Client | null;
}

export const load: PageLoad = async ({ params, fetch }): Promise<SessionEditPageData> => {
	const session = await getSession(params.id, fetch);
	let client: Client | null = null;
	try {
		client = await getClient(session.client_id, fetch);
	} catch {
		client = null;
	}
	return { session, client };
};
