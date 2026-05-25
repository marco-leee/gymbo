<script lang="ts">
	import { page } from "$app/stores";
	import { goto, invalidateAll } from "$app/navigation";
	import { untrack } from "svelte";
	import { Button } from "$lib/components/ui/button/index.js";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import { Card, CardContent } from "$lib/components/ui/card/index.js";
	import { Input } from "$lib/components/ui/input/index.js";
	import { Label } from "$lib/components/ui/label/index.js";
	import { Textarea } from "$lib/components/ui/textarea/index.js";
	import * as Select from "$lib/components/ui/select/index.js";
	import * as Collapsible from "$lib/components/ui/collapsible/index.js";
	import ChevronLeftIcon from "@lucide/svelte/icons/chevron-left";
	import ChevronDownIcon from "@lucide/svelte/icons/chevron-down";
	import PlusIcon from "@lucide/svelte/icons/plus";
	import CheckIcon from "@lucide/svelte/icons/check";
	import VideoIcon from "@lucide/svelte/icons/video";
	import BarChart3Icon from "@lucide/svelte/icons/bar-chart-3";
	import { Dialog } from "bits-ui";
	import * as Sheet from "$lib/components/ui/sheet/index.js";
	import SetPoseChart from "./chart.svelte";
	import SessionExerciseTimeline from "../run/session-exercise-timeline.svelte";
	import { getMediaPlayUrl } from "$lib/api/media";
	import {
		addSet,
		recordSet,
		startSession,
		completeSession,
		type SessionExercise,
		type ExerciseSet,
		type ExerciseSetVideoMetadata,
		type PoseChartPoint,
	} from "$lib/api/sessions";
	import { createMutation } from "@tanstack/svelte-query";

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
	}));

	const recordSetMutation = createMutation(() => ({
		mutationFn: (vars: {
			exerciseId: string;
			setId: string;
			payload: Parameters<typeof recordSet>[3];
		}) => recordSet(sessionId!, vars.exerciseId, vars.setId, vars.payload),
		onSuccess: () => invalidateAll(),
	}));

	const MAX_VIDEO_SIZE = 200 * 1024 * 1024; // 200MB
	const MAX_VIDEO_DURATION_SEC = 60;

	type CameraViewChoice = "FRONT" | "BACK" | "LEFT" | "RIGHT";

	const CAMERA_VIEW_OPTIONS: { value: CameraViewChoice; label: string }[] = [
		// { value: "FRONT", label: "Front" },
		// { value: "BACK", label: "Back" },
		{ value: "LEFT", label: "Left" },
		{ value: "RIGHT", label: "Right" },
	];

	let uploadingVideoSetId = $state<string | null>(null);

	let videoUploadDialogOpen = $state(false);
	let uploadTargetSet = $state<ExerciseSet | null>(null);
	let uploadPreviewUrl = $state<string | null>(null);
	let uploadStagedFile = $state<File | null>(null);
	let uploadCameraView = $state<CameraViewChoice>("FRONT");
	let uploadDialogError = $state("");
	let uploadPreviewReady = $state(false);
	let uploadPreviewVideoEl = $state<HTMLVideoElement | null>(null);
	let uploadDropActive = $state(false);

	let videoPreviewOpen = $state(false);
	let videoPreviewUrl = $state<string | null>(null);
	let videoPreviewLoading = $state(false);
	let videoPreviewError = $state("");

	async function openVideoPreview(storageKeyOrUrl: string, presignedFallback?: string | null) {
		videoPreviewError = "";
		videoPreviewUrl = null;
		videoPreviewLoading = true;
		videoPreviewOpen = true;
		const raw = storageKeyOrUrl.trim();
		try {
			if (/^https?:\/\//i.test(raw)) {
				videoPreviewUrl = raw;
				return;
			}
			try {
				videoPreviewUrl = await getMediaPlayUrl(raw);
			} catch (firstErr) {
				const fb = presignedFallback?.trim();
				if (fb) {
					videoPreviewUrl = fb;
				} else {
					throw firstErr;
				}
			}
		} catch (e) {
			videoPreviewError =
				e instanceof Error ? e.message : "Could not load video";
		} finally {
			videoPreviewLoading = false;
		}
	}

	let poseChartSheetOpen = $state(false);
	let poseChartSheet = $state<{
		exerciseName: string;
		setNumber: number;
		exerciseKey?: string;
		points: PoseChartPoint[];
	} | null>(null);
	let poseChartSheetVideoEl = $state<HTMLVideoElement | null>(null);
	let poseChartSheetVideoUrl = $state<string | null>(null);
	let poseChartSheetVideoLoading = $state(false);
	let poseChartSheetVideoError = $state("");

	async function resolveChartSheetVideoUrl(set: ExerciseSet): Promise<string | null> {
		const http = (s?: string | null) => {
			const t = s?.trim();
			return t && /^https?:\/\//i.test(t) ? t : null;
		};
		const direct =
			http(set.processed_video_play_url) ?? http(set.video_play_url);
		if (direct) return direct;

		const keyToUrl = async (key?: string | null) => {
			const k = key?.trim();
			if (!k) return null;
			if (http(k)) return k;
			try {
				return await getMediaPlayUrl(k);
			} catch {
				return null;
			}
		};
		return (
			(await keyToUrl(set.processed_video_url)) ??
			(await keyToUrl(set.video_url))
		);
	}

	async function openPoseChartSheet(
		exerciseName: string,
		set: ExerciseSet,
		exerciseKey?: string
	) {
		poseChartSheet = {
			exerciseName,
			setNumber: set.set_number,
			exerciseKey,
			points: set.pose_chart_data ? [...set.pose_chart_data] : [],
		};
		poseChartSheetVideoEl = null;
		poseChartSheetVideoUrl = null;
		poseChartSheetVideoError = "";
		poseChartSheetVideoLoading = true;
		poseChartSheetOpen = true;
		try {
			const url = await resolveChartSheetVideoUrl(set);
			poseChartSheetVideoUrl = url;
			if (!url) {
				poseChartSheetVideoError = "No preview video available for this set.";
			}
		} catch (e) {
			poseChartSheetVideoError =
				e instanceof Error ? e.message : "Could not load video";
		} finally {
			poseChartSheetVideoLoading = false;
		}
	}

	function setFieldsLocked(set: ExerciseSet): boolean {
		return set.status === "completed" || set.status === "processing";
	}

	const canCreateSets = $derived(
		session?.status === "scheduled" || session?.status === "in-progress",
	);

	let timelineExercises = $state<SessionExercise[]>([]);
	let currentExercise = $state<SessionExercise | null>(null);
	let openedSetId = $state<string | null>(null);

	type InlineSetDraft = {
		exerciseId: string;
		setId: string;
		actual_reps: string;
		actual_duration: string;
		weight_kg: string;
		notes: string;
	};

	type InlineFields = Omit<InlineSetDraft, "setId" | "exerciseId">;

	const EMPTY_INLINE_FIELDS: InlineFields = {
		actual_reps: "",
		actual_duration: "",
		weight_kg: "",
		notes: "",
	};

	function seedNewSetFormFromExercise(
		ex: SessionExercise | null,
	): InlineFields {
		if (!ex?.measurement) return { ...EMPTY_INLINE_FIELDS };
		return {
			actual_reps:
				ex.measurement === "reps" && ex.target_reps != null
					? String(ex.target_reps)
					: "",
			actual_duration:
				ex.measurement === "duration" && ex.target_duration != null
					? String(ex.target_duration)
					: "",
			weight_kg: ex.target_weight_kg != null ? String(ex.target_weight_kg) : "",
			notes: "",
		};
	}

	let openedSetDraft = $state<InlineSetDraft | null>(null);

	let newSetForm = $state<InlineFields>({ ...EMPTY_INLINE_FIELDS });

	let createFormAnchoredExerciseId = $state<string | null>(null);

	let creatingNewSet = $state(false);

	/** Pre-fill Create set from exercise targets whenever the selected exercise changes. */
	$effect(() => {
		const ex = currentExercise;
		if (!ex) {
			createFormAnchoredExerciseId = null;
			return;
		}
		if (createFormAnchoredExerciseId === ex.id) return;
		createFormAnchoredExerciseId = ex.id;
		untrack(() => {
			newSetForm = seedNewSetFormFromExercise(ex);
		});
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
				openedSetId = null;
				currentExercise = sorted[0];
			} else {
				currentExercise = sorted.find((e) => e.id === curId) ?? sorted[0];
			}
		});
	});

	const sortedSetsForCurrent = $derived.by(() => {
		const ex = currentExercise;
		if (!ex) return [];
		return [...(ex.sets ?? [])].sort((a, b) => a.set_number - b.set_number);
	});

	const openSetLive = $derived.by(() => {
		if (!openedSetId || !currentExercise) return null;
		return (
			(currentExercise.sets ?? []).find((s) => s.id === openedSetId) ?? null
		);
	});

	const openSetFinger = $derived.by(() => {
		const os = openSetLive;
		if (!os) return "";
		return `${os.id}:${String(os.actual_reps ?? "")}:${String(os.actual_duration ?? "")}:${String(os.weight_kg ?? "")}:${String(os.notes ?? "")}:${os.status}`;
	});

	/** Sync accordion inline form from server when selection or persisted set snapshot changes — not while local draft diverges unless server updates fingerprint. */
	$effect(() => {
		if (
			!openedSetId ||
			!currentExercise ||
			!openSetLive ||
			openSetLive.id !== openedSetId
		) {
			openedSetDraft = null;
			return;
		}
		void openSetFinger;
		const os = openSetLive;
		const ex = currentExercise;
		openedSetDraft = {
			exerciseId: ex.id,
			setId: os.id,
			actual_reps:
				os.actual_reps != null
					? String(os.actual_reps)
					: ex.measurement === "reps" && ex.target_reps != null
						? String(ex.target_reps)
						: "",
			actual_duration:
				os.actual_duration != null
					? String(os.actual_duration)
					: ex.measurement === "duration" && ex.target_duration != null
						? String(ex.target_duration)
						: "",
			weight_kg:
				os.weight_kg != null
					? String(os.weight_kg)
					: ex.target_weight_kg != null
						? String(ex.target_weight_kg)
						: "",
			notes: os.notes ?? "",
		};
	});

	function buildRecordPayload(
		exercise: SessionExercise,
		fields: InlineFields,
	): Parameters<typeof recordSet>[3] {
		const payload: Parameters<typeof recordSet>[3] = {};

		const n = fields.notes?.trim();
		if (n) payload.notes = n;

		if (exercise.measurement === "reps" && fields.actual_reps.trim() !== "") {
			payload.actual_reps = parseInt(fields.actual_reps, 10);
		}
		if (
			exercise.measurement === "duration" &&
			fields.actual_duration.trim() !== ""
		) {
			payload.actual_duration = parseInt(fields.actual_duration, 10);
		}
		if (fields.weight_kg.trim() !== "") {
			payload.weight_kg = parseFloat(fields.weight_kg);
		}

		return payload;
	}

	function saveAccordionDraft() {
		const ex = currentExercise;
		const draft = openedSetDraft;
		if (!ex || !draft || !sessionId) return;
		const target = (ex.sets ?? []).find((s) => s.id === draft.setId);
		if (!target || setFieldsLocked(target)) return;

		const fields: InlineFields = {
			actual_reps: draft.actual_reps,
			actual_duration: draft.actual_duration,
			weight_kg: draft.weight_kg,
			notes: draft.notes,
		};
		recordSetMutation.mutate({
			exerciseId: ex.id,
			setId: draft.setId,
			payload: buildRecordPayload(ex, fields),
		});
	}

	async function submitNewSetFromBottom() {
		const ex = currentExercise;
		if (!sessionId || !ex || creatingNewSet || !canCreateSets) return;
		creatingNewSet = true;
		try {
			const sess = await addSetMutation.mutateAsync({
				exerciseId: ex.id,
			});
			const synced = sess.exercises.find((e) => e.id === ex.id);
			const setsSorted = [...(synced?.sets ?? [])].sort(
				(a, b) => a.set_number - b.set_number,
			);
			const newSet = setsSorted.at(-1);
			if (!newSet) throw new Error("Added set missing from session response.");

			await recordSetMutation.mutateAsync({
				exerciseId: ex.id,
				setId: newSet.id,
				payload: buildRecordPayload(ex, newSetForm),
			});

			newSetForm = seedNewSetFormFromExercise(ex);
			openedSetId = newSet.id;
		} catch (e) {
			console.error(e);
		} finally {
			creatingNewSet = false;
		}
	}

	function revokeUploadBlobOnly() {
		if (uploadPreviewUrl) {
			URL.revokeObjectURL(uploadPreviewUrl);
			uploadPreviewUrl = null;
		}
		uploadPreviewReady = false;
	}

	function resetVideoUploadDialog() {
		uploadDialogError = "";
		revokeUploadBlobOnly();
		uploadStagedFile = null;
		uploadTargetSet = null;
		uploadCameraView = "FRONT";
		uploadDropActive = false;
	}

	function openVideoUploadDialog(set: ExerciseSet) {
		const ex = currentExercise;
		uploadDialogError = "";
		if (!ex || !sessionId || setFieldsLocked(set)) return;
		resetVideoUploadDialog();
		uploadTargetSet = set;
		videoUploadDialogOpen = true;
	}

	async function validateDurationSec(blobUrl: string): Promise<boolean> {
		return new Promise((resolve) => {
			const v = document.createElement("video");
			v.preload = "metadata";
			v.muted = true;
			v.playsInline = true;
			v.src = blobUrl;
			v.onloadedmetadata = () => {
				const dur = v.duration;
				v.removeAttribute("src");
				v.load();
				resolve(!Number.isNaN(dur) && dur > 0 && dur <= MAX_VIDEO_DURATION_SEC);
			};
			v.onerror = () => {
				v.removeAttribute("src");
				v.load();
				resolve(false);
			};
		});
	}

	async function stageUploadVideoFile(file: File | undefined | null) {
		uploadDialogError = "";
		if (!file) return;

		if (file.type !== "video/mp4") {
			uploadDialogError = "Only MP4 video is allowed.";
			return;
		}
		if (file.size > MAX_VIDEO_SIZE) {
			uploadDialogError = `File must be under ${MAX_VIDEO_SIZE / (1024 * 1024)}MB.`;
			return;
		}

		const nextUrl = URL.createObjectURL(file);
		const durationOk = await validateDurationSec(nextUrl);
		if (!durationOk) {
			URL.revokeObjectURL(nextUrl);
			uploadDialogError = `Video must be under ${MAX_VIDEO_DURATION_SEC} seconds.`;
			return;
		}

		revokeUploadBlobOnly();
		uploadPreviewUrl = nextUrl;
		uploadStagedFile = file;
		uploadPreviewReady = false;
	}

	function onUploadDragOver(e: DragEvent) {
		e.preventDefault();
		e.stopPropagation();
		uploadDropActive = true;
	}

	function onUploadDragLeave(e: DragEvent) {
		e.preventDefault();
		e.stopPropagation();
		uploadDropActive = false;
	}

	async function onUploadDrop(e: DragEvent) {
		e.preventDefault();
		e.stopPropagation();
		uploadDropActive = false;
		const file = e.dataTransfer?.files?.[0];
		await stageUploadVideoFile(file);
	}

	async function onUploadFileInputChange(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		input.value = "";
		await stageUploadVideoFile(file);
	}

	async function confirmVideoUpload() {
		const set = uploadTargetSet;
		const file = uploadStagedFile;
		const ex = currentExercise;
		uploadDialogError = "";

		if (!file || !set || !ex || !sessionId) return;
		if (setFieldsLocked(set)) return;

		const videoEl = uploadPreviewVideoEl;
		if (!videoEl || !uploadPreviewReady) {
			uploadDialogError =
				"Video preview isn’t ready yet. Wait a moment or pick another file.";
			return;
		}

		const dur = videoEl.duration;
		const vw = videoEl.videoWidth;
		const vh = videoEl.videoHeight;
		if (Number.isNaN(dur) || dur <= 0 || dur > MAX_VIDEO_DURATION_SEC) {
			uploadDialogError = `Video must be under ${MAX_VIDEO_DURATION_SEC} seconds.`;
			return;
		}

		const video_metadata: ExerciseSetVideoMetadata = {
			camera_view: uploadCameraView,
			duration_sec: dur,
			...(vw > 0 ? { video_width: vw } : {}),
			...(vh > 0 ? { video_height: vh } : {}),
		};

		uploadingVideoSetId = set.id;
		try {
			const signRes = await fetch("/api/media/sign", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					session_id: sessionId,
					exercise_id: ex.id,
					set_id: set.id,
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

			await recordSetMutation.mutateAsync({
				exerciseId: ex.id,
				setId: set.id,
				payload: { video_url: key, video_metadata },
			});

			videoUploadDialogOpen = false;
			resetVideoUploadDialog();
		} catch (err) {
			uploadDialogError = err instanceof Error ? err.message : "Upload failed.";
		} finally {
			uploadingVideoSetId = null;
		}
	}

	const uploadCameraTriggerLabel = $derived(
		CAMERA_VIEW_OPTIONS.find((o) => o.value === uploadCameraView)?.label ??
			"Camera view",
	);
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

	function mergedVolumeLabel(ex: SessionExercise): string {
		return ex.measurement === "reps" ? "Reps" : "Duration";
	}

	function volumeActualPrimary(ex: SessionExercise, set: ExerciseSet): string {
		if (ex.measurement === "reps") {
			return set.actual_reps != null ? `${set.actual_reps} reps` : "—";
		}
		return set.actual_duration != null ? `${set.actual_duration}s` : "—";
	}

	function volumePlanSecondary(ex: SessionExercise): string | null {
		if (ex.measurement === "reps") {
			if (ex.target_reps != null) return `plan ${ex.target_reps} reps`;
			return null;
		}
		if (ex.target_duration != null) return `plan ${ex.target_duration}s`;
		return null;
	}

	function restDisplayPrimary(ex: SessionExercise): string {
		if (ex.rest_seconds != null && ex.rest_seconds > 0) {
			return `${ex.rest_seconds}s`;
		}
		return "—";
	}

	function setAccordionSummaryTitle(
		ex: SessionExercise,
		set: ExerciseSet,
	): string {
		const loadPrimary = set.weight_kg != null ? `${set.weight_kg} kg` : "—";
		const notesPart = set.notes?.trim() ? ` · Notes: ${set.notes.trim()}` : "";
		const planSecondary = volumePlanSecondary(ex);
		const volumePart = `${volumeActualPrimary(ex, set)}${
			planSecondary ? ` · ${planSecondary}` : ""
		}`;
		return `Set ${set.set_number} · ${mergedVolumeLabel(ex)} ${volumePart} · Load ${loadPrimary}${
			ex.target_weight_kg != null ? ` (plan ${ex.target_weight_kg} kg)` : ""
		} · Rest ${restDisplayPrimary(ex)}${notesPart}`;
	}
</script>

<div
	class="app-run fixed inset-0 z-[200] flex flex-col gap-3 overflow-hidden p-3 pt-[max(0.75rem,env(safe-area-inset-top))] pb-[max(0.75rem,env(safe-area-inset-bottom))] md:p-4"
>
	<div
		class="flex w-full shrink-0 items-center justify-between gap-2 border-b border-white/10 pb-3"
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
					Recording
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

	<div class="flex w-full min-h-0 flex-1 flex-col gap-3 overflow-hidden">
		<Card
			class="w-full shrink-0 gap-0 rounded-xl border-white/15 bg-black/30 py-0 text-zinc-100 shadow-none"
		>
			<CardContent class="p-3 sm:p-4">
				{#if timelineExercises.length}
					<SessionExerciseTimeline
						exercises={timelineExercises}
						{currentExercise}
						hideExerciseActions={true}
						omitOuterTimelineChrome={true}
						onSelectExercise={(id) => {
							const ex = timelineExercises.find((e) => e.id === id);
							if (ex) {
								if (currentExercise?.id !== ex.id) openedSetId = null;
								currentExercise = ex;
							}
						}}
					/>
				{:else}
					<p class="text-sm text-zinc-400">No exercises in this session.</p>
				{/if}
			</CardContent>
		</Card>

		<div class="min-h-0 w-full flex-1 space-y-4 overflow-y-auto">
			{#if currentExercise}
				{#if sortedSetsForCurrent.length === 0}
					<p class="text-center text-sm" style="color: var(--app-muted);">
						No sets yet. Add one below.
					</p>
				{/if}

				{#each sortedSetsForCurrent as set (set.id)}
					{@const summaryTitle = setAccordionSummaryTitle(currentExercise, set)}
					{@const planVol = volumePlanSecondary(currentExercise)}
					<Collapsible.Root
						open={openedSetId === set.id}
						onOpenChange={(open) => {
							if (open) openedSetId = set.id;
							else if (openedSetId === set.id) openedSetId = null;
						}}
					>
						<div class="app-card overflow-hidden p-0">
							<div
								class="flex items-start gap-2 border-b px-4 py-3"
								style="border-color: var(--app-border);"
							>
								<Collapsible.Trigger
									class="flex min-w-0 flex-1 gap-3 text-left hover:opacity-90"
									style="color: var(--app-text);"
									aria-expanded={openedSetId === set.id}
									title={summaryTitle}
								>
									<ChevronDownIcon
										class={`h-5 w-5 shrink-0 translate-y-0.5 transition-transform ${openedSetId === set.id ? "rotate-180" : ""}`}
										style="color: var(--app-muted);"
										aria-hidden="true"
									/>
									<div class="min-w-0 flex-1">
										<div class="flex flex-wrap items-center gap-x-2 gap-y-1">
											<span class="text-lg font-bold leading-tight">
												Set {set.set_number}
											</span>
											{#if set.status === "completed"}
												<Badge variant="secondary" class="text-xs">Done</Badge>
											{:else if set.status === "processing"}
												<Badge
													variant="outline"
													class="text-xs border-amber-500/40 bg-amber-950/40 text-amber-100"
												>
													Processing
												</Badge>
											{:else}
												<Badge
													variant="outline"
													class="border-[var(--app-border)] bg-white/5 text-xs"
												>
													Pending
												</Badge>
											{/if}
										</div>
										<div class="mt-2 space-y-2">
											<div class="grid grid-cols-3 gap-x-3 gap-y-2 text-xs">
												<div class="min-w-0">
													<div
														class="font-medium"
														style="color: var(--app-muted);"
													>
														{mergedVolumeLabel(currentExercise)}
													</div>
													<div
														class="mt-0.5 text-sm font-semibold tabular-nums text-zinc-100"
													>
														{volumeActualPrimary(currentExercise, set)}
													</div>
													{#if planVol}
														<span
															class="mt-0.5 block text-[11px] font-normal"
															style="color: var(--app-muted);"
														>
															{planVol}
														</span>
													{/if}
												</div>
												<div class="min-w-0">
													<div
														class="font-medium"
														style="color: var(--app-muted);"
													>
														Load
													</div>
													<div
														class="mt-0.5 text-sm font-semibold tabular-nums text-zinc-100"
													>
														{#if set.weight_kg != null}
															{set.weight_kg} kg
														{:else}
															—
														{/if}
														{#if currentExercise.target_weight_kg != null}
															<span
																class="mt-0.5 block text-[11px] font-normal"
																style="color: var(--app-muted);"
															>
																plan {currentExercise.target_weight_kg} kg
															</span>
														{/if}
													</div>
												</div>
												<div class="min-w-0">
													<div
														class="font-medium"
														style="color: var(--app-muted);"
													>
														Rest
													</div>
													<div
														class="mt-0.5 text-sm font-semibold tabular-nums text-zinc-100"
													>
														{restDisplayPrimary(currentExercise)}
													</div>
												</div>
											</div>
											{#if set.notes?.trim()}
												<p
													class="text-xs leading-snug break-words"
													style="color: var(--app-muted);"
												>
													{set.notes.trim()}
												</p>
											{/if}
										</div>
									</div>
								</Collapsible.Trigger>
								{#if set.video_url}
									<Button
										type="button"
										variant="outline"
										size="sm"
										class="shrink-0 rounded-lg border-[var(--app-border)] bg-white/5 px-2.5 text-xs text-zinc-100 hover:bg-white/10"
										onclick={() =>
											void openVideoPreview(set.video_url!, set.video_play_url)}
										aria-label="View uploaded set video"
									>
										<VideoIcon class="mr-1.5 size-4" />
										View
									</Button>
								{/if}
								{#if set.processed_video_url}
									<Button
										type="button"
										variant="outline"
										size="sm"
										class="shrink-0 rounded-lg border-[var(--app-border)] bg-white/5 px-2.5 text-xs text-zinc-100 hover:bg-white/10"
										onclick={() =>
											void openVideoPreview(
												set.processed_video_url!,
												set.processed_video_play_url
											)}
										aria-label="View processed set video"
									>
										<VideoIcon class="mr-1.5 size-4" />
										View Processed Video
									</Button>
								{/if}
								{#if set.pose_chart_data?.length}
									<Button
										type="button"
										variant="outline"
										size="sm"
										class="shrink-0 rounded-lg border-[var(--app-border)] bg-white/5 px-2.5 text-xs text-zinc-100 hover:bg-white/10"
										onclick={() => {
											if (!currentExercise) return;
											void openPoseChartSheet(
												currentExercise.name,
												set,
												currentExercise.exercise_key
											);
										}}
										aria-label="View pose angle charts for this set"
									>
										<BarChart3Icon class="mr-1.5 size-4" />
										Charts
									</Button>
								{/if}
							</div>
							<Collapsible.Content>
								<div
									class="border-t p-4"
									style="border-color: var(--app-border);"
								>
									{#if openedSetDraft && openedSetDraft.setId === set.id}
										{@const locked = setFieldsLocked(set)}
										{#if locked}
											<p
												class="mb-4 text-xs"
												style="color: var(--app-muted);"
											>
												This set can’t be edited while it’s processing or after
												it’s marked done.
											</p>
										{/if}
										<div class="grid gap-4 sm:grid-cols-2">
											{#if currentExercise.measurement === "reps"}
												<div class="space-y-2 sm:col-span-1">
													<Label
														for={"set-" + set.id + "-reps"}
														class="text-xs"
														style="color: var(--app-muted);"
													>
														Planned Reps
													</Label>
													<Input
														id={"set-" + set.id + "-reps"}
														type="number"
														min="0"
														bind:value={openedSetDraft.actual_reps}
														disabled={locked}
														class="border-[var(--app-border)] bg-black/20 text-zinc-100 disabled:opacity-60"
													/>
												</div>
											{:else}
												<div class="space-y-2 sm:col-span-1">
													<Label
														for={"set-" + set.id + "-dur"}
														class="text-xs"
														style="color: var(--app-muted);"
													>
														Duration (s)
														{#if currentExercise.target_duration != null}
															<span class="font-normal opacity-75">
																(plan {currentExercise.target_duration}s)</span
															>
														{/if}
													</Label>
													<Input
														id={"set-" + set.id + "-dur"}
														type="number"
														min="0"
														bind:value={openedSetDraft.actual_duration}
														disabled={locked}
														class="border-[var(--app-border)] bg-black/20 text-zinc-100 disabled:opacity-60"
													/>
												</div>
											{/if}
											<div class="space-y-2 sm:col-span-1">
												<Label
													for={"set-" + set.id + "-wt"}
													class="text-xs"
													style="color: var(--app-muted);"
												>
													Planned Weight (kg)
												</Label>
												<Input
													id={"set-" + set.id + "-wt"}
													type="number"
													step="0.5"
													min="0"
													bind:value={openedSetDraft.weight_kg}
													disabled={locked}
													class="border-[var(--app-border)] bg-black/20 text-zinc-100 disabled:opacity-60"
												/>
											</div>
											<div class="space-y-2 sm:col-span-2">
												<Label
													for={"set-" + set.id + "-notes"}
													class="text-xs"
													style="color: var(--app-muted);">Notes</Label
												>
												<Textarea
													id={"set-" + set.id + "-notes"}
													rows={3}
													bind:value={openedSetDraft.notes}
													disabled={locked}
													class="border-[var(--app-border)] bg-black/20 text-zinc-100 disabled:opacity-60"
												/>
											</div>
										</div>
										{#if !locked}
											<div
												class="mt-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center"
											>
												<div class="flex flex-wrap gap-2">
													<Button
														type="button"
														class="app-cta rounded-lg"
														disabled={recordSetMutation.isPending ||
															uploadingVideoSetId === set.id}
														onclick={() => saveAccordionDraft()}
													>
														Save
													</Button>
													<Button
														type="button"
														variant="outline"
														class="rounded-lg border-[var(--app-border)] bg-white/5 text-zinc-100"
														disabled={recordSetMutation.isPending ||
															uploadingVideoSetId === set.id}
														onclick={() => openVideoUploadDialog(set)}
													>
														{#if uploadingVideoSetId === set.id}
															Uploading…
														{:else}
															<VideoIcon class="mr-2 h-4 w-4" />
															Upload video
														{/if}
													</Button>
												</div>
											</div>
										{/if}
									{/if}
								</div>
							</Collapsible.Content>
						</div>
					</Collapsible.Root>
				{/each}

				{#if canCreateSets}
					<section
						class="app-card overflow-hidden space-y-4 p-4"
						aria-labelledby="record-new-set-heading"
					>
						<h2
							id="record-new-set-heading"
							class="text-base font-bold"
							style="color: var(--app-text);"
						>
							Create set
						</h2>
						<div class="grid gap-4 sm:grid-cols-2">
							{#if currentExercise.measurement === "reps"}
								<div class="space-y-2">
									<Label
										for="new-set-reps"
										class="text-xs"
										style="color: var(--app-muted);"
									>
										Reps
										{#if currentExercise.target_reps != null}
											<span class="font-normal opacity-75">
												(plan {currentExercise.target_reps})</span
											>
										{/if}
									</Label>
									<Input
										id="new-set-reps"
										type="number"
										min="0"
										bind:value={newSetForm.actual_reps}
										class="border-[var(--app-border)] bg-black/20 text-zinc-100"
									/>
								</div>
							{:else}
								<div class="space-y-2">
									<Label
										for="new-set-duration"
										class="text-xs"
										style="color: var(--app-muted);"
									>
										Duration (s)
										{#if currentExercise.target_duration != null}
											<span class="font-normal opacity-75">
												(plan {currentExercise.target_duration}s)</span
											>
										{/if}
									</Label>
									<Input
										id="new-set-duration"
										type="number"
										min="0"
										bind:value={newSetForm.actual_duration}
										class="border-[var(--app-border)] bg-black/20 text-zinc-100"
									/>
								</div>
							{/if}
							<div class="space-y-2">
								<Label
									for="new-set-weight"
									class="text-xs"
									style="color: var(--app-muted);"
								>
									Weight (kg)
									{#if currentExercise.target_weight_kg != null}
										<span class="font-normal opacity-75">
											(plan {currentExercise.target_weight_kg})</span
										>
									{/if}
								</Label>
								<Input
									id="new-set-weight"
									type="number"
									step="0.5"
									min="0"
									bind:value={newSetForm.weight_kg}
									class="border-[var(--app-border)] bg-black/20 text-zinc-100"
								/>
							</div>
							<div class="space-y-2 sm:col-span-2">
								<Label
									for="new-set-notes"
									class="text-xs"
									style="color: var(--app-muted);">Notes</Label
								>
								<Textarea
									id="new-set-notes"
									rows={3}
									bind:value={newSetForm.notes}
									class="border-[var(--app-border)] bg-black/20 text-zinc-100"
								/>
							</div>
						</div>
						<Button
							type="button"
							class="app-cta w-full rounded-lg sm:w-auto"
							disabled={creatingNewSet ||
								recordSetMutation.isPending ||
								addSetMutation.isPending}
							onclick={() => submitNewSetFromBottom()}
						>
							<PlusIcon class="mr-2 h-4 w-4" />
							Create set
						</Button>
					</section>
				{/if}
			{:else}
				<p class="text-center text-sm text-zinc-500">
					Select an exercise above.
				</p>
			{/if}
		</div>
	</div>

	<Dialog.Root
		bind:open={videoUploadDialogOpen}
		onOpenChange={(o) => {
			if (!o) resetVideoUploadDialog();
		}}
	>
		<Dialog.Portal>
			<Dialog.Overlay
				class="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 fixed inset-0 z-[252] bg-black/80"
			/>
			<Dialog.Content
				aria-labelledby="record-upload-video-dialog-title"
				class="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 fixed left-[50%] top-[50%] z-[253] grid max-h-[min(90vh,calc(100vh-2rem))] w-[calc(100vw-1.5rem)] max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 overflow-y-auto rounded-xl border border-white/15 bg-zinc-950 p-4 shadow-xl duration-200"
			>
				<Dialog.Title
					class="text-lg font-semibold leading-none text-white"
					id="record-upload-video-dialog-title"
				>
					Upload set video
				</Dialog.Title>
				<Dialog.Description class="text-sm" style="color: var(--app-muted);">
					Drop an MP4 here (max {MAX_VIDEO_DURATION_SEC}s, {(
						MAX_VIDEO_SIZE /
						(1024 * 1024)
					).toFixed(0)}MB). Choose camera angle, then upload.
				</Dialog.Description>

				<input
					id="record-upload-video-input"
					type="file"
					accept="video/mp4,.mp4"
					class="sr-only"
					onchange={onUploadFileInputChange}
				/>

				<div
					role="presentation"
					class={`rounded-xl border-2 border-dashed px-4 py-8 text-center transition-colors ${uploadDropActive ? "border-emerald-400/60 bg-emerald-950/30" : "border-[var(--app-border)] bg-black/25"}`}
					ondragover={onUploadDragOver}
					ondragleave={onUploadDragLeave}
					ondrop={onUploadDrop}
				>
					<p class="text-sm text-zinc-300">Drag and drop your video here</p>
					<Button
						type="button"
						variant="outline"
						class="mt-4 rounded-lg border-[var(--app-border)] bg-white/5 text-zinc-100"
						onclick={() =>
							document.getElementById("record-upload-video-input")?.click()}
					>
						Choose file
					</Button>
				</div>

				{#if uploadPreviewUrl}
					<div class="space-y-2">
						<Label class="text-xs" style="color: var(--app-muted);"
							>Preview</Label
						>
						<!-- svelte-ignore a11y_media_has_caption -->
						{#key uploadPreviewUrl}
							<video
								bind:this={uploadPreviewVideoEl}
								src={uploadPreviewUrl}
								controls
								muted
								class="aspect-video w-full rounded-lg bg-black"
								playsinline
								preload="metadata"
								onloadedmetadata={() => {
									uploadPreviewReady = true;
								}}
								onerror={() => {
									uploadPreviewReady = false;
									uploadDialogError =
										"This file couldn’t be previewed. Try another MP4.";
								}}
							></video>
						{/key}
					</div>
				{/if}

				<div class="space-y-2">
					<Label
						for="record-upload-camera-view"
						class="text-xs"
						style="color: var(--app-muted);"
					>
						Camera view
					</Label>
					<Select.Root
						type="single"
						value={uploadCameraView}
						onValueChange={(v) => {
							if (v) uploadCameraView = v as CameraViewChoice;
						}}
					>
						<Select.Trigger
							class="min-h-11 w-full border-[var(--app-border)] bg-black/20 text-zinc-100"
							id="record-upload-camera-view"
						>
							{uploadCameraTriggerLabel}
						</Select.Trigger>
						<!-- Above Dialog overlay/content (z-[252]/253); default Select uses z-50 and renders behind -->
						<Select.Content class="z-[260]">
							{#each CAMERA_VIEW_OPTIONS as opt (opt.value)}
								<Select.Item value={opt.value}>{opt.label}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				</div>

				{#if uploadDialogError}
					<p class="text-xs text-red-400">{uploadDialogError}</p>
				{/if}

				<div class="flex flex-wrap justify-end gap-2 pt-2">
					<Dialog.Close
						class="inline-flex h-9 items-center justify-center rounded-lg border border-[var(--app-border)] bg-white/5 px-4 text-sm font-medium text-zinc-100 hover:bg-white/10"
					>
						Cancel
					</Dialog.Close>
					<Button
						type="button"
						class="app-cta rounded-lg"
						disabled={!uploadStagedFile ||
							!uploadPreviewReady ||
							uploadingVideoSetId !== null ||
							recordSetMutation.isPending}
						onclick={() => void confirmVideoUpload()}
					>
						{#if uploadingVideoSetId !== null && uploadTargetSet?.id === uploadingVideoSetId}
							Uploading…
						{:else}
							Upload
						{/if}
					</Button>
				</div>
			</Dialog.Content>
		</Dialog.Portal>
	</Dialog.Root>

	<Dialog.Root
		bind:open={videoPreviewOpen}
		onOpenChange={(o) => {
			if (!o) {
				videoPreviewUrl = null;
				videoPreviewError = "";
				videoPreviewLoading = false;
			}
		}}
	>
		<Dialog.Portal>
			<Dialog.Overlay
				class="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 fixed inset-0 z-[250] bg-black/80"
			/>
			<Dialog.Content
				aria-labelledby="record-set-video-dialog-title"
				class="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 fixed left-[50%] top-[50%] z-[251] grid w-[calc(100vw-1.5rem)] max-w-3xl translate-x-[-50%] translate-y-[-50%] gap-4 rounded-xl border border-white/15 bg-zinc-950 p-4 shadow-xl duration-200"
			>
				<Dialog.Title
					class="text-lg font-semibold leading-none text-white"
					id="record-set-video-dialog-title"
				>
					Set video
				</Dialog.Title>
				<Dialog.Description class="sr-only">
					Uploaded video for this set. Use the controls to play or pause.
				</Dialog.Description>
				{#if videoPreviewLoading}
					<p class="text-sm" style="color: var(--app-muted);">Loading…</p>
				{:else if videoPreviewError}
					<p class="text-sm text-red-400">{videoPreviewError}</p>
				{:else if videoPreviewUrl}
					{#key videoPreviewUrl}
						<!-- svelte-ignore a11y_media_has_caption -->
						<video
							src={videoPreviewUrl}
							controls
							class="aspect-video w-full max-h-[75vh] rounded-lg bg-black"
							playsinline
							preload="metadata"
						></video>
					{/key}
				{/if}
				<div class="flex justify-end gap-2 pt-2">
					<Dialog.Close
						class="inline-flex h-9 items-center justify-center rounded-lg border border-[var(--app-border)] bg-white/5 px-4 text-sm font-medium text-zinc-100 hover:bg-white/10"
					>
						Close
					</Dialog.Close>
				</div>
			</Dialog.Content>
		</Dialog.Portal>
	</Dialog.Root>

	<Sheet.Root
		bind:open={poseChartSheetOpen}
		onOpenChange={(o) => {
			if (!o) {
				poseChartSheet = null;
				poseChartSheetVideoUrl = null;
				poseChartSheetVideoLoading = false;
				poseChartSheetVideoError = "";
			}
		}}
	>
		<Sheet.Content
			side="bottom"
			class="z-[260] flex h-[85vh] max-h-[85vh] flex-col gap-0 overflow-hidden rounded-t-xl border border-white/15 border-b-0 bg-zinc-950 p-0 text-zinc-100"
		>
			<Sheet.Header class="border-b border-white/10 p-4 text-left">
				<Sheet.Title class="text-lg font-semibold text-white">
					Pose angles
				</Sheet.Title>
				{#if poseChartSheet}
					<Sheet.Description class="text-sm text-zinc-400">
						{poseChartSheet.exerciseName} · Set {poseChartSheet.setNumber} ·
						Video preview and inside knee vs outside hip (degrees) by frame
					</Sheet.Description>
				{/if}
			</Sheet.Header>
			<div
				class="flex min-h-0 flex-1 flex-col gap-4 overflow-hidden p-4 md:flex-row md:gap-4"
			>
				<div
					class="flex w-full shrink-0 flex-col md:w-[40%] md:min-h-0 md:max-w-[40%]"
				>
					<p
						class="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500"
					>
						Preview
					</p>
					<div
						class="flex min-h-[min(40vh,280px)] flex-1 items-center justify-center rounded-lg border border-white/10 bg-black/40 md:min-h-0"
					>
						{#if poseChartSheetVideoLoading}
							<p class="text-sm text-zinc-400">Loading video…</p>
						{:else if poseChartSheetVideoError && !poseChartSheetVideoUrl}
							<p class="max-w-[90%] px-2 text-center text-sm text-red-400">
								{poseChartSheetVideoError}
							</p>
						{:else if poseChartSheetVideoUrl}
							{#key poseChartSheetVideoUrl}
								<!-- svelte-ignore a11y_media_has_caption -->
								<video
									bind:this={poseChartSheetVideoEl}
									src={poseChartSheetVideoUrl}
									controls
									class="max-h-full w-full rounded-md object-contain"
									playsinline
									preload="metadata"
								></video>
							{/key}
						{:else}
							<p class="text-sm text-zinc-400">No preview video.</p>
						{/if}
					</div>
				</div>
				<div
					class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden md:min-w-0"
				>
					<p
						class="mb-2 shrink-0 text-xs font-medium uppercase tracking-wide text-zinc-500"
					>
						Chart
					</p>
					<div
						class="min-h-0 flex-1 overflow-y-auto overflow-x-hidden overscroll-y-contain touch-pan-y p-6"
					>
						{#if poseChartSheet?.points.length}
							<div class="flex flex-col gap-6 pb-1">
								<SetPoseChart
									data={poseChartSheet.points}
									exerciseKey={poseChartSheet.exerciseKey}
									video={poseChartSheetVideoEl}
								/>
							</div>
						{:else}
							<p class="text-sm text-zinc-400" role="status">
								No chart data for this set.
							</p>
						{/if}
					</div>
				</div>
			</div>
		</Sheet.Content>
	</Sheet.Root>
</div>
