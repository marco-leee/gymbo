import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { env } from '$lib/env';

export const load: PageServerLoad = async ({ locals }) => {
	if (locals.user) {
		redirect(303, '/app-v2/sessions');
	}

	return {
		githubEnabled: Boolean(env.GITHUB_CLIENT_ID && env.GITHUB_CLIENT_SECRET)
	};
};
