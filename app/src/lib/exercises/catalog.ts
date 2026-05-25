import type { SessionExercise, SessionExerciseType } from '$lib/api/sessions';
import type { KipName } from '$lib/pose/pose-chart-types';

/**
 * Managed exercise presets for UI + `exercise_key` on session exercises.
 * Only `key` is required; every other field is optional and merged over form defaults.
 */
export type ExerciseCatalogEntry = Readonly<
	{ readonly key: string } & Partial<{
		readonly label: string;
		readonly type: SessionExerciseType;
		readonly measurement: 'reps' | 'duration';
		readonly target_reps: number;
		readonly target_duration: number;
		readonly target_weight_kg: number;
		readonly target_sets: number;
		readonly rest_seconds: number;
		readonly pose_chart_series: readonly { readonly key: KipName; readonly label: string }[];
	}>
>;

function titleCaseKey(key: string): string {
	return key.replace(/_/g, ' ').replace(/\b[a-z]/g, (ch) => ch.toUpperCase());
}

/** Display label for presets (dropdown / headers). Uses `label` when set; otherwise derives from key. */
export function catalogEntryLabel(e: ExerciseCatalogEntry): string {
	const raw = e.label?.trim();
	return raw && raw.length > 0 ? raw : titleCaseKey(e.key);
}

export const EXERCISE_CATALOG: readonly ExerciseCatalogEntry[] = [
	{
		key: 'squat',
		label: 'Squat',
		type: 'strength',
		measurement: 'reps',
		pose_chart_series: [
			{ key: 'INSIDE_KNEE', label: 'Inside Knee' },
			{ key: 'OUTSIDE_HIP', label: 'Outside Hip' }
		]
	},
	{
		key: 'deadlift',
		label: 'Deadlift',
		type: 'strength',
		measurement: 'reps',
		pose_chart_series: [{ key: 'HIP_HINGE', label: 'Hip Hinge' }]
	},
	// {
	// 	key: 'lunges',
	// 	label: 'Lunges',
	// 	type: 'strength',
	// 	measurement: 'reps',
	// 	pose_chart_series: [{ key: 'FRONT_KNEE', label: 'Front Knee' }]
	// }
];

export const CATALOG_KEYS = EXERCISE_CATALOG.map((e) => e.key);

export function findCatalogEntry(key: string): ExerciseCatalogEntry | undefined {
	return EXERCISE_CATALOG.find((e) => e.key === key);
}

export const CUSTOM_PRESET_VALUE = 'custom';

/** Local form state for new / draft session exercises (preset + custom). */
export type SessionExerciseFormRow = {
	catalogKey: string;
	name: string;
	type: SessionExercise['type'];
	measurement: SessionExercise['measurement'];
	target_reps?: number;
	target_duration?: number;
	target_weight_kg?: number;
	/** Empty / unset = no placeholder sets; add sets during the session. */
	target_sets?: number;
	rest_seconds: number;
	notes: string;
};

export function emptySessionExerciseFormRow(): SessionExerciseFormRow {
	return {
		catalogKey: 'squat',
		name: 'Squat',
		type: 'strength',
		measurement: 'reps',
		rest_seconds: 60,
		notes: ''
	};
}

export function applyCatalogPreset(row: SessionExerciseFormRow, key: string): void {
	if (key === CUSTOM_PRESET_VALUE || key.trim() === '') {
		row.catalogKey = CUSTOM_PRESET_VALUE;
		row.name = '';
		return;
	}
	const e = findCatalogEntry(key);
	if (!e) return;

	const preservedNotes = row.notes;
	const next = emptySessionExerciseFormRow();
	next.catalogKey = e.key;
	next.name = catalogEntryLabel(e);
	next.notes = preservedNotes;

	next.type = e.type ?? next.type;
	next.measurement = e.measurement ?? next.measurement;

	const meas = next.measurement;
	if (meas === 'reps') {
		next.target_duration = undefined;
		if (e.target_reps !== undefined) next.target_reps = e.target_reps;
	} else {
		next.target_reps = undefined;
		if (e.target_duration !== undefined) next.target_duration = e.target_duration;
	}

	if (e.target_weight_kg !== undefined) next.target_weight_kg = e.target_weight_kg;
	if (e.target_sets !== undefined) next.target_sets = e.target_sets;
	if (e.rest_seconds !== undefined) next.rest_seconds = e.rest_seconds;

	Object.assign(row, next);
}

/** Builds the JSON body for POST create/add exercise from form state. */
export function sessionExerciseApiBodyFromFormRow(row: SessionExerciseFormRow): {
	name: string;
	type: SessionExercise['type'];
	measurement: SessionExercise['measurement'];
	exercise_key?: string;
	target_reps?: number;
	target_duration?: number;
	target_weight_kg?: number;
	target_sets?: number;
	rest_seconds: number;
	notes?: string;
} {
	const trimmedNotes = row.notes.trim();
	const rawTs = row.target_sets;
	const hasTargetSets =
		typeof rawTs === 'number' && !Number.isNaN(rawTs) && Number.isFinite(rawTs);
	const target_sets = hasTargetSets ? Math.max(0, Math.floor(rawTs)) : undefined;

	return {
		name: row.name.trim(),
		type: row.type,
		measurement: row.measurement,
		...(row.catalogKey !== CUSTOM_PRESET_VALUE ? { exercise_key: row.catalogKey } : {}),
		...(row.measurement === 'reps'
			? { target_reps: row.target_reps ?? 0 }
			: { target_duration: row.target_duration ?? 0 }),
		...(row.target_weight_kg != null && row.target_weight_kg >= 0
			? { target_weight_kg: row.target_weight_kg }
			: {}),
		...(target_sets !== undefined ? { target_sets } : {}),
		rest_seconds: Math.max(0, row.rest_seconds ?? 60),
		...(trimmedNotes.length > 0 ? { notes: trimmedNotes } : {})
	};
}
