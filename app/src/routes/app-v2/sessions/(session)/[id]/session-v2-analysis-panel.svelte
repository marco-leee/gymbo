<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import * as Chart from '$lib/components/ui/chart/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { LineChart } from 'layerchart';
	import BarChart3Icon from '@lucide/svelte/icons/bar-chart-3';
	import { getMediaPlayUrl } from '$lib/api/media';
	import { exerciseTypeLabel, type ExerciseSet, type SessionExercise } from '$lib/api/sessions';

	type CombinedChartRow = {
		frame: number;
		timestampSec: number;
	} & Record<string, number | undefined>;

	let { data } = $props();

	const chartPalette = [
		{ inside: '#EF4444', outside: '#F97316' },
		{ inside: '#7C3AED', outside: '#A78BFA' },
		{ inside: '#2563EB', outside: '#06B6D4' },
		{ inside: '#059669', outside: '#84CC16' },
		{ inside: '#D97706', outside: '#EAB308' }
	];

	type CombinedChartLegendItem = {
		key: string;
		label: string;
		color: string;
	};

	let analysisSheetOpen = $state(false);
	let selectedAnalysisContext = $state<{
		exerciseName: string;
		setNumber: number;
	} | null>(null);
	let playUrls = $state<Record<string, string>>({});
	let loadingVideoSetIds = $state<Record<string, boolean>>({});

	function durationMinutes(): number {
		if (!data.session.started_at || !data.session.completed_at) return 0;
		return Math.round(
			(new Date(data.session.completed_at).getTime() -
				new Date(data.session.started_at).getTime()) /
				60000
		);
	}

	function totalVolume(exercises: SessionExercise[]): number {
		return exercises.reduce((acc, ex) => {
			const sets = ex.sets ?? [];
			return (
				acc +
				sets.reduce((sacc, s) => sacc + (s.actual_reps ?? 0) * (s.weight_kg ?? 0), 0)
			);
		}, 0);
	}

	function avgRPE(exercises: SessionExercise[]): string {
		const rpes = exercises.flatMap((ex) =>
			(ex.sets ?? []).map((s) => s.rpe).filter((r): r is number => r != null)
		);
		if (rpes.length === 0) return '—';
		const avg = rpes.reduce((a, b) => a + b, 0) / rpes.length;
		return avg.toFixed(1);
	}

	const setsCompleted = $derived(
		data.session.exercises?.reduce(
			(acc: number, ex: SessionExercise) =>
				acc + (ex.sets?.filter((s: ExerciseSet) => s.status === 'completed').length ?? 0),
			0
		) ?? 0
	);
	const volume = $derived(totalVolume(data.session.exercises ?? []));
	const combinedAnalysisChart = $derived.by(() => {
		const rows = new Map<number, CombinedChartRow>();
		const legend: CombinedChartLegendItem[] = [];
		const config: Chart.ChartConfig = {};
		const series: { key: string; color: string }[] = [];
		let analyzedSetIndex = 0;

		for (const exercise of data.session.exercises ?? []) {
			for (const set of exercise.sets ?? []) {
				if (!set.pose_chart_data?.length) continue;

				const safeExerciseId = exercise.id.replace(/[^a-zA-Z0-9_]/g, '_');
				const safeSetId = set.id.replace(/[^a-zA-Z0-9_]/g, '_');
				const setKeyPrefix = `${safeExerciseId}_${safeSetId}_${set.set_number}`;
				const palette = chartPalette[analyzedSetIndex % chartPalette.length];
				const insideKey = `${setKeyPrefix}_insideKnee`;
				const outsideKey = `${setKeyPrefix}_outsideHip`;
				const insideLabel = `${exercise.name} - Set ${set.set_number} - Inside Knee`;
				const outsideLabel = `${exercise.name} - Set ${set.set_number} - Outside Hip`;

				legend.push(
					{ key: insideKey, label: insideLabel, color: palette.inside },
					{ key: outsideKey, label: outsideLabel, color: palette.outside }
				);
				series.push(
					{ key: insideKey, color: palette.inside },
					{ key: outsideKey, color: palette.outside }
				);
				config[insideKey] = { label: insideLabel, color: palette.inside };
				config[outsideKey] = { label: outsideLabel, color: palette.outside };

				for (const point of set.pose_chart_data) {
					const row: CombinedChartRow =
						rows.get(point.frame) ??
						({
							frame: point.frame,
							timestampSec: point.timestampSec
						} as CombinedChartRow);
					row[insideKey] = point.insideKnee;
					row[outsideKey] = point.outsideHip;
					rows.set(point.frame, row);
				}

				analyzedSetIndex += 1;
			}
		}

		const final = [...rows.values()].sort((a, b) => a.frame - b.frame);

		return {
			data: final,
			legend,
			series: [...series].reverse(),
			config
		};
	});
	const hasCombinedAnalysisData = $derived(combinedAnalysisChart.series.length > 0);

	function openCombinedAnalysisSheet(exerciseName: string, set: ExerciseSet) {
		selectedAnalysisContext = {
			exerciseName,
			setNumber: set.set_number
		};
		analysisSheetOpen = true;
	}

	function getSetVideoSrc(set: ExerciseSet): string | null {
		return set.video_play_url ?? playUrls[set.id] ?? null;
	}

	function isVideoLoading(setId: string): boolean {
		return Boolean(loadingVideoSetIds[setId]);
	}

	async function loadVideoPlayback(set: ExerciseSet) {
		if (!set.video_url || getSetVideoSrc(set) || isVideoLoading(set.id)) return;

		loadingVideoSetIds = { ...loadingVideoSetIds, [set.id]: true };
		try {
			const playUrl = await getMediaPlayUrl(set.video_url);
			playUrls = { ...playUrls, [set.id]: playUrl };
		} finally {
			const nextLoadingVideoSetIds = { ...loadingVideoSetIds };
			delete nextLoadingVideoSetIds[set.id];
			loadingVideoSetIds = nextLoadingVideoSetIds;
		}
	}

	const summaryLine = $derived(
		`${data.session.exercises?.length ?? 0} exercises, ${setsCompleted} sets completed, ${durationMinutes()} min, avg RPE ${avgRPE(data.session.exercises ?? [])}.`
	);
