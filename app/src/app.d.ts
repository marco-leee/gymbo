// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
import type { AuthSession } from '$lib/auth';

declare global {
	namespace App {
		// interface Error {}
		interface Locals {
			user?: AuthSession['user'] | null;
			session?: AuthSession['session'] | null;
			trainerId?: string;
		}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
