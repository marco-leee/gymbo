import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { env } from '$lib/env';

export const load: PageServerLoad = async ({ locals, url }) => {
	if (locals.user) {
		const redirectTo = url.searchParams.get('redirectTo') || '/app/sessions';
		redirect(303, redirectTo);
	}

	return {
		googleEnabled: Boolean(env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET)
	};
};
