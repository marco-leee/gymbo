<script lang="ts">
	import * as Chart from '$lib/components/ui/chart/index.js';
	import { createChartSeekHandlers } from '$lib/pose/pose-chart-seek';
	import type { CombinedChartRow } from '$lib/pose/pose-chart-series';
	import { LineChart } from 'layerchart';

	let {
		data,
		series,
		config,
		video = null
	}: {
		data: CombinedChartRow[];
		series: { key: string; color: string }[];
		config: Chart.ChartConfig;
		video?: HTMLVideoElement | null;
	} = $props();

	const seekHandlers = $derived(createChartSeekHandlers(video));
	const chartClickable = $derived(video != null);
</script>

<Chart.Container
	{config}
	class="min-h-[320px] w-full {chartClickable ? 'cursor-pointer' : ''}"
>
	<LineChart
		{data}
		x={(d: CombinedChartRow) => d.timestampSec}
		{series}
		grid={true}
		legend
		points={chartClickable}
		onTooltipClick={chartClickable ? seekHandlers.onTooltipClick : undefined}
		onPointClick={chartClickable ? seekHandlers.onPointClick : undefined}
		props={{
			xAxis: {
				format: (v: number) => `${Number(v).toFixed(1)}s`
			}
		}}
	/>
</Chart.Container>
