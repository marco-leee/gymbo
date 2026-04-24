<script lang="ts">
	import { Button } from "$lib/components/ui/button/index.js";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import PlusIcon from "@lucide/svelte/icons/plus";
	import type { ExerciseSet, SessionExercise } from "$lib/api/sessions";

	let {
		exercises = [],
		currentExercise = null,
		sessionInProgress = false,
		addSetPending = false,
		onSelectExercise,
		onLogSet,
		onAddSet,
	}: {
		exercises: SessionExercise[];
		currentExercise: SessionExercise | null;
		sessionInProgress?: boolean;
		addSetPending?: boolean;
		onSelectExercise?: (exerciseId: string) => void;
		onLogSet?: (exercise: SessionExercise, set: ExerciseSet) => void | Promise<void>;
		onAddSet?: (exerciseId: string) => void;
	} = $props();

	function setsProgress(ex: SessionExercise): { done: number; total: number } {
		const sets = ex.sets ?? [];
		const total = sets.length;
		const done = sets.filter((s) => s.status === "completed").length;
		return { done, total };
	}

	function primarySetForExercise(ex: SessionExercise): ExerciseSet | null {
		const sets = [...(ex.sets ?? [])].sort((a, b) => a.set_number - b.set_number);
		for (const s of sets) {
			if (s.status !== "completed") return s;
		}
		return sets.length > 0 ? sets[sets.length - 1] : null;
	}

	function exerciseTargetRepsLabel(ex: SessionExercise): string {
		if (ex.measurement === "reps") {
			return `${ex.target_reps ?? "—"} reps`;
		}
		return `${ex.target_duration ?? "—"}s`;
	}
</script>

<div
	class="shrink-0 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2.5"
>
	<p class="mb-2 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
		Session timeline
	</p>
	<div
		role="list"
		aria-label="Exercises in session order"
		class="flex flex-nowrap items-stretch gap-0 overflow-x-auto overscroll-x-contain pb-0.5 [-ms-overflow-style:none] [scrollbar-width:none]"
	>
		{#each exercises as exercise, exerciseIndex (exercise.id)}
			{@const isCurrent = currentExercise?.id === exercise.id}
			{@const progress = setsProgress(exercise)}
			{@const primarySet = primarySetForExercise(exercise)}
			<button type="button" class="flex shrink-0 items-stretch" onclick={() => onSelectExercise?.(exercise.id)}>
				<div
					class="flex w-48 min-w-48 max-w-48 shrink-0 flex-col rounded-lg border px-2.5 py-2 text-left transition-colors {isCurrent
						? 'border-emerald-400/60 bg-emerald-950/30 ring-1 ring-emerald-400/35'
						: 'border-white/10 bg-white/[0.04] hover:border-white/20'}"
				>
					<div class="mb-1 flex items-center gap-1.5">
						<span
							class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold {isCurrent
								? 'bg-emerald-500 text-zinc-950'
								: 'bg-zinc-700 text-zinc-200'}"
						>
							{exerciseIndex + 1}
						</span>
						<Badge
							variant="outline"
							class="shrink-0 border-white/20 capitalize text-[10px] text-zinc-300"
						>
							{exercise.type}
						</Badge>
					</div>
					<div
						class="w-full rounded-md text-left text-zinc-100"
					>
						<span class="line-clamp-2 text-sm font-medium text-white">
							{exercise.name}
						</span>
					</div>
					<dl class="mt-2 space-y-0.5 text-[11px] leading-snug text-zinc-400">
						<div class="flex justify-between gap-1">
							<dt class="text-zinc-500">Sets</dt>
							<dd class="text-right text-zinc-300">
								{progress.total} logged
								<span class="text-zinc-500">·</span>
								{progress.done} Done
								<span class="text-zinc-500">·</span>
								Goal {exercise.target_sets ?? "—"}
							</dd>
						</div>
						<div class="flex justify-between gap-1">
							<dt class="text-zinc-500">Target</dt>
							<dd class="text-right font-medium text-zinc-200">
								{exerciseTargetRepsLabel(exercise)}
							</dd>
						</div>
					</dl>
					{#if isCurrent}
						<div class="mt-2 flex flex-wrap gap-1.5 border-t border-white/10 pt-2">
							{#if primarySet}
								<Button
									type="button"
									variant="outline"
									size="sm"
									class="h-7 flex-1 border-white/20 bg-white/5 px-2 text-xs text-zinc-100"
									onclick={() => onLogSet?.(exercise, primarySet)}
								>
									Log set
								</Button>
							{:else if sessionInProgress}
								<Button
									type="button"
									variant="outline"
									size="sm"
									class="h-7 flex-1 border-white/20 bg-white/5 px-2 text-xs text-zinc-100"
									disabled={addSetPending}
									onclick={() => onAddSet?.(exercise.id)}
								>
									<PlusIcon class="mr-0.5 h-3.5 w-3.5" />
									Add
								</Button>
							{/if}
						</div>
					{/if}
				</div>
				{#if exerciseIndex < exercises.length - 1}
					<div
						class="flex w-5 shrink-0 items-center self-center px-0.5"
						aria-hidden="true"
					>
						<div class="h-0.5 w-full rounded-full bg-white/25"></div>
					</div>
				{/if}
			</button>
		{/each}
	</div>
</div>
