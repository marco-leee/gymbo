import { env } from '$lib/env';
import { pushVideoJobRedis } from './redis';
import { pushVideoJobRunpod } from './runpod';
import type { VideoProcessingJob } from './types';

/** Best-effort: logs on failure; never throws (PUT must still succeed). */
export async function enqueueVideoProcessingJob(job: VideoProcessingJob): Promise<void> {
	try {
		if (env.VIDEO_QUEUE_RUNPOD_URL) {
			await pushVideoJobRunpod(job);
			return;
		}
		if (env.REDIS_URL) {
			await pushVideoJobRedis(job, env.REDIS_URL, env.REDIS_VIDEO_QUEUE_KEY);
			return;
		}
		console.warn(
			'[video-queue] Skip enqueue: set REDIS_URL (local) or VIDEO_QUEUE_RUNPOD_URL (deployed)'
		);
	} catch (err) {
		console.error('[video-queue] Enqueue failed (best-effort):', err);
	}
}
