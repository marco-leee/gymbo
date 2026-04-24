<script lang="ts">
	import * as Chart from "$lib/components/ui/chart/index.js";
	import type { SquatChartPoint } from "$lib/pose/types";
	import { LineChart } from "layerchart";
	export type ChartPoint = SquatChartPoint;

	let {
		data = [],
		emptyHint = "Upload a video to populate the squat angle chart.",
	}: { data?: ChartPoint[]; emptyHint?: string } = $props();

	const series = [
		{ key: "insideKnee", color: "red" },
		{ key: "outsideHip", color: "blue" },
	];

	const chartConfig = {
		insideKnee: {
			label: "Inside Knee",
			color: "hsl(var(--chart-1))",
		},
		outsideHip: {
			label: "Outside Hip",
			color: "hsl(var(--chart-2))",
		},
	} satisfies Chart.ChartConfig;
</script>

<Chart.Container config={chartConfig} class="min-h-[200px] w-full">
	{#if data.length > 0}
		<LineChart data={data} x={(d) => d.frame} series={series} grid={true} />
	{:else}
		<div class="text-muted-foreground flex min-h-[200px] items-center justify-center px-4 text-center text-sm">
			{emptyHint}
		</div>
	{/if}
</Chart.Container>
