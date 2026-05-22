import { env } from '$lib/env';
import type { VideoProcessingJob } from './types';

export async function pushVideoJobRunpod(job: VideoProcessingJob): Promise<void> {
	const url = env.VIDEO_QUEUE_RUNPOD_URL;
	if (!url) throw new Error('VIDEO_QUEUE_RUNPOD_URL is not configured');

	const headers: Record<string, string> = {
		'Content-Type': 'application/json'
	};
	if (env.VIDEO_QUEUE_RUNPOD_API_KEY) {
		headers.Authorization = `Bearer ${env.VIDEO_QUEUE_RUNPOD_API_KEY}`;
	}

	const res = await fetch(url, {
		method: 'POST',
		headers,
		body: JSON.stringify({ input: job })
	});

	if (!res.ok) {
		const text = await res.text();
		throw new Error(`RunPod queue HTTP ${res.status}: ${text || res.statusText}`);
	}
}
