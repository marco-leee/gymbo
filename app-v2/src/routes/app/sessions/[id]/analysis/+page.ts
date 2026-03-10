import type { PageLoad } from './$types';
import { getSession, type Session } from '$lib/api/sessions';
import { getClient, type Client } from '$lib/api/clients';

export interface SessionAnalysisPageData {
	session: Session;
	client: Client | null;
}

export const load: PageLoad = async ({ params }): Promise<SessionAnalysisPageData> => {
	const session = await getSession(params.id);
	let client: Client | null = null;
	try {
		client = await getClient(session.client_id);
	} catch {
		client = null;
	}
	return { session, client };
};
