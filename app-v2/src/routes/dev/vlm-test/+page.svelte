<script lang="ts">
	import { VlmWorkerClient, type VlmResult } from '$lib/ml/vlm-worker-client';
	import { onMount } from 'svelte';

	let status = $state<string>('Not initialized');
	let result = $state<VlmResult | null>(null);
	let isInferring = $state(false);
	let client: VlmWorkerClient | null = null;
	let videoElement: HTMLVideoElement | null = null;
	let canvasElement: HTMLCanvasElement | null = null;
	let stream: MediaStream | null = null;
	let inferenceCount = $state(0);
	let lastInferenceTime = $state<string>('—');

	async function initVlm() {
		try {
			status = 'Initializing VLM worker...';
			client = new VlmWorkerClient();
			await client.init();
			status = 'VLM worker ready';
		} catch (error) {
			status = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
			console.error('VLM init error:', error);
		}
	}

	async function startCamera() {
		try {
			stream = await navigator.mediaDevices.getUserMedia({ video: true });
			if (videoElement) {
				videoElement.srcObject = stream;
			}
			status = 'Camera started';
		} catch (error) {
			status = `Camera error: ${error instanceof Error ? error.message : 'Unknown error'}`;
			console.error('Camera error:', error);
		}
	}

	async function runInference() {
		if (!client || !videoElement || !canvasElement) {
			status = 'Missing client, video, or canvas';
			return;
		}

		if (videoElement.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
			status = 'Video not ready';
			return;
		}

		try {
			isInferring = true;
			const startTime = performance.now();

			// Draw video frame to canvas
			const ctx = canvasElement.getContext('2d');
			if (!ctx) {
				throw new Error('Cannot get canvas context');
			}
			
			canvasElement.width = 640;
			canvasElement.height = 640;
			ctx.drawImage(videoElement, 0, 0, 640, 640);

			// Create ImageBitmap (will be transferred to worker)
			const bitmap = await createImageBitmap(canvasElement);

			// Run inference
			const vlmResult = await client.run(bitmap);

			const duration = Math.round(performance.now() - startTime);
			
			if (vlmResult) {
				result = vlmResult;
				inferenceCount++;
				lastInferenceTime = `${duration}ms`;
				status = `Inference completed in ${duration}ms`;
			} else {
				status = 'Inference dropped (single-flight)';
			}
		} catch (error) {
			status = `Inference error: ${error instanceof Error ? error.message : 'Unknown error'}`;
			console.error('Inference error:', error);
		} finally {
			isInferring = false;
		}
	}

	async function runContinuous() {
		if (!client || !client.isReady) {
			status = 'Client not ready';
			return;
		}

		// Run inference every 1 second (like SessionPhaseController will)
		const interval = setInterval(async () => {
			if (!client?.isReady) {
				clearInterval(interval);
				return;
			}
			await runInference();
		}, 1000);

		// Store interval for cleanup
		return () => clearInterval(interval);
	}

	async function cleanup() {
		if (stream) {
			stream.getTracks().forEach(track => track.stop());
			stream = null;
		}
		if (client) {
			await client.dispose();
			client = null;
		}
		status = 'Cleaned up';
	}

	onMount(() => {
		return () => {
			cleanup();
		};
	});
</script>

<div class="container mx-auto p-8 max-w-4xl">
	<h1 class="text-3xl font-bold mb-6">VLM Worker Test</h1>

	<div class="space-y-4">
		<!-- Status -->
		<div class="p-4 bg-gray-100 rounded-lg dark:bg-gray-800">
			<div class="font-semibold">Status</div>
			<div class="text-sm">{status}</div>
		</div>

		<!-- Controls -->
		<div class="flex gap-2 flex-wrap">
			<button
				onclick={initVlm}
				disabled={client !== null}
				class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
			>
				1. Init VLM Worker
			</button>

			<button
				onclick={startCamera}
				disabled={stream !== null || !client}
				class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
			>
				2. Start Camera
			</button>

			<button
				onclick={runInference}
				disabled={!client || !stream || isInferring}
				class="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
			>
				3. Run Once
			</button>

			<button
				onclick={runContinuous}
				disabled={!client || !stream}
				class="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
			>
				4. Run Continuous (1s)
			</button>

			<button
				onclick={cleanup}
				class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
			>
				Cleanup
			</button>
		</div>

		<!-- Stats -->
		<div class="grid grid-cols-2 gap-4">
			<div class="p-4 bg-gray-100 rounded-lg dark:bg-gray-800">
				<div class="text-sm text-gray-600 dark:text-gray-400">Inferences Run</div>
				<div class="text-2xl font-bold">{inferenceCount}</div>
			</div>
			<div class="p-4 bg-gray-100 rounded-lg dark:bg-gray-800">
				<div class="text-sm text-gray-600 dark:text-gray-400">Last Duration</div>
				<div class="text-2xl font-bold">{lastInferenceTime}</div>
			</div>
		</div>

		<!-- Result -->
		{#if result}
			<div class="p-4 bg-gray-100 rounded-lg dark:bg-gray-800">
				<div class="font-semibold mb-2">Latest Result</div>
				<div class="space-y-1 text-sm">
					<div><span class="font-medium">Label:</span> <code class="px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded">{result.label}</code></div>
					<div><span class="font-medium">Confidence:</span> {result.confidence.toFixed(2)}</div>
					{#if result.stateHint}
						<div><span class="font-medium">State Hint:</span> {result.stateHint}</div>
					{/if}
				</div>
			</div>
		{/if}

		<!-- Video and Canvas -->
		<div class="grid grid-cols-2 gap-4">
			<div>
				<div class="text-sm font-medium mb-2">Camera Feed</div>
				<video
					bind:this={videoElement}
					autoplay
					playsinline
					muted
					class="w-full border rounded-lg"
				></video>
			</div>
			<div>
				<div class="text-sm font-medium mb-2">Canvas (640x640)</div>
				<canvas
					bind:this={canvasElement}
					class="w-full border rounded-lg"
				></canvas>
			</div>
		</div>

		<!-- Info -->
		<div class="p-4 bg-blue-50 rounded-lg dark:bg-blue-900/20">
			<h2 class="font-semibold mb-2">About This Test</h2>
			<ul class="text-sm space-y-1 list-disc list-inside">
				<li>This page tests the VLM worker and client implementation</li>
				<li>Currently using placeholder (always returns "unknown")</li>
				<li>Tests worker initialization, message passing, and single-flight logic</li>
				<li>Run "Continuous" to simulate SessionPhaseController behavior (1s intervals)</li>
				<li>Check DevTools console for worker messages</li>
				<li>Check DevTools Performance tab to verify worker thread usage</li>
			</ul>
		</div>

		<!-- Client State -->
		{#if client}
			<div class="p-4 bg-gray-100 rounded-lg dark:bg-gray-800">
				<div class="font-semibold mb-2">Client State</div>
				<div class="space-y-1 text-sm">
					<div><span class="font-medium">Ready:</span> {client.isReady ? '✅' : '❌'}</div>
					<div><span class="font-medium">Inferring:</span> {client.isInferring ? '⏳' : '—'}</div>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	video {
		aspect-ratio: 4/3;
		object-fit: cover;
		background: black;
	}
	
	canvas {
		aspect-ratio: 1;
		background: black;
	}
</style>
