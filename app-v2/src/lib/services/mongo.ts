import { MongoClient, ObjectId, type Collection, type WithId, type Filter, ServerApiVersion } from 'mongodb';
import { z } from 'zod';
import { env } from '$lib/env';
import { v7 as uuidv7 } from 'uuid';

const MONGO_URI = env.MONGO_URI;

let client: MongoClient | null = null;

export async function getMongoClient(): Promise<MongoClient> {
	if (!client) {
		client = new MongoClient(MONGO_URI, {
			serverApi: {
				version: ServerApiVersion.v1,
				strict: true,
				deprecationErrors: true,
			},
		});
		await client.connect();
	}
	return client;
}

export async function getDb() {
	const mongo = await getMongoClient();
	return mongo.db();
}

export function generateUUID(): string {
    return uuidv7();
}

// Session Schemas

export const PoseChartPointSchema = z.object({
	frame: z.number().int().nonnegative(),
	timestampSec: z.number().nonnegative(),
	insideKnee: z.number(),
	outsideHip: z.number()
});

export const ExerciseSetSchema = z.object({
	_id: z.instanceof(ObjectId).optional(),
	set_number: z.number().int().nonnegative(),
	actual_reps: z.number().int().nonnegative().optional(),
	actual_duration: z.number().int().nonnegative().optional(),
	weight_kg: z.number().nonnegative().optional(),
	rpe: z.number().int().min(1).max(10).optional(),
	video_url: z.string().optional(),
	pose_chart_data: z.array(PoseChartPointSchema).optional(),
	status: z.enum(['pending', 'completed', 'processing']).default('pending'),
	notes: z.string().optional(),
	created_at: z.date(),
	updated_at: z.date()
});

export const SessionExerciseSchema = z.object({
	_id: z.instanceof(ObjectId).optional(),
	name: z.string().min(1),
	type: z.enum(['strength', 'cardio', 'flexibility']),
	measurement: z.enum(['reps', 'duration']),
	target_reps: z.number().int().nonnegative().optional(),
	target_duration: z.number().int().nonnegative().optional(),
	target_sets: z.number().int().nonnegative().default(3),
	rest_seconds: z.number().int().nonnegative().default(60),
	order_index: z.number().int().nonnegative(),
	sets: z.array(ExerciseSetSchema).default([])
});

export const SessionSchema = z.object({
	client_id: z.string(),
	trainer_id: z.string(),
	status: z.enum(['scheduled', 'in-progress', 'completed', 'cancelled']).default('scheduled'),
	scheduled_at: z.date(),
	notes: z.string().optional(),
	started_at: z.date().optional(),
	completed_at: z.date().optional(),
	exercises: z.array(SessionExerciseSchema).default([]),
	created_at: z.date(),
	updated_at: z.date(),
	deleted_at: z.date().nullable().optional()
});

export const CreateSessionSchema = z.object({
	client_id: z.string(),
	scheduled_at: z.string().datetime(),
	notes: z.string().optional(),
	exercises: z.array(z.object({
		name: z.string().min(1),
		type: z.enum(['strength', 'cardio', 'flexibility']),
		measurement: z.enum(['reps', 'duration']),
		target_reps: z.number().int().nonnegative().optional(),
		target_duration: z.number().int().nonnegative().optional(),
		target_sets: z.number().int().nonnegative().default(3),
		rest_seconds: z.number().int().nonnegative().default(60),
		order_index: z.number().int().nonnegative()
	})).default([])
});

export const UpdateSessionSchema = z.object({
	scheduled_at: z.string().datetime().optional(),
	notes: z.string().optional()
});

export type ExerciseSetDoc = z.infer<typeof ExerciseSetSchema>;
export type SessionExerciseDoc = z.infer<typeof SessionExerciseSchema>;
export type SessionDoc = z.infer<typeof SessionSchema>;
export type CreateSessionInput = z.infer<typeof CreateSessionSchema>;
export type UpdateSessionInput = z.infer<typeof UpdateSessionSchema>;
export type SessionWithId = WithId<SessionDoc>;

// Session Service Functions

export async function getSessionsCollection(): Promise<Collection<SessionDoc>> {
	const db = await getDb();
	return db.collection<SessionDoc>('sessions');
}

export async function listSessions(filter: Filter<SessionDoc> = {}): Promise<SessionWithId[]> {
	const collection = await getSessionsCollection();
	return collection.find(filter).sort({ scheduled_at: -1 }).toArray();
}

export async function getSessionById(id: string): Promise<SessionWithId | null> {
	const collection = await getSessionsCollection();
	return collection.findOne({ _id: new ObjectId(id) } as Filter<SessionDoc>);
}

export async function createSession(
	data: Omit<SessionDoc, 'created_at' | 'updated_at' | 'exercises'> & { exercises: Omit<SessionExerciseDoc, '_id'>[] }
): Promise<SessionWithId> {
	const collection = await getSessionsCollection();
	const now = new Date();

	// Add _id to each exercise and initialize empty sets
	const exercisesWithIds: SessionExerciseDoc[] = data.exercises.map((ex, idx) => ({
		...ex,
		_id: new ObjectId(),
		order_index: ex.order_index ?? idx,
		sets: []
	}));

	const doc: SessionDoc = {
		...data,
		exercises: exercisesWithIds,
		created_at: now,
		updated_at: now
	};

	const result = await collection.insertOne(doc);
	return { _id: result.insertedId, ...doc };
}

