import { json, error, isHttpError } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import { assertSessionOwned, getTrainerId, requireTrainer } from '$lib/server/trainer-auth';
import {
	createCoachedExerciseRun,
	deriveConfigFromSessionExercise,
	findActiveRunForExercise,
	serializeRun
} from '$lib/server/trainer-runs';

const CreateRunSchema = z.object({
	gymbo_session_id: z.string().min(1),
	session_exercise_id: z.string().min(1),
	config_overrides: z
		.object({
			frame_sample_rate_fps: z.number().positive().max(5).optional(),
			voice_repeat_threshold: z.number().int().min(1).optional()
		})
		.optional()
});

export const POST: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const trainerId = getTrainerId(event);
		const body = CreateRunSchema.parse(await event.request.json());

		const session = await assertSessionOwned(trainerId, body.gymbo_session_id);
		const exercise = session.exercises?.find(
			(e) => e._id?.toString() === body.session_exercise_id
		);
		if (!exercise) {
			throw error(404, 'Exercise not found in session');
		}

		const existing = await findActiveRunForExercise(body.gymbo_session_id, body.session_exercise_id);
		if (existing) {
			throw error(409, 'Exercise already has an active run');
		}

		const config = deriveConfigFromSessionExercise(exercise);
		if (body.config_overrides?.frame_sample_rate_fps != null) {
			config.frame_sample_rate_fps = body.config_overrides.frame_sample_rate_fps;
		}
		if (body.config_overrides?.voice_repeat_threshold != null) {
			config.voice_repeat_threshold = body.config_overrides.voice_repeat_threshold;
		}

		const run = await createCoachedExerciseRun({
			gymboSessionId: body.gymbo_session_id,
			sessionExerciseId: body.session_exercise_id,
			trainerId,
			clientId: session.client_id.toString(),
			exerciseType: exercise.exercise_key ?? 'overhead_squat',
			config
		});

		return json(
			{
				...serializeRun(run),
				ws_url: '/trainer'
			},
			{ status: 201 }
		);
	} catch (err) {
		if (isHttpError(err)) throw err;
		if (err instanceof z.ZodError) {
			throw error(400, { message: err.issues.map((i) => i.message).join(', ') });
		}
		console.error('Create exercise run failed:', err);
		throw error(500, 'Failed to create exercise run');
	}
};
