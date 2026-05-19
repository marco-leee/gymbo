import {
	MongoClient,
	ObjectId,
	type Collection,
	type WithId,
	type Filter,
	type ClientSession,
	ServerApiVersion
} from 'mongodb';
import { z } from 'zod';
import { env } from '$lib/env';
import { parseObjectId, objectIdToString } from '$lib/services/object-id';
import { CATALOG_KEYS } from '$lib/exercises/catalog';

const MONGO_URI = env.MONGO_URI;

const COLLECTION_EXERCISES = 'exercises';
const COLLECTION_EXERCISE_SETS = 'exercise_sets';
const COLLECTION_SET_BIOMETRICS = 'set_biometrics';
const SET_BIOMETRICS_VERSION = 1;

let client: MongoClient | null = null;
let indexesEnsured = false;
let sessionIndexesEnsured = false;

export async function getMongoClient(): Promise<MongoClient> {
	if (!client) {
		client = new MongoClient(MONGO_URI, {
			serverApi: {
				version: ServerApiVersion.v1,
				strict: true,
				deprecationErrors: true
			}
		});
		await client.connect();
	}
	return client;
}

export async function getDb() {
	const mongo = await getMongoClient();
	return mongo.db();
}

// Session Schemas

export const PoseChartPointSchema = z.object({
	frame: z.number().int().nonnegative(),
	timestampSec: z.number().nonnegative(),
	insideKnee: z.number(),
	outsideHip: z.number()
});

/** Stored on `exercise_sets` rows (backend VideoMetadata shape). */
export const ExerciseSetVideoMetadataSchema = z
	.object({
		camera_view: z.string().optional(),
		duration_sec: z.number().optional(),
		video_width: z.number().int().optional(),
		video_height: z.number().int().optional(),
		fps: z.number().optional(),
		total_frames: z.number().int().optional()
	})
	.strict()
	.optional();

/** Hydrated onto exercise sets from `set_biometrics` (version 1). */
export const ExerciseSetSchema = z.object({
	_id: z.instanceof(ObjectId).optional(),
	set_number: z.number().int().nonnegative(),
	actual_reps: z.number().int().nonnegative().optional(),
	actual_duration: z.number().int().nonnegative().optional(),
	weight_kg: z.number().nonnegative().optional(),
	rpe: z.number().int().min(1).max(10).optional(),
	video_url: z.string().optional(),
	processed_video_url: z.string().optional(),
	video_metadata: ExerciseSetVideoMetadataSchema,
	pose_chart_data: z.array(PoseChartPointSchema).optional(),
	status: z.enum(['pending', 'completed', 'processing']).default('pending'),
	notes: z.string().optional(),
	created_at: z.date(),
	updated_at: z.date()
});

export const SESSION_EXERCISE_TYPES = ['strength', 'cardio', 'flexibility', 'warm_up'] as const;

const ExerciseKeySchema = z
	.string()
	.optional()
	.refine((k) => k == null || (CATALOG_KEYS as readonly string[]).includes(k), {
		message: 'Invalid exercise_key'
	});

export const SessionExerciseSchema = z.object({
	_id: z.instanceof(ObjectId).optional(),
	name: z.string().min(1),
	type: z.enum(SESSION_EXERCISE_TYPES),
	measurement: z.enum(['reps', 'duration']),
	exercise_key: ExerciseKeySchema,
	target_reps: z.number().int().nonnegative().optional(),
	target_duration: z.number().int().nonnegative().optional(),
	target_weight_kg: z.number().nonnegative().optional(),
	target_sets: z.number().int().nonnegative().optional(),
	rest_seconds: z.number().int().nonnegative().default(60),
	order_index: z.number().int().nonnegative(),
	notes: z.string().optional(),
	sets: z.array(ExerciseSetSchema).default([])
});

