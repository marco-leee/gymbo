<script lang="ts">
	import CheckIcon from '@lucide/svelte/icons/check';

	let {
		steps,
		currentStepIndex = 0
	}: {
		steps: { id: string; title: string }[];
		currentStepIndex?: number;
	} = $props();
</script>

<nav aria-label="Onboarding progress" class="w-full">
	<ol class="flex flex-col gap-0 md:gap-1">
		{#each steps as step, index (step.id)}
			{@const isComplete = index < currentStepIndex}
			{@const isCurrent = index === currentStepIndex}
			<li class="flex gap-3 md:gap-4">
				<div class="flex flex-col items-center">
					<span
						class="flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold transition-colors md:size-9 {isComplete
							? 'bg-emerald-500 text-zinc-950'
							: isCurrent
								? 'bg-[var(--app-accent)] text-zinc-950 ring-2 ring-[var(--app-accent)]/35'
								: 'border border-zinc-600 bg-zinc-900/50 text-zinc-400'}"
						aria-current={isCurrent ? 'step' : undefined}
					>
						{#if isComplete}
							<CheckIcon class="size-4" aria-hidden="true" />
							<span class="sr-only">Completed step {index + 1}: {step.title}</span>
						{:else}
							{index + 1}
						{/if}
					</span>
					{#if index < steps.length - 1}
						<span
							class="my-1 w-px flex-1 min-h-6 md:min-h-8 {isComplete
								? 'bg-emerald-500/70'
								: 'bg-zinc-700'}"
							aria-hidden="true"
						></span>
					{/if}
				</div>
				<div class="min-w-0 flex-1 pb-5 md:pb-6">
					<p
						class="text-xs font-medium uppercase tracking-wider {isCurrent || isComplete
							? 'text-zinc-300'
							: 'text-zinc-500'}"
					>
						Step {index + 1} of {steps.length}
					</p>
					<p
						class="mt-0.5 text-sm md:text-base {isCurrent
							? 'font-semibold text-zinc-100'
							: isComplete
								? 'text-zinc-400'
								: 'text-zinc-500'}"
					>
						{step.title}
					</p>
				</div>
			</li>
		{/each}
	</ol>
</nav>
