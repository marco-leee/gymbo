import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getTrainerId, requireTrainer } from '$lib/server/trainer-auth';
import { getCoachedExerciseRun, updateCoachedExerciseRun, serializeRun } from '$lib/server/trainer-runs';
import { resumeTrainerRun } from '$lib/server/trainer-worker';
import { objectIdsEqual } from '$lib/services/object-id';

export const POST: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const trainerId = getTrainerId(event);
		const runId = event.params.run_id;
		const run = await getCoachedExerciseRun(runId);
		if (!run) throw error(404, 'Run not found');
		if (!objectIdsEqual(run.trainer_id, trainerId)) throw error(403, 'Forbidden');
		if (run.status !== 'paused') throw error(409, 'Run is not paused');

		await resumeTrainerRun(runId);
		const updated = await updateCoachedExerciseRun(runId, { status: 'active' });
		return json(serializeRun(updated ?? run));
	} catch (err) {
		if (isHttpError(err)) throw err;
		throw error(500, 'Failed to resume exercise run');
	}
};