</script>

<p class="sr-only" aria-live="polite">
	Analysis summary: {summaryLine}
</p>

{#if data.session.status !== 'completed' && setsCompleted === 0}
	<Card class="border-dashed">
		<CardHeader>
			<CardTitle class="text-base">No session results yet</CardTitle>
			<p class="text-muted-foreground text-sm">
				Analysis and videos show up after you record sets. Open the Overview tab to start recording.
			</p>
		</CardHeader>
	</Card>
{/if}

<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
	<Card>
		<CardHeader class="pb-2">
			<CardTitle class="text-sm font-medium text-muted-foreground">Exercises</CardTitle>
		</CardHeader>
		<CardContent>
			<span class="text-2xl font-semibold tabular-nums">{data.session.exercises?.length ?? 0}</span>
		</CardContent>
	</Card>
	<Card>
		<CardHeader class="pb-2">
			<CardTitle class="text-sm font-medium text-muted-foreground">Sets completed</CardTitle>
		</CardHeader>
		<CardContent>
			<span class="text-2xl font-semibold tabular-nums">{setsCompleted}</span>
		</CardContent>
	</Card>
	<Card>
		<CardHeader class="pb-2">
			<CardTitle class="text-sm font-medium text-muted-foreground">Duration</CardTitle>
		</CardHeader>
		<CardContent>
			<span class="text-2xl font-semibold tabular-nums">{durationMinutes()} min</span>
		</CardContent>
	</Card>
	<Card>
		<CardHeader class="pb-2">
			<CardTitle class="text-sm font-medium text-muted-foreground">Avg RPE</CardTitle>
		</CardHeader>
		<CardContent>
			<span class="text-2xl font-semibold tabular-nums">{avgRPE(data.session.exercises ?? [])}</span>
		</CardContent>
	</Card>
</div>

{#if volume > 0}
	<Card>
		<CardHeader class="pb-2">
			<CardTitle class="text-sm font-medium text-muted-foreground">Total volume (kg)</CardTitle>
		</CardHeader>
		<CardContent>
			<span class="text-2xl font-semibold tabular-nums">{volume}</span>
		</CardContent>
	</Card>
{/if}

<Card>
	<CardHeader>
		<CardTitle>Exercises & sets</CardTitle>
		<p class="text-muted-foreground text-sm">
			Video analysis and form feedback appear when processing is available. Table below supplements charts for
			accessibility.
		</p>
	</CardHeader>
	<CardContent>
		{#if data.session.exercises?.length}
			<div class="space-y-4">
				{#each (data.session.exercises ?? []).sort((a: SessionExercise, b: SessionExercise) => a.order_index - b.order_index) as exercise (exercise.id)}
					<div class="rounded-lg border p-3">
						<div class="mb-2 space-y-1">
							<div class="flex items-center justify-between gap-2">
								<span class="font-medium">{exercise.name}</span>
								<Badge variant="outline" class="capitalize">{exerciseTypeLabel(exercise.type)}</Badge>
							</div>
							{#if exercise.notes?.trim()}
								<p class="text-muted-foreground text-xs whitespace-pre-wrap">{exercise.notes}</p>
							{/if}
						</div>
						<Table.Root>
							<Table.Header>
								<Table.Row>
									<Table.Head>Set</Table.Head>
									<Table.Head>Target</Table.Head>
									<Table.Head>Actual</Table.Head>
									<Table.Head>Weight</Table.Head>
									<Table.Head>RPE</Table.Head>
									<Table.Head>Video</Table.Head>
								</Table.Row>
							</Table.Header>
							<Table.Body>
								{#each (exercise.sets ?? []).sort((a: ExerciseSet, b: ExerciseSet) => a.set_number - b.set_number) as set (set.id)}
									<Table.Row>
										<Table.Cell class="tabular-nums">{set.set_number}</Table.Cell>
										<Table.Cell>
											{#if exercise.measurement === 'reps'}
												{exercise.target_reps ?? '—'} reps
											{:else}
												{exercise.target_duration ?? '—'}s
											{/if}
										</Table.Cell>
										<Table.Cell class="tabular-nums">
											{#if exercise.measurement === 'reps'}
												{set.actual_reps ?? '—'}
											{:else}
												{set.actual_duration ?? '—'}s
											{/if}
										</Table.Cell>
										<Table.Cell class="tabular-nums">{set.weight_kg ?? '—'} kg</Table.Cell>
										<Table.Cell class="tabular-nums">{set.rpe ?? '—'}</Table.Cell>
										<Table.Cell>
											<div class="flex min-w-[140px] flex-col gap-2">
												{#if getSetVideoSrc(set)}
													<Badge variant="secondary">Recorded</Badge>
													<video
														src={getSetVideoSrc(set) ?? undefined}
														controls
														class="max-h-24 w-full rounded border bg-muted"
														muted
														playsinline
														preload="metadata"
													></video>
												{:else if set.video_url}
													<Badge variant="secondary">Recorded</Badge>
													<Button
														type="button"
														variant="outline"
														size="sm"
														class="min-h-10 w-full"
														onclick={() => loadVideoPlayback(set)}
														disabled={isVideoLoading(set.id)}
													>
														{isVideoLoading(set.id) ? 'Loading video...' : 'Load video'}
													</Button>
												{:else}
													<span class="text-muted-foreground">—</span>
												{/if}
												<Button
													type="button"
													variant="outline"
													size="sm"
													class="min-h-10 w-full"
													onclick={() => openCombinedAnalysisSheet(exercise.name, set)}
													disabled={!hasCombinedAnalysisData}
												>
													<BarChart3Icon class="mr-2 h-4 w-4 shrink-0" aria-hidden="true" />
													View chart
												</Button>
											</div>
										</Table.Cell>
									</Table.Row>
								{/each}
							</Table.Body>
						</Table.Root>
					</div>
				{/each}
			</div>
		{:else}
			<p class="text-muted-foreground py-4 text-center text-sm">No exercises in this session.</p>
		{/if}
	</CardContent>
</Card>

<Sheet.Root bind:open={analysisSheetOpen}>
	<Sheet.Content
		side="bottom"
		class="flex h-[80vh] max-h-[80vh] flex-col overflow-hidden rounded-t-xl"
	>
		<Sheet.Header>
			<Sheet.Title>Combined set analysis</Sheet.Title>
			{#if selectedAnalysisContext}
				<p class="text-muted-foreground text-sm">
					Opened from {selectedAnalysisContext.exerciseName} set {selectedAnalysisContext.setNumber}. Showing all
					saved analysis lines in this session.
				</p>
			{/if}
		</Sheet.Header>
		<div class="min-h-0 flex-1 overflow-y-auto p-4">
			{#if hasCombinedAnalysisData}
				<div class="space-y-4">
					<div>
						<h3 class="text-sm font-medium">All analysis data points</h3>
						<p class="text-muted-foreground text-sm">
							Each set contributes two lines: inside knee and outside hip. Colors pair with the legend.
						</p>
					</div>

					<div class="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
						{#each combinedAnalysisChart.legend as item (item.key)}
							<div class="flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
								<span
									class="h-2.5 w-2.5 shrink-0 rounded-[2px]"
									style={`background: ${item.color};`}
									aria-hidden="true"
								></span>
								<span class="truncate">{item.label}</span>
							</div>
						{/each}
					</div>

					<Chart.Container config={combinedAnalysisChart.config} class="min-h-[320px] w-full">
						<LineChart
							data={combinedAnalysisChart.data}
							x={(d) => d.timestampSec}
							series={combinedAnalysisChart.series}
							grid={true}
							legend
						/>
					</Chart.Container>
				</div>
			{:else}
				<div
					class="text-muted-foreground flex min-h-[320px] items-center justify-center rounded-md border text-sm"
					role="status"
				>
					No saved pose analysis data yet.
				</div>
			{/if}
		</div>
	</Sheet.Content>
</Sheet.Root>
