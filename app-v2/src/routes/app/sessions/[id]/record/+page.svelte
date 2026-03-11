<script lang="ts">
	import { page } from "$app/stores";
	import { invalidateAll } from "$app/navigation";
	import { onDestroy } from "svelte";
	import { Button } from "$lib/components/ui/button/index.js";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import {
		Card,
		CardContent,
		CardHeader,
		CardTitle,
	} from "$lib/components/ui/card/index.js";
	import { Input } from "$lib/components/ui/input/index.js";
	import { Label } from "$lib/components/ui/label/index.js";
	import * as Table from "$lib/components/ui/table/index.js";
	import * as Sheet from "$lib/components/ui/sheet/index.js";
	import * as Collapsible from "$lib/components/ui/collapsible/index.js";
	import ChevronLeftIcon from "@lucide/svelte/icons/chevron-left";
	import PlusIcon from "@lucide/svelte/icons/plus";
	import VideoIcon from "@lucide/svelte/icons/video";
	import CheckIcon from "@lucide/svelte/icons/check";
	import Chart, { type ChartPoint } from "./chart.svelte";
	import {
		addSet,
		recordSet,
		startSession,
		completeSession,
		type SessionExercise,
		type ExerciseSet,
	} from "$lib/api/sessions";
	import { createMutation } from "@tanstack/svelte-query";
	import { getPoseModelData } from "$lib/services/model-cache";
	import YoloWorker from "$lib/workers/yolo.worker?worker";
	// import { LineChart } from "layerchart";

	type PoseKeypoint = {
		x: number;
		y: number;
		confidence: number;
	};

	type PoseDetection = {
		confidence: number;
		classId: number;
		box: {
			x: number;
			y: number;
			width: number;
			height: number;
		};
		keypoints: PoseKeypoint[];
	};

	type SquatInterestPoint = {
		idxToCoordinates: Record<number, [number, number]>;
		angle: number;
		rotationAngle: number;
		comment: "GOOD" | "TOO LOW" | "LOWER" | null;
	};

	type PoseWorkerMessage =
		| { type: "ready" }
		| {
				type: "result";
				id: number;
				inputName: string;
				outputNames: string[];
				pose: PoseDetection | null;
		  }
		| {
				type: "error";
				id?: number;
				message: string;
		  };

	let { data } = $props();
	const sessionId = $derived($page.params.id);
	const session = $derived(data.session);

	const startMutation = createMutation(() => ({
		mutationFn: () => startSession(sessionId!),
		onSuccess: () => invalidateAll(),
	}));

	const completeMutation = createMutation(() => ({
		mutationFn: () => completeSession(sessionId!),
		onSuccess: () => invalidateAll(),
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
	const POSE_CONFIDENCE_THRESHOLD = 0.25;
	const RIGHT_SHOULDER_IDX = 6;
	const RIGHT_HIP_IDX = 12;
	const RIGHT_KNEE_IDX = 14;
	const RIGHT_ANKLE_IDX = 16;

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
	let uploadError = $state("");
	let isUploading = $state(false);
	let chartData = $state<ChartPoint[]>([]);
	let videoInputEl = $state<HTMLInputElement | null>(null);
	let durationCheckVideoEl = $state<HTMLVideoElement | null>(null);
	let yoloWorker: Worker | null = null;
	let yoloWorkerReadyPromise: Promise<void> | null = null;
	let yoloWorkerBootPromise: Promise<void> | null = null;
	let resolveYoloWorkerReady: (() => void) | null = null;
	let rejectYoloWorkerReady: ((reason?: unknown) => void) | null = null;
	let nextPoseRequestId = 1;
	const pendingPoseRequests = new Map<
		number,
		{
			resolve: (
				value: Extract<PoseWorkerMessage, { type: "result" }>,
			) => void;
			reject: (reason?: unknown) => void;
		}
	>();

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
		if (videoBlobUrl) URL.revokeObjectURL(videoBlobUrl);
		selectedExercise = exercise;
		selectedSet = set;
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
		chartData = [];
		uploadError = "";
		isUploading = false;
		drawerOpen = true;
	}

	function getVideoDisplaySrc(): string | null {
		if (videoBlobUrl) return videoBlobUrl;
		if (selectedSet?.video_play_url) return selectedSet.video_play_url;
		return null;
	}

	function resetYoloWorkerReadyPromise() {
		yoloWorkerReadyPromise = new Promise<void>((resolve, reject) => {
			resolveYoloWorkerReady = resolve;
			rejectYoloWorkerReady = reject;
		});
	}

	function rejectPendingPoseRequests(reason: unknown) {
		for (const pending of pendingPoseRequests.values()) {
			pending.reject(reason);
		}
		pendingPoseRequests.clear();
	}

	function destroyYoloWorker(reason = new Error("Pose worker destroyed")) {
		rejectYoloWorkerReady?.(reason);
		rejectYoloWorkerReady = null;
		resolveYoloWorkerReady = null;
		rejectPendingPoseRequests(reason);
		if (yoloWorker) {
			yoloWorker.postMessage({ type: "dispose" });
			yoloWorker.terminate();
			yoloWorker = null;
		}
		yoloWorkerReadyPromise = null;
		yoloWorkerBootPromise = null;
	}

	function handleYoloWorkerMessage(event: MessageEvent<PoseWorkerMessage>) {
		const message = event.data;
		if (message.type === "ready") {
			resolveYoloWorkerReady?.();
			resolveYoloWorkerReady = null;
			rejectYoloWorkerReady = null;
			return;
		}

		if (message.type === "error") {
			if (message.id != null) {
				const pending = pendingPoseRequests.get(message.id);
				if (pending) {
					pendingPoseRequests.delete(message.id);
					pending.reject(new Error(message.message));
					return;
				}
			}

			destroyYoloWorker(new Error(message.message));
			console.error("Pose worker error", message.message);
			return;
		}

		const pending = pendingPoseRequests.get(message.id);
		if (!pending) return;

		pendingPoseRequests.delete(message.id);
		pending.resolve(message);
	}

	async function createYoloWorker() {
		if (yoloWorker) return;
		if (yoloWorkerBootPromise) {
			await yoloWorkerBootPromise;
			return;
		}

		resetYoloWorkerReadyPromise();
		yoloWorkerBootPromise = (async () => {
			const modelData = await getPoseModelData();
			const worker = new YoloWorker();
			worker.onmessage = handleYoloWorkerMessage;
			worker.onerror = (event) => {
				const error = new Error(event.message || "Pose worker crashed");
				destroyYoloWorker(error);
				console.error("Pose worker crashed", error);
			};
			yoloWorker = worker;
			worker.postMessage({ type: "init", modelData }, [modelData]);
			await yoloWorkerReadyPromise;
		})()
			.catch((error) => {
				destroyYoloWorker(
					error instanceof Error ? error : new Error("Pose worker failed"),
				);
				throw error;
			})
			.finally(() => {
				yoloWorkerBootPromise = null;
			});

		await yoloWorkerBootPromise;
	}

	async function ensureYoloWorkerReady() {
		await createYoloWorker();
		if (!yoloWorker || !yoloWorkerReadyPromise) {
			throw new Error("Pose worker was not created");
		}

		await yoloWorkerReadyPromise;
		return yoloWorker;
	}

	function createModelInputFromCanvas(ctx: CanvasRenderingContext2D) {
		const imageData = ctx.getImageData(
			0,
			0,
			MODEL_INPUT_SIZE,
			MODEL_INPUT_SIZE,
		).data;
		const channelSize = MODEL_INPUT_SIZE * MODEL_INPUT_SIZE;
		const input = new Float32Array(channelSize * 3);

		for (let pixelIdx = 0; pixelIdx < channelSize; pixelIdx++) {
			const rgbaIdx = pixelIdx * 4;
			input[pixelIdx] = imageData[rgbaIdx] / 255;
			input[channelSize + pixelIdx] = imageData[rgbaIdx + 1] / 255;
			input[channelSize * 2 + pixelIdx] = imageData[rgbaIdx + 2] / 255;
		}

		return input;
	}

	function scaleKeypointToSource(
		keypoint: PoseKeypoint,
		sourceWidth: number,
		sourceHeight: number,
	): [number, number] {
		return [
			(keypoint.x / MODEL_INPUT_SIZE) * sourceWidth,
			(keypoint.y / MODEL_INPUT_SIZE) * sourceHeight,
		];
	}

	function calculateAngle(
		a: [number, number],
		b: [number, number],
		c: [number, number],
		outer = false,
	) {
		const radians =
			Math.atan2(c[1] - b[1], c[0] - b[0]) -
			Math.atan2(a[1] - b[1], a[0] - b[0]);
		let angle = Math.abs((radians * 180) / Math.PI);
		if (outer || angle > 180) {
			angle = 360 - angle;
		}

		return Math.trunc(angle);
	}

	function classifySquatAngle(angle: number): "GOOD" | "TOO LOW" | "LOWER" | null {
		if (angle >= 90 && angle < 120) return "GOOD";
		if (angle < 90) return "TOO LOW";
		if (angle >= 120 && angle < 150) return "LOWER";
		return null;
	}

	function hasConfidentKeypoint(keypoint: PoseKeypoint | undefined) {
		return (keypoint?.confidence ?? 0) >= POSE_CONFIDENCE_THRESHOLD;
	}

	function calculateSquatInterestPoints(
		pose: PoseDetection,
		sourceWidth: number,
		sourceHeight: number,
	): Record<"INSIDE_KNEE" | "OUTSIDE_HIP", SquatInterestPoint> | null {
		const shoulder = pose.keypoints[RIGHT_SHOULDER_IDX];
		const hip = pose.keypoints[RIGHT_HIP_IDX];
		const knee = pose.keypoints[RIGHT_KNEE_IDX];
		const ankle = pose.keypoints[RIGHT_ANKLE_IDX];

		if (
			!hasConfidentKeypoint(shoulder) ||
			!hasConfidentKeypoint(hip) ||
			!hasConfidentKeypoint(knee) ||
			!hasConfidentKeypoint(ankle)
		) {
			return null;
		}

		const shoulderCoord = scaleKeypointToSource(
			shoulder,
			sourceWidth,
			sourceHeight,
		);
		const hipCoord = scaleKeypointToSource(hip, sourceWidth, sourceHeight);
		const kneeCoord = scaleKeypointToSource(knee, sourceWidth, sourceHeight);
		const ankleCoord = scaleKeypointToSource(ankle, sourceWidth, sourceHeight);

		const insideKneeAngle = calculateAngle(hipCoord, kneeCoord, ankleCoord);
		const outsideHipAngle = calculateAngle(
			shoulderCoord,
			hipCoord,
			kneeCoord,
			true,
		);

		return {
			INSIDE_KNEE: {
				idxToCoordinates: {
					[RIGHT_HIP_IDX]: hipCoord,
					[RIGHT_KNEE_IDX]: kneeCoord,
					[RIGHT_ANKLE_IDX]: ankleCoord,
				},
				angle: insideKneeAngle,
				rotationAngle: calculateAngle(
					[kneeCoord[0] + 90, kneeCoord[1]],
					kneeCoord,
					ankleCoord,
				),
				comment: classifySquatAngle(insideKneeAngle),
			},
			OUTSIDE_HIP: {
				idxToCoordinates: {
					[RIGHT_SHOULDER_IDX]: shoulderCoord,
					[RIGHT_HIP_IDX]: hipCoord,
					[RIGHT_KNEE_IDX]: kneeCoord,
				},
				angle: outsideHipAngle,
				rotationAngle: calculateAngle(
					[hipCoord[0] + 90, hipCoord[1]],
					hipCoord,
					kneeCoord,
				),
				comment: classifySquatAngle(outsideHipAngle),
			},
		};
	}

	async function runPoseInference(
		worker: Worker,
		input: Float32Array,
	): Promise<PoseDetection | null> {
		const requestId = nextPoseRequestId++;
		const result = await new Promise<Extract<PoseWorkerMessage, { type: "result" }>>(
			(resolve, reject) => {
				pendingPoseRequests.set(requestId, { resolve, reject });
				worker.postMessage(
					{
						type: "run",
						id: requestId,
						input: {
							data: input.buffer,
							dims: [1, 3, MODEL_INPUT_SIZE, MODEL_INPUT_SIZE],
							type: "float32",
						},
					},
					[input.buffer],
				);
			},
		);

		return result.pose;
	}

	function logSquatInterestPoints(
		fileName: string,
		frameIndex: number,
		timestampSec: number,
		pose: PoseDetection | null,
		squatPoints: Record<"INSIDE_KNEE" | "OUTSIDE_HIP", SquatInterestPoint> | null,
	) {
		if (!pose || !squatPoints) {
			console.log(`Squat frame ${frameIndex}`, {
				fileName,
				timestampSec,
				poseDetected: false,
			});
			return;
		}

		console.log(`Squat frame ${frameIndex}`, {
			fileName,
			timestampSec,
			poseConfidence: pose.confidence,
			insideKnee: squatPoints.INSIDE_KNEE,
			outsideHip: squatPoints.OUTSIDE_HIP,
		});
	}

	function appendChartPoint(
		frameIndex: number,
		timestampSec: number,
		squatPoints: Record<"INSIDE_KNEE" | "OUTSIDE_HIP", SquatInterestPoint> | null,
	) {
		if (!squatPoints) return;

		chartData = [
			...chartData,
			{
				frame: frameIndex,
				timestampSec,
				insideKnee: squatPoints.INSIDE_KNEE.angle,
				outsideHip: squatPoints.OUTSIDE_HIP.angle,
			},
		];
	}

	async function processUploadedVideo(file: File) {
		const worker = await ensureYoloWorkerReady();
		const blobUrl = URL.createObjectURL(file);
		const video = document.createElement("video");
		video.muted = true;
		video.playsInline = true;
		video.preload = "auto";

		try {
			chartData = [];

			await new Promise<void>((resolve, reject) => {
				video.onloadedmetadata = () => resolve();
				video.onerror = () => reject(new Error("Cannot decode uploaded video"));
				video.src = blobUrl;
				video.load();
			});

			const canvas = document.createElement("canvas");
			canvas.width = MODEL_INPUT_SIZE;
			canvas.height = MODEL_INPUT_SIZE;
			const ctx = canvas.getContext("2d", { willReadFrequently: true });
			if (!ctx) throw new Error("Cannot create video canvas");

			console.log("Starting squat video analysis", {
				fileName: file.name,
				width: video.videoWidth,
				height: video.videoHeight,
				durationSec: video.duration,
			});

			await new Promise<void>((resolve, reject) => {
				let settled = false;
				let callbackId: number | null = null;

				const finish = (error?: unknown) => {
					if (settled) return;
					settled = true;
					if (
						callbackId != null &&
						typeof video.cancelVideoFrameCallback === "function"
					) {
						video.cancelVideoFrameCallback(callbackId);
					}
					video.pause();
					video.onended = null;
					video.onerror = null;
					if (error) {
						reject(error);
						return;
					}
					resolve();
				};

				const processFrame = async (timestampSec: number, frameIndex: number) => {
					ctx.drawImage(video, 0, 0, MODEL_INPUT_SIZE, MODEL_INPUT_SIZE);
					const pose = await runPoseInference(
						worker,
						createModelInputFromCanvas(ctx),
					);
					const squatPoints = pose
						? calculateSquatInterestPoints(
								pose,
								video.videoWidth,
								video.videoHeight,
							)
						: null;
					appendChartPoint(frameIndex, timestampSec, squatPoints);
					logSquatInterestPoints(
						file.name,
						frameIndex,
						timestampSec,
						pose,
						squatPoints,
					);
				};

				const requestNextFrame = () => {
					callbackId = video.requestVideoFrameCallback((_, metadata) => {
						video.pause();
						void processFrame(
							metadata.mediaTime,
							Math.max(0, metadata.presentedFrames - 1),
						)
							.then(() => {
								if (
									video.currentTime >= video.duration ||
									metadata.mediaTime >= video.duration
								) {
									finish();
									return;
								}
								requestNextFrame();
								void video.play().catch(finish);
							})
							.catch(finish);
					});
				};

				video.onended = () => finish();
				video.onerror = () => finish(new Error("Video frame processing failed"));
				requestNextFrame();
				void video.play().catch(finish);
			});
		} catch (error) {
			uploadError =
				error instanceof Error ? error.message : "Pose processing failed";
			console.error("Pose processing failed", error);
		} finally {
			video.pause();
			video.removeAttribute("src");
			video.load();
			URL.revokeObjectURL(blobUrl);
		}
	}

	onDestroy(() => {
		destroyYoloWorker();
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
			void processUploadedVideo(file);
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

	function targetLabel(ex: SessionExercise): string {
		if (ex.measurement === "reps") return `${ex.target_reps ?? "—"} reps`;
		return `${ex.target_duration ?? "—"}s`;
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
					{formatTime(session?.scheduled_at ?? "")}
					{#if session?.status === "in-progress"}
						· {elapsedMinutes()} min
					{/if}
				</p>
			</div>
		</div>
		<div class="flex items-center gap-2">
			<Badge
				variant={session?.status === "in-progress" ? "default" : "outline"}
			>
				{session?.status ?? "scheduled"}
			</Badge>
			{#if session?.status === "scheduled"}
				<Button
					onclick={() => startMutation.mutate()}
					disabled={startMutation.isPending}
				>
					Start Session
				</Button>
			{/if}
			{#if session?.status === "in-progress"}
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
		{#each (session?.exercises ?? []).sort((a, b) => a.order_index - b.order_index) as exercise (exercise.id)}
			<Collapsible.Root open={true}>
				<Card>
					<CardHeader class="pb-2">
						<Collapsible.Trigger
							class="flex w-full items-center justify-between text-left"
						>
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
								{#each (exercise.sets ?? []).sort((a, b) => a.set_number - b.set_number) as set (set.id)}
									<Table.Row
										class="cursor-pointer hover:bg-muted/50"
										onclick={() => openSetDrawer(exercise, set)}
									>
										<Table.Cell class="font-medium">{set.set_number}</Table.Cell
										>
										<Table.Cell>{targetLabel(exercise)}</Table.Cell>
										<Table.Cell>
											{#if exercise.measurement === "reps"}
												{set.actual_reps ?? "—"}
											{:else}
												{set.actual_duration ?? "—"}s
											{/if}
										</Table.Cell>
										<Table.Cell>{set.weight_kg ?? "—"}</Table.Cell>
										<Table.Cell>
											{#if set.status === "completed"}
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
						{#if session?.status === "in-progress"}
							<Button
								variant="outline"
								size="sm"
								onclick={() =>
									addSetMutation.mutate({ exerciseId: exercise.id })}
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
							disabled={isUploading}
							onclick={() => videoInputEl?.click()}
						>
							{#if isUploading}
								Uploading…
							{:else}
								<VideoIcon class="mr-2 h-4 w-4" />
								Choose video
							{/if}
						</Button>
						{#if uploadError}
							<p class="text-destructive text-sm">{uploadError}</p>
						{/if}
						{#if getVideoDisplaySrc()}
							<div class="rounded-md border bg-muted/30 overflow-hidden">
								<video
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
						disabled={recordSetMutation.isPending}
					>
						Save set
					</Button>
				</div>

				<div class="space-y-2 border-t p-4 pt-4">
					<h3 class="text-sm font-medium">Set analysis (angle over time)</h3>
					<Chart data={chartData} />
				</div>
			</div>
		</Sheet.Content>
	</Sheet.Root>
</div>
