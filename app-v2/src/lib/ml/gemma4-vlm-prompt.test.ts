import assert from "node:assert/strict";
import { describe, test } from "node:test";
import { buildExerciseDetectionPrompt } from "./gemma4-vlm-prompt";

describe("buildExerciseDetectionPrompt", () => {
	test("renders a multimodal Gemma 4 chat turn with image content first", () => {
		let capturedMessages: unknown;
		let capturedOptions: unknown;

		const prompt = buildExerciseDetectionPrompt({
			apply_chat_template(messages, options) {
				capturedMessages = messages;
				capturedOptions = options;
				return "<|turn>user\n<|image|>Classify movement\n<|turn>model\n";
			},
		});

		assert.equal(prompt, "<|turn>user\n<|image|>Classify movement\n<|turn>model\n");
		assert.deepEqual(capturedMessages, [
			{
				role: "user",
				content: [
					{ type: "image" },
					{
						type: "text",
						text: 'Is this person actively performing exercise repetitions? Answer with one word: "exercising", "not_exercising", or "unknown".',
					},
				],
			},
		]);
		assert.deepEqual(capturedOptions, {
			enable_thinking: false,
			add_generation_prompt: true,
		});
	});
});
