<script lang="ts">
	import { goto } from '$app/navigation';
	import { createQuery, createMutation } from '@tanstack/svelte-query';
	import { Button } from '$lib/components/ui/button/index.js';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import * as Collapsible from '$lib/components/ui/collapsible/index.js';
	import ChevronLeftIcon from '@lucide/svelte/icons/chevron-left';
	import UserIcon from '@lucide/svelte/icons/user';
	import PlusIcon from '@lucide/svelte/icons/plus';
	import Trash2Icon from '@lucide/svelte/icons/trash-2';
	import { listClients } from '$lib/api/clients';
	import { createSession } from '$lib/api/sessions';
	import SessionV2ExerciseFields from '$lib/components/session-v2-exercise-fields.svelte';
	import {
		emptySessionExerciseFormRow,
		sessionExerciseApiBodyFromFormRow,
		type SessionExerciseFormRow
	} from '$lib/exercises/catalog';

	type ExerciseRow = SessionExerciseFormRow;

	function defaultExerciseRow(): ExerciseRow {
		return emptySessionExerciseFormRow();
	}

	const now = new Date();
	const defaultDate = now.toISOString().slice(0, 10);
	const defaultTime = now.toTimeString().slice(0, 5);

	let clientId = $state('');
	let date = $state(defaultDate);
	let time = $state(defaultTime);
	let notes = $state('');
	let exercises = $state<ExerciseRow[]>([]);

	const clientsQuery = createQuery(() => ({
		queryKey: ['clients', 'all'],
		queryFn: () => listClients()
	}));

	const createMutationState = createMutation(() => ({
		mutationFn: (payload: {
			client_id: string;
			scheduled_at: string;
			notes?: string;
			exercises: Omit<import('$lib/api/sessions').SessionExercise, 'id'>[];
		}) => createSession(payload),
		onSuccess: (session) => {
			goto(`/app-v2/sessions/${session.id}?view=session`);
		}
	}));

	function addExercise() {
		exercises = [...exercises, defaultExerciseRow()];
	}

	function removeExercise(index: number) {
		exercises = exercises.filter((_, i) => i !== index);
	}

	function handleSubmit() {
		if (!clientId) {
			alert('Please select a client');
			return;
		}
		const payloadExercises = exercises.map((row, idx) => {
			const hasName = row.name.trim().length > 0;
			const hasTarget =
				row.measurement === 'reps'
					? row.target_reps != null && row.target_reps >= 0
					: row.target_duration != null && row.target_duration >= 0;
			if (!hasName || !hasTarget) {
				return null;
			}
			return {
				...sessionExerciseApiBodyFromFormRow(row),
				order_index: idx
			};
		});
		const valid = payloadExercises.filter((ex): ex is NonNullable<typeof ex> => ex != null);
		const hasPartial = exercises.some((row) => {
			const filled =
				row.name.trim().length > 0 ||
				row.target_reps != null ||
				row.target_duration != null;
			const complete =
				row.name.trim().length > 0 &&
				(row.measurement === 'reps'
					? row.target_reps != null && row.target_reps >= 0
					: row.target_duration != null && row.target_duration >= 0);
			return filled && !complete;
		});
		if (hasPartial) {
			alert('Fill all exercise fields (name and target) or remove the row.');
			return;
		}
		const scheduled_at = new Date(`${date}T${time}`).toISOString();
		createMutationState.mutate({
			client_id: clientId,
			scheduled_at,
			notes: notes || undefined,
			exercises: valid
		});
	}
