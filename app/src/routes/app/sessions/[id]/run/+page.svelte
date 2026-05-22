<script lang="ts">
	import { page } from "$app/stores";
	import { goto, invalidateAll } from "$app/navigation";
	import { onDestroy, onMount, tick, untrack } from "svelte";
	import { Button } from "$lib/components/ui/button/index.js";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import { Input } from "$lib/components/ui/input/index.js";
	import { Label } from "$lib/components/ui/label/index.js";
	import * as Sheet from "$lib/components/ui/sheet/index.js";
	import ChevronLeftIcon from "@lucide/svelte/icons/chevron-left";
	import VideoIcon from "@lucide/svelte/icons/video";
	import CheckIcon from "@lucide/svelte/icons/check";
	import CameraIcon from "@lucide/svelte/icons/camera";
	import Chart, { type ChartPoint } from "./chart.svelte";
	import SessionExerciseTimeline from "./session-exercise-timeline.svelte";
	import SessionRunCountingBoard from "./session-run-counting-board.svelte";
	import {
		AnalysisStateMachine,
		type AnalysisMachineOutput,
	} from "$lib/ml/analysis-state-machine";
	import {
		ExerciseVlmPlaceholder,
		type VlmResult,
	} from "$lib/ml/exercise-vlm-placeholder";
	import { getMediaPlayUrl } from "$lib/api/media";
	import { resolveExercisePoseEngineKey } from "$lib/pose/exercise-key";
	import {
		createExercisePoseEngine,
		UnsupportedPoseEngineError,
	} from "$lib/pose/exercise-pose-engine-factory";
	import { createPoseEngineRuntime } from "$lib/pose/pose-runtime";
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
			await goto(`/app/sessions/${sessionId}?view=analysis`);
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

	const MAX_VIDEO_SIZE = 200 * 1024 * 1024; // 200MB
	const MAX_VIDEO_DURATION_SEC = 60;
	const MODEL_INPUT_SIZE = 640;
	const ANALYSIS_FPS = 5;
	const VIDEO_SEEK_EPSILON_SEC = 0.001;
	const poseRuntime = createPoseEngineRuntime({
		modelInputSize: MODEL_INPUT_SIZE,
		analysisFps: ANALYSIS_FPS,
		videoSeekEpsilonSec: VIDEO_SEEK_EPSILON_SEC,
	});

	const exerciseVlm = new ExerciseVlmPlaceholder();
	const analysisMachine = new AnalysisStateMachine();

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
	let videoUrlKey = $state<string | null>(null);
	let videoBlobUrl = $state<string | null>(null);
	let existingVideoPlayUrl = $state<string | null>(null);
	let uploadError = $state("");
	let isUploading = $state(false);
	let isProcessingVideo = $state(false);
	let isAutoSavingPose = $state(false);
	let isLoadingExistingVideo = $state(false);
	let chartData = $state<ChartPoint[]>([]);
	let drawerPreviewVideoEl = $state<HTMLVideoElement | null>(null);
	let videoInputEl = $state<HTMLInputElement | null>(null);
	let durationCheckVideoEl = $state<HTMLVideoElement | null>(null);

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
	let machineOutput = $state<AnalysisMachineOutput>({
		phase: "idle",
		repsInSet: 0,
		lastRepAtMs: null,
	});

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
		liveChartData = [];
		analysisMachine.reset();
		machineOutput = { phase: "idle", repsInSet: 0, lastRepAtMs: null };
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

	async function openSetDrawer(exercise: SessionExercise, set: ExerciseSet) {
		if (videoBlobUrl) URL.revokeObjectURL(videoBlobUrl);
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
		videoUrlKey = set.video_url ?? null;
		videoBlobUrl = null;
		existingVideoPlayUrl = null;
		chartData = set.pose_chart_data ? [...set.pose_chart_data] : [];
		uploadError = "";
		isUploading = false;
		isProcessingVideo = false;
		isAutoSavingPose = false;
		isLoadingExistingVideo = false;
		drawerOpen = true;

		if (!set.video_url) return;

		const selectedSetId = set.id;
		isLoadingExistingVideo = true;
		try {
			const playUrl = await getMediaPlayUrl(set.video_url);
			if (selectedSet?.id === selectedSetId) {
				existingVideoPlayUrl = playUrl;
			}
		} catch (err) {
			if (selectedSet?.id === selectedSetId) {
				uploadError =
					err instanceof Error ? err.message : "Failed to load video preview";
			}
		} finally {
			if (selectedSet?.id === selectedSetId) {
				isLoadingExistingVideo = false;
			}
		}
	}

	function getVideoDisplaySrc(): string | null {
		if (videoBlobUrl) return videoBlobUrl;
		if (existingVideoPlayUrl) return existingVideoPlayUrl;
		if (selectedSet?.video_play_url) return selectedSet.video_play_url;
		return null;
	}

	async function autoSavePoseChartData(
		exerciseId: string,
		setId: string,
		videoUrl: string,
		poseChartData: ChartPoint[],
	) {
		if (!sessionId) return;

		isAutoSavingPose = true;
		try {
			await recordSet(sessionId, exerciseId, setId, {
				video_url: videoUrl,
				pose_chart_data: poseChartData,
			});
			await invalidateAll();
		} finally {
			isAutoSavingPose = false;
		}
	}

	async function processUploadedVideo(
		file: File,
		exerciseId: string,
		setId: string,
		videoUrl: string,
	) {
		isProcessingVideo = true;

		try {
			if (!selectedExercise) {
				console.error("No selected exercise");
				return;
			}
			const exerciseKey = resolveExercisePoseEngineKey(selectedExercise);
			if (!exerciseKey) {
				console.error("No exercise key");
				return;
			}

			const engine = createExercisePoseEngine(exerciseKey, poseRuntime);
			chartData = [];
			let nextChartData: ChartPoint[] = [];

			for await (const iteration of engine.analyzeVideo({ file })) {
				if (!engine.chartPointFromIteration) continue;
				const point = engine.chartPointFromIteration(iteration);
				nextChartData = [...nextChartData, point];
				chartData = nextChartData;
			}

			await autoSavePoseChartData(exerciseId, setId, videoUrl, nextChartData);
		} catch (error) {
			if (error instanceof UnsupportedPoseEngineError) {
				return;
			}
			uploadError =
				error instanceof Error ? error.message : "Pose processing failed";
			console.error("Pose processing failed", error);
		} finally {
			isProcessingVideo = false;
		}
	}

	$effect(() => {
		if (!cameraActive || !liveVideoEl || !mediaStream || isProcessingVideo)
			return;
		if (livePoseKey !== "squat") {
			liveChartData = [];
			analysisMachine.reset();
			machineOutput = { phase: "idle", repsInSet: 0, lastRepAtMs: null };
			return;
		}

		const video = liveVideoEl;
		const sessionStatus = session?.status;
		const ac = new AbortController();
		const { signal } = ac;

		void (async () => {
			await exerciseVlm.init();
			try {
				const targetFps = prefersReducedMotion ? 2 : ANALYSIS_FPS;
				const engine = createExercisePoseEngine("squat", poseRuntime);
				analysisMachine.reset();
				let chartBuf: ChartPoint[] = [];
				liveChartData = [];

				let vlmEvery = 0;
				let lastVlm: VlmResult = { label: "unknown", confidence: 0 };

				for await (const iteration of engine.analyzeLiveVideo(video, {
					signal,
					targetFps,
				})) {
					if (signal.aborted) break;

					if (engine.chartPointFromIteration) {
						const point = engine.chartPointFromIteration(iteration);
						chartBuf = [...chartBuf, point];
						if (chartBuf.length > 400) chartBuf = chartBuf.slice(-400);
						liveChartData = chartBuf;
					}

					if (vlmEvery++ % 20 === 0) {
						try {
							const bmp = await createImageBitmap(video);
							lastVlm = await exerciseVlm.inferFrame(bmp);
							bmp.close();
						} catch {
							/* ignore frame grab errors */
						}
					}

					machineOutput = analysisMachine.tick({
						nowMs: performance.now(),
						pose: iteration.analysis,
						vlm: lastVlm,
						repCountingEnabled: sessionStatus === "in-progress",
					});
				}
			} catch (e) {
				if (!signal.aborted) console.error("Live pose loop", e);
			} finally {
				await exerciseVlm.dispose();
			}
		})();

		return () => {
			ac.abort();
		};
	});

	onDestroy(() => {
		stopCamera();
		poseRuntime.dispose();
	});

	async function handleVideoFileSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file || !selectedExercise || !selectedSet || !sessionId) return;

		uploadError = "";
		if (file.type !== "video/mp4") {
			uploadError = "Only MP4 video is allowed.";
			input.value = "";
			return;
		}
		if (file.size > MAX_VIDEO_SIZE) {
			uploadError = `File must be under ${MAX_VIDEO_SIZE / (1024 * 1024)}MB.`;
			input.value = "";
			return;
		}

		const blobUrl = URL.createObjectURL(file);
		const videoEl = durationCheckVideoEl;
		if (!videoEl) {
			URL.revokeObjectURL(blobUrl);
			uploadError = "Cannot check video duration.";
			return;
		}

		const durationOk = await new Promise<boolean>((resolve) => {
			videoEl.src = blobUrl;
			videoEl.onloadedmetadata = () => {
				const dur = videoEl.duration;
				URL.revokeObjectURL(blobUrl);
				videoEl.src = "";
				resolve(!Number.isNaN(dur) && dur > 0 && dur <= MAX_VIDEO_DURATION_SEC);
			};
			videoEl.onerror = () => {
				URL.revokeObjectURL(blobUrl);
				videoEl.src = "";
				resolve(false);
			};
		});

		if (!durationOk) {
			uploadError = `Video must be under ${MAX_VIDEO_DURATION_SEC} seconds.`;
			input.value = "";
			return;
		}

		isUploading = true;
		try {
			const signRes = await fetch("/api/media/sign", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					session_id: sessionId,
					exercise_id: selectedExercise.id,
					set_id: selectedSet.id,
					file_name: file.name,
					file_type: file.type,
					file_size: file.size,
				}),
			});
			if (!signRes.ok) {
				const err = await signRes.text();
				throw new Error(err || signRes.statusText);
			}
			const { upload_url, key } = (await signRes.json()) as {
				upload_url: string;
				key: string;
			};

			const putRes = await fetch(upload_url, {
				method: "PUT",
				headers: { "Content-Type": "video/mp4" },
				body: file,
			});
			if (!putRes.ok) throw new Error("Upload failed");

			if (videoBlobUrl) URL.revokeObjectURL(videoBlobUrl);
			videoUrlKey = key;
			videoBlobUrl = URL.createObjectURL(file);
			void processUploadedVideo(file, selectedExercise.id, selectedSet.id, key);
		} catch (err) {
			uploadError = err instanceof Error ? err.message : "Upload failed";
		} finally {
			isUploading = false;
			input.value = "";
		}
	}

	$effect(() => {
		if (!drawerOpen && videoBlobUrl) {
			const url = videoBlobUrl;
			videoBlobUrl = null;
			URL.revokeObjectURL(url);
		}
		if (!drawerOpen && chartData.length > 0) {
			chartData = [];
		}
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
		if (videoUrlKey) payload.video_url = videoUrlKey;
		recordSetMutation.mutate({
			exerciseId: selectedExercise.id,
			setId: selectedSet.id,
			payload,
		});
	}
</script>

<div
	class="app-run fixed inset-0 z-[200] flex flex-col gap-3 overflow-hidden p-3 pt-[max(0.75rem,env(safe-area-inset-top))] pb-[max(0.75rem,env(safe-area-inset-bottom))] md:p-4"
>
	<!-- Minimal header -->
	<div
		class="flex shrink-0 items-center justify-between gap-2 border-b border-white/10 pb-3"
	>
		<div class="flex min-w-0 items-center gap-2">
			<Button
				href="/app/sessions/{sessionId}?view=session"
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
					class="app-cta rounded-lg"
					onclick={() => startMutation.mutate()}
					disabled={startMutation.isPending}
				>
					Start
				</Button>
			{/if}
			{#if session?.status === "in-progress"}
				<Button
					class="app-cta rounded-lg"
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
									class="app-cta rounded-lg"
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

	<!-- Set recorder drawer -->
	<Sheet.Root bind:open={drawerOpen}>
		<Sheet.Content
			side="bottom"
			class="flex h-[80vh] max-h-[80vh] flex-col overflow-hidden rounded-t-xl"
		>
			<Sheet.Header>
				<Sheet.Title>
					{selectedExercise?.name} — Set {selectedSet?.set_number}
				</Sheet.Title>
			</Sheet.Header>
			<div class="min-h-0 flex-1 overflow-y-auto">
				<div class="space-y-4 p-4 py-4">
					{#if selectedExercise?.measurement === "reps"}
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
						<Input
							id="notes"
							bind:value={recordForm.notes}
							placeholder="Optional notes"
						/>
					</div>
					<!-- Hidden video for duration check -->
					<video
						bind:this={durationCheckVideoEl}
						class="hidden"
						muted
						playsinline
						preload="metadata"
					></video>
					<div class="space-y-2">
						<Label>Video (MP4, under 1 min, max 200MB)</Label>
						<input
							bind:this={videoInputEl}
							type="file"
							accept="video/mp4,.mp4"
							class="hidden"
							onchange={handleVideoFileSelect}
						/>
						<Button
							type="button"
							variant="outline"
							class="w-full"
							disabled={isUploading || isProcessingVideo || isAutoSavingPose}
							onclick={() => videoInputEl?.click()}
						>
							{#if isUploading}
								Uploading…
							{:else if isProcessingVideo}
								Processing video…
							{:else if isAutoSavingPose}
								Saving analysis…
							{:else}
								<VideoIcon class="mr-2 h-4 w-4" />
								Choose video
							{/if}
						</Button>
						{#if uploadError}
							<p class="text-destructive text-sm">{uploadError}</p>
						{/if}
						{#if isLoadingExistingVideo}
							<p class="text-muted-foreground text-sm">
								Loading saved video...
							</p>
						{/if}
						{#if getVideoDisplaySrc()}
							<div class="rounded-md border bg-muted/30 overflow-hidden">
								<video
									bind:this={drawerPreviewVideoEl}
									src={getVideoDisplaySrc()!}
									controls
									class="w-full max-h-48"
									muted
									playsinline
									preload="metadata"
								></video>
							</div>
						{/if}
					</div>
					<Button
						class="w-full"
						onclick={submitRecord}
						disabled={recordSetMutation.isPending ||
							isProcessingVideo ||
							isAutoSavingPose}
					>
						Save set
					</Button>
				</div>

				<div class="space-y-2 border-t p-4 pt-4">
					<h3 class="text-sm font-medium">Set analysis (angle over time)</h3>
					<Chart
						data={chartData}
						exerciseKey={selectedExercise?.exercise_key}
						video={drawerPreviewVideoEl}
					/>
				</div>
			</div>
		</Sheet.Content>
	</Sheet.Root>
</div>
