import type { LayoutLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { getSession, type Session } from '$lib/api/sessions';
import { getClient, type Client } from '$lib/api/clients';

export interface SessionV2LayoutData {
	session: Session;
	client: Client | null;
}

const VIEWS = ['overview', 'plan', 'analysis'] as const;

export const load: LayoutLoad = async ({ params, url, fetch }): Promise<SessionV2LayoutData> => {
	const view = url.searchParams.get('view');
	if (!view || !VIEWS.includes(view as (typeof VIEWS)[number])) {
		redirect(302, `/app/sessions/v2/${params.id}?view=overview`);
	}

	const session = await getSession(params.id, fetch, {
		includePoseChartData: true,
		includeVideoPlayUrl: false
	});

	let client: Client | null = null;
	try {
		client = await getClient(session.client_id, fetch);
	} catch {
		client = null;
	}

	return { session, client };
};