export async function updateSession(
	id: string,
	data: Partial<Omit<SessionDoc, '_id' | 'created_at'>>
): Promise<SessionWithId | null> {
	const collection = await getSessionsCollection();
	const update = {
		$set: {
			...data,
			updated_at: new Date()
		}
	};
	await collection.updateOne({ _id: new ObjectId(id) } as Filter<SessionDoc>, update);
	return getSessionById(id);
}

export async function softDeleteSession(id: string): Promise<boolean> {
	const collection = await getSessionsCollection();
	const result = await collection.updateOne(
		{ _id: new ObjectId(id) } as Filter<SessionDoc>,
		{ $set: { deleted_at: new Date(), updated_at: new Date() } }
	);
	return result.modifiedCount === 1;
}

export async function startSession(id: string): Promise<SessionWithId | null> {
	const collection = await getSessionsCollection();
	const now = new Date();
	const result = await collection.updateOne(
		{ _id: new ObjectId(id) } as Filter<SessionDoc>,
		{
			$set: {
				status: 'in-progress',
				started_at: now,
				updated_at: now
			}
		}
	);
	if (result.modifiedCount === 0) return null;
	return getSessionById(id);
}

export async function completeSession(id: string): Promise<SessionWithId | null> {
	const collection = await getSessionsCollection();
	const now = new Date();
	const result = await collection.updateOne(
		{ _id: new ObjectId(id) } as Filter<SessionDoc>,
		{
			$set: {
				status: 'completed',
				completed_at: now,
				updated_at: now
			}
		}
	);
	if (result.modifiedCount === 0) return null;
	return getSessionById(id);
}

// Set Management Functions

export async function addSetToExercise(
	sessionId: string,
	exerciseId: string
): Promise<SessionWithId | null> {
	const collection = await getSessionsCollection();
	const now = new Date();

	// First, get the session to find the next set number
	const session = await getSessionById(sessionId);
	if (!session) return null;

	const exercise = session.exercises.find(ex => ex._id?.toString() === exerciseId);
	if (!exercise) return null;

	const nextSetNumber = (exercise.sets?.length ?? 0) + 1;

	const newSet: ExerciseSetDoc = {
		_id: new ObjectId(),
		set_number: nextSetNumber,
		status: 'pending',
		created_at: now,
		updated_at: now
	};

	const result = await collection.updateOne(
		{ _id: new ObjectId(sessionId), 'exercises._id': new ObjectId(exerciseId) } as Filter<SessionDoc>,
		{
			$push: { 'exercises.$.sets': newSet },
			$set: { updated_at: now }
		}
	);

	if (result.modifiedCount === 0) return null;
	return getSessionById(sessionId);
}

export async function updateSetInExercise(
	sessionId: string,
	exerciseId: string,
	setId: string,
	data: {
		actual_reps?: number;
		actual_duration?: number;
		weight_kg?: number;
		rpe?: number;
		video_url?: string;
		pose_chart_data?: z.infer<typeof PoseChartPointSchema>[];
		status?: 'pending' | 'completed' | 'processing';
		notes?: string;
	}
): Promise<SessionWithId | null> {
	const collection = await getSessionsCollection();
	const now = new Date();

	// Build the $set object dynamically
	const setObj: Record<string, unknown> = { updated_at: now };
	if (data.actual_reps !== undefined) setObj['exercises.$[ex].sets.$[set].actual_reps'] = data.actual_reps;
	if (data.actual_duration !== undefined) setObj['exercises.$[ex].sets.$[set].actual_duration'] = data.actual_duration;
	if (data.weight_kg !== undefined) setObj['exercises.$[ex].sets.$[set].weight_kg'] = data.weight_kg;
	if (data.rpe !== undefined) setObj['exercises.$[ex].sets.$[set].rpe'] = data.rpe;
	if (data.video_url !== undefined) setObj['exercises.$[ex].sets.$[set].video_url'] = data.video_url;
	if (data.pose_chart_data !== undefined) setObj['exercises.$[ex].sets.$[set].pose_chart_data'] = data.pose_chart_data;
	if (data.status !== undefined) setObj['exercises.$[ex].sets.$[set].status'] = data.status;
	if (data.notes !== undefined) setObj['exercises.$[ex].sets.$[set].notes'] = data.notes;
	setObj['exercises.$[ex].sets.$[set].updated_at'] = now;

	const result = await collection.updateOne(
		{ _id: new ObjectId(sessionId) } as Filter<SessionDoc>,
		{ $set: setObj },
		{
			arrayFilters: [
				{ 'ex._id': new ObjectId(exerciseId) },
				{ 'set._id': new ObjectId(setId) }
			]
		}
	);

	if (result.modifiedCount === 0) return null;
	return getSessionById(sessionId);
}

export async function deleteSetFromExercise(
	sessionId: string,
	exerciseId: string,
	setId: string
): Promise<SessionWithId | null> {
	const collection = await getSessionsCollection();
	const now = new Date();

	const result = await collection.updateOne(
		{ _id: new ObjectId(sessionId), 'exercises._id': new ObjectId(exerciseId) } as Filter<SessionDoc>,
		{
			$pull: { 'exercises.$.sets': { _id: new ObjectId(setId) } },
			$set: { updated_at: now }
		}
	);

	if (result.modifiedCount === 0) return null;
	return getSessionById(sessionId);
}
