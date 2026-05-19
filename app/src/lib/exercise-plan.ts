import type { SessionExercise } from '$lib/api/sessions';

/** Only when every set is still `pending` (vacuous truth if there are no sets). */
export function exerciseDeletionAllowed(ex: Pick<SessionExercise, 'sets'>): boolean {
	const sets = ex.sets ?? [];
	return sets.every((s) => s.status === 'pending');
}
