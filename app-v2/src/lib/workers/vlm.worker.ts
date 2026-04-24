/**
 * VLM (Vision Language Model) Web Worker for exercise repetition detection.
 * 
 * Uses Transformers.js + Gemma 4 VLM for inference.
 * 
 * The VLM detects whether the user is performing repetitions (exercising),
 * NOT the specific exercise type. Exercise identification is handled by the pose engine.
 */

import {
	AutoProcessor,
	Gemma4ForConditionalGeneration,
	RawImage,
	type Processor,
	type PreTrainedModel,
} from "@huggingface/transformers";

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

type LogMessage = {
	type: "log";
	message: string;
};

type WorkerOutputMessage = ReadyMessage | ResultMessage | ErrorMessage | LogMessage;

// Model configuration
const MODEL_ID = "onnx-community/gemma-4-E2B-it-ONNX";

// Worker state
let processor: Processor | null = null;
let model: PreTrainedModel | null = null;
let isReady = false;

/**
 * Helper to send log messages to main thread.
 */
function postLog(message: string): void {
	workerScope.postMessage({ type: "log", message } satisfies LogMessage);
	console.log(message);
}

/**
 * Load Gemma 4 VLM model.
 * Reports progress via console during download.
 */
async function loadModel(): Promise<void> {
	if (isReady && processor && model) {
		return;
	}

	postLog("[VLM Worker] Loading Gemma 4 model...");

	try {
		const [loadedProcessor, loadedModel] = await Promise.all([
			AutoProcessor.from_pretrained(MODEL_ID),
			Gemma4ForConditionalGeneration.from_pretrained(MODEL_ID, {
				dtype: "q4f16",
				device: "webgpu",
				progress_callback: (info: { status: string; progress?: number; file?: string }) => {
					if (info.status === "progress" && info.progress !== undefined) {
						const progress = Math.round(info.progress);
						if (progress % 10 === 0) {
							postLog(`[VLM Worker] Loading: ${progress}%`);
						}
					}
					if (info.status === "download" && info.file) {
						postLog(`[VLM Worker] Downloading: ${info.file}`);
					}
				},
			}),
		]);

		processor = loadedProcessor;
		model = loadedModel;
		isReady = true;

		postLog("[VLM Worker] ✅ Model loaded successfully");
	} catch (error) {
		postLog(`[VLM Worker] ❌ Model load error: ${error instanceof Error ? error.message : String(error)}`);
		throw error;
	}
}

/**
 * Run inference on a video frame using Gemma 2.
 * 
 * @param bitmap - ImageBitmap from video frame
 * @returns VlmResult with exercising/not_exercising/unknown
 */
async function inferFrame(bitmap: ImageBitmap): Promise<VlmResult> {
	if (!processor || !model) {
		throw new Error("VLM model not initialized");
	}

	try {
		// Convert ImageBitmap to format Transformers.js expects
		const blob = await new Promise<Blob>((resolve, reject) => {
			const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
			const ctx = canvas.getContext("2d");
			if (!ctx) {
				reject(new Error("Cannot get canvas context"));
				return;
			}
			ctx.drawImage(bitmap, 0, 0);
			canvas.convertToBlob({ type: "image/jpeg", quality: 0.8 }).then(resolve).catch(reject);
		});

		const image = await RawImage.fromBlob(blob);

		// Create prompt for repetition detection
		const prompt = `<start_of_turn>user
<image>
Is this person actively performing exercise repetitions? Answer with one word: "exercising", "not_exercising", or "unknown".<end_of_turn>
<start_of_turn>model`;

		// Process inputs
		const inputs = await processor(prompt, image);

		// Generate response
		const outputs = await model.generate({
			...inputs,
			max_new_tokens: 10,
			do_sample: false,
			temperature: 0.0,
		});

		// Extract tensor data from output
		// The output can be a Tensor or ModelOutput with sequences
		let outputIds: number[][];
		if (Array.isArray(outputs)) {
			outputIds = outputs;
		} else if ('sequences' in outputs) {
			// ModelOutput has sequences property
			const sequences = (outputs as any).sequences;
			outputIds = sequences.tolist ? sequences.tolist() : [[]]
;
		} else {
			// Fallback: try tolist on the output directly
			outputIds = (outputs as any).tolist ? (outputs as any).tolist() : [[]];
		}

		// Decode output
		const outputText = processor.batch_decode(outputIds, {
			skip_special_tokens: true,
		})[0] || "";

		// Parse response
		return parseVlmResponse(outputText);
	} catch (error) {
		console.error("[VLM Worker] Inference error:", error);
		return {
			label: "unknown",
			confidence: 0.0,
			raw: error instanceof Error ? error.message : String(error),
		};
	}
}

/**
 * Parse VLM model response into VlmResult.
 * 
 * @param text - Raw model output text
 * @returns Parsed VlmResult
 */
function parseVlmResponse(text: string): VlmResult {
	const lower = text.toLowerCase().trim();

	// Extract the response after the model turn marker
	const responseStart = lower.indexOf("<start_of_turn>model");
	const responseText = responseStart >= 0 ? lower.substring(responseStart + 20).trim() : lower;

	// Look for keywords
	if (responseText.includes("exercising") && !responseText.includes("not_exercising")) {
		// Check confidence based on response clarity
		const confidence = responseText === "exercising" ? 0.9 : 0.7;
		return { label: "exercising", confidence };
	}

	if (responseText.includes("not_exercising") || responseText.includes("not exercising")) {
		const confidence = responseText === "not_exercising" || responseText === "not exercising" ? 0.9 : 0.7;
		return { label: "not_exercising", confidence };
	}

	// Unknown or unclear response
	return { label: "unknown", confidence: 0.0, raw: text };
}

/**
 * Cleanup model state.
 */
function disposeModel(): void {
	processor = null;
	model = null;
	isReady = false;
	postLog("[VLM Worker] Model disposed");
}

// Message handler
workerScope.onmessage = async (event: MessageEvent<WorkerInputMessage>) => {
	const message = event.data;

	try {
		if (message.type === "init") {
			await loadModel();
			workerScope.postMessage({ type: "ready" } satisfies ReadyMessage);
			return;
		}

		if (message.type === "run") {
			if (!isReady) {
				throw new Error("VLM worker not initialized. Call init() first.");
			}

			const vlm = await inferFrame(message.bitmap);
			
			workerScope.postMessage({
				type: "result",
				id: message.id,
				vlm,
			} satisfies ResultMessage);
			return;
		}

		if (message.type === "dispose") {
			disposeModel();
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
