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

// import {
// 	Gemma4ForConditionalGeneration,
// 	AutoProcessor,
// 	PreTrainedModel,
// 	Processor,
// 	pipeline,
// 	type AutomaticSpeechRecognitionPipeline,
// } from "@huggingface/transformers";

// #processor: Processor | null = null;
// #llm: PreTrainedModel | null = null;
// const tokenizer = this.#processor?.tokenizer;

// export async function loadGemmaProcessorAndModel(): Promise<{
// 	processor: Processor;
// 	llm: PreTrainedModel;
// }> {
// 	const model_id = "onnx-community/gemma-4-E2B-it-ONNX";

// 	const [processor, llm] = await Promise.all([
// 		AutoProcessor.from_pretrained(model_id),
// 		Gemma4ForConditionalGeneration.from_pretrained(model_id, {
// 			dtype: "q4f16",
// 			device: "webgpu",
// 			progress_callback: (info) => {
// 				if (info.status === "progress_total") {
// 					const progress = Math.round(info.progress);
// 					if (progress % 10 === 0) {
// 						console.log(`Loading model: ${progress}%`);
// 					}
// 				}
// 			},
// 		}),
// 	]);
// 	return { processor, llm };
// }

// const runReply = async (messages: ChatMessage[]) => {
// 	await streamAssistantReply(
// 		this.#processor!,
// 		this.#llm!,
// 		tokenizer,
// 		messages,
// 		signal,
// 		() => this.#alive(myGen, signal),
// 		(text) => {
// 			this.#responseQueue.push(text);
// 			this.#syncPublicState();
// 		},
// 	);
// };

// export async function streamAssistantReply(
// 	processor: Processor,
// 	llm: PreTrainedModel,
// 	tokenizer: NonNullable<Processor["tokenizer"]>,
// 	messages: ChatMessage[],
// 	signal: AbortSignal,
// 	isAlive: () => boolean,
// 	onTextChunk: (text: string) => void,
// ): Promise<void> {
// 	const prompt = processor.apply_chat_template(messages as never, APPLY_OPTS);
// 	const inputs = await processor(prompt);
// 	await llm.generate({
// 		...inputs,
// 		max_new_tokens: 512,
// 		do_sample: false,
// 		streamer: new TextStreamer(tokenizer, {
// 			skip_prompt: true,
// 			skip_special_tokens: false,
// 			callback_function: (text) => {
// 				if (!isAlive()) return;
// 				if (text.includes("<turn|>")) return;
// 				onTextChunk(text);
// 				console.log("[wait response] chunk →", JSON.stringify(text));
// 			},
// 		}),
// 	});
// }

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
