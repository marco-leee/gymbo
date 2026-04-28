<script lang="ts">
	import { page } from '$app/stores';
	import { Button } from '$lib/components/ui/button/index.js';
	import VideoIcon from '@lucide/svelte/icons/video';
	import BarChart3Icon from '@lucide/svelte/icons/bar-chart-3';
	import type { SessionExercise } from '$lib/api/sessions';
	import WorkoutPlanSection from './workout-plan-section.svelte';

	let { data } = $props();

	const sessionId = $derived($page.params.id);
	const view = $derived(($page.url.searchParams.get('view') ?? 'session') as 'session' | 'analysis');

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

{#if view === 'session'}
	<div class="flex flex-col gap-10">
		<!-- At a glance -->
		<section aria-labelledby="session-glance-heading" class="app-v2-card overflow-hidden">
			<div class="grid gap-6 p-6 md:grid-cols-[1fr_auto] md:items-center">
				<div>
					<h2 id="session-glance-heading" class="app-v2-display text-2xl text-[var(--app-v2-accent)]">
						At a glance
					</h2>
					<p class="mt-2 max-w-prose text-sm" style="color: var(--app-v2-muted);">
						Start execution for a minimal full-screen recorder, or open the table recorder.
					</p>
					<div class="mt-6 flex flex-wrap gap-2">
						{#if data.session.status === 'completed'}
							<Button href="/app-v2/sessions/{sessionId}?view=analysis" class="app-v2-cta min-h-12 rounded-lg px-6">
								<BarChart3Icon class="mr-2 h-5 w-5" aria-hidden="true" />
								View analysis
							</Button>
						{:else if showRecordPrimary}
							<Button href="/app-v2/sessions/{sessionId}/run" class="app-v2-cta min-h-12 rounded-lg px-6 text-base">
								<VideoIcon class="mr-2 h-5 w-5" aria-hidden="true" />
								{data.session.status === 'in-progress' ? 'Continue workout' : 'Start workout'}
							</Button>
						{:else}
							<Button href="/app-v2/sessions/{sessionId}?view=analysis" variant="outline" class="app-v2-outline min-h-12 rounded-lg">
								Analysis
							</Button>
						{/if}
					</div>
				</div>
				<div class="grid grid-cols-3 gap-3 text-center md:text-left">
					<div>
						<p class="app-v2-hero-num">{data.session.exercises?.length ?? 0}</p>
						<p class="text-xs font-semibold uppercase tracking-wide" style="color: var(--app-v2-muted);">Exercises</p>
					</div>
					<div>
						<p class="app-v2-hero-num">{setsCompleted}<span class="text-lg text-zinc-500">/{setsPlanned}</span></p>
						<p class="text-xs font-semibold uppercase tracking-wide" style="color: var(--app-v2-muted);">Sets</p>
					</div>
					<div>
						{#if data.session.started_at && data.session.completed_at}
							<p class="app-v2-hero-num">
								{Math.round(
									(new Date(data.session.completed_at).getTime() -
										new Date(data.session.started_at).getTime()) /
										60000
								)}
							</p>
						{:else}
							<p class="app-v2-hero-num">—</p>
						{/if}
						<p class="text-xs font-semibold uppercase tracking-wide" style="color: var(--app-v2-muted);">Min</p>
					</div>
				</div>
			</div>
		</section>

		{#if data.session.notes}
			<section class="app-v2-card p-6">
				<h2 class="text-sm font-bold uppercase tracking-wider" style="color: var(--app-v2-muted);">Notes</h2>
				<p class="mt-2 whitespace-pre-wrap text-sm leading-relaxed" style="color: var(--app-v2-text);">
					{data.session.notes}
				</p>
			</section>
		{/if}

		<!-- Workout plan -->
		<WorkoutPlanSection session={data.session} />
	</div>
{:else if view === 'analysis'}
	{#await import('./session-v2-analysis-panel.svelte')}
		<div
			class="app-v2-card py-16 text-center text-sm"
			style="color: var(--app-v2-muted);"
			role="status"
		>
			Loading analysis…
		</div>
	{:then { default: SessionV2AnalysisPanel }}
		<div class="flex flex-col gap-4">
			<SessionV2AnalysisPanel {data} />
		</div>
	{/await}
{/if}
