<script lang="ts">
	import { page } from '$app/stores';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import ChevronLeftIcon from '@lucide/svelte/icons/chevron-left';
	import BarChart3Icon from '@lucide/svelte/icons/bar-chart-3';
	import type { SessionExercise } from '$lib/api/sessions';

	let { data } = $props();
	const sessionId = $derived($page.params.id);

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
												{#if set.video_play_url}
													<div class="flex flex-col gap-1">
														<Badge variant="secondary">Recorded</Badge>
														<video
															src={set.video_play_url}
															controls
															class="max-h-24 w-full rounded border bg-muted"
															muted
															playsinline
															preload="metadata"
														></video>
													</div>
												{:else if set.video_url}
													<Badge variant="secondary">Recorded</Badge>
												{:else}
													<span class="text-muted-foreground">—</span>
												{/if}
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
