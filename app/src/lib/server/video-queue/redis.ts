import type { VideoProcessingJob } from './types';

export async function pushVideoJobRedis(
	job: VideoProcessingJob,
	redisUrl: string,
	listKey: string
): Promise<void> {
	const { default: Redis } = await import('ioredis');
	const client = new Redis(redisUrl);
	try {
		await client.lpush(listKey, JSON.stringify(job));
	} finally {
		await client.quit();
	}
}