</script>

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<div class="flex items-center gap-2">
		<Button href="/app-v2/sessions" variant="ghost" size="icon" aria-label="Back to sessions">
			<ChevronLeftIcon class="h-4 w-4" />
		</Button>
		<h1 class="text-2xl font-semibold">New Session</h1>
	</div>

	<div class="flex w-full justify-center">
		<Card class="w-full max-w-6xl">
			<CardHeader>
				<CardTitle>Session Information</CardTitle>
				<CardDescription>Set up a new training session (hub v2)</CardDescription>
			</CardHeader>
			<CardContent class="space-y-4">
				<div class="space-y-2">
					<Label for="client">Client *</Label>
					<Select.Root type="single" value={clientId} onValueChange={(v) => (clientId = v ?? '')}>
						<Select.Trigger class="w-full min-h-11">
							<UserIcon class="mr-2 h-4 w-4" aria-hidden="true" />
							<span class={clientId ? '' : 'text-muted-foreground'}>
								{clientId && clientsQuery.data?.clients
									? (clientsQuery.data.clients.find((c) => c.id === clientId)?.full_name ??
										'Select client')
									: 'Select client'}
							</span>
						</Select.Trigger>
						<Select.Content>
							{#if clientsQuery.isLoading}
								<Select.Item value="" disabled>Loading clients...</Select.Item>
							{:else if clientsQuery.data?.clients?.length}
								{#each clientsQuery.data.clients as client (client.id)}
									<Select.Item value={client.id}>{client.full_name}</Select.Item>
								{/each}
							{:else}
								<Select.Item value="" disabled>No clients found</Select.Item>
							{/if}
						</Select.Content>
					</Select.Root>
				</div>

				<div class="grid gap-4 md:grid-cols-2">
					<div class="space-y-2">
						<Label for="date">Date *</Label>
						<Input id="date" type="date" bind:value={date} class="min-h-11" />
					</div>
					<div class="space-y-2">
						<Label for="time">Time *</Label>
						<Input id="time" type="time" bind:value={time} class="min-h-11" />
					</div>
				</div>

				<div class="space-y-2">
					<Label for="notes">Session Notes</Label>
					<Textarea id="notes" bind:value={notes} placeholder="Any notes for this session..." />
				</div>

				<div class="space-y-3">
					<div>
						<h3 class="text-sm font-medium">Exercises</h3>
						<p class="text-muted-foreground text-xs">Add exercises to this session (optional).</p>
					</div>
					<div class="space-y-2">
						{#each exercises as row, index (index)}
							<Collapsible.Root open={exercises.length === 1 || index === exercises.length - 1}>
								<Card>
									<CardHeader class="flex flex-row items-center justify-between space-y-0 py-3">
										<Collapsible.Trigger
											class="flex flex-1 items-center justify-between text-left min-h-11"
										>
											<span class="text-sm font-medium">
												{row.name.trim() || `Exercise ${index + 1}`}
											</span>
										</Collapsible.Trigger>
										<Button
											type="button"
											variant="ghost"
											size="icon"
											class="h-11 w-11 shrink-0"
											onclick={(e) => {
												e.preventDefault();
												removeExercise(index);
											}}
											aria-label="Remove exercise"
										>
											<Trash2Icon class="h-4 w-4" />
										</Button>
									</CardHeader>
									<Collapsible.Content>
										<CardContent class="space-y-4 pt-0">
											<SessionV2ExerciseFields bind:row={exercises[index]} idPrefix={`sess-ex-${index}`} />
										</CardContent>
									</Collapsible.Content>
								</Card>
							</Collapsible.Root>
						{/each}
					</div>
					<Button type="button" variant="outline" onclick={addExercise} class="w-full min-h-11 sm:w-auto">
						<PlusIcon class="mr-2 h-4 w-4" />
						Add exercise
					</Button>
				</div>

				<div class="flex flex-wrap gap-2 pt-4">
					<Button
						onclick={handleSubmit}
						disabled={createMutationState.isPending || !clientId}
						class="min-h-11"
					>
						{createMutationState.isPending ? 'Creating...' : 'Create Session'}
					</Button>
					<Button href="/app-v2/sessions" variant="outline" class="min-h-11">Cancel</Button>
				</div>
			</CardContent>
		</Card>
	</div>
</div>
