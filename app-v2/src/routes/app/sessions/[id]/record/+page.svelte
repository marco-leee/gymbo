<script lang="ts">
	import { page } from '$app/stores';
	import { invalidateAll } from '$app/navigation';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import * as Collapsible from '$lib/components/ui/collapsible/index.js';
	import ChevronLeftIcon from '@lucide/svelte/icons/chevron-left';
	import PlusIcon from '@lucide/svelte/icons/plus';
	import VideoIcon from '@lucide/svelte/icons/video';
	import CheckIcon from '@lucide/svelte/icons/check';
	import {
		addSet,
		recordSet,
		startSession,
		completeSession,
		type SessionExercise,
		type ExerciseSet
	} from '$lib/api/sessions';
	import { createMutation } from '@tanstack/svelte-query';

	let { data } = $props();
	const sessionId = $derived($page.params.id);
	const session = $derived(data.session);

	const startMutation = createMutation(() => ({
		mutationFn: () => startSession(sessionId!),
		onSuccess: () => invalidateAll()
	}));

	const completeMutation = createMutation(() => ({
		mutationFn: () => completeSession(sessionId!),
		onSuccess: () => invalidateAll()
	}));

	const addSetMutation = createMutation(() => ({
		mutationFn: ({ exerciseId }: { exerciseId: string }) => addSet(sessionId!, exerciseId),
		onSuccess: () => invalidateAll()
	}));

	const recordSetMutation = createMutation(() => ({
		mutationFn: (vars: {
			exerciseId: string;
			setId: string;
			payload: Parameters<typeof recordSet>[3];
		}) => recordSet(sessionId!, vars.exerciseId, vars.setId, vars.payload),
		onSuccess: () => {
			drawerOpen = false;
			invalidateAll();
		}
	}));

	let drawerOpen = $state(false);
	let selectedExercise = $state<SessionExercise | null>(null);
	let selectedSet = $state<ExerciseSet | null>(null);
	let recordForm = $state({
		actual_reps: '',
		actual_duration: '',
		weight_kg: '',
		rpe: '',
		notes: ''
	});

	function formatTime(dateStr: string): string {
		return new Date(dateStr).toLocaleTimeString(undefined, {
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function elapsedMinutes(): string {
		if (!session?.started_at) return '0';
		const end = session.completed_at ? new Date(session.completed_at) : new Date();
		const mins = Math.floor(
			(end.getTime() - new Date(session.started_at).getTime()) / 60000
		);
		return String(mins);
	}

	function openSetDrawer(exercise: SessionExercise, set: ExerciseSet) {
		selectedExercise = exercise;
		selectedSet = set;
		recordForm = {
			actual_reps: set.actual_reps != null ? String(set.actual_reps) : '',
			actual_duration: set.actual_duration != null ? String(set.actual_duration) : '',
			weight_kg: set.weight_kg != null ? String(set.weight_kg) : '',
			rpe: set.rpe != null ? String(set.rpe) : '',
			notes: set.notes ?? ''
		};
		drawerOpen = true;
	}

	function submitRecord() {
		if (!selectedExercise || !selectedSet) return;
		const payload: Parameters<typeof recordSet>[3] = {
			status: 'completed',
			notes: recordForm.notes || undefined
		};
		if (selectedExercise.measurement === 'reps' && recordForm.actual_reps) {
			payload.actual_reps = parseInt(recordForm.actual_reps, 10);
		}
		if (selectedExercise.measurement === 'duration' && recordForm.actual_duration) {
			payload.actual_duration = parseInt(recordForm.actual_duration, 10);
		}
		if (recordForm.weight_kg) payload.weight_kg = parseFloat(recordForm.weight_kg);
		if (recordForm.rpe) payload.rpe = Math.min(10, Math.max(1, parseInt(recordForm.rpe, 10)));
		recordSetMutation.mutate({
			exerciseId: selectedExercise.id,
			setId: selectedSet.id,
			payload
		});
	}

	function targetLabel(ex: SessionExercise): string {
		if (ex.measurement === 'reps') return `${ex.target_reps ?? '—'} reps`;
		return `${ex.target_duration ?? '—'}s`;
	}
</script>

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-2">
			<Button href="/app/sessions/{sessionId}" variant="ghost" size="icon">
				<ChevronLeftIcon class="h-4 w-4" />
			</Button>
			<div>
				<h1 class="text-xl font-semibold">
					{data.client?.full_name ?? session?.client_name ?? session?.client_id}
				</h1>
				<p class="text-muted-foreground text-sm">
					{formatTime(session?.scheduled_at ?? '')}
					{#if session?.status === 'in-progress'}
						· {elapsedMinutes()} min
					{/if}
				</p>
			</div>
		</div>
		<div class="flex items-center gap-2">
			<Badge variant={session?.status === 'in-progress' ? 'default' : 'outline'}>
				{session?.status ?? 'scheduled'}
			</Badge>
			{#if session?.status === 'scheduled'}
				<Button
					onclick={() => startMutation.mutate()}
					disabled={startMutation.isPending}
				>
					Start Session
				</Button>
			{/if}
			{#if session?.status === 'in-progress'}
				<Button
					variant="default"
					onclick={() => completeMutation.mutate()}
					disabled={completeMutation.isPending}
				>
					<CheckIcon class="mr-2 h-4 w-4" />
					Complete Session
				</Button>
			{/if}
		</div>
	</div>

	<!-- Exercise cards -->
	<div class="space-y-4">
		{#each (session?.exercises ?? []).sort((a, b) => a.order_index - b.order_index) as exercise (
			exercise.id
		)}
			<Collapsible.Root open={true}>
				<Card>
					<CardHeader class="pb-2">
						<Collapsible.Trigger class="flex w-full items-center justify-between text-left">
							<CardTitle class="text-base">{exercise.name}</CardTitle>
							<Badge variant="outline">{exercise.type}</Badge>
						</Collapsible.Trigger>
					</CardHeader>
					<CardContent class="space-y-3">
						<Table.Root>
							<Table.Header>
								<Table.Row>
									<Table.Head>Set</Table.Head>
									<Table.Head>Target</Table.Head>
									<Table.Head>Actual</Table.Head>
									<Table.Head>Weight</Table.Head>
									<Table.Head class="w-[100px]"></Table.Head>
								</Table.Row>
							</Table.Header>
							<Table.Body>
								{#each (exercise.sets ?? []).sort((a, b) => a.set_number - b.set_number) as set (
									set.id
								)}
									<Table.Row
										class="cursor-pointer hover:bg-muted/50"
										onclick={() => openSetDrawer(exercise, set)}
									>
										<Table.Cell class="font-medium">{set.set_number}</Table.Cell>
										<Table.Cell>{targetLabel(exercise)}</Table.Cell>
										<Table.Cell>
											{#if exercise.measurement === 'reps'}
												{set.actual_reps ?? '—'}
											{:else}
												{set.actual_duration ?? '—'}s
											{/if}
										</Table.Cell>
										<Table.Cell>{set.weight_kg ?? '—'}</Table.Cell>
										<Table.Cell>
											{#if set.status === 'completed'}
												<Badge variant="secondary">Done</Badge>
											{:else}
												<Button variant="ghost" size="sm">
													<VideoIcon class="h-4 w-4" />
												</Button>
											{/if}
										</Table.Cell>
									</Table.Row>
								{/each}
							</Table.Body>
						</Table.Root>
						{#if session?.status === 'in-progress'}
							<Button
								variant="outline"
								size="sm"
								onclick={() => addSetMutation.mutate({ exerciseId: exercise.id })}
								disabled={addSetMutation.isPending}
							>
								<PlusIcon class="mr-2 h-4 w-4" />
								Add set
							</Button>
						{/if}
					</CardContent>
				</Card>
			</Collapsible.Root>
		{/each}
	</div>

	<!-- Set recorder drawer -->
	<Sheet.Root bind:open={drawerOpen}>
		<Sheet.Content side="bottom" class="h-[70vh]">
			<Sheet.Header>
				<Sheet.Title>
					{selectedExercise?.name} — Set {selectedSet?.set_number}
				</Sheet.Title>
			</Sheet.Header>
			<div class="space-y-4 py-4">
				{#if selectedExercise?.measurement === 'reps'}
					<div class="space-y-2">
						<Label for="reps">Reps</Label>
						<Input
							id="reps"
							type="number"
							min="0"
							bind:value={recordForm.actual_reps}
							placeholder="Actual reps"
						/>
					</div>
				{:else}
					<div class="space-y-2">
						<Label for="duration">Duration (seconds)</Label>
						<Input
							id="duration"
							type="number"
							min="0"
							bind:value={recordForm.actual_duration}
							placeholder="Seconds"
						/>
					</div>
				{/if}
				<div class="space-y-2">
					<Label for="weight">Weight (kg)</Label>
					<Input
						id="weight"
						type="number"
						step="0.5"
						min="0"
						bind:value={recordForm.weight_kg}
						placeholder="0"
					/>
				</div>
				<div class="space-y-2">
					<Label for="rpe">RPE (1–10)</Label>
					<Input
						id="rpe"
						type="number"
						min="1"
						max="10"
						bind:value={recordForm.rpe}
						placeholder="1-10"
					/>
				</div>
				<div class="space-y-2">
					<Label for="notes">Notes</Label>
					<Input id="notes" bind:value={recordForm.notes} placeholder="Optional notes" />
				</div>
				<div class="rounded-md border border-dashed p-6 text-center text-muted-foreground text-sm">
					Video upload (camera or file) — coming soon
				</div>
				<Button
					class="w-full"
					onclick={submitRecord}
					disabled={recordSetMutation.isPending}
				>
					Save set
				</Button>
			</div>
		</Sheet.Content>
	</Sheet.Root>
</div>
