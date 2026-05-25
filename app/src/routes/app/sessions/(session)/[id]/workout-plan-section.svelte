<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as Collapsible from '$lib/components/ui/collapsible/index.js';
	import ChevronDownIcon from '@lucide/svelte/icons/chevron-down';
	import PlusIcon from '@lucide/svelte/icons/plus';
	import Trash2Icon from '@lucide/svelte/icons/trash-2';
	import SessionV2ExerciseFields from '$lib/components/session-v2-exercise-fields.svelte';
	import { exerciseDeletionAllowed } from '$lib/exercise-plan';
	import { addSessionExercise, deleteSessionExercise, exerciseTypeLabel, type Session, type SessionExercise } from '$lib/api/sessions';
	import SessionExerciseNotes from './session-exercise-notes.svelte';
	import {
		emptySessionExerciseFormRow,
		sessionExerciseApiBodyFromFormRow,
		type SessionExerciseFormRow
	} from '$lib/exercises/catalog';

	function hasVideos(session: Session): boolean {
		return session.exercises?.some((ex) => ex.sets?.some((s) => s.video_url)) ?? false;
	}

	let { session }: { session: Session } = $props();

	let openedId = $state<string | null>(null);
	let draftRow = $state<SessionExerciseFormRow | null>(null);
	let savingDraft = $state(false);
	let deletingExerciseId = $state<string | null>(null);

	const canEditPlan = $derived(
		(session.status === 'scheduled' || session.status === 'in-progress') && !hasVideos(session)
	);

	const sortedExercises = $derived(
		[...(session.exercises ?? [])].sort((a, b) => a.order_index - b.order_index)
	);

	function exerciseAccordionMeta(ex: SessionExercise): string {
		const parts: string[] = [];
		if (ex.measurement === 'reps') {
			if (ex.target_reps != null) parts.push(`${ex.target_reps} reps`);
		} else if (ex.target_duration != null) {
			parts.push(`${ex.target_duration}s`);
		}
		if (ex.target_weight_kg != null) parts.push(`${ex.target_weight_kg} kg`);
		if (ex.target_sets != null && ex.target_sets > 0) {
			parts.push(`${ex.target_sets} ${ex.target_sets === 1 ? 'set' : 'sets'}`);
		}
		if (ex.rest_seconds != null && ex.rest_seconds > 0) parts.push(`${ex.rest_seconds}s rest`);
		return parts.join(' · ');
	}

	function startDraft() {
		draftRow = emptySessionExerciseFormRow();
	}

	function discardDraft() {
		draftRow = null;
	}

	async function saveDraft() {
		if (!draftRow) return;
		const row = draftRow;
		const hasName = row.name.trim().length > 0;
		const hasTarget =
			row.measurement === 'reps'
				? row.target_reps != null && row.target_reps >= 0
				: row.target_duration != null && row.target_duration >= 0;
		if (!hasName || !hasTarget) {
			alert('Add a name and a valid target (reps or duration).');
			return;
		}

		savingDraft = true;
		try {
			await addSessionExercise(session.id, sessionExerciseApiBodyFromFormRow(row));
			draftRow = null;
			await invalidateAll();
		} catch (e) {
			alert(e instanceof Error ? e.message : 'Failed to add exercise');
		} finally {
			savingDraft = false;
		}
	}

	async function removeExerciseConfirmed(exercise: SessionExercise) {
		if (!canEditPlan || !exerciseDeletionAllowed(exercise)) return;
		if (!confirm(`Remove “${exercise.name.trim() || 'this exercise'}” from the plan?`)) return;

		deletingExerciseId = exercise.id;
		try {
			await deleteSessionExercise(session.id, exercise.id);
			if (openedId === exercise.id) openedId = null;
			await invalidateAll();
		} catch (err) {
			alert(err instanceof Error ? err.message : 'Failed to remove exercise');
		} finally {
			deletingExerciseId = null;
		}
	}
</script>

