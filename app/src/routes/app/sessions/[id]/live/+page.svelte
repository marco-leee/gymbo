<script lang="ts">
	import { browser } from '$app/environment';
	import { onDestroy } from 'svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { ExerciseRunFlow } from '$lib/trainer/exercise-run-flow';
	import { LiveRunState } from '$lib/trainer/live-state.svelte';

	let { data } = $props();

	const liveState = new LiveRunState();
	let videoEl = $state<HTMLVideoElement | null>(null);
	let canvasEl = $state<HTMLCanvasElement | null>(null);
	let flow = $state<ExerciseRunFlow | null>(null);
	let cameraActive = $state(false);
	let errorMessage = $state<string | null>(null);

	const exercises = $derived(
		(data.session.exercises ?? []).map((e) => ({
			id: e.id,
			exercise_key: e.exercise_key ?? 'overhead_squat',
			target_sets: e.target_sets ?? 3,
			target_reps: e.target_reps ?? 10,
			rest_seconds: e.rest_seconds ?? 60,
			name: e.name
		}))
	);

	async function startLive() {
		errorMessage = null;
		try {
			flow = new ExerciseRunFlow({
				sessionId: data.session.id,
				clientId: data.session.client_id,
				wsUrl: data.trainerWsUrl,
				exercises,
				onStateChange: (state) =>
					liveState.applyTrainerState(state as Parameters<typeof liveState.applyTrainerState>[0]),
				onPhaseMessage: ({ message }) => liveState.setPhaseMessage(message),
				onEmergency: ({ description }) => liveState.setEmergency(description)
			});
			await flow.startCurrentExercise();
			await startCamera();
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : 'Failed to start live coaching';
		}
	}

	function stopVideoStream(video: HTMLVideoElement | null) {
		const src = video?.srcObject;
		if (!src || typeof src !== 'object' || !('getTracks' in src)) return;
		const getTracks = (src as { getTracks?: () => { stop: () => void }[] }).getTracks;
		if (typeof getTracks !== 'function') return;
		for (const track of getTracks()) track.stop();
	}

	async function startCamera() {
		if (!browser || !videoEl || !canvasEl || !flow) return;
		const stream = await navigator.mediaDevices.getUserMedia({
			video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
			audio: false
		});
		videoEl.srcObject = stream;
		await videoEl.play();
		cameraActive = true;
		flow.startCamera(videoEl, canvasEl, 1);
		liveState.setConnection(true);
	}

	async function endRun() {
		await flow?.endCurrentRun();
		cameraActive = false;
		stopVideoStream(videoEl);
	}

	async function resumeRun() {
		flow?.resume();
		liveState.clearEmergency();
	}

	onDestroy(() => {
		if (browser) void endRun();
	});
</script>

<div class="mx-auto flex max-w-3xl flex-col gap-6 p-4">
	<header class="space-y-1">
		<h1 class="text-2xl font-semibold tracking-tight">Live coaching</h1>
		<p class="text-muted-foreground text-sm">
			Session {data.session.id.slice(-6)} — {exercises.length} exercise(s) planned
		</p>
	</header>

	{#if errorMessage}
		<p class="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
			{errorMessage}
		</p>
	{/if}

	{#if liveState.emergencyMessage}
		<div class="rounded-md border border-amber-500/50 bg-amber-500/10 p-4 space-y-2">
			<p class="font-medium text-amber-900 dark:text-amber-100">Emergency pause</p>
			<p class="text-sm">{liveState.emergencyMessage}</p>
			<div class="flex gap-2">
				<Button size="sm" onclick={resumeRun}>Resume</Button>
				<Button size="sm" variant="outline" onclick={endRun}>End run</Button>
			</div>
		</div>
	{/if}

	<section class="relative aspect-video overflow-hidden rounded-xl border bg-black">
		<!-- svelte-ignore a11y_media_has_caption -->
		<video bind:this={videoEl} class="h-full w-full object-cover" playsinline muted></video>
		<canvas bind:this={canvasEl} class="hidden" aria-hidden="true"></canvas>
		{#if !cameraActive}
			<div class="absolute inset-0 flex items-center justify-center bg-black/60 text-white text-sm">
				Camera preview
			</div>
		{/if}
	</section>

	<section class="grid grid-cols-2 gap-3 sm:grid-cols-4">
		<div class="rounded-lg border p-3">
			<p class="text-muted-foreground text-xs">Set</p>
			<p class="text-xl font-semibold tabular-nums">{liveState.setNumber}</p>
		</div>
		<div class="rounded-lg border p-3">
			<p class="text-muted-foreground text-xs">Reps</p>
			<p class="text-xl font-semibold tabular-nums">
				{liveState.completedReps}<span class="text-muted-foreground text-base">/{liveState.targetReps || '—'}</span>
			</p>
		</div>
		<div class="rounded-lg border p-3">
			<p class="text-muted-foreground text-xs">Phase</p>
			<p class="text-sm font-medium capitalize">{liveState.phase.replaceAll('_', ' ') || '—'}</p>
		</div>
		<div class="rounded-lg border p-3">
			<p class="text-muted-foreground text-xs">Connection</p>
			<Badge variant={liveState.connected ? 'default' : 'secondary'}>
				{liveState.connected ? 'Live' : 'Offline'}
			</Badge>
		</div>
	</section>

	{#if liveState.activeIssues.length > 0}
		<ul class="flex flex-wrap gap-2">
			{#each liveState.activeIssues as issue (issue)}
				<Badge variant="outline">{issue}</Badge>
			{/each}
		</ul>
	{/if}

	{#if liveState.phaseMessage}
		<p class="text-muted-foreground text-sm">{liveState.phaseMessage}</p>
	{/if}

	<div class="flex flex-wrap gap-2">
		{#if !flow}
			<Button onclick={startLive}>Start live coaching</Button>
		{:else}
			<Button variant="outline" onclick={endRun}>End exercise</Button>
		{/if}
	</div>
</div>
