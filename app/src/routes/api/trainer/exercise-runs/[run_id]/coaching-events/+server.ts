import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getTrainerId, requireTrainer } from '$lib/server/trainer-auth';
import { getCoachedExerciseRun, listCoachingEvents } from '$lib/server/trainer-runs';
import { objectIdsEqual } from '$lib/services/object-id';

export const GET: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const trainerId = getTrainerId(event);
		const runId = event.params.run_id;
		const run = await getCoachedExerciseRun(runId);
		if (!run) throw error(404, 'Run not found');
		if (!objectIdsEqual(run.trainer_id, trainerId)) throw error(403, 'Forbidden');

		const limit = Number(event.url.searchParams.get('limit') ?? 50);
		const offset = Number(event.url.searchParams.get('offset') ?? 0);
		const { events, total } = await listCoachingEvents(runId, limit, offset);
		return json({ events, total });
	} catch (err) {
		if (isHttpError(err)) throw err;
		throw error(500, 'Failed to list coaching events');
	}
};
