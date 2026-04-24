type ChatTemplateProcessor = {
	apply_chat_template: (
		messages: Array<{
			role: "user";
			content: Array<
				| { type: "image" }
				| {
						type: "text";
						text: string;
				  }
			>;
		}>,
		options: {
			enable_thinking: boolean;
			add_generation_prompt: boolean;
		},
	) => unknown;
};

const EXERCISE_DETECTION_QUESTION =
	'Is this person actively performing exercise repetitions? Answer with one word: "exercising", "not_exercising", or "unknown".';

export function buildExerciseDetectionPrompt(processor: ChatTemplateProcessor): string {
	const prompt = processor.apply_chat_template(
		[
			{
				role: "user",
				content: [{ type: "image" }, { type: "text", text: EXERCISE_DETECTION_QUESTION }],
			},
		],
		{
			enable_thinking: false,
			add_generation_prompt: true,
		},
	);

	if (typeof prompt !== "string") {
		throw new Error("Gemma 4 chat template did not return a string prompt");
	}

	return prompt;
}