export const SessionSchema = z.object({
	client_id: z.instanceof(ObjectId),
	trainer_id: z.instanceof(ObjectId),
	status: z.enum(['scheduled', 'in-progress', 'completed', 'cancelled']).default('scheduled'),
	scheduled_at: z.date(),
	notes: z.string().optional(),
	started_at: z.date().optional(),
	completed_at: z.date().optional(),
	created_at: z.date(),
	updated_at: z.date(),
	deleted_at: z.date().nullable().optional()
});

/** Single exercise as embedded in POST /sessions or POST /sessions/[id]/exercises */
export const SessionExercisePayloadSchema = z.object({
	name: z.string().min(1),
	type: z.enum(SESSION_EXERCISE_TYPES),
	measurement: z.enum(['reps', 'duration']),
	exercise_key: ExerciseKeySchema,
	target_reps: z.number().int().nonnegative().optional(),
	target_duration: z.number().int().nonnegative().optional(),
	target_weight_kg: z.number().nonnegative().optional(),
	target_sets: z.number().int().nonnegative().optional(),
	rest_seconds: z.number().int().nonnegative().default(60),
	order_index: z.number().int().nonnegative().optional(),
	notes: z.string().max(10000).optional()
});

export const UpdateSessionExercisePayloadSchema = z.object({
	notes: z.union([z.string().max(10000), z.null()])
});

export const CreateSessionSchema = z.object({
	client_id: z.string(),
	scheduled_at: z.string().datetime(),
	notes: z.string().optional(),
	exercises: z
		.array(
			SessionExercisePayloadSchema.and(
				z.object({ order_index: z.number().int().nonnegative() })
			)
		)
		.default([])
});

export const UpdateSessionSchema = z.object({
	scheduled_at: z.string().datetime().optional(),
	notes: z.string().optional()
});

export type ExerciseSetDoc = z.infer<typeof ExerciseSetSchema>;
export type SessionExerciseDoc = z.infer<typeof SessionExerciseSchema>;
/** Fields persisted on the `sessions` document (no embedded exercises). */
export type StoredSessionDoc = z.infer<typeof SessionSchema>;
/** Session after hydration from `exercises` + `exercise_sets`. */
export type SessionDoc = StoredSessionDoc & { exercises: SessionExerciseDoc[] };
export type CreateSessionInput = z.infer<typeof CreateSessionSchema>;
export type UpdateSessionInput = z.infer<typeof UpdateSessionSchema>;
export type SessionWithId = WithId<SessionDoc>;

function exerciseIdEquals(a: SessionExerciseDoc['_id'], exerciseParam: string): boolean {
	if (a == null) return false;
	return a.toString() === exerciseParam;
}

function coerceExerciseDocId(id: string): ObjectId {
	return parseObjectId(id);
}

export async function ensureSessionIndexes(): Promise<void> {
	if (sessionIndexesEnsured) return;
	const collection = await getSessionsCollection();
	await collection.createIndex(
		{ trainer_id: 1, deleted_at: 1, scheduled_at: -1 },
		{ name: 'by_trainer_deleted_scheduled' }
	);
	sessionIndexesEnsured = true;
}

export async function ensureExerciseMongoIndexes(): Promise<void> {
	if (indexesEnsured) return;
	const db = await getDb();
	const exercises = db.collection(COLLECTION_EXERCISES);
	const exerciseSets = db.collection(COLLECTION_EXERCISE_SETS);
	const setBiometrics = db.collection(COLLECTION_SET_BIOMETRICS);
	await exercises.createIndex({ session_id: 1 }, { name: 'by_session_id' });
	await exerciseSets.createIndex(
		{ exercise_id: 1, set_index: 1 },
		{ unique: true, name: 'uniq_exercise_set_index' }
	);
	await exerciseSets.createIndex({ exercise_id: 1 }, { name: 'by_exercise_id' });
	await setBiometrics.createIndex(
		{ set_id: 1, version: 1 },
		{ unique: true, name: 'uniq_set_biometrics_version' }
	);
	indexesEnsured = true;
}

