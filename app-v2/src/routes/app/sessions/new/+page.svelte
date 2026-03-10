<script lang="ts">
	import { goto } from '$app/navigation';
	import { createQuery, createMutation } from '@tanstack/svelte-query';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
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

	type ExerciseRow = {
		name: string;
		type: 'strength' | 'cardio' | 'flexibility';
		measurement: 'reps' | 'duration';
		target_reps?: number;
		target_duration?: number;
		target_sets: number;
		rest_seconds: number;
	};

	function defaultExerciseRow(): ExerciseRow {
		return {
			name: '',
			type: 'strength',
			measurement: 'reps',
			target_sets: 3,
			rest_seconds: 60
		};
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
			goto(`/app/sessions/${session.id}`);
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
				name: row.name.trim(),
				type: row.type,
				measurement: row.measurement,
				...(row.measurement === 'reps' ? { target_reps: row.target_reps ?? 0 } : { target_duration: row.target_duration ?? 0 }),
				target_sets: Math.max(0, row.target_sets ?? 3),
				rest_seconds: Math.max(0, row.rest_seconds ?? 60),
				order_index: idx
			};
		});
		const valid = payloadExercises.filter((ex): ex is NonNullable<typeof ex> => ex != null);
		const hasPartial = exercises.some((row) => {
			const filled = row.name.trim().length > 0 || row.target_reps != null || row.target_duration != null;
			const complete =
				row.name.trim().length > 0 &&
				(row.measurement === 'reps' ? row.target_reps != null && row.target_reps >= 0 : row.target_duration != null && row.target_duration >= 0);
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
		<Button href="/app/sessions" variant="ghost" size="icon">
			<ChevronLeftIcon class="h-4 w-4" />
		</Button>
		<h1 class="text-2xl font-semibold">New Session</h1>
	</div>

	<Card class="mx-auto max-w-2xl">
		<CardHeader>
			<CardTitle>Session Information</CardTitle>
			<CardDescription>Set up a new training session</CardDescription>
		</CardHeader>
		<CardContent class="space-y-4">
			<div class="space-y-2">
				<Label for="client">Client *</Label>
				<Select.Root
					type="single"
					value={clientId}
					onValueChange={(v) => (clientId = v ?? '')}
				>
					<Select.Trigger class="w-full">
						<UserIcon class="mr-2 h-4 w-4" />
						<span class={clientId ? '' : 'text-muted-foreground'}>
							{clientId && clientsQuery.data?.clients
								? clientsQuery.data.clients.find((c) => c.id === clientId)?.full_name ?? 'Select client'
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
					<Input id="date" type="date" bind:value={date} />
				</div>
				<div class="space-y-2">
					<Label for="time">Time *</Label>
					<Input id="time" type="time" bind:value={time} />
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
									<Collapsible.Trigger class="flex flex-1 items-center justify-between text-left">
										<span class="text-sm font-medium">
											{row.name.trim() || `Exercise ${index + 1}`}
										</span>
									</Collapsible.Trigger>
									<Button
										type="button"
										variant="ghost"
										size="icon"
										class="h-8 w-8 shrink-0"
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
										<div class="space-y-2">
											<Label for="ex-name-{index}">Name *</Label>
											<Input
												id="ex-name-{index}"
												type="text"
												bind:value={row.name}
												placeholder="e.g. Bench press"
											/>
										</div>
										<div class="grid gap-4 sm:grid-cols-2">
											<div class="space-y-2">
												<Label for="ex-type-{index}">Type</Label>
												<Select.Root
													type="single"
													value={row.type}
													onValueChange={(v) => (row.type = (v ?? 'strength') as ExerciseRow['type'])}
												>
													<Select.Trigger class="w-full">
														<span>{row.type}</span>
													</Select.Trigger>
													<Select.Content>
														<Select.Item value="strength">Strength</Select.Item>
														<Select.Item value="cardio">Cardio</Select.Item>
														<Select.Item value="flexibility">Flexibility</Select.Item>
													</Select.Content>
												</Select.Root>
											</div>
											<div class="space-y-2">
												<Label for="ex-measurement-{index}">Measurement</Label>
												<Select.Root
													type="single"
													value={row.measurement}
													onValueChange={(v) => (row.measurement = (v ?? 'reps') as ExerciseRow['measurement'])}
												>
													<Select.Trigger class="w-full">
														<span>{row.measurement === 'reps' ? 'Reps' : 'Duration'}</span>
													</Select.Trigger>
													<Select.Content>
														<Select.Item value="reps">Reps</Select.Item>
														<Select.Item value="duration">Duration</Select.Item>
													</Select.Content>
												</Select.Root>
											</div>
										</div>
										{#if row.measurement === 'reps'}
											<div class="space-y-2">
												<Label for="ex-target-reps-{index}">Target reps</Label>
												<Input
													id="ex-target-reps-{index}"
													type="number"
													min="0"
													bind:value={row.target_reps}
													placeholder="e.g. 12"
												/>
											</div>
										{:else}
											<div class="space-y-2">
												<Label for="ex-target-duration-{index}">Target duration (sec)</Label>
												<Input
													id="ex-target-duration-{index}"
													type="number"
													min="0"
													bind:value={row.target_duration}
													placeholder="e.g. 60"
												/>
											</div>
										{/if}
										<div class="grid gap-4 sm:grid-cols-2">
											<div class="space-y-2">
												<Label for="ex-sets-{index}">Sets</Label>
												<Input
													id="ex-sets-{index}"
													type="number"
													min="0"
													bind:value={row.target_sets}
												/>
											</div>
											<div class="space-y-2">
												<Label for="ex-rest-{index}">Rest (sec)</Label>
												<Input
													id="ex-rest-{index}"
													type="number"
													min="0"
													bind:value={row.rest_seconds}
												/>
											</div>
										</div>
									</CardContent>
								</Collapsible.Content>
							</Card>
						</Collapsible.Root>
					{/each}
				</div>
				<Button type="button" variant="outline" onclick={addExercise} class="w-full sm:w-auto">
					<PlusIcon class="mr-2 h-4 w-4" />
					Add exercise
				</Button>
			</div>

			<div class="flex gap-2 pt-4">
				<Button
					onclick={handleSubmit}
					disabled={createMutationState.isPending || !clientId}
				>
					{createMutationState.isPending ? 'Creating...' : 'Create Session'}
				</Button>
				<Button href="/app/sessions" variant="outline">Cancel</Button>
			</div>
		</CardContent>
	</Card>
</div>
