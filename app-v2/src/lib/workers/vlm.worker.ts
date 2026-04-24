/**
 * VLM (Vision Language Model) Web Worker for exercise repetition detection.
 * 
 * Placeholder implementation for Phase 1A.
 * This will be upgraded to use Transformers.js + Gemma 4 VLM in Phase 1B.
 * 
 * The VLM detects whether the user is performing repetitions (exercising),
 * NOT the specific exercise type. Exercise identification is handled by the pose engine.
 */

type WorkerScope = {
	onmessage: ((event: MessageEvent<WorkerInputMessage>) => void | Promise<void>) | null;
	postMessage: (message: unknown, transfer?: Transferable[]) => void;
};

const workerScope = self as unknown as WorkerScope;

// Message types: main thread → worker

type InitMessage = {
	type: "init";
};

type RunMessage = {
	type: "run";
	id: number;
	bitmap: ImageBitmap;
};

type DisposeMessage = {
	type: "dispose";
};

type WorkerInputMessage = InitMessage | RunMessage | DisposeMessage;

// Message types: worker → main thread

export type VlmResult = {
	label: "unknown" | "exercising" | "not_exercising";
	confidence: number;
	stateHint?: string;
	raw?: unknown;
};

type ReadyMessage = {
	type: "ready";
};

type ResultMessage = {
	type: "result";
	id: number;
	vlm: VlmResult;
};

type ErrorMessage = {
	type: "error";
	id?: number;
	message: string;
};

type WorkerOutputMessage = ReadyMessage | ResultMessage | ErrorMessage;

// Worker state
let isReady = false;

/**
 * Placeholder initialization.
 * In Phase 1B, this will load Transformers.js + Gemma 4 VLM model.
 */
async function initializePlaceholder(): Promise<void> {
	if (isReady) return;
	
	// Simulate model loading delay
	await new Promise(resolve => setTimeout(resolve, 100));
	
	console.log("[VLM Worker] Placeholder initialized");
	isReady = true;
}

/**
 * Placeholder inference.
 * In Phase 1B, this will use Gemma 4 to detect repetition activity.
 * 
 * @param bitmap - ImageBitmap from video frame
 * @returns VlmResult with exercising/not_exercising/unknown
 */
async function inferFramePlaceholder(_bitmap: ImageBitmap): Promise<VlmResult> {
	// Placeholder: always return unknown
	// Real implementation will analyze the image and return exercising/not_exercising
	
	return {
		label: "unknown",
		confidence: 0.0,
	};
}

/**
 * Cleanup placeholder state.
 * In Phase 1B, this will dispose the Transformers.js model.
 */
function disposePlaceholder(): void {
	isReady = false;
	console.log("[VLM Worker] Placeholder disposed");
}

// Message handler
workerScope.onmessage = async (event: MessageEvent<WorkerInputMessage>) => {
	const message = event.data;

	try {
		if (message.type === "init") {
			await initializePlaceholder();
			workerScope.postMessage({ type: "ready" } satisfies ReadyMessage);
			return;
		}

		if (message.type === "run") {
			if (!isReady) {
				throw new Error("VLM worker not initialized. Call init() first.");
			}

			const vlm = await inferFramePlaceholder(message.bitmap);
			
			workerScope.postMessage({
				type: "result",
				id: message.id,
				vlm,
			} satisfies ResultMessage);
			return;
		}

		if (message.type === "dispose") {
			disposePlaceholder();
			return;
		}
	} catch (error) {
		const errorMessage: ErrorMessage = {
			type: "error",
			message: error instanceof Error ? error.message : "VLM worker failed",
		};

		if (message.type === "run") {
			workerScope.postMessage({ ...errorMessage, id: message.id });
			return;
		}

		workerScope.postMessage(errorMessage);
	}
};
