import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { z } from 'zod';
import { getPresignedPutUrl } from '$lib/server/storage';

const MAX_FILE_SIZE = 200 * 1024 * 1024; // 200MB

const SignBodySchema = z.object({
	session_id: z.string().min(1),
	exercise_id: z.string().min(1),
	set_id: z.string().min(1),
	file_name: z.string().min(1),
	file_type: z.string(),
	file_size: z.number().int().nonnegative()
});

export const POST: RequestHandler = async ({ request }) => {
	try {
		const body = await request.json();
		const parsed = SignBodySchema.parse(body);

		if (parsed.file_type !== 'video/mp4') {
			throw error(400, 'Only video/mp4 is allowed');
		}
		if (parsed.file_size > MAX_FILE_SIZE) {
			throw error(400, `File size must not exceed ${MAX_FILE_SIZE / (1024 * 1024)}MB`);
		}

		const key = `session/${parsed.session_id}/exercises/${parsed.exercise_id}/sets/${parsed.set_id}/video.mp4`;
		const upload_url = await getPresignedPutUrl(key, 'video/mp4');

		return json({ upload_url, key });
	} catch (err) {
		if (err instanceof z.ZodError) {
			throw error(400, err.issues.map((e) => e.message).join(', '));
		}
		if (err instanceof Error && 'status' in err) throw err;
		console.error('Failed to sign media upload:', err);
		throw error(500, 'Failed to sign media upload');
	}
};
