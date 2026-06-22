import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getTrainerId, requireTrainer } from '$lib/server/trainer-auth';
import { getCoachedExerciseRun, serializeRun } from '$lib/server/trainer-runs';
import { startTrainerRun } from '$lib/server/trainer-worker';
import { objectIdsEqual } from '$lib/services/object-id';

export const POST: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const trainerId = getTrainerId(event);
		const runId = event.params.run_id;
		const run = await getCoachedExerciseRun(runId);
		if (!run) throw error(404, 'Run not found');
		if (!objectIdsEqual(run.trainer_id, trainerId)) throw error(403, 'Forbidden');

		try {
			await startTrainerRun(runId);
		} catch (workerErr) {
			console.error('Trainer worker unavailable:', workerErr);
			throw error(503, 'Agent unavailable');
		}

		const refreshed = await getCoachedExerciseRun(runId);
		return json(serializeRun(refreshed ?? run));
	} catch (err) {
		if (isHttpError(err)) throw err;
		throw error(500, 'Failed to start exercise run');
	}
};
