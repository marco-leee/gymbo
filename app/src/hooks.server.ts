import { auth } from '$lib/auth';
import { svelteKitHandler } from 'better-auth/svelte-kit';
import { building } from '$app/environment';
import type { Handle } from '@sveltejs/kit';
import { getOrCreateTrainerForAuthUser } from '$lib/services/models/trainer';

export const handle: Handle = async ({ event, resolve }) => {
	const session = await auth.api.getSession({
		headers: event.request.headers
	});

	if (session) {
		event.locals.session = session.session;
		event.locals.user = session.user;
		const trainer = await getOrCreateTrainerForAuthUser({
			id: session.user.id,
			email: session.user.email,
			name: session.user.name
		});
		event.locals.trainerId = trainer._id.toString();
	}

	const { pathname } = event.url;
	if (
		pathname.startsWith('/api/') &&
		!pathname.startsWith('/api/auth') &&
		!event.locals.user
	) {
		return new Response('Unauthorized', { status: 401 });
	}

	return svelteKitHandler({ event, resolve, auth, building });
};
