<script lang="ts">
	import PoseSetChart from '$lib/pose/pose-set-chart.svelte';
	import type { PoseChartPoint } from '$lib/pose/pose-chart-types';

	export type ChartPoint = PoseChartPoint;

	let {
		data = [],
		exerciseKey = 'squat',
		video = null,
		emptyHint
	}: {
		data?: readonly Record<string, unknown>[];
		exerciseKey?: string;
		video?: HTMLVideoElement | null;
		emptyHint?: string;
	} = $props();
</script>

<PoseSetChart {data} {exerciseKey} {video} {emptyHint} />
