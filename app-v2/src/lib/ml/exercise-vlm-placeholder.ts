/**
 * Placeholder for a future Transformers.js exercise classifier.
 * Replace `inferFrame` with a real `@huggingface/transformers` pipeline when ready.
 */
export type VlmResult = {
	label: "unknown" | "squat" | "not_exercising";
	confidence: number;
	/** Optional hint for the analysis state machine (future use). */
	stateHint?: string;
	raw?: unknown;
};

export class ExerciseVlmPlaceholder {
	async init(): Promise<void> {
		return;
	}

	async dispose(): Promise<void> {
		return;
	}

	async inferFrame(
		_input: ImageBitmap | VideoFrame | OffscreenCanvas,
	): Promise<VlmResult> {
		return { label: "unknown", confidence: 0 };
	}
}
