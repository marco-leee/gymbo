<script lang="ts">
	import {
		Card,
		CardContent,
		CardHeader,
		CardTitle,
	} from "$lib/components/ui/card/index.js";
	import type { AnalysisPhase } from "$lib/ml/analysis-state-machine";

	let {
		phase,
		prefersReducedMotion = false,
		exerciseName,
		setNumber,
		showSquatLiveReps = false,
		liveRepsInSet = 0,
		targetReps = null,
		setsDoneForExercise,
		setsDoneTotal,
		class: className = "",
	}: {
		phase: AnalysisPhase;
		prefersReducedMotion?: boolean;
		exerciseName: string;
		setNumber: string | number;
		showSquatLiveReps?: boolean;
		liveRepsInSet?: number;
		targetReps?: number | null;
		setsDoneForExercise: number;
		setsDoneTotal: number;
		class?: string;
	} = $props();

	function phaseLabel(p: AnalysisPhase): string {
		switch (p) {
			case "idle":
				return "Idle";
			case "exercising":
				return "Exercising";
			case "rep_peak":
				return "Rep";
			case "rest":
				return "Rest";
		}
	}
</script>

<div class="grid grid-cols-1 gap-2 sm:grid-cols-3 xl:grid-cols-5 {className}">
	<Card class="border-white/10 bg-white/5">
		<CardHeader class="pb-1">
			<CardTitle class="text-xs font-medium text-zinc-400">Status</CardTitle>
		</CardHeader>
		<CardContent class="pt-0">
			<p class="text-sm font-semibold capitalize text-white">
				{phaseLabel(phase)}
			</p>
			{#if prefersReducedMotion}
				<p class="mt-1 text-[11px] text-zinc-500">Reduced motion FPS</p>
			{/if}
		</CardContent>
	</Card>
	<Card class="border-white/10 bg-white/5">
		<CardHeader class="pb-1">
			<CardTitle class="text-xs font-medium text-zinc-400">Exercise</CardTitle>
		</CardHeader>
		<CardContent class="pt-0">
			<p class="truncate text-sm font-semibold text-white">
				{exerciseName}
			</p>
		</CardContent>
	</Card>
	<Card class="border-white/10 bg-white/5">
		<CardHeader class="pb-1">
			<CardTitle class="text-xs font-medium text-zinc-400">Set</CardTitle>
		</CardHeader>
		<CardContent class="pt-0">
			<p class="text-sm font-semibold text-white">
				{setNumber}
			</p>
		</CardContent>
	</Card>
	<Card class="border-white/10 bg-white/5">
		<CardHeader class="pb-1">
			<CardTitle class="text-xs font-medium text-zinc-400">Reps (live)</CardTitle>
		</CardHeader>
		<CardContent class="pt-0">
			<p class="text-sm font-semibold text-white">
				{#if showSquatLiveReps}
					{liveRepsInSet}
					{#if targetReps != null}
						<span class="text-zinc-500"> / {targetReps}</span>
					{/if}
				{:else}
					—
				{/if}
			</p>
		</CardContent>
	</Card>
	<Card class="border-white/10 bg-white/5">
		<CardHeader class="pb-1">
			<CardTitle class="text-xs font-medium text-zinc-400">Sets done</CardTitle>
		</CardHeader>
		<CardContent class="pt-0">
			<p class="text-sm font-semibold text-white">
				{setsDoneForExercise}
				<span class="text-zinc-500"> Done</span>
				· {setsDoneTotal}
				<span class="text-zinc-500"> Goal</span>
			</p>
		</CardContent>
	</Card>
</div>
