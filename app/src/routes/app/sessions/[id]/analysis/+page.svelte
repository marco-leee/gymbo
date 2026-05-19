<script lang="ts">
	import { page } from '$app/stores';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import * as Chart from '$lib/components/ui/chart/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { LineChart } from 'layerchart';
	import ChevronLeftIcon from '@lucide/svelte/icons/chevron-left';
	import BarChart3Icon from '@lucide/svelte/icons/bar-chart-3';
	import { getMediaPlayUrl } from '$lib/api/media';
	import type { ExerciseSet, SessionExercise } from '$lib/api/sessions';

	let { data } = $props();
	const sessionId = $derived($page.params.id);
	const chartPalette = [
		{ inside: '#EF4444', outside: '#F97316' },
		{ inside: '#7C3AED', outside: '#A78BFA' },
		{ inside: '#2563EB', outside: '#06B6D4' },
		{ inside: '#059669', outside: '#84CC16' },
		{ inside: '#D97706', outside: '#EAB308' }
	];

	type CombinedChartRow = {
		frame: number;
		timestampSec: number;
		[key: string]: number | undefined;
	};

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

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString(undefined, {
			weekday: 'short',
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function formatTime(dateStr: string): string {
		return new Date(dateStr).toLocaleTimeString(undefined, {
			hour: '2-digit',
			minute: '2-digit'
		});
	}

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
		const rpes = exercises.flatMap(ex =>
			(ex.sets ?? []).map(s => s.rpe).filter((r): r is number => r != null)
		);
		if (rpes.length === 0) return '—';
		const avg = rpes.reduce((a, b) => a + b, 0) / rpes.length;
		return avg.toFixed(1);
	}

	const setsCompleted = $derived(
		data.session.exercises?.reduce(
			(acc, ex) => acc + (ex.sets?.filter(s => s.status === 'completed').length ?? 0),
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
					{
						key: outsideKey,
						label: outsideLabel,
						color: palette.outside
					}
				);
				series.push(
					{ key: insideKey, color: palette.inside },
					{
						key: outsideKey,
						color: palette.outside
					}
				);
				config[insideKey] = { label: insideLabel, color: palette.inside };
				config[outsideKey] = {
					label: outsideLabel,
					color: palette.outside
				};

				for (const point of set.pose_chart_data) {
					const row = rows.get(point.frame) ?? {
						frame: point.frame,
						timestampSec: point.timestampSec
					};
					row[insideKey] = point.insideKnee;
					row[outsideKey] = point.outsideHip;
					rows.set(point.frame, row);
				}

				analyzedSetIndex += 1;
			}
		}

		const final = [...rows.values()].sort((a, b) => a.frame - b.frame);
		console.log(final);

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
</script>

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<div class="flex items-center gap-2">
		<Button href="/app/sessions/{sessionId}" variant="ghost" size="icon">
			<ChevronLeftIcon class="h-4 w-4" />
		</Button>
		<div class="flex-1">
			<h1 class="text-2xl font-semibold">Session Analysis</h1>
			<p class="text-muted-foreground text-sm">
				{data.client?.full_name ?? data.session.client_name ?? data.session.client_id} · {formatDate(
					data.session.scheduled_at
				)} {formatTime(data.session.scheduled_at)}
			</p>
		</div>
	</div>

	<!-- Overview cards -->
	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		<Card>
			<CardHeader class="pb-2">
				<CardTitle class="text-sm font-medium text-muted-foreground">Exercises</CardTitle>
			</CardHeader>
			<CardContent>
				<span class="text-2xl font-semibold">{data.session.exercises?.length ?? 0}</span>
			</CardContent>
		</Card>
		<Card>
			<CardHeader class="pb-2">
				<CardTitle class="text-sm font-medium text-muted-foreground">Sets completed</CardTitle>
			</CardHeader>
			<CardContent>
				<span class="text-2xl font-semibold">{setsCompleted}</span>
			</CardContent>
		</Card>
		<Card>
			<CardHeader class="pb-2">
				<CardTitle class="text-sm font-medium text-muted-foreground">Duration</CardTitle>
			</CardHeader>
			<CardContent>
				<span class="text-2xl font-semibold">{durationMinutes()} min</span>
			</CardContent>
		</Card>
		<Card>
			<CardHeader class="pb-2">
				<CardTitle class="text-sm font-medium text-muted-foreground">Avg RPE</CardTitle>
			</CardHeader>
			<CardContent>
				<span class="text-2xl font-semibold">{avgRPE(data.session.exercises ?? [])}</span>
			</CardContent>
		</Card>
	</div>

	{#if volume > 0}
		<Card>
			<CardHeader class="pb-2">
				<CardTitle class="text-sm font-medium text-muted-foreground">Total volume (kg)</CardTitle>
			</CardHeader>
			<CardContent>
				<span class="text-2xl font-semibold">{volume}</span>
			</CardContent>
		</Card>
	{/if}

	<!-- Exercise analysis list -->
	<Card>
		<CardHeader>
			<CardTitle>Exercises & sets</CardTitle>
			<p class="text-muted-foreground text-sm">
				Video analysis and form feedback will appear here when processing is available.
			</p>
		</CardHeader>
		<CardContent>
			{#if data.session.exercises?.length}
				<div class="space-y-4">
					{#each (data.session.exercises ?? []).sort(
						(a, b) => a.order_index - b.order_index
					) as exercise (exercise.id)}
						<div class="rounded-lg border p-3">
							<div class="mb-2 flex items-center justify-between">
								<span class="font-medium">{exercise.name}</span>
								<Badge variant="outline">{exercise.type}</Badge>
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
									{#each (exercise.sets ?? []).sort(
										(a, b) => a.set_number - b.set_number
									) as set (set.id)}
										<Table.Row>
											<Table.Cell>{set.set_number}</Table.Cell>
											<Table.Cell>
												{#if exercise.measurement === 'reps'}
													{exercise.target_reps ?? '—'} reps
												{:else}
													{exercise.target_duration ?? '—'}s
												{/if}
											</Table.Cell>
											<Table.Cell>
												{#if exercise.measurement === 'reps'}
													{set.actual_reps ?? '—'}
												{:else}
													{set.actual_duration ?? '—'}s
												{/if}
											</Table.Cell>
											<Table.Cell>{set.weight_kg ?? '—'} kg</Table.Cell>
											<Table.Cell>{set.rpe ?? '—'}</Table.Cell>
											<Table.Cell>
												<div class="flex flex-col gap-2">
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
															class="w-full"
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
														class="w-full"
														onclick={() => openCombinedAnalysisSheet(exercise.name, set)}
														disabled={!hasCombinedAnalysisData}
													>
														<BarChart3Icon class="mr-2 h-4 w-4" />
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
</div>

<Sheet.Root bind:open={analysisSheetOpen}>
	<Sheet.Content
		side="bottom"
		class="flex h-[80vh] max-h-[80vh] flex-col overflow-hidden rounded-t-xl"
	>
		<Sheet.Header>
			<Sheet.Title>Combined set analysis</Sheet.Title>
			{#if selectedAnalysisContext}
				<p class="text-muted-foreground text-sm">
					Opened from {selectedAnalysisContext.exerciseName} set {selectedAnalysisContext.setNumber}.
					Showing all saved analysis lines in this session.
				</p>
			{/if}
		</Sheet.Header>
		<div class="min-h-0 flex-1 overflow-y-auto p-4">
			{#if hasCombinedAnalysisData}
				<div class="space-y-4">
					<div>
						<h3 class="text-sm font-medium">All analysis data points</h3>
						<p class="text-muted-foreground text-sm">
							Each set contributes two lines: inside knee and outside hip.
						</p>
					</div>

					<div class="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
						{#each combinedAnalysisChart.legend as item (item.key)}
							<div class="flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
								<span
									class="h-2.5 w-2.5 shrink-0 rounded-[2px]"
									style={`background: ${item.color};`}
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
				>
					No saved pose analysis data yet.
				</div>
			{/if}
		</div>
	</Sheet.Content>
</Sheet.Root>
