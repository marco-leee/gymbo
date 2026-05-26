import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';
import { getTrainerByAuthUserId } from '$lib/services/models/trainer';

export const load: LayoutServerLoad = async ({ locals, url }) => {
	if (!locals.user) {
		redirect(303, `/login?redirectTo=${encodeURIComponent(url.pathname + url.search)}`);
	}

	const trainer = await getTrainerByAuthUserId(locals.user.id);
	const completed = Boolean(trainer?.onboarding_completed_at);
	const onOnboarding = url.pathname.startsWith('/app/onboarding');

	if (!completed && !onOnboarding) {
		redirect(303, '/app/onboarding');
	}
	if (completed && onOnboarding) {
		redirect(303, '/app/sessions');
	}

	return {
		user: locals.user,
		onboardingCompleted: completed
	};
};
