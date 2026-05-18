/**
 * One-time migration: move embedded `sessions.exercises` (+ nested sets) into
 * `exercises` and `exercise_sets` collections (split layout used by app-v2 + backend).
 *
 * Run from `app-v2/` with Bun (loads `.env` automatically):
 *   bun run scripts/migrate-embedded-sessions-to-split.ts
 *
 * Requires `MONGO_URI`. Idempotent only if re-run skips sessions that already
 * have rows in `exercises` for that session_id — this script skips a session when
 * any exercise doc exists with `session_id` equal to the session's `_id` string.
 */

import { MongoClient, ObjectId, type Document } from 'mongodb';

const uri = process.env.MONGO_URI;
if (!uri) {
	console.error('MONGO_URI is not set');
	process.exit(1);
}

function isNonEmptyEmbedded(exercises: unknown): exercises is Document[] {
	return Array.isArray(exercises) && exercises.length > 0;
}

async function main() {
	const client = new MongoClient(uri);
	await client.connect();
	const db = client.db();
	const sessions = db.collection('sessions');
	const exercises = db.collection('exercises');
	const exerciseSets = db.collection('exercise_sets');

	const cursor = sessions.find({ 'exercises.0': { $exists: true } } as Document);

	let migrated = 0;
	let skipped = 0;

	for await (const session of cursor) {
		const sid = session._id instanceof ObjectId ? session._id.toString() : String(session._id);
		const existing = await exercises.countDocuments({ session_id: sid, deleted_at: null });
		if (existing > 0) {
			skipped++;
			continue;
		}

		const embedded = session.exercises;
		if (!isNonEmptyEmbedded(embedded)) continue;

		const clientId = session.client_id as string;
		const now = new Date();

		for (const ex of embedded) {
			const exOid =
				ex._id instanceof ObjectId ? ex._id : new ObjectId(String(ex._id));
			await exercises.insertOne({
				_id: exOid,
				session_id: sid,
				client_id: clientId,
				name: ex.name,
				description: typeof ex.notes === 'string' ? ex.notes : '',
				type: ex.type,
				comment: '',
				created_at: ex.created_at ?? session.created_at ?? now,
				updated_at: now,
				deleted_at: null,
				measurement: ex.measurement,
				...(ex.exercise_key ? { exercise_key: ex.exercise_key } : {}),
				...(ex.target_reps != null ? { target_reps: ex.target_reps } : {}),
				...(ex.target_duration != null ? { target_duration: ex.target_duration } : {}),
				...(ex.target_weight_kg != null ? { target_weight_kg: ex.target_weight_kg } : {}),
				...(ex.target_sets != null ? { target_sets: ex.target_sets } : {}),
				rest_seconds: ex.rest_seconds ?? 60,
				order_index: ex.order_index ?? 0,
				...(typeof ex.notes === 'string' && ex.notes ? { notes: ex.notes } : {})
			});

			const sets = Array.isArray(ex.sets) ? ex.sets : [];
			for (const set of sets) {
				const setOid =
					set._id instanceof ObjectId ? set._id : new ObjectId(String(set._id));
				const setNum = typeof set.set_number === 'number' ? set.set_number : 1;
				await exerciseSets.insertOne({
					_id: setOid,
					exercise_id: exOid.toString(),
					set_index: Math.max(0, setNum - 1),
					original_video_uri: typeof set.video_url === 'string' ? set.video_url : '',
					processed_video_uri: '',
					pose_detection_model_name: null,
					video_metadata: { camera_view: 'UNKNOWN' },
					rep_set_summary: null,
					schema_version: 1,
					created_at: set.created_at ?? now,
					updated_at: set.updated_at ?? now,
					app_status: set.status ?? 'pending',
					...(set.actual_reps != null ? { actual_reps: set.actual_reps } : {}),
					...(set.actual_duration != null ? { actual_duration: set.actual_duration } : {}),
					...(set.weight_kg != null ? { weight_kg: set.weight_kg } : {}),
					...(set.rpe != null ? { rpe: set.rpe } : {}),
					...(typeof set.video_url === 'string' && set.video_url ? { video_url: set.video_url } : {}),
					...(set.pose_chart_data ? { pose_chart_data: set.pose_chart_data } : {}),
					...(typeof set.notes === 'string' ? { notes: set.notes } : {})
				});
			}
		}

		await sessions.updateOne(
			{ _id: session._id },
			{ $set: { exercises: [], updated_at: now } }
		);
		migrated++;
		console.log('Migrated session', sid);
	}

	await client.close();
	console.log(`Done. Migrated ${migrated} session(s), skipped ${skipped} (already had split exercises).`);
}

main().catch((e) => {
	console.error(e);
	process.exit(1);
});
