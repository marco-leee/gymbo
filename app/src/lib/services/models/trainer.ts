import { ObjectId, type Collection, type Filter, type WithId } from 'mongodb';
import { z } from 'zod';
import { getDb } from '../mongo';

export const CountRangeSchema = z.enum(['1_5', '6_15', '16_30', '31_plus']);
export type CountRange = z.infer<typeof CountRangeSchema>;

export const TrainerTypeSchema = z.enum(['freelance', 'chain_gym', 'small_studio', 'gym_owner']);
export type TrainerType = z.infer<typeof TrainerTypeSchema>;

export const SessionDurationSchema = z.enum(['under_30', '30_45', '45_60', '60_90', '90_plus']);
export type SessionDuration = z.infer<typeof SessionDurationSchema>;

export const OnboardingAnswersSchema = z.object({
	trainer_type: TrainerTypeSchema,
	typical_client_count: CountRangeSchema,
	sessions_per_week: CountRangeSchema,
	session_duration: SessionDurationSchema
});

export type OnboardingAnswers = z.infer<typeof OnboardingAnswersSchema>;

export const SubmitOnboardingSchema = OnboardingAnswersSchema;

export const TrainerSchema = z.object({
	auth_user_id: z.string().min(1),
	email: z.email().optional(),
	name: z.string().optional(),
	onboarding_completed_at: z.date().optional(),
	onboarding_answers: OnboardingAnswersSchema.optional(),
	created_at: z.date(),
	updated_at: z.date()
});

export type TrainerDoc = z.infer<typeof TrainerSchema>;
export type TrainerWithId = WithId<TrainerDoc>;

export type TrainerOnboardingStatus = {
	completed: boolean;
	answers?: OnboardingAnswers;
};

let trainerIndexesEnsured = false;

export async function ensureTrainerIndexes(): Promise<void> {
	if (trainerIndexesEnsured) return;
	const collection = await getTrainersCollection();
	await collection.createIndex({ auth_user_id: 1 }, { unique: true, name: 'uniq_auth_user_id' });
	trainerIndexesEnsured = true;
}

export async function getTrainersCollection(): Promise<Collection<TrainerDoc>> {
	const db = await getDb();
	return db.collection<TrainerDoc>('trainers');
}

export async function getTrainerByAuthUserId(authUserId: string): Promise<TrainerWithId | null> {
	await ensureTrainerIndexes();
	const collection = await getTrainersCollection();
	return collection.findOne({ auth_user_id: authUserId } as Filter<TrainerDoc>);
}

export type AuthUserForTrainer = {
	id: string;
	email?: string | null;
	name?: string | null;
};

export async function getOrCreateTrainerForAuthUser(user: AuthUserForTrainer): Promise<TrainerWithId> {
	await ensureTrainerIndexes();
	const collection = await getTrainersCollection();
	const now = new Date();
	const email = user.email ?? undefined;
	const name = user.name ?? undefined;

	const existing = await collection.findOne({ auth_user_id: user.id } as Filter<TrainerDoc>);
	if (existing) {
		const updates: Partial<TrainerDoc> = {};
		if (email && existing.email !== email) updates.email = email;
		if (name && existing.name !== name) updates.name = name;
		if (Object.keys(updates).length > 0) {
			updates.updated_at = now;
			await collection.updateOne({ _id: existing._id }, { $set: updates });
			return { ...existing, ...updates } as TrainerWithId;
		}
		return existing;
	}

	const doc: TrainerDoc = {
		auth_user_id: user.id,
		...(email ? { email } : {}),
		...(name ? { name } : {}),
		created_at: now,
		updated_at: now
	};
	const result = await collection.insertOne(doc);
	return { _id: result.insertedId, ...doc };
}

export function trainerObjectId(trainerIdHex: string): ObjectId {
	return new ObjectId(trainerIdHex);
}

export async function getTrainerById(trainerIdHex: string): Promise<TrainerWithId | null> {
	await ensureTrainerIndexes();
	const collection = await getTrainersCollection();
	return collection.findOne({ _id: trainerObjectId(trainerIdHex) } as Filter<TrainerDoc>);
}

export function getTrainerOnboardingStatus(trainer: Pick<TrainerDoc, 'onboarding_completed_at' | 'onboarding_answers'>): TrainerOnboardingStatus {
	return {
		completed: Boolean(trainer.onboarding_completed_at),
		...(trainer.onboarding_answers ? { answers: trainer.onboarding_answers } : {})
	};
}

export async function completeTrainerOnboarding(
	trainerIdHex: string,
	answers: OnboardingAnswers
): Promise<TrainerWithId> {
	await ensureTrainerIndexes();
	const collection = await getTrainersCollection();
	const trainerId = trainerObjectId(trainerIdHex);
	const existing = await collection.findOne({ _id: trainerId } as Filter<TrainerDoc>);

	if (!existing) {
		throw new Error('Trainer not found');
	}
	if (existing.onboarding_completed_at) {
		throw new Error('Onboarding already completed');
	}

	const now = new Date();
	const updates: Partial<TrainerDoc> = {
		onboarding_completed_at: now,
		onboarding_answers: answers,
		updated_at: now
	};

	await collection.updateOne({ _id: trainerId }, { $set: updates });
	return { ...existing, ...updates } as TrainerWithId;
}
