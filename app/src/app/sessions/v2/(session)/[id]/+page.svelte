<script lang="ts">
	import { page } from '$app/stores';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import VideoIcon from '@lucide/svelte/icons/video';
	import BarChart3Icon from '@lucide/svelte/icons/bar-chart-3';
	import type { SessionExercise } from '$lib/api/sessions';

	let { data } = $props();

	const sessionId = $derived($page.params.id);
	const view = $derived(($page.url.searchParams.get('view') ?? 'overview') as
		| 'overview'
		| 'plan'
		| 'analysis');

	function totalSetsCompleted(exercises: SessionExercise[]): number {
		return exercises.reduce(
			(acc, ex) => acc + (ex.sets?.filter((s) => s.status === 'completed').length ?? 0),
			0
		);
	}

	function totalSetsPlanned(exercises: SessionExercise[]): number {
		return exercises.reduce((acc, ex) => acc + (ex.sets?.length ?? ex.target_sets ?? 0), 0);
	}

	const setsCompleted = $derived(totalSetsCompleted(data.session.exercises ?? []));
	const setsPlanned = $derived(totalSetsPlanned(data.session.exercises ?? []));

	const showRecordPrimary = $derived(
		data.session.status === 'scheduled' || data.session.status === 'in-progress'
	);
</script>

{#if view === 'overview'}
	<div class="flex flex-col gap-4">
		<div class="flex flex-wrap items-center gap-2">
			{#if data.session.status === 'completed'}
				<Button href="/app/sessions/v2/{sessionId}?view=analysis" class="min-h-11">
					<BarChart3Icon class="mr-2 h-4 w-4" aria-hidden="true" />
					View analysis
				</Button>
				<Button href="/app/sessions/v2/{sessionId}?view=plan" variant="outline" class="min-h-11">
					View plan
				</Button>
			{:else if showRecordPrimary}
				<Button href="/app/sessions/v2/{sessionId}/record" class="min-h-11">
					<VideoIcon class="mr-2 h-4 w-4" aria-hidden="true" />
					{data.session.status === 'in-progress' ? 'Continue recording' : 'Record session'}
				</Button>
				<Button href="/app/sessions/v2/{sessionId}?view=plan" variant="outline" class="min-h-11">
					View plan
				</Button>
				<Button href="/app/sessions/v2/{sessionId}?view=analysis" variant="outline" class="min-h-11">
					Analysis
				</Button>
			{:else}
				<Button href="/app/sessions/v2/{sessionId}?view=plan" variant="outline" class="min-h-11">
					View plan
				</Button>
				<Button href="/app/sessions/v2/{sessionId}?view=analysis" variant="outline" class="min-h-11">
					Analysis
				</Button>
			{/if}
		</div>

		<div class="grid gap-4 sm:grid-cols-3">
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
					<CardTitle class="text-sm font-medium text-muted-foreground">Sets</CardTitle>
				</CardHeader>
				<CardContent>
					<span class="text-2xl font-semibold tabular-nums">{setsCompleted} / {setsPlanned}</span>
				</CardContent>
			</Card>
			<Card>
				<CardHeader class="pb-2">
					<CardTitle class="text-sm font-medium text-muted-foreground">Duration</CardTitle>
				</CardHeader>
				<CardContent>
					{#if data.session.started_at && data.session.completed_at}
						<span class="text-2xl font-semibold tabular-nums">
							{Math.round(
								(new Date(data.session.completed_at).getTime() -
									new Date(data.session.started_at).getTime()) /
									60000
							)}
							min
						</span>
					{:else}
						<span class="text-muted-foreground">—</span>
					{/if}
				</CardContent>
			</Card>
		</div>

		{#if data.session.notes}
			<Card>
				<CardHeader class="pb-2">
					<CardTitle class="text-sm font-medium">Notes</CardTitle>
				</CardHeader>
				<CardContent class="text-muted-foreground text-sm whitespace-pre-wrap">
					{data.session.notes}
				</CardContent>
			</Card>
		{/if}
	</div>
{:else if view === 'plan'}
	<Card>
		<CardHeader>
			<CardTitle>Plan</CardTitle>
			<p class="text-muted-foreground text-sm">Exercises and targets for this session.</p>
		</CardHeader>
		<CardContent>
			{#if data.session.exercises?.length}
				<div class="space-y-4">
					{#each (data.session.exercises ?? []).sort((a, b) => a.order_index - b.order_index) as exercise (exercise.id)}
						<div class="rounded-lg border p-3">
							<div class="mb-2 flex items-center justify-between gap-2">
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
										<Table.Head>Status</Table.Head>
									</Table.Row>
								</Table.Header>
								<Table.Body>
									{#each (exercise.sets ?? []).sort((a, b) => a.set_number - b.set_number) as set (set.id)}
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
											<Table.Cell>
												<Badge variant="outline" class="text-xs">{set.status}</Badge>
											</Table.Cell>
										</Table.Row>
									{/each}
								</Table.Body>
							</Table.Root>
							{#if !exercise.sets?.length}
								<p class="text-muted-foreground py-2 text-sm">No sets recorded yet.</p>
							{/if}
						</div>
					{/each}
				</div>
			{:else}
				<p class="text-muted-foreground py-4 text-center text-sm">No exercises in this session.</p>
			{/if}
		</CardContent>
	</Card>
{:else if view === 'analysis'}
	{#await import('./session-v2-analysis-panel.svelte')}
		<div class="text-muted-foreground rounded-lg border border-dashed p-8 text-center text-sm" role="status">
			Loading analysis…
		</div>
	{:then { default: SessionV2AnalysisPanel }}
		<div class="flex flex-col gap-4">
			<SessionV2AnalysisPanel {data} />
		</div>
	{/await}
{/if}
