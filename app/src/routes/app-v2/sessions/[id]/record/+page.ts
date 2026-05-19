import type { PageLoad } from './$types';
import { getSession, type Session } from '$lib/api/sessions';
import { getClient, type Client } from '$lib/api/clients';

export interface SessionRecordPageData {
	session: Session;
	client: Client | null;
}

export const load: PageLoad = async ({ params, fetch }): Promise<SessionRecordPageData> => {
	const session = await getSession(params.id, fetch, {
		includeVideoPlayUrl: true,
		includePoseChartData: true,
	});
	let client: Client | null = null;
	try {
		client = await getClient(session.client_id, fetch);
	} catch {
		client = null;
	}
	return { session, client };
};