export async function getExercisesCollection(): Promise<Collection<Record<string, unknown>>> {
	const db = await getDb();
	return db.collection(COLLECTION_EXERCISES);
}

export async function getExerciseSetsCollection(): Promise<Collection<Record<string, unknown>>> {
	const db = await getDb();
	return db.collection(COLLECTION_EXERCISE_SETS);
}

export async function getSetBiometricsCollection(): Promise<Collection<Record<string, unknown>>> {
	const db = await getDb();
	return db.collection(COLLECTION_SET_BIOMETRICS);
}

function isTransactionUnsupportedError(e: unknown): boolean {
	const msg = e instanceof Error ? e.message : String(e);
	const code = typeof e === 'object' && e !== null && 'code' in e ? (e as { code: number }).code : 0;
	return (
		code === 20 ||
		/Transaction numbers are only allowed/i.test(msg) ||
		/replica set/i.test(msg)
	);
}

/** Reject legacy ingest paths; allow R2-style keys or absolute playback URLs. */
function normalizeProcessedVideoRef(raw: string): string | undefined {
	const t = raw.trim();
	if (!t) return undefined;
	if (/^https?:\/\//i.test(t)) return t;
	if (t.startsWith('/')) return undefined;
	if (/^[a-zA-Z]:[\\/]/.test(t)) return undefined;
	if (/^file:/i.test(t)) return undefined;
	return t;
}

function buildExerciseSetPlaceholderDoc(
	exerciseId: ObjectId,
	setIndex: number,
	now: Date
): Record<string, unknown> {
	return {
		exercise_id: exerciseId,
		set_index: setIndex,
		original_video_uri: '',
		processed_video_uri: '',
		pose_detection_model_name: null,
		video_metadata: { camera_view: 'UNKNOWN' },
		rep_set_summary: null,
		schema_version: 1,
		created_at: now,
		updated_at: now,
		app_status: 'pending'
	};
}

function setRowToExerciseSetDoc(
	row: Record<string, unknown>,
	poseChartBySetId?: Map<string, ExerciseSetDoc['pose_chart_data']>
): ExerciseSetDoc {
	const idVal = row._id;
	const _id = idVal instanceof ObjectId ? idVal : new ObjectId(idVal as string);
	const setIndex = row.set_index as number;
	const appStatus = row.app_status as string | undefined;
	const origUri = (row.original_video_uri as string) || '';
	const processedUriRaw = (row.processed_video_uri as string) || '';
	const processedVideoUrl = normalizeProcessedVideoRef(processedUriRaw);
	const videoUrl = (row.video_url as string | undefined) ?? undefined;
	let status: ExerciseSetDoc['status'] = 'pending';
	if (appStatus === 'completed' || appStatus === 'processing' || appStatus === 'pending') {
		status = appStatus;
	} else if (origUri || videoUrl) {
		status = 'completed';
	}
	const vm = row.video_metadata;
	let video_metadata: ExerciseSetDoc['video_metadata'];
	if (vm != null && typeof vm === 'object' && !Array.isArray(vm)) {
		video_metadata = vm as ExerciseSetDoc['video_metadata'];
	}
	const setIdStr = _id.toString();
	const pose_chart_data =
		poseChartBySetId?.get(setIdStr) ??
		(row.pose_chart_data as ExerciseSetDoc['pose_chart_data']);
	return {
		_id,
		set_number: setIndex + 1,
		actual_reps: row.actual_reps as number | undefined,
		actual_duration: row.actual_duration as number | undefined,
		weight_kg: row.weight_kg as number | undefined,
		rpe: row.rpe as number | undefined,
		video_url: videoUrl || (origUri ? origUri : undefined),
		processed_video_url: processedVideoUrl,
		video_metadata,
		pose_chart_data,
		status,
		notes: row.notes as string | undefined,
		created_at: row.created_at as Date,
		updated_at: row.updated_at as Date
	};
}

function rowToSessionExerciseDoc(
	row: Record<string, unknown>,
	setRows: Record<string, unknown>[],
	poseChartBySetId?: Map<string, ExerciseSetDoc['pose_chart_data']>
): SessionExerciseDoc {
	const sets = [...setRows]
		.sort((a, b) => (a.set_index as number) - (b.set_index as number))
		.map((setRow) => setRowToExerciseSetDoc(setRow, poseChartBySetId));
	const rowId = row._id;
	const exerciseOid = rowId instanceof ObjectId ? rowId : new ObjectId(String(rowId));
	return {
		_id: exerciseOid,
		name: row.name as string,
		type: row.type as SessionExerciseDoc['type'],
		measurement: row.measurement as SessionExerciseDoc['measurement'],
		exercise_key: row.exercise_key as SessionExerciseDoc['exercise_key'],
		target_reps: row.target_reps as number | undefined,
		target_duration: row.target_duration as number | undefined,
		target_weight_kg: row.target_weight_kg as number | undefined,
		target_sets: row.target_sets as number | undefined,
		rest_seconds: (row.rest_seconds as number) ?? 60,
		order_index: row.order_index as number,
		notes: row.notes as string | undefined,
		sets
	};
}

export async function hydrateSessionFromStored(
	raw: WithId<StoredSessionDoc> | null,
	mongoSession?: ClientSession
): Promise<SessionWithId | null> {
	if (!raw) return null;
	const sessionOid = raw._id;
	const opts = mongoSession ? { session: mongoSession } : {};
	const exCol = await getExercisesCollection();
	const setCol = await getExerciseSetsCollection();
	const exerciseRows = await exCol
		.find({ session_id: sessionOid, deleted_at: null }, { sort: { order_index: 1 }, ...opts })
		.toArray();
	const exIds = exerciseRows.map((r) => {
		const id = r._id;
		return id instanceof ObjectId ? id : new ObjectId(String(id));
	});
	const allSets =
		exIds.length > 0
			? await setCol
					.find({ exercise_id: { $in: exIds } }, { sort: { exercise_id: 1, set_index: 1 }, ...opts })
					.toArray()
			: [];
	const setIds = allSets
		.map((s) => s._id)
		.filter((id): id is ObjectId => id instanceof ObjectId);
	const poseChartBySetId = new Map<string, ExerciseSetDoc['pose_chart_data']>();
	if (setIds.length > 0) {
		const bioCol = await getSetBiometricsCollection();
		const bioRows = await bioCol
			.find(
				{ set_id: { $in: setIds }, version: SET_BIOMETRICS_VERSION },
				{ ...opts }
			)
			.toArray();
		for (const row of bioRows) {
			const sid = row.set_id instanceof ObjectId ? row.set_id : new ObjectId(String(row.set_id));
			poseChartBySetId.set(
				sid.toString(),
				row.pose_chart_data as ExerciseSetDoc['pose_chart_data']
			);
		}
	}
	const setsByEx = new Map<string, Record<string, unknown>[]>();
	for (const s of allSets) {
		const k = objectIdToString(s.exercise_id as ObjectId | string);
		const arr = setsByEx.get(k) ?? [];
		arr.push(s);
		setsByEx.set(k, arr);
	}
	const exercises: SessionExerciseDoc[] = exerciseRows.map((row) => {
		const rowId = row._id;
		const key = rowId instanceof ObjectId ? rowId.toString() : String(rowId);
		return rowToSessionExerciseDoc(row, setsByEx.get(key) ?? [], poseChartBySetId);
	});
	return { ...raw, exercises } as SessionWithId;
}

async function getSessionDocumentById(id: string): Promise<WithId<StoredSessionDoc> | null> {
	const collection = await getSessionsCollection();
	return collection.findOne({ _id: new ObjectId(id) } as Filter<StoredSessionDoc>);
}

// Session Service Functions

export async function getSessionsCollection(): Promise<Collection<StoredSessionDoc>> {
	const db = await getDb();
	return db.collection<StoredSessionDoc>('sessions');
}

export async function listSessions(
	filter: Filter<StoredSessionDoc> = {}
): Promise<SessionWithId[]> {
	await ensureSessionIndexes();
	await ensureExerciseMongoIndexes();
	const collection = await getSessionsCollection();
	const rows = await collection.find(filter).sort({ scheduled_at: -1 }).toArray();
	const hydrated = await Promise.all(
		rows.map((r) => hydrateSessionFromStored(r))
	);
	return hydrated.filter((s): s is SessionWithId => s != null);
}

export async function getSessionById(id: string): Promise<SessionWithId | null> {
	await ensureExerciseMongoIndexes();
	const raw = await getSessionDocumentById(id);
	return hydrateSessionFromStored(raw);
}

export async function createSession(
	data: Omit<StoredSessionDoc, 'created_at' | 'updated_at'> & {
		exercises: Omit<SessionExerciseDoc, '_id' | 'sets'>[];
	}
): Promise<SessionWithId> {
	await ensureExerciseMongoIndexes();
	const now = new Date();
	const client = await getMongoClient();
	const sessions = await getSessionsCollection();
	const exercisesCol = await getExercisesCollection();
	const setsCol = await getExerciseSetsCollection();

	const sessionPayload: StoredSessionDoc = {
		client_id: data.client_id,
		trainer_id: data.trainer_id,
		status: data.status ?? 'scheduled',
		scheduled_at: data.scheduled_at,
		notes: data.notes,
		started_at: data.started_at,
		completed_at: data.completed_at,
		created_at: now,
		updated_at: now,
		deleted_at: data.deleted_at ?? null
	};

	const insertAll = async (mongoSession: ClientSession | undefined) => {
		const opts = mongoSession ? { session: mongoSession } : {};
		const res = await sessions.insertOne(sessionPayload, opts);
		const insertedId = res.insertedId;

		for (const [idx, ex] of data.exercises.entries()) {
			const order_index = ex.order_index ?? idx;
			const rawTargetSets = ex.target_sets;
			const ts = rawTargetSets === undefined ? 0 : Math.max(0, Math.floor(rawTargetSets));
			const trimmedNotes = ex.notes?.trim();

			const exerciseDoc: Record<string, unknown> = {
				session_id: insertedId,
				client_id: data.client_id,
				name: ex.name,
				description: trimmedNotes ?? '',
				type: ex.type,
				comment: '',
				created_at: now,
				updated_at: now,
				deleted_at: null,
				measurement: ex.measurement,
				rest_seconds: ex.rest_seconds,
				order_index,
				...(ex.exercise_key ? { exercise_key: ex.exercise_key } : {}),
				...(ex.target_reps != null ? { target_reps: ex.target_reps } : {}),
				...(ex.target_duration != null ? { target_duration: ex.target_duration } : {}),
				...(ex.target_weight_kg != null ? { target_weight_kg: ex.target_weight_kg } : {}),
				...(rawTargetSets !== undefined ? { target_sets: ts } : {}),
				...(trimmedNotes ? { notes: trimmedNotes } : {})
			};
			const exInsert = await exercisesCol.insertOne(exerciseDoc, opts);
			const exerciseOid = exInsert.insertedId;

			for (let setIdx = 0; setIdx < ts; setIdx++) {
				const setDoc = buildExerciseSetPlaceholderDoc(exerciseOid, setIdx, now);
				await setsCol.insertOne(setDoc, opts);
			}
		}

		const raw = await sessions.findOne({ _id: insertedId }, opts);
		return hydrateSessionFromStored(raw as WithId<StoredSessionDoc> | null, mongoSession);
	};

	let result: SessionWithId | null = null;
	const mongoSession = client.startSession();
	try {
		try {
			await mongoSession.withTransaction(async () => {
				result = await insertAll(mongoSession);
			});
		} catch (e) {
			if (!isTransactionUnsupportedError(e)) throw e;
			result = await insertAll(undefined);
		}
	} finally {
		await mongoSession.endSession();
	}

	if (!result) throw new Error('createSession failed');
	return result;
}

export async function updateSession(
	id: string,
	data: Partial<Omit<StoredSessionDoc, '_id' | 'created_at'>>
): Promise<SessionWithId | null> {
	const collection = await getSessionsCollection();
	const { exercises: _ignore, ...rest } = data as Partial<StoredSessionDoc> & {
		exercises?: unknown;
	};
	const update = {
		$set: {
			...rest,
			updated_at: new Date()
		}
	};
	await collection.updateOne({ _id: new ObjectId(id) } as Filter<StoredSessionDoc>, update);
	return getSessionById(id);
}

export async function softDeleteSession(id: string): Promise<boolean> {
	const collection = await getSessionsCollection();
	const exercisesCol = await getExercisesCollection();
	const now = new Date();
	const [r1, r2] = await Promise.all([
		collection.updateOne(
			{ _id: new ObjectId(id) } as Filter<StoredSessionDoc>,
			{ $set: { deleted_at: now, updated_at: now } }
		),
		exercisesCol.updateMany(
			{ session_id: new ObjectId(id) },
			{ $set: { deleted_at: now, updated_at: now } }
		)
	]);
	return r1.modifiedCount === 1;
}

export async function startSession(id: string): Promise<SessionWithId | null> {
	const collection = await getSessionsCollection();
	const now = new Date();
	const result = await collection.updateOne(
		{ _id: new ObjectId(id) } as Filter<StoredSessionDoc>,
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
		{ _id: new ObjectId(id) } as Filter<StoredSessionDoc>,
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

/** Appends one exercise. Caller must verify session exists, is editable, and has no sets with uploaded video. */
export async function addExerciseToSession(
	sessionId: string,
	payload: z.infer<typeof SessionExercisePayloadSchema>
): Promise<SessionWithId | null> {
	const raw = await getSessionDocumentById(sessionId);
	if (!raw || raw.deleted_at) return null;

	const now = new Date();
	const sessionHydrated = (await hydrateSessionFromStored(raw))!;
	const maxOrder = sessionHydrated.exercises.reduce((m, ex) => Math.max(m, ex.order_index ?? 0), -1);
	const order_index = maxOrder + 1;
	const rawTargetSets = payload.target_sets;
	const ts = rawTargetSets === undefined ? 0 : Math.max(0, Math.floor(rawTargetSets));
	const trimmedNotes = payload.notes?.trim();
	const sessionOid = new ObjectId(sessionId);

	const exercisesCol = await getExercisesCollection();
	const setsCol = await getExerciseSetsCollection();

	const exerciseDoc: Record<string, unknown> = {
		session_id: sessionOid,
		client_id: raw.client_id,
		name: payload.name,
		description: trimmedNotes ?? '',
		type: payload.type,
		comment: '',
		created_at: now,
		updated_at: now,
		deleted_at: null,
		measurement: payload.measurement,
		rest_seconds: payload.rest_seconds,
		order_index,
		...(payload.exercise_key ? { exercise_key: payload.exercise_key } : {}),
		...(payload.target_reps != null ? { target_reps: payload.target_reps } : {}),
		...(payload.target_duration != null ? { target_duration: payload.target_duration } : {}),
		...(payload.target_weight_kg != null ? { target_weight_kg: payload.target_weight_kg } : {}),
		...(rawTargetSets !== undefined ? { target_sets: ts } : {}),
		...(trimmedNotes ? { notes: trimmedNotes } : {})
	};

	const exInsert = await exercisesCol.insertOne(exerciseDoc);
	const exerciseOid = exInsert.insertedId;

	for (let setIdx = 0; setIdx < ts; setIdx++) {
		const setDoc = buildExerciseSetPlaceholderDoc(exerciseOid, setIdx, now);
		await setsCol.insertOne(setDoc);
	}

	await (await getSessionsCollection()).updateOne(
		{ _id: sessionOid, deleted_at: null } as Filter<StoredSessionDoc>,
		{ $set: { updated_at: now } }
	);

	return getSessionById(sessionId);
}

export type DeleteExerciseFromSessionOutcome =
	| { ok: true; session: SessionWithId }
	| { ok: false; reason: 'not_found' | 'sets_not_pending' };

/** Drops exercise only when every set is `pending`. */
export async function deleteExerciseFromSession(
	sessionId: string,
	exerciseId: string
): Promise<DeleteExerciseFromSessionOutcome> {
	const raw = await getSessionDocumentById(sessionId);
	if (!raw || raw.deleted_at) return { ok: false, reason: 'not_found' };

	const session = (await hydrateSessionFromStored(raw))!;
	const exercise = session.exercises.find((ex) => exerciseIdEquals(ex._id, exerciseId));
	if (!exercise) return { ok: false, reason: 'not_found' };
	const sets = exercise.sets ?? [];
	if (!sets.every((s) => s.status === 'pending')) {
		return { ok: false, reason: 'sets_not_pending' };
	}

	const exercisesCol = await getExercisesCollection();
	const setsCol = await getExerciseSetsCollection();
	const now = new Date();
	const exerciseOid = coerceExerciseDocId(exerciseId);
	const delSets = await setsCol.deleteMany({ exercise_id: exerciseOid });
	void delSets;
	const exRes = await exercisesCol.updateOne(
		{
			_id: exerciseOid,
			session_id: new ObjectId(sessionId),
			deleted_at: null
		} as unknown as Filter<Record<string, unknown>>,
		{ $set: { deleted_at: now, updated_at: now } }
	);
	if (exRes.matchedCount === 0) return { ok: false, reason: 'not_found' };

	await (await getSessionsCollection()).updateOne(
		{ _id: new ObjectId(sessionId), deleted_at: null } as Filter<StoredSessionDoc>,
		{ $set: { updated_at: now } }
	);

	const updated = await getSessionById(sessionId);
	if (!updated) return { ok: false, reason: 'not_found' };
	return { ok: true, session: updated };
}

/** Update nested exercise meta. Pass `notes: null` to clear. Caller must enforce session editable rules. */
export async function updateExerciseNotesInSession(
	sessionId: string,
	exerciseId: string,
	notes: string | null
): Promise<SessionWithId | null> {
	const raw = await getSessionDocumentById(sessionId);
	if (!raw || raw.deleted_at) return null;

	const now = new Date();

	const exercisesCol = await getExercisesCollection();
	const $set: Record<string, unknown> = { updated_at: now };
	if (notes === null) {
		$set.description = '';
		$set.notes = null;
	} else {
		const trimmed = notes.trim();
		if (trimmed.length === 0) {
			$set.description = '';
			$set.notes = null;
		} else {
			$set.description = trimmed;
			$set.notes = trimmed;
		}
	}

	const exRes = await exercisesCol.updateOne(
		{
			_id: coerceExerciseDocId(exerciseId),
			session_id: new ObjectId(sessionId),
			deleted_at: null
		} as unknown as Filter<Record<string, unknown>>,
		{ $set: $set }
	);
	if (exRes.matchedCount === 0) return null;

	await (await getSessionsCollection()).updateOne(
		{ _id: new ObjectId(sessionId), deleted_at: null } as Filter<StoredSessionDoc>,
		{ $set: { updated_at: now } }
	);

	return getSessionById(sessionId);
}

// Set Management Functions

export async function addSetToExercise(
	sessionId: string,
	exerciseId: string
): Promise<SessionWithId | null> {
	const raw = await getSessionDocumentById(sessionId);
	if (!raw || raw.deleted_at) return null;
	const now = new Date();

	const session = (await hydrateSessionFromStored(raw))!;
	const exercise = session.exercises.find((ex) => exerciseIdEquals(ex._id, exerciseId));
	if (!exercise) return null;

	const setsCol = await getExerciseSetsCollection();
	const exerciseOid = coerceExerciseDocId(exerciseId);
	const maxAgg = await setsCol
		.aggregate<{ maxIdx: number }>([
			{ $match: { exercise_id: exerciseOid } },
			{ $group: { _id: null, maxIdx: { $max: '$set_index' } } }
		])
		.toArray();
	const nextIndex = (maxAgg[0]?.maxIdx ?? -1) + 1;
	const setDoc = buildExerciseSetPlaceholderDoc(exerciseOid, nextIndex, now);
	await setsCol.insertOne(setDoc);

	await (await getSessionsCollection()).updateOne(
		{ _id: new ObjectId(sessionId), deleted_at: null } as Filter<StoredSessionDoc>,
		{ $set: { updated_at: now } }
	);

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
		video_metadata?: {
			camera_view?: string;
			duration_sec?: number;
			video_width?: number;
			video_height?: number;
			fps?: number;
			total_frames?: number;
		};
		pose_chart_data?: z.infer<typeof PoseChartPointSchema>[];
		status?: 'pending' | 'completed' | 'processing';
		notes?: string;
	}
): Promise<SessionWithId | null> {
	const raw = await getSessionDocumentById(sessionId);
	if (!raw || raw.deleted_at) return null;
	const now = new Date();

	const setsCol = await getExerciseSetsCollection();
	const $set: Record<string, unknown> = { updated_at: now };
	if (data.actual_reps !== undefined) $set.actual_reps = data.actual_reps;
	if (data.actual_duration !== undefined) $set.actual_duration = data.actual_duration;
	if (data.weight_kg !== undefined) $set.weight_kg = data.weight_kg;
	if (data.rpe !== undefined) $set.rpe = data.rpe;
	if (data.notes !== undefined) $set.notes = data.notes;
	if (data.status !== undefined) $set.app_status = data.status;
	if (data.video_url !== undefined) {
		$set.video_url = data.video_url;
		$set.original_video_uri = data.video_url;
	}
	if (data.video_metadata !== undefined) {
		$set.video_metadata = data.video_metadata;
	}

	const setOid = new ObjectId(setId);
	if (data.pose_chart_data !== undefined) {
		const bioCol = await getSetBiometricsCollection();
		await bioCol.replaceOne(
			{ set_id: setOid, version: SET_BIOMETRICS_VERSION },
			{
				set_id: setOid,
				version: SET_BIOMETRICS_VERSION,
				pose_chart_data: data.pose_chart_data
			},
			{ upsert: true }
		);
	}

	const r = await setsCol.updateOne(
		{ _id: setOid, exercise_id: coerceExerciseDocId(exerciseId) },
		{ $set: $set }
	);
	if (r.matchedCount === 0) return null;

	await (await getSessionsCollection()).updateOne(
		{ _id: new ObjectId(sessionId), deleted_at: null } as Filter<StoredSessionDoc>,
		{ $set: { updated_at: now } }
	);

	return getSessionById(sessionId);
}

export async function deleteSetFromExercise(
	sessionId: string,
	exerciseId: string,
	setId: string
): Promise<SessionWithId | null> {
	const raw = await getSessionDocumentById(sessionId);
	if (!raw || raw.deleted_at) return null;
	const now = new Date();

	const setsCol = await getExerciseSetsCollection();
	const setOid = new ObjectId(setId);
	const r = await setsCol.deleteOne({
		_id: setOid,
		exercise_id: coerceExerciseDocId(exerciseId)
	});
	if (r.deletedCount === 0) return null;

	const bioCol = await getSetBiometricsCollection();
	await bioCol.deleteMany({ set_id: setOid });

	await (await getSessionsCollection()).updateOne(
		{ _id: new ObjectId(sessionId), deleted_at: null } as Filter<StoredSessionDoc>,
		{ $set: { updated_at: now } }
	);

	return getSessionById(sessionId);
}
