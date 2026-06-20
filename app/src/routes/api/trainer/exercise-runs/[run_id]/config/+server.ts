import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import { getTrainerId, requireTrainer } from '$lib/server/trainer-auth';
import { getCoachedExerciseRun, updateCoachedExerciseRun, serializeRun } from '$lib/server/trainer-runs';
import { objectIdsEqual } from '$lib/services/object-id';

const PatchSchema = z.object({
	frame_sample_rate_fps: z.number().positive().max(5).optional(),
	voice_repeat_threshold: z.number().int().min(1).optional()
});

export const PATCH: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const trainerId = getTrainerId(event);
		const runId = event.params.run_id;
		const run = await getCoachedExerciseRun(runId);
		if (!run) throw error(404, 'Run not found');
		if (!objectIdsEqual(run.trainer_id, trainerId)) throw error(403, 'Forbidden');
		if (run.status !== 'created' && run.status !== 'preparing' && run.status !== 'setup') {
			throw error(409, 'Cannot update config after set started');
		}

		const patch = PatchSchema.parse(await event.request.json());
		const config = { ...run.config, ...patch };
		const updated = await updateCoachedExerciseRun(runId, { config });
		return json(serializeRun(updated ?? run));
	} catch (err) {
		if (isHttpError(err)) throw err;
		if (err instanceof z.ZodError) throw error(400, err.message);
		throw error(500, 'Failed to update config');
	}
};
