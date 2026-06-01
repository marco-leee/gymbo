import { findCatalogEntry } from '$lib/exercises/catalog';
import { KIP_COLORS_HEX } from '$lib/pose/kip-colors';
import {
	KIP_NAMES,
	type KipName,
	type PoseChartPoint
} from '$lib/pose/pose-chart-types';

export const POSE_CHART_FIXED_KEYS = new Set(['frame', 'timestampSec']);

/** Legacy camelCase keys from older persisted charts. */
const LEGACY_ANGLE_KEY_TO_KIP: Record<string, KipName> = {
	insideKnee: 'INSIDE_KNEE',
	outsideHip: 'OUTSIDE_HIP'
};

const KIP_LABELS: Record<KipName, string> = {
	INSIDE_KNEE: 'Inside Knee',
	OUTSIDE_HIP: 'Outside Hip',
	HIP_HINGE: 'Hip Hinge',
	FRONT_KNEE: 'Front Knee'
};

/** Stable chart color per KIP (matches video overlay palette in kip-colors.ts). */
export const KIP_CHART_COLORS: Record<KipName, string> = KIP_COLORS_HEX;

export function colorForKipName(key: KipName): string {
	return KIP_CHART_COLORS[key];
}

export function humanizeKipName(name: string): string {
	if (name in KIP_LABELS) {
		return KIP_LABELS[name as KipName];
	}
	return name.replace(/_/g, ' ').replace(/\b[a-z]/g, (ch) => ch.toUpperCase());
}

/** Map legacy camelCase chart point to KIP-named PoseChartPoint. */
export function normalizePoseChartPoint(
	point: Record<string, unknown>
): PoseChartPoint {
	const frame = Number(point.frame);
	const timestampSec = Number(point.timestampSec);
	const out: PoseChartPoint = {
		frame: Number.isFinite(frame) ? frame : 0,
		timestampSec: Number.isFinite(timestampSec) ? timestampSec : 0
	};

	for (const [key, value] of Object.entries(point)) {
		if (POSE_CHART_FIXED_KEYS.has(key)) continue;
		const kip = LEGACY_ANGLE_KEY_TO_KIP[key] ?? (KIP_NAMES.includes(key as KipName) ? key : null);
		if (!kip) continue;
		if (value === null) {
			out[kip as KipName] = null;
		} else if (typeof value === 'number' && Number.isFinite(value)) {
			out[kip as KipName] = value;
		}
	}

	return out;
}

export function normalizePoseChartData(
	points: readonly Record<string, unknown>[] | undefined
): PoseChartPoint[] {
	if (!points?.length) return [];
	return points.map((p) => normalizePoseChartPoint(p));
}

function isKipName(key: string): key is KipName {
	return (KIP_NAMES as readonly string[]).includes(key);
}

/** Union of angle keys present in chart points (KIP names only, after legacy normalization). */
export function poseChartAngleKeys(points: readonly PoseChartPoint[]): KipName[] {
	const keys = new Set<KipName>();
	for (const point of points) {
		for (const key of Object.keys(point)) {
			if (POSE_CHART_FIXED_KEYS.has(key)) continue;
			if (isKipName(key) && typeof point[key] === 'number') {
				keys.add(key);
			}
		}
	}
	return [...keys].sort();
}

export type PoseChartSeriesItem = { key: KipName; label: string; color: string };

export function chartSeriesForExerciseKey(
	exerciseKey: string | undefined,
	points: readonly PoseChartPoint[]
): PoseChartSeriesItem[] {
	const fromData = poseChartAngleKeys(points);
	const catalogSeries = exerciseKey
		? findCatalogEntry(exerciseKey)?.pose_chart_series
		: undefined;
	const angleKeys =
		catalogSeries?.map((s) => s.key) ??
		(fromData.length > 0 ? fromData : []);

	return angleKeys.map((key) => {
		const fromCatalog = catalogSeries?.find((s) => s.key === key);
		return {
			key,
			label: fromCatalog?.label ?? humanizeKipName(key),
			color: colorForKipName(key)
		};
	});
}

export function chartConfigFromSeries(
	series: readonly PoseChartSeriesItem[]
): Record<string, { label: string; color: string }> {
	return Object.fromEntries(series.map((s) => [s.key, { label: s.label, color: s.color }]));
}

const COMBINED_CHART_COLORS = [
	'#EF4444',
	'#F97316',
	'#7C3AED',
	'#2563EB',
	'#06B6D4',
	'#059669',
	'#D97706',
	'#EAB308'
] as const;

export type CombinedChartRow = {
	frame: number;
	timestampSec: number;
} & Record<string, number | null | undefined>;

export type CombinedChartLegendItem = {
	key: string;
	label: string;
	color: string;
};

export function buildCombinedAnalysisChart(
	exercises: readonly { id: string; name: string; exercise_key?: string; sets?: readonly { id: string; set_number: number; pose_chart_data?: readonly Record<string, unknown>[] }[] }[]
): {
	data: CombinedChartRow[];
	legend: CombinedChartLegendItem[];
	series: { key: string; color: string }[];
	config: Record<string, { label: string; color: string }>;
} {
	const rows = new Map<number, CombinedChartRow>();
	const legend: CombinedChartLegendItem[] = [];
	const config: Record<string, { label: string; color: string }> = {};
	const series: { key: string; color: string }[] = [];
	let colorIndex = 0;

	for (const exercise of exercises) {
		for (const set of exercise.sets ?? []) {
			if (!set.pose_chart_data?.length) continue;

			const points = normalizePoseChartData(set.pose_chart_data);
			const chartSeries = chartSeriesForExerciseKey(exercise.exercise_key, points);
			if (chartSeries.length === 0) continue;

			const safeExerciseId = exercise.id.replace(/[^a-zA-Z0-9_]/g, '_');
			const safeSetId = set.id.replace(/[^a-zA-Z0-9_]/g, '_');
			const setKeyPrefix = `${safeExerciseId}_${safeSetId}_${set.set_number}`;

			for (const item of chartSeries) {
				const prefixedKey = `${setKeyPrefix}_${item.key}`;
				const color = COMBINED_CHART_COLORS[colorIndex % COMBINED_CHART_COLORS.length];
				colorIndex += 1;
				const label = `${exercise.name} - Set ${set.set_number} - ${item.label}`;

				legend.push({ key: prefixedKey, label, color });
				series.push({ key: prefixedKey, color });
				config[prefixedKey] = { label, color };

				for (const point of points) {
					const row: CombinedChartRow =
						rows.get(point.frame) ??
						({
							frame: point.frame,
							timestampSec: point.timestampSec
						} as CombinedChartRow);
					const angle = point[item.key];
					row[prefixedKey] =
						typeof angle === 'number' && Number.isFinite(angle) ? angle : null;
					rows.set(point.frame, row);
				}
			}
		}
	}

	return {
		data: [...rows.values()].sort((a, b) => a.frame - b.frame),
		legend,
		series: [...series].reverse(),
		config
	};
}
