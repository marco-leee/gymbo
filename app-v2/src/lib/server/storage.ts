import {
	GetObjectCommand,
	HeadObjectCommand,
	PutObjectCommand,
	S3Client
} from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { env } from '$lib/env';

const PRESIGN_PUT_EXPIRES_IN = 15 * 60; // 15 minutes
const PRESIGN_GET_EXPIRES_IN = 15 * 60; // 15 minutes
const MODEL_PRESIGN_GET_EXPIRES_IN = 60 * 60; // 1 hour

function getS3Client(): S3Client {
	const endpoint = env.STORAGE_ENDPOINT;
	const region = env.STORAGE_REGION;
	const accessKey = env.STORAGE_ACCESS_KEY;
	const secretKey = env.STORAGE_SECRET_KEY;

	return new S3Client({
		region,
		endpoint,
		credentials: accessKey && secretKey ? { accessKeyId: accessKey, secretAccessKey: secretKey } : undefined,
		forcePathStyle: true
	});
}

export function getPresignedPutUrl(key: string, contentType: string): Promise<string> {
	const bucket = env.STORAGE_BUCKET;
	const client = getS3Client();
	return getSignedUrl(
		client,
		new PutObjectCommand({
			Bucket: bucket,
			Key: key,
			ContentType: contentType
		}),
		{ expiresIn: PRESIGN_PUT_EXPIRES_IN }
	);
}

export async function getPresignedPlayUrl(key: string): Promise<string> {
	return getPresignedGetUrl(key);
}

export function getPresignedGetUrl(
	key: string,
	options?: {
		bucket?: string;
		expiresIn?: number;
	}
): Promise<string> {
	const bucket = options?.bucket || env.STORAGE_BUCKET;
	const client = getS3Client();
	return getSignedUrl(
		client,
		new GetObjectCommand({
			Bucket: bucket,
			Key: key
		}),
		{ expiresIn: options?.expiresIn ?? PRESIGN_GET_EXPIRES_IN }
	);
}

export async function getModelDownload(): Promise<{
	version: string;
	downloadUrl: string;
	etag?: string;
	contentLength?: number;
}> {
	const key = env.MODEL_KEY;
	if (!key) {
		throw new Error('MODEL_KEY is required');
	}

	const bucket = env.STORAGE_BUCKET;
	const client = getS3Client();
	const head = await client.send(
		new HeadObjectCommand({
			Bucket: bucket,
			Key: key
		})
	);

	return {
		version: env.MODEL_VERSION || head.ETag || key,
		downloadUrl: await getPresignedGetUrl(key, {
			bucket,
			expiresIn: MODEL_PRESIGN_GET_EXPIRES_IN
		}),
		etag: head.ETag ?? undefined,
		contentLength: typeof head.ContentLength === 'number' ? head.ContentLength : undefined
	};
}
