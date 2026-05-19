<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import ChevronLeftIcon from '@lucide/svelte/icons/chevron-left';
	import UserIcon from '@lucide/svelte/icons/user';
	import VideoIcon from '@lucide/svelte/icons/video';
	import BarChart3Icon from '@lucide/svelte/icons/bar-chart-3';
	import PencilIcon from '@lucide/svelte/icons/pencil';
	import Trash2Icon from '@lucide/svelte/icons/trash-2';
	import type { SessionExercise, ExerciseSet } from '$lib/api/sessions';
	import { deleteSession } from '$lib/api/sessions';

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

	function getStatusBadgeVariant(
		status: string
	): 'default' | 'secondary' | 'destructive' | 'outline' {
		switch (status) {
			case 'scheduled':
				return 'outline';
			case 'in-progress':
				return 'default';
			case 'completed':
				return 'secondary';
			case 'cancelled':
				return 'destructive';
			default:
				return 'outline';
		}
	}

	function totalSetsCompleted(exercises: SessionExercise[]): number {
		return exercises.reduce(
			(acc, ex) => acc + (ex.sets?.filter(s => s.status === 'completed').length ?? 0),
			0
		);
	}

	function totalSetsPlanned(exercises: SessionExercise[]): number {
		return exercises.reduce((acc, ex) => acc + (ex.sets?.length ?? ex.target_sets ?? 0), 0);
	}

	function hasVideos(session: typeof data.session): boolean {
		return session.exercises?.some(ex =>
			ex.sets?.some(s => s.video_url)
		) ?? false;
	}

	async function handleDelete() {
		if (!confirm('Delete this session? This cannot be undone.')) return;
		const id = sessionId;
		if (!id) return;
		try {
			await deleteSession(id);
			await goto('/app/sessions');
		} catch (e) {
			alert(e instanceof Error ? e.message : 'Failed to delete');
		}
	}

	const canEdit = $derived(
		data.session.status === 'scheduled' && !hasVideos(data.session)
	);
	const canDelete = $derived(
		(data.session.status === 'scheduled' || data.session.status === 'in-progress') &&
			!hasVideos(data.session)
	);
	const setsCompleted = $derived(totalSetsCompleted(data.session.exercises ?? []));
	const setsPlanned = $derived(totalSetsPlanned(data.session.exercises ?? []));
</script>

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<div class="flex items-center gap-2">
		<Button href="/app/sessions" variant="ghost" size="icon">
			<ChevronLeftIcon class="h-4 w-4" />
		</Button>
		<div class="flex-1">
			<h1 class="text-2xl font-semibold">Session</h1>
			<p class="text-muted-foreground text-sm">
				{data.client?.full_name ?? data.session.client_name ?? data.session.client_id} · {formatDate(
					data.session.scheduled_at
				)} {formatTime(data.session.scheduled_at)}
			</p>
		</div>
		<Badge variant={getStatusBadgeVariant(data.session.status)}>
			{data.session.status.replace('-', ' ')}
		</Badge>
	</div>

	<!-- Action buttons -->
	<div class="flex flex-wrap items-center gap-2">
		{#if data.session.status === 'scheduled' || data.session.status === 'in-progress'}
			<Button href="/app/sessions/{sessionId}/record">
				<VideoIcon class="mr-2 h-4 w-4" />
				Record
			</Button>
		{/if}
		<Button href="/app/sessions/{sessionId}/analysis">
			<BarChart3Icon class="mr-2 h-4 w-4" />
			Analysis
		</Button>
		{#if canEdit}
			<Button href="/app/sessions/{sessionId}/edit" variant="outline">
				<PencilIcon class="mr-2 h-4 w-4" />
				Edit
			</Button>
		{/if}
		{#if canDelete}
			<Button variant="outline" onclick={handleDelete}>
				<Trash2Icon class="mr-2 h-4 w-4" />
				Delete
			</Button>
		{/if}
	</div>

	<!-- Summary cards -->
	<div class="grid gap-4 sm:grid-cols-3">
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
				<CardTitle class="text-sm font-medium text-muted-foreground">Sets</CardTitle>
			</CardHeader>
			<CardContent>
				<span class="text-2xl font-semibold">{setsCompleted} / {setsPlanned}</span>
			</CardContent>
		</Card>
		<Card>
			<CardHeader class="pb-2">
				<CardTitle class="text-sm font-medium text-muted-foreground">Duration</CardTitle>
			</CardHeader>
			<CardContent>
				{#if data.session.started_at && data.session.completed_at}
					<span class="text-2xl font-semibold">
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

	<!-- Exercise list -->
	<Card>
		<CardHeader>
			<CardTitle>Exercises</CardTitle>
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
										<Table.Head>Status</Table.Head>
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
											<Table.Cell>
												<Badge variant="outline" class="text-xs">
													{set.status}
												</Badge>
											</Table.Cell>
										</Table.Row>
									{/each}
								</Table.Body>
							</Table.Root>
							{#if !exercise.sets?.length}
								<p class="text-muted-foreground py-2 text-sm">
									No sets recorded yet.
								</p>
							{/if}
						</div>
					{/each}
				</div>
			{:else}
				<p class="text-muted-foreground py-4 text-center text-sm">No exercises in this session.</p>
			{/if}
		</CardContent>
	</Card>
</div>
