import { GetObjectCommand, PutObjectCommand, S3Client } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { env } from '$env/dynamic/private';

const PRESIGN_PUT_EXPIRES_IN = 15 * 60; // 15 minutes
const PRESIGN_GET_EXPIRES_IN = 15 * 60; // 15 minutes

function getS3Client(): S3Client {
	const endpoint = env.STORAGE_ENDPOINT || 'http://localhost:9000';
	const region = env.STORAGE_REGION || 'ap-southeast-1';
	const accessKey = env.STORAGE_ACCESS_KEY || 'admin';
	const secretKey = env.STORAGE_SECRET_KEY || 'qwertyui';


	console.log('endpoint', endpoint);
	console.log('region', region);
	console.log('accessKey', accessKey);
	console.log('secretKey', secretKey);

	return new S3Client({
		region,
		endpoint,
		credentials: accessKey && secretKey ? { accessKeyId: accessKey, secretAccessKey: secretKey } : undefined,
		forcePathStyle: true
	});
}

export function getPresignedPutUrl(key: string, contentType: string): Promise<string> {
	const bucket = env.STORAGE_BUCKET || 'gymbo';
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
	const bucket = env.STORAGE_BUCKET || 'gymbo';
	const client = getS3Client();
	return getSignedUrl(
		client,
		new GetObjectCommand({
			Bucket: bucket,
			Key: key
		}),
		{ expiresIn: PRESIGN_GET_EXPIRES_IN }
	);
}
