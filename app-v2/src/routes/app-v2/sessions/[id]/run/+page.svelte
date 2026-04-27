<script lang="ts">
	import { page } from "$app/stores";
	import { goto as navigateTo, invalidateAll } from "$app/navigation";
	import { onDestroy, onMount, tick, untrack } from "svelte";
	import { Button } from "$lib/components/ui/button/index.js";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import { Input } from "$lib/components/ui/input/index.js";
	import { Label } from "$lib/components/ui/label/index.js";
	import * as Sheet from "$lib/components/ui/sheet/index.js";
	import ChevronLeftIcon from "@lucide/svelte/icons/chevron-left";
	import CheckIcon from "@lucide/svelte/icons/check";
	import CameraIcon from "@lucide/svelte/icons/camera";
	import Chart, { type ChartPoint } from "./chart.svelte";
	import SessionExerciseTimeline from "./session-exercise-timeline.svelte";
	import SessionRunCountingBoard from "./session-run-counting-board.svelte";
	import { createLiveSessionAnalyser } from "$lib/ml/live-session-analyser";
	import { SessionPhaseController } from "$lib/ml/session-phase-controller";
	import { VlmWorkerClient } from "$lib/ml/vlm-worker-client";
	import type { SquatRepOutput } from "$lib/ml/rep";
	import { resolveExercisePoseEngineKey } from "$lib/pose/exercise-key";
	import { createPoseEngineRuntime } from "$lib/pose/pose-runtime";
	import type { SquatFrameAnalysis } from "$lib/pose/types";
	import {
		addSet,
		recordSet,
		startSession,
		completeSession,
		type SessionExercise,
		type ExerciseSet,
	} from "$lib/api/sessions";
	import { createMutation } from "@tanstack/svelte-query";
	// import { LineChart } from "layerchart";

	let { data } = $props();
	const sessionId = $derived($page.params.id);
	const session = $derived(data.session);

	const startMutation = createMutation(() => ({
		mutationFn: () => startSession(sessionId!),
		onSuccess: () => invalidateAll(),
	}));

	const completeMutation = createMutation(() => ({
		mutationFn: () => completeSession(sessionId!),
		onSuccess: async () => {
			await invalidateAll();
			await navigateTo(`/app-v2/sessions/${sessionId}?view=analysis`);
		},
	}));

	const addSetMutation = createMutation(() => ({
		mutationFn: ({ exerciseId }: { exerciseId: string }) =>
			addSet(sessionId!, exerciseId),
		onSuccess: () => invalidateAll(),
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
		},
	}));

	const MODEL_INPUT_SIZE = 640;
	const ANALYSIS_FPS = 5;
	const VIDEO_SEEK_EPSILON_SEC = 0.001;
	const VLM_INTERVAL_MS = 1000;
	const MAX_LIVE_CHART_POINTS = 400;
	const LIVE_MACHINE_IDLE_OUTPUT: SquatRepOutput = {
		phase: "idle",
		repsInSet: 0,
		lastRepAtMs: null,
	};
	const poseRuntime = createPoseEngineRuntime({
		modelInputSize: MODEL_INPUT_SIZE,
		analysisFps: ANALYSIS_FPS,
		videoSeekEpsilonSec: VIDEO_SEEK_EPSILON_SEC,
	});

	let drawerOpen = $state(false);
	let selectedExercise = $state<SessionExercise | null>(null);
	let selectedSet = $state<ExerciseSet | null>(null);
	let recordForm = $state({
		actual_reps: "",
		actual_duration: "",
		weight_kg: "",
		rpe: "",
		notes: "",
	});

	/** Ordered steps for the session timeline (synced from server in $effect). */
	let timelineExercises = $state<SessionExercise[]>([]);
	/** Active timeline step; drives scoreboard / live target when set drawer is closed. */
	let currentExercise = $state<SessionExercise | null>(null);
	let liveVideoEl = $state<HTMLVideoElement | null>(null);
	let mediaStream = $state<MediaStream | null>(null);
	let cameraActive = $state(false);
	let cameraError = $state("");
	let videoDevices = $state<MediaDeviceInfo[]>([]);
	let selectedDeviceId = $state("");
	let liveChartData = $state<ChartPoint[]>([]);
	let prefersReducedMotion = $state(false);
	let userExercising = $state(false);
	let machineOutput = $state<SquatRepOutput>({ ...LIVE_MACHINE_IDLE_OUTPUT });

	$effect(() => {
		const sorted = [...(session?.exercises ?? [])].sort(
			(a, b) => a.order_index - b.order_index,
		);
		timelineExercises = sorted;
		if (sorted.length === 0) {
			currentExercise = null;
			return;
		}
		untrack(() => {
			const curId = currentExercise?.id;
			if (!curId || !sorted.some((e) => e.id === curId)) {
				currentExercise = sorted[0];
			} else {
				currentExercise = sorted.find((e) => e.id === curId) ?? sorted[0];
			}
		});
	});

	const liveTarget = $derived.by(() => {
		// return { exercise: SessionEx, set: null }
		if (drawerOpen && selectedExercise && selectedSet) {
			return { exercise: selectedExercise, set: selectedSet };
		}
		const ex = currentExercise;
		if (!ex) return null;
		const sets = [...(ex.sets ?? [])].sort(
			(a, b) => a.set_number - b.set_number,
		);
		for (const s of sets) {
			if (s.status !== "completed") return { exercise: ex, set: s };
		}
		if (sets.length > 0) {
			return { exercise: ex, set: sets[sets.length - 1] };
		}
		return null;
	});

	const livePoseKey = $derived(
		liveTarget ? resolveExercisePoseEngineKey(liveTarget.exercise) : null,
	);

	const controllerExercises = $derived.by(() =>
		timelineExercises.filter(
			(exercise) => resolveExercisePoseEngineKey(exercise) !== null,
		),
	);

	const setsCompletedTotal = $derived(
		(session?.exercises ?? []).reduce(
			(acc, ex) =>
				acc + (ex.sets?.filter((s) => s.status === "completed").length ?? 0),
			0,
		),
	);

	const setsCompletedForLiveExercise = $derived(
		liveTarget
			? (liveTarget.exercise.sets?.filter((s) => s.status === "completed")
					.length ?? 0)
			: 0,
	);

	const liveChartEmptyHint = $derived.by(() => {
		if (!cameraActive) return "Start the camera for live squat angles.";
		if (livePoseKey !== "squat")
			return "Live pose tracking is available for squat exercises.";
		return "Move into frame — chart fills as angles are detected.";
	});

	onMount(() => {
		const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
		prefersReducedMotion = mq.matches;
		const onChange = () => {
			prefersReducedMotion = mq.matches;
		};
		mq.addEventListener("change", onChange);
		return () => mq.removeEventListener("change", onChange);
	});

	function resetLiveAnalysisState() {
		userExercising = false;
		liveChartData = [];
		machineOutput = { ...LIVE_MACHINE_IDLE_OUTPUT };
	}

	function appendLiveChartPoint(point: ChartPoint) {
		const next = [...liveChartData, point];
		liveChartData =
			next.length > MAX_LIVE_CHART_POINTS
				? next.slice(-MAX_LIVE_CHART_POINTS)
				: next;
	}

	function chartPointFromSquatAnalysis(
		frameIndex: number,
		timestampSec: number,
		analysis: SquatFrameAnalysis | null,
	): ChartPoint | null {
		if (!analysis) {
			return null;
		}

		return {
			frame: frameIndex,
			timestampSec,
			insideKnee: analysis.INSIDE_KNEE.angle,
			outsideHip: analysis.OUTSIDE_HIP.angle,
		};
	}

	async function refreshVideoDevices() {
		try {
			const devices = await navigator.mediaDevices.enumerateDevices();
			videoDevices = devices.filter((d) => d.kind === "videoinput");
		} catch {
			videoDevices = [];
		}
	}

	function stopCamera() {
		mediaStream?.getTracks().forEach((t) => t.stop());
		mediaStream = null;
		cameraActive = false;
		cameraError = "";
		if (liveVideoEl) liveVideoEl.srcObject = null;
		resetLiveAnalysisState();
	}

	async function startCamera() {
		cameraError = "";
		mediaStream?.getTracks().forEach((t) => t.stop());
		try {
			const stream = await navigator.mediaDevices.getUserMedia({
				video: selectedDeviceId
					? { deviceId: { exact: selectedDeviceId } }
					: true,
				audio: false,
			});
			mediaStream = stream;
			cameraActive = true;
			await tick();
			if (liveVideoEl) {
				liveVideoEl.srcObject = stream;
				await liveVideoEl.play().catch(() => {});
			}
			await refreshVideoDevices();
		} catch (err) {
			cameraActive = false;
			mediaStream = null;
			cameraError =
				err instanceof Error ? err.message : "Could not access the camera.";
		}
	}

	function formatTime(dateStr: string): string {
		return new Date(dateStr).toLocaleTimeString(undefined, {
			hour: "2-digit",
			minute: "2-digit",
		});
	}

	function elapsedMinutes(): string {
		if (!session?.started_at) return "0";
		const end = session.completed_at
			? new Date(session.completed_at)
			: new Date();
		const mins = Math.floor(
			(end.getTime() - new Date(session.started_at).getTime()) / 60000,
		);
		return String(mins);
	}

	function openSetDrawer(exercise: SessionExercise, set: ExerciseSet) {
		selectedExercise = exercise;
		selectedSet = set;
		const synced = timelineExercises.find((e) => e.id === exercise.id);
		currentExercise = synced ?? exercise;
		recordForm = {
			actual_reps: set.actual_reps != null ? String(set.actual_reps) : "",
			actual_duration:
				set.actual_duration != null ? String(set.actual_duration) : "",
			weight_kg: set.weight_kg != null ? String(set.weight_kg) : "",
			rpe: set.rpe != null ? String(set.rpe) : "",
			notes: set.notes ?? "",
		};
		drawerOpen = true;
	}

	$effect(() => {
		const currentExercise = liveTarget?.exercise ?? null;

		if (!cameraActive || !liveVideoEl || !mediaStream) return;

		const video = liveVideoEl;
		if (!livePoseKey || !currentExercise) {
			resetLiveAnalysisState();
			return;
		}
		const ac = new AbortController();
		const { signal } = ac;
		const targetFps = prefersReducedMotion ? 2 : ANALYSIS_FPS;
		let controller: SessionPhaseController | null = null;
		resetLiveAnalysisState();
		const analyser = createLiveSessionAnalyser({
			getVideo: () => video,
			poseRuntime,
			modelInputSize: MODEL_INPUT_SIZE,
			targetFps,
			getSessionInProgress: () => session?.status === "in-progress",
			getUserExercising: () => userExercising,
			orchestrationHooks: {
				onAnalysisFrame: ({ exercise, iteration }) => {
					if (resolveExercisePoseEngineKey(exercise) !== "squat") {
						return;
					}

					const point = chartPointFromSquatAnalysis(
						iteration.frameIndex,
						iteration.timestampSec,
						iteration.analysis as SquatFrameAnalysis | null,
					);
					if (point) {
						appendLiveChartPoint(point);
					}
				},
				onError: (error) => {
					if (!signal.aborted) {
						console.error("[run/live] analyser error", error);
						resetLiveAnalysisState();
					}
				},
			},
			signal,
			createRepHooks: () => ({
				onOutput: (output) => {
					machineOutput = output;
				},
				onError: (error) => {
					if (!signal.aborted) {
						console.error("[run/live] rep error", error);
						resetLiveAnalysisState();
					}
				},
			}),
		});

		analyser.start();
		console.debug("[run/live] live analysis start", {
			exerciseId: currentExercise.id,
			vlmIntervalMs: VLM_INTERVAL_MS,
		});
		controller = new SessionPhaseController({
			signal,
			exercises: controllerExercises,
			currentExerciseId: currentExercise.id,
			vlm: new VlmWorkerClient(),
			vlmIntervalMs: VLM_INTERVAL_MS,
			getSessionInProgress: () => session?.status === "in-progress",
			getVideo: () => liveVideoEl,
			onAnalyserCommand: (command) => {
				analyser.applyCommand(command);
			},
			mapVlmToUserExercising: (result) => result.label === "exercising",
			onUserExercisingChange: (value) => {
				userExercising = value;
			},
			onError: (error) => {
				if (!signal.aborted) {
					console.error("[run/live] controller error", error);
					resetLiveAnalysisState();
				}
			},
		});

		return () => {
			console.debug("[run/live] live analysis stop");
			analyser.stop();
			ac.abort();
			void controller?.dispose();
			resetLiveAnalysisState();
		};
	});

	onDestroy(() => {
		stopCamera();
		poseRuntime.dispose();
	});

	function submitRecord() {
		if (!selectedExercise || !selectedSet) return;
		const payload: Parameters<typeof recordSet>[3] = {
			status: "completed",
			notes: recordForm.notes || undefined,
		};
		if (selectedExercise.measurement === "reps" && recordForm.actual_reps) {
			payload.actual_reps = parseInt(recordForm.actual_reps, 10);
		}
		if (
			selectedExercise.measurement === "duration" &&
			recordForm.actual_duration
		) {
			payload.actual_duration = parseInt(recordForm.actual_duration, 10);
		}
		if (recordForm.weight_kg)
			payload.weight_kg = parseFloat(recordForm.weight_kg);
		if (recordForm.rpe)
			payload.rpe = Math.min(10, Math.max(1, parseInt(recordForm.rpe, 10)));
		recordSetMutation.mutate({
			exerciseId: selectedExercise.id,
			setId: selectedSet.id,
			payload,
		});
	}
