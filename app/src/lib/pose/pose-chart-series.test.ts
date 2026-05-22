import { describe, expect, test } from 'bun:test';
import {
	buildCombinedAnalysisChart,
	colorForKipName,
	normalizePoseChartPoint,
	poseChartAngleKeys
} from './pose-chart-series';

describe('pose-chart-series', () => {
	test('normalizePoseChartPoint maps legacy camelCase to KIP names', () => {
		const out = normalizePoseChartPoint({
			frame: 1,
			timestampSec: 0.5,
			insideKnee: 90,
			outsideHip: 100
		});
		expect(out.INSIDE_KNEE).toBe(90);
		expect(out.OUTSIDE_HIP).toBe(100);
	});

	test('poseChartAngleKeys reads KIP-named points', () => {
		const keys = poseChartAngleKeys([
			{ frame: 0, timestampSec: 0, HIP_HINGE: 120 }
		]);
		expect(keys).toEqual(['HIP_HINGE']);
	});

	test('colorForKipName returns stable CSS var per KIP', () => {
		expect(colorForKipName('INSIDE_KNEE')).toBe('var(--chart-1)');
		expect(colorForKipName('HIP_HINGE')).toBe('var(--chart-3)');
	});

	test('normalizePoseChartPoint preserves explicit null KIPs', () => {
		const out = normalizePoseChartPoint({
			frame: 2,
			timestampSec: 0.2,
			INSIDE_KNEE: null,
			OUTSIDE_HIP: null
		});
		expect(out.INSIDE_KNEE).toBeNull();
		expect(out.OUTSIDE_HIP).toBeNull();
	});

	test('buildCombinedAnalysisChart writes null gaps in series rows', () => {
		const chart = buildCombinedAnalysisChart([
			{
				id: 'ex1',
				name: 'Squat',
				exercise_key: 'squat',
				sets: [
					{
						id: 's1',
						set_number: 1,
						pose_chart_data: [
							{ frame: 0, timestampSec: 0, INSIDE_KNEE: 90, OUTSIDE_HIP: 100 },
							{ frame: 1, timestampSec: 0.1, INSIDE_KNEE: null, OUTSIDE_HIP: null }
						]
					}
				]
			}
		]);
		const insideKey = chart.series.find((s) => s.key.includes('INSIDE_KNEE'))?.key;
		expect(insideKey).toBeDefined();
		expect(chart.data[1][insideKey!]).toBeNull();
	});

	test('buildCombinedAnalysisChart prefixes series per set', () => {
		const chart = buildCombinedAnalysisChart([
			{
				id: 'ex1',
				name: 'Deadlift',
				exercise_key: 'deadlift',
				sets: [
					{
						id: 's1',
						set_number: 1,
						pose_chart_data: [{ frame: 0, timestampSec: 0, HIP_HINGE: 130 }]
					}
				]
			}
		]);
		expect(chart.series.length).toBe(1);
		expect(chart.series[0].key).toContain('HIP_HINGE');
		expect(chart.data[0][chart.series[0].key]).toBe(130);
	});
});
