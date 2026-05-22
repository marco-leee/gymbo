import { describe, expect, test } from 'bun:test';
import {
	createChartSeekHandlers,
	seekVideoToTimestamp,
	timestampSecFromChartRow
} from './pose-chart-seek';

describe('pose-chart-seek', () => {
	test('timestampSecFromChartRow reads timestampSec', () => {
		expect(timestampSecFromChartRow({ frame: 1, timestampSec: 2.5 })).toBe(2.5);
		expect(timestampSecFromChartRow({ frame: 1 })).toBe(null);
	});

	test('seekVideoToTimestamp sets currentTime', () => {
		const video = {
			duration: 10,
			currentTime: 0,
			play: () => Promise.resolve()
		} as HTMLVideoElement;
		seekVideoToTimestamp(video, 3.2);
		expect(video.currentTime).toBeCloseTo(3.2);
	});

	test('createChartSeekHandlers seeks from tooltip data', () => {
		let sought: number | null = null;
		const video = {
			duration: 60,
			currentTime: 0,
			play: () => Promise.resolve()
		} as HTMLVideoElement;
		const handlers = createChartSeekHandlers(video, (t) => {
			sought = t;
		});
		handlers.onTooltipClick({} as MouseEvent, {
			data: { frame: 10, timestampSec: 4.5, INSIDE_KNEE: 90 }
		});
		expect(sought).toBe(4.5);
		expect(video.currentTime).toBeCloseTo(4.5);
	});
});
