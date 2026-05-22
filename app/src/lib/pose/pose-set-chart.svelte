<script lang="ts">
	import * as Chart from "$lib/components/ui/chart/index.js";
	import type { PoseChartPoint } from "$lib/pose/pose-chart-types";
	import {
		chartConfigFromSeries,
		chartSeriesForExerciseKey,
		normalizePoseChartData,
		type PoseChartSeriesItem,
	} from "$lib/pose/pose-chart-series";
	import { createChartSeekHandlers } from "$lib/pose/pose-chart-seek";
	import { LineChart, Spline } from "layerchart";

	export type ChartPoint = PoseChartPoint;

	let {
		data = [],
		exerciseKey = "squat",
		video = null,
		emptyHint = "Upload a video to populate the angle chart.",
		onSeek,
	}: {
		data?: readonly Record<string, unknown>[];
		exerciseKey?: string;
		video?: HTMLVideoElement | null;
		emptyHint?: string;
		onSeek?: (timestampSec: number) => void;
	} = $props();

	const normalized = $derived(normalizePoseChartData(data));
	const series = $derived(chartSeriesForExerciseKey(exerciseKey, normalized));
	const chartConfig = $derived(chartConfigFromSeries(series));
	const lineSeries = $derived(
		series.map((s: PoseChartSeriesItem) => ({ key: s.key, color: s.color })),
	);
	const seekHandlers = $derived(createChartSeekHandlers(video, onSeek));
	const chartClickable = $derived(video != null);
</script>

<Chart.Container
	config={chartConfig}
	class="min-h-[200px] w-full {chartClickable ? 'cursor-pointer' : ''}"
>
	{#if normalized.length > 0 && series.length > 0}
		<LineChart
			data={normalized}
			x={(d: PoseChartPoint) => d.timestampSec}
			series={lineSeries}
			grid={true}
			points={chartClickable}
			onTooltipClick={chartClickable ? seekHandlers.onTooltipClick : undefined}
			onPointClick={chartClickable ? seekHandlers.onPointClick : undefined}
			props={{
				xAxis: {
					format: (v: number) => `${Number(v).toFixed(1)}s`,
				},
				yAxis: {
					format: (v: number) => `${Number(v).toFixed(0)}°`,
				},
			}}
			legend={true}
		>
		</LineChart>
	{:else}
		<div
			class="text-muted-foreground flex min-h-[200px] items-center justify-center text-sm"
		>
			{emptyHint}
		</div>
	{/if}
</Chart.Container>
