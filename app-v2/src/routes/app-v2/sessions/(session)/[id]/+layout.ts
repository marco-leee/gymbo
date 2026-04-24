import type { LayoutLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { getSession, type Session } from '$lib/api/sessions';
import { getClient, type Client } from '$lib/api/clients';

export interface AppV2SessionLayoutData {
	session: Session;
	client: Client | null;
}

const VIEWS = ['session', 'analysis'] as const;

export const load: LayoutLoad = async ({ params, url, fetch }): Promise<AppV2SessionLayoutData> => {
	const raw = url.searchParams.get('view');
	let view = raw;

	if (!view || (!VIEWS.includes(view as (typeof VIEWS)[number]) && view !== 'overview' && view !== 'plan')) {
		redirect(302, `/app-v2/sessions/${params.id}?view=session`);
	}

	if (view === 'overview' || view === 'plan') {
		redirect(302, `/app-v2/sessions/${params.id}?view=session`);
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
