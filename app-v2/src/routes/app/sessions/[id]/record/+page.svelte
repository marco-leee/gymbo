<script lang="ts">
	import { page } from "$app/stores";
	import { invalidateAll } from "$app/navigation";
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
	import {
		addSet,
		recordSet,
		startSession,
		completeSession,
		type SessionExercise,
		type ExerciseSet,
	} from "$lib/api/sessions";
	import { createMutation } from "@tanstack/svelte-query";
	import {
		// ChartContainer,
		type ChartConfig,
	} from "$lib/components/ui/chart/index.js";
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
	let videoInputEl = $state<HTMLInputElement | null>(null);
	let durationCheckVideoEl = $state<HTMLVideoElement | null>(null);

	// Placeholder: angle (degrees) per frame, squat-like; real data will match backend angles_of_interest
	const placeholderChartData = (() => {
		const frames = 20;
		const data: { frame: number; set1: number; set2: number; set3: number }[] =
			[];
		for (let i = 0; i < frames; i++) {
			const t = i / (frames - 1);
			const phase = t < 0.5 ? 2 * t : 2 * (1 - t);
			const base = 90 + 30 * Math.sin(phase * Math.PI);
			data.push({
				frame: i,
				set1: Math.round(base),
				set2: Math.round(base + 2 * Math.sin(i * 0.5)),
				set3: Math.round(base - 1.5 * Math.cos(i * 0.4)),
			});
		}
		return data;
	})();

	const setAnalysisChartConfig: ChartConfig = {
		set1: { label: "Set 1", color: "hsl(var(--chart-1))" },
		set2: { label: "Set 2", color: "hsl(var(--chart-2))" },
		set3: { label: "Set 3", color: "hsl(var(--chart-3))" },
	};

	const setAnalysisSeries = [
		{
			key: "set1",
			label: "Set 1",
			value: (d: (typeof placeholderChartData)[number]) => d.set1,
			color: "hsl(var(--chart-1))",
		},
		{
			key: "set2",
			label: "Set 2",
			value: (d: (typeof placeholderChartData)[number]) => d.set2,
			color: "hsl(var(--chart-2))",
		},
		{
			key: "set3",
			label: "Set 3",
			value: (d: (typeof placeholderChartData)[number]) => d.set3,
			color: "hsl(var(--chart-3))",
		},
	];

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
		uploadError = "";
		isUploading = false;
		drawerOpen = true;
	}

	function getVideoDisplaySrc(): string | null {
		if (videoBlobUrl) return videoBlobUrl;
		if (selectedSet?.video_play_url) return selectedSet.video_play_url;
		return null;
	}

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
		<Sheet.Content side="bottom" class="h-[70vh]">
			<Sheet.Header>
				<Sheet.Title>
					{selectedExercise?.name} — Set {selectedSet?.set_number}
				</Sheet.Title>
			</Sheet.Header>
			<div class="space-y-4 py-4 p-4">
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

			<div class="space-y-2 border-t pt-4">
				<h3 class="text-sm font-medium">Set analysis (angle over time)</h3>
				<!-- <ChartContainer config={setAnalysisChartConfig} class="min-h-[200px] w-full">
					<LineChart
						data={placeholderChartData}
						x={(d) => d.frame}
						series={setAnalysisSeries}
						grid={true}
						axis={true}
						tooltip={true}
						points={true}
						legend={true}
					/>
				</ChartContainer> -->
			</div>
		</Sheet.Content>
	</Sheet.Root>
</div>