<section id="workout-plan" aria-labelledby="workout-plan-heading" class="flex flex-col gap-4">
	<div class="flex items-center gap-2">
		<h2 id="workout-plan-heading" class="app-display text-2xl" style="color: var(--app-text);">
			Workout plan
		</h2>
		<ChevronDownIcon class="h-5 w-5 text-zinc-500" aria-hidden="true" />
	</div>
	<p class="text-sm" style="color: var(--app-muted);">Targets and logged sets for this session.</p>

	{#if !canEditPlan}
		<p class="text-xs" style="color: var(--app-muted);">
			You can&apos;t edit the exercise plan once the session is completed, cancelled, or has uploaded
			videos.
		</p>
	{/if}

	{#if sortedExercises.length || draftRow}
		<div class="space-y-4">
			{#each sortedExercises as exercise (exercise.id)}
				{@const metaLine = exerciseAccordionMeta(exercise)}
				{@const canRemoveExercise = canEditPlan && exerciseDeletionAllowed(exercise)}
				<Collapsible.Root
					open={openedId === exercise.id}
					onOpenChange={(open) => {
						if (open) openedId = exercise.id;
						else if (openedId === exercise.id) openedId = null;
					}}
				>
					<div class="app-card overflow-hidden p-0">
						<div
							class="flex min-w-0 flex-wrap items-center justify-between gap-x-3 gap-y-2 border-b px-4 py-3"
							style="border-color: var(--app-border);"
						>
							<Collapsible.Trigger
								class="flex min-h-11 min-w-0 flex-1 basis-0 items-center gap-2 text-left font-semibold hover:opacity-90"
								style="color: var(--app-text);"
								aria-expanded={openedId === exercise.id}
							>
								<ChevronDownIcon
									class={`h-5 w-5 shrink-0 transition-transform ${openedId === exercise.id ? 'rotate-180' : ''}`}
									style="color: var(--app-muted);"
									aria-hidden="true"
								/>
								<span class="min-w-0 truncate text-lg font-bold">{exercise.name}</span>
							</Collapsible.Trigger>
							<div class="flex min-w-0 flex-[0_1_auto] items-center justify-end gap-2 sm:gap-3">
								{#if metaLine}
									<p
										class="min-w-0 max-w-[min(28rem,calc(100vw-11rem))] truncate text-xs tabular-nums sm:max-w-sm md:max-w-md"
										style="color: var(--app-muted);"
										title={metaLine}
									>
										{metaLine}
									</p>
								{/if}
								<Badge variant="outline" class="shrink-0 border-[var(--app-border)] bg-white/5">
									{exerciseTypeLabel(exercise.type)}
								</Badge>
								{#if canRemoveExercise}
									<Button
										type="button"
										variant="ghost"
										size="icon"
										class="h-9 w-9 shrink-0 text-zinc-500 hover:text-red-600"
										aria-label={`Remove ${exercise.name}`}
										disabled={deletingExerciseId === exercise.id}
										onclick={() => removeExerciseConfirmed(exercise)}
									>
										<Trash2Icon class="h-4 w-4" />
									</Button>
								{/if}
							</div>
						</div>
						<Collapsible.Content>
							<div class="space-y-3 p-4">
								<div class="overflow-x-auto rounded-lg border" style="border-color: var(--app-border);">
									<Table.Root>
										<Table.Header>
											<Table.Row class="border-[var(--app-border)] hover:bg-transparent">
												<Table.Head class="text-[var(--app-muted)]">Set</Table.Head>
												<Table.Head class="text-[var(--app-muted)]">Target</Table.Head>
												<Table.Head class="text-[var(--app-muted)]">Actual</Table.Head>
												<Table.Head class="text-[var(--app-muted)]">Weight</Table.Head>
												<Table.Head class="text-[var(--app-muted)]">Status</Table.Head>
											</Table.Row>
										</Table.Header>
										<Table.Body>
											{#each (exercise.sets ?? []).sort((a, b) => a.set_number - b.set_number) as set (set.id)}
												<Table.Row class="border-[var(--app-border)]">
													<Table.Cell class="tabular-nums font-medium">{set.set_number}</Table.Cell>
													<Table.Cell>
														{#if exercise.measurement === 'reps'}
															{exercise.target_reps ?? '—'} reps{#if exercise.target_weight_kg != null}
																<span class="text-[var(--app-muted)]"> · </span>{exercise.target_weight_kg} kg{/if}
														{:else}
															{exercise.target_duration ?? '—'}s{#if exercise.target_weight_kg != null}
																<span class="text-[var(--app-muted)]"> · </span>{exercise.target_weight_kg} kg{/if}
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
														<Badge variant="outline" class="text-xs capitalize">{set.status}</Badge>
													</Table.Cell>
												</Table.Row>
											{/each}
										</Table.Body>
									</Table.Root>
								</div>
								{#if !exercise.sets?.length}
									<p class="py-1 text-sm" style="color: var(--app-muted);">No sets yet.</p>
								{/if}
								<SessionExerciseNotes
									sessionId={session.id}
									exerciseId={exercise.id}
									notes={exercise.notes}
									canEdit={canEditPlan}
								/>
							</div>
						</Collapsible.Content>
					</div>
				</Collapsible.Root>
			{/each}

			{#if draftRow}
				<div class="overflow-hidden rounded-xl border bg-white/[0.02] p-0" style="border-color: var(--app-accent);">
					<div
						class="flex flex-wrap items-center justify-between gap-2 border-b px-4 py-3"
						style="border-color: var(--app-border);"
					>
						<span class="min-h-11 flex flex-1 items-center text-left text-sm font-medium" style="color: var(--app-text);">
							{draftRow.name.trim() || 'New exercise'}
						</span>
						{#if canEditPlan}
							<Button
								type="button"
								variant="ghost"
								size="icon"
								class="h-11 w-11 shrink-0"
								onclick={discardDraft}
								aria-label="Discard draft"
							>
								<Trash2Icon class="h-4 w-4" />
							</Button>
						{/if}
					</div>
					<div class="space-y-4 p-4">
						<SessionV2ExerciseFields bind:row={draftRow} idPrefix="draft-ex" />
						{#if canEditPlan}
								<div class="flex flex-wrap gap-2">
									<Button
										type="button"
										class="app-cta min-h-11"
										disabled={savingDraft}
										onclick={saveDraft}
									>
										{savingDraft ? 'Saving…' : 'Save exercise'}
									</Button>
									<Button type="button" variant="outline" class="min-h-11 app-outline" onclick={discardDraft}>
										Cancel
									</Button>
								</div>
							{/if}
					</div>
				</div>
			{/if}
		</div>
	{:else}
		<div
			class="app-card py-12 text-center text-sm"
			style="color: var(--app-muted);"
			aria-live="polite"
		>
			No exercises in this session.
		</div>
	{/if}

	{#if canEditPlan && !draftRow}
		<div>
			<Button
				type="button"
				variant="outline"
				data-tour="session-hub-add-exercise"
				class="w-full min-h-11 app-outline sm:w-auto"
				onclick={startDraft}
			>
				<PlusIcon class="mr-2 h-4 w-4" aria-hidden="true" />
				Add exercise
			</Button>
		</div>
	{/if}
</section>