</script>

<div
	class="app-v2-run fixed inset-0 z-[200] flex flex-col gap-3 overflow-hidden p-3 pt-[max(0.75rem,env(safe-area-inset-top))] pb-[max(0.75rem,env(safe-area-inset-bottom))] md:p-4"
>
	<!-- Minimal header -->
	<div
		class="flex shrink-0 items-center justify-between gap-2 border-b border-white/10 pb-3"
	>
		<div class="flex min-w-0 items-center gap-2">
			<Button
				href="/app-v2/sessions/{sessionId}?view=session"
				variant="ghost"
				size="icon"
				class="shrink-0 text-zinc-300 hover:bg-white/10 hover:text-white"
				aria-label="Back to session hub"
			>
				<ChevronLeftIcon class="h-5 w-5" />
			</Button>
			<div class="min-w-0">
				<p
					class="truncate text-xs font-medium uppercase tracking-wider text-zinc-500"
				>
					Execution
				</p>
				<h1 class="truncate text-lg font-bold text-white md:text-xl">
					{data.client?.full_name ?? session?.client_name ?? session?.client_id}
				</h1>
				<p class="text-xs text-zinc-400">
					{formatTime(session?.scheduled_at ?? "")}
					{#if session?.status === "in-progress"}
						· {elapsedMinutes()} min elapsed
					{/if}
				</p>
			</div>
		</div>
		<div class="flex shrink-0 flex-wrap items-center justify-end gap-2">
			<Badge
				variant={session?.status === "in-progress" ? "default" : "outline"}
				class="capitalize border-white/20 bg-white/5 text-zinc-200"
			>
				{session?.status?.replace("-", " ") ?? "scheduled"}
			</Badge>
			{#if session?.status === "scheduled"}
				<Button
					class="app-v2-cta rounded-lg"
					onclick={() => startMutation.mutate()}
					disabled={startMutation.isPending}
				>
					Start
				</Button>
			{/if}
			{#if session?.status === "in-progress"}
				<Button
					class="app-v2-cta rounded-lg"
					onclick={() => completeMutation.mutate()}
					disabled={completeMutation.isPending}
				>
					<CheckIcon class="mr-2 h-4 w-4" />
					Done
				</Button>
			{/if}
		</div>
	</div>

	<div class="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden">
		<div
			class="min-h-0 flex-1 grid grid-cols-1 gap-4 overflow-hidden md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]"
		>
			<!-- Live camera (~40%): full height of main area, controls overlaid at bottom -->
			<div
				class="flex min-h-[min(42vh,360px)] flex-1 flex-col overflow-hidden md:min-h-0"
			>
				<div
					class="relative min-h-0 flex-1 overflow-hidden rounded-lg border border-white/10 bg-black/40"
				>
					<video
						bind:this={liveVideoEl}
						class="absolute inset-0 h-full w-full object-fill"
						autoplay
						playsinline
						muted
					></video>
					{#if !cameraActive}
						<div
							class="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/50 pb-28 text-center text-xs text-zinc-400"
						>
							Camera off
						</div>
					{/if}
					<div
						class="absolute bottom-[16px] left-1/2 z-20 w-[80%] max-w-full -translate-x-1/2 space-y-2 rounded-xl border border-white/15 bg-black/70 px-3 py-2.5 shadow-lg backdrop-blur-md"
					>
						<div class="flex flex-wrap items-center gap-2">
							{#if !cameraActive}
								<Button
									type="button"
									class="app-v2-cta rounded-lg"
									onclick={() => void startCamera()}
								>
									<CameraIcon class="mr-2 h-4 w-4" />
									Start camera
								</Button>
							{:else}
								<Button
									type="button"
									variant="secondary"
									class="rounded-lg border-white/20 bg-white/10 text-white hover:bg-white/20"
									onclick={stopCamera}
								>
									Stop camera
								</Button>
							{/if}
							<Button
								type="button"
								variant="ghost"
								size="sm"
								class="text-zinc-300 hover:bg-white/10 hover:text-white"
								onclick={() => void refreshVideoDevices()}
							>
								Refresh devices
							</Button>
							<div class="space-y-1">
								<select
									id="cam-device"
									bind:value={selectedDeviceId}
									onchange={() => {
										if (cameraActive) void startCamera();
									}}
									class="border-input bg-background ring-offset-background focus-visible:ring-ring flex h-9 w-full rounded-md border px-2 text-sm text-zinc-100 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none"
								>
									<option value="">Default</option>
									{#each videoDevices as device (device.deviceId)}
										<option value={device.deviceId}>
											{device.label || `Camera ${device.deviceId.slice(0, 8)}…`}
										</option>
									{/each}
								</select>
							</div>
						</div>
						<p class="text-[10px] leading-snug text-zinc-400">
							On Mac, pick your iPhone under Continuity Camera in the list
							below.
						</p>
						{#if cameraError}
							<p class="text-destructive text-xs">{cameraError}</p>
						{/if}
					</div>
				</div>
			</div>

			<!-- Live analytics (~60%): horizontal timeline on top, then metrics + chart -->
			<div class="flex min-h-0 flex-col gap-3 overflow-hidden">
				<SessionExerciseTimeline
					exercises={timelineExercises}
					{currentExercise}
					sessionInProgress={session?.status === "in-progress"}
					addSetPending={addSetMutation.isPending}
					onSelectExercise={(id) => {
						const ex = timelineExercises.find((e) => e.id === id);
						if (ex) currentExercise = ex;
					}}
					onLogSet={(ex, set) => void openSetDrawer(ex, set)}
					onAddSet={(exerciseId) => addSetMutation.mutate({ exerciseId })}
				/>

				<SessionRunCountingBoard
					phase={machineOutput.phase}
					{prefersReducedMotion}
					exerciseName={liveTarget?.exercise.name ?? "—"}
					setNumber={liveTarget?.set.set_number ?? "—"}
					showSquatLiveReps={livePoseKey === "squat"}
					liveRepsInSet={machineOutput.repsInSet}
					targetReps={liveTarget?.exercise.measurement === "reps"
						? (liveTarget.exercise.target_reps ?? null)
						: null}
					setsDoneForExercise={setsCompletedForLiveExercise}
					setsDoneTotal={setsCompletedTotal}
				/>

				<div class="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto">
					<Chart data={liveChartData} emptyHint={liveChartEmptyHint} />
				</div>
			</div>
		</div>
	</div>
</div>
