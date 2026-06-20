import { env as privateEnv } from '$env/dynamic/private';

const DEFAULT_WORKER_URL = 'http://localhost:10001';

export function getTrainerWorkerUrl(): string {
	return privateEnv.TRAINER_WORKER_URL?.trim() || DEFAULT_WORKER_URL;
}

export async function trainerWorkerFetch(
	path: string,
	init?: RequestInit
): Promise<Response> {
	const base = getTrainerWorkerUrl().replace(/\/$/, '');
	return fetch(`${base}${path}`, {
		...init,
		headers: {
			'Content-Type': 'application/json',
			...(init?.headers ?? {})
		}
	});
}

export async function startTrainerRun(runId: string): Promise<void> {
	const res = await trainerWorkerFetch(`/internal/runs/${runId}/start`, { method: 'POST' });
	if (!res.ok) {
		const text = await res.text();
		throw new Error(`Trainer worker start failed: ${res.status} ${text}`);
	}
}

export async function resumeTrainerRun(runId: string): Promise<void> {
	const res = await trainerWorkerFetch(`/internal/runs/${runId}/resume`, { method: 'POST' });
	if (!res.ok) {
		throw new Error(`Trainer worker resume failed: ${res.status}`);
	}
}

export async function endTrainerRun(runId: string): Promise<void> {
	const res = await trainerWorkerFetch(`/internal/runs/${runId}/end`, { method: 'POST' });
	if (!res.ok) {
		throw new Error(`Trainer worker end failed: ${res.status}`);
	}
}
