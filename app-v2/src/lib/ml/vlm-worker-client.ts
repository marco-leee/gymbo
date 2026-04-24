/**
 * VLM Worker Client
 * 
 * Main thread client for the VLM (Vision Language Model) worker.
 * Handles lifecycle, message passing, and single-flight inference.
 */

import type { VlmResult } from "../workers/vlm.worker";

// Message types: client → worker

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

// Message types: worker → client

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

// Request tracking

type PendingRequest = {
	id: number;
	resolve: (result: VlmResult | null) => void;
	reject: (error: Error) => void;
};

/**
 * Client for the VLM worker that detects exercise repetition activity.
 * 
 * Features:
 * - Async init/dispose lifecycle
 * - Single-flight inference (drops concurrent requests)
 * - Transferable ImageBitmap for zero-copy performance
 * - Type-safe message passing
 * 
 * @example
 * ```ts
 * const client = new VlmWorkerClient();
 * await client.init();
 * 
 * // In your analysis loop (e.g. 1s interval):
 * const bitmap = await createImageBitmap(canvas);
 * const result = await client.run(bitmap);
 * if (result) {
 *   console.log(result.label, result.confidence);
 * }
 * 
 * // Cleanup:
 * await client.dispose();
 * ```
 */
export class VlmWorkerClient {
	private worker: Worker | null = null;
	private nextRequestId = 1;
	private pendingRequests = new Map<number, PendingRequest>();
	private readyPromise: Promise<void> | null = null;
	private readyResolver: (() => void) | null = null;
	private _isReady = false;
	private _isInferring = false;

	/**
	 * Check if the worker is ready for inference.
	 */
	get isReady(): boolean {
		return this._isReady;
	}

	/**
	 * Check if inference is currently in progress.
	 */
	get isInferring(): boolean {
		return this._isInferring;
	}

	/**
	 * Initialize the worker and load the VLM model.
	 * Resolves when the worker is ready.
	 * 
	 * @throws {Error} If worker fails to initialize
	 */
	async init(): Promise<void> {
		if (this.worker) {
			// Already initialized
			return this.readyPromise ?? Promise.resolve();
		}

		// Create worker
		this.worker = new Worker(
			new URL("../workers/vlm.worker.ts", import.meta.url),
			{ type: "module" }
		);

		// Set up message handler
		this.worker.onmessage = (event: MessageEvent<WorkerOutputMessage>) => {
			this.handleWorkerMessage(event.data);
		};

		this.worker.onerror = (error) => {
			console.error("[VLM Client] Worker error:", error);
			this.rejectAllPending(new Error("VLM worker crashed"));
		};

		// Create ready promise
		this.readyPromise = new Promise<void>((resolve, reject) => {
			this.readyResolver = resolve;
			
			// Timeout after 30 seconds
			const timeout = setTimeout(() => {
				reject(new Error("VLM worker init timeout"));
			}, 30000);

			// Clear timeout when ready
			this.readyPromise?.then(() => clearTimeout(timeout));
		});

		// Send init message
		const initMsg: InitMessage = { type: "init" };
		this.worker.postMessage(initMsg);

		// Wait for ready
		return this.readyPromise;
	}

	/**
	 * Run inference on a video frame.
	 * 
	 * Single-flight: If inference is already in progress, this request is dropped
	 * and returns null immediately.
	 * 
	 * @param bitmap - ImageBitmap to analyze (ownership transferred to worker)
	 * @returns VlmResult or null if dropped due to single-flight
	 * @throws {Error} If worker not initialized or inference fails
	 */
	async run(bitmap: ImageBitmap): Promise<VlmResult | null> {
		if (!this.worker || !this._isReady) {
			throw new Error("VLM worker not initialized. Call init() first.");
		}

		// Single-flight: drop if already inferring
		if (this._isInferring) {
			console.log("[VLM Client] Dropping request (inference in progress)");
			return null;
		}

		this._isInferring = true;
		const requestId = this.nextRequestId++;

		// Create promise for this request
		const resultPromise = new Promise<VlmResult | null>((resolve, reject) => {
			this.pendingRequests.set(requestId, {
				id: requestId,
				resolve,
				reject,
			});
		});

		// Send run message with transferable bitmap
		const runMsg: RunMessage = {
			type: "run",
			id: requestId,
			bitmap,
		};
		this.worker.postMessage(runMsg, [bitmap]);

		try {
			return await resultPromise;
		} finally {
			this._isInferring = false;
		}
	}

	/**
	 * Dispose the worker and free resources.
	 */
	async dispose(): Promise<void> {
		if (!this.worker) {
			return;
		}

		// Send dispose message
		const disposeMsg: DisposeMessage = { type: "dispose" };
		this.worker.postMessage(disposeMsg);

		// Terminate worker
		this.worker.terminate();
		this.worker = null;

		// Reject any pending requests
		this.rejectAllPending(new Error("VLM worker disposed"));

		// Reset state
		this._isReady = false;
		this._isInferring = false;
		this.readyPromise = null;
		this.readyResolver = null;
	}

	/**
	 * Optional callback for worker messages (for debugging/logging).
	 */
	onWorkerMessage?: (message: WorkerOutputMessage) => void;

	/**
	 * Handle messages from the worker.
	 */
	private handleWorkerMessage(message: WorkerOutputMessage): void {
		// Call optional callback for external logging
		this.onWorkerMessage?.(message);

		if (message.type === "ready") {
			this._isReady = true;
			this.readyResolver?.();
			console.log("[VLM Client] Worker ready");
			return;
		}

		if (message.type === "result") {
			const pending = this.pendingRequests.get(message.id);
			if (pending) {
				pending.resolve(message.vlm);
				this.pendingRequests.delete(message.id);
			}
			return;
		}

		if (message.type === "error") {
			const error = new Error(message.message);
			
			if (message.id !== undefined) {
				// Error for specific request
				const pending = this.pendingRequests.get(message.id);
				if (pending) {
					pending.reject(error);
					this.pendingRequests.delete(message.id);
				}
			} else {
				// General worker error
				console.error("[VLM Client] Worker error:", message.message);
				this.rejectAllPending(error);
			}
			return;
		}

		if (message.type === "log") {
			// Forward log to callback if provided
			// (onWorkerMessage will handle it)
			return;
		}
	}

	/**
	 * Reject all pending requests with an error.
	 */
	private rejectAllPending(error: Error): void {
		for (const pending of this.pendingRequests.values()) {
			pending.reject(error);
		}
		this.pendingRequests.clear();
	}
}

// Re-export VlmResult type for convenience
export type { VlmResult };
