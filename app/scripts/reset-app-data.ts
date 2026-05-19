/**
 * Wipes app-owned MongoDB collections (not Better Auth tables).
 * Run: bun run scripts/reset-app-data.ts
 */
import { getDb } from '../src/lib/services/mongo';

const COLLECTIONS = [
	'clients',
	'sessions',
	'exercises',
	'exercise_sets',
	'set_biometrics',
	'trainers'
] as const;

const db = await getDb();

for (const name of COLLECTIONS) {
	const result = await db.collection(name).deleteMany({});
	console.log(`Deleted ${result.deletedCount} documents from ${name}`);
}

console.log('Done.');
