import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import {
	completeTrainerOnboarding,
	getTrainerById,
	getTrainerOnboardingStatus,
	SubmitOnboardingSchema
} from '$lib/services/models/trainer';
import { getTrainerId, requireTrainer } from '$lib/server/trainer-auth';

export const GET: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const trainerId = getTrainerId(event);
		const trainer = await getTrainerById(trainerId);

		if (!trainer) {
			throw error(404, 'Trainer not found');
		}

		return json(getTrainerOnboardingStatus(trainer));
	} catch (err) {
		if (err && typeof err === 'object' && 'status' in err) {
			throw err;
		}
		console.error('Failed to get onboarding status:', err);
		throw error(500, 'Failed to get onboarding status');
	}
};

export const PUT: RequestHandler = async (event) => {
	try {
		requireTrainer(event);
		const trainerId = getTrainerId(event);
		const trainer = await getTrainerById(trainerId);

		if (!trainer) {
			throw error(404, 'Trainer not found');
		}
		if (trainer.onboarding_completed_at) {
			throw error(409, 'Onboarding already completed');
		}

		const body = await event.request.json();
		const validated = SubmitOnboardingSchema.parse(body);
		const updated = await completeTrainerOnboarding(trainerId, validated);

		return json(getTrainerOnboardingStatus(updated));
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map((issue) => issue.message).join(', '));
		}
		if (err instanceof Error && err.message === 'Onboarding already completed') {
			throw error(409, err.message);
		}
		if (err && typeof err === 'object' && 'status' in err) {
			throw err;
		}
		console.error('Failed to submit onboarding:', err);
		throw error(500, 'Failed to submit onboarding');
	}
};
