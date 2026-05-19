import { env as privateEnv } from '$env/dynamic/private';

export const env = {
	MONGO_URI: privateEnv.MONGO_URI || 'mongodb://gymbo:gymbo@localhost:27017/gymbo?authSource=admin',
	STORAGE_ENDPOINT: privateEnv.STORAGE_ENDPOINT || 'http://localhost:9000',
	STORAGE_REGION: privateEnv.STORAGE_REGION || 'auto',
	STORAGE_ACCESS_KEY: privateEnv.STORAGE_ACCESS_KEY || 'admin',
	STORAGE_SECRET_KEY: privateEnv.STORAGE_SECRET_KEY || 'qwertyui',
	STORAGE_BUCKET: privateEnv.STORAGE_BUCKET || 'gymbo',
	MODEL_KEY: privateEnv.MODEL_KEY || 'yolo26s-pose.onnx',
	MODEL_VERSION: privateEnv.MODEL_VERSION || 'v1',
	/** Local video queue: Redis list LPUSH. Omit when using RunPod in deployed envs. */
	REDIS_URL: privateEnv.REDIS_URL,
	REDIS_VIDEO_QUEUE_KEY: privateEnv.REDIS_VIDEO_QUEUE_KEY || 'video_jobs',
	/** Deployed: POST same JSON job body as Redis. When set, Redis is not used. */
	VIDEO_QUEUE_RUNPOD_URL: privateEnv.VIDEO_QUEUE_RUNPOD_URL,
	VIDEO_QUEUE_RUNPOD_API_KEY: privateEnv.VIDEO_QUEUE_RUNPOD_API_KEY,
	/** Better Auth signing secret (min 32 chars). Override in production. */
	BETTER_AUTH_SECRET:
		privateEnv.BETTER_AUTH_SECRET ||
		'dev-only-better-auth-secret-change-in-production-32chars',
	BETTER_AUTH_URL: privateEnv.BETTER_AUTH_URL || 'http://localhost:5173',
	GITHUB_CLIENT_ID: privateEnv.GITHUB_CLIENT_ID,
	GITHUB_CLIENT_SECRET: privateEnv.GITHUB_CLIENT_SECRET,
	GOOGLE_CLIENT_ID: privateEnv.GOOGLE_CLIENT_ID,
	GOOGLE_CLIENT_SECRET: privateEnv.GOOGLE_CLIENT_SECRET
};