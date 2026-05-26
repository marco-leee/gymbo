<script lang="ts">
	import { goto } from '$app/navigation';
	import { createMutation } from '@tanstack/svelte-query';
	import { Button } from '$lib/components/ui/button/index.js';
	import OnboardingTimeline from '$lib/components/onboarding-timeline.svelte';
	import DumbbellIcon from '@lucide/svelte/icons/dumbbell';
	import { submitOnboarding } from '$lib/api/onboarding';
	import {
		createEmptyOnboardingAnswers,
		ONBOARDING_STEPS,
		type OnboardingField
	} from '$lib/onboarding-questions';
	import type { OnboardingAnswers } from '$lib/services/models/trainer';

	let currentStepIndex = $state(0);
	let answers = $state<Partial<OnboardingAnswers>>(createEmptyOnboardingAnswers());
	let fieldError = $state('');

	const currentStep = $derived(ONBOARDING_STEPS[currentStepIndex]);
	const isLastStep = $derived(currentStepIndex === ONBOARDING_STEPS.length - 1);

	const onboardingMutation = createMutation(() => ({
		mutationFn: submitOnboarding,
		onSuccess: async () => {
			await goto('/app/sessions');
		},
		onError: (error: Error) => {
			console.error('Failed to submit onboarding:', error);
		}
	}));

	function validateCurrentStep(): boolean {
		fieldError = '';
		const value = answers[currentStep.id];
		if (!value) {
			fieldError = 'Please choose an option to continue.';
			return false;
		}
		return true;
	}

	function selectOption(field: OnboardingField, value: string) {
		answers = { ...answers, [field]: value as OnboardingAnswers[typeof field] };
		fieldError = '';
	}

	function goBack() {
		if (currentStepIndex === 0) return;
		fieldError = '';
		currentStepIndex -= 1;
	}

	function goNext() {
		if (!validateCurrentStep()) return;
		if (isLastStep) {
			submitAnswers();
			return;
		}
		currentStepIndex += 1;
	}

	function submitAnswers() {
		if (!validateCurrentStep()) return;

		const { trainer_type, typical_client_count, sessions_per_week, session_duration } = answers;
		if (!trainer_type || !typical_client_count || !sessions_per_week || !session_duration) {
			fieldError = 'Please answer all questions before finishing.';
			return;
		}

		onboardingMutation.mutate({
			trainer_type,
			typical_client_count,
			sessions_per_week,
			session_duration
		});
	}
</script>

<div class="flex min-h-dvh flex-col" style="background: var(--app-bg);">
	<header
		class="flex h-14 shrink-0 items-center justify-center border-b px-4 md:h-16"
		style="border-color: var(--app-border);"
	>
		<div class="flex items-center gap-2">
			<DumbbellIcon class="size-5 md:size-6" style="color: var(--app-accent);" aria-hidden="true" />
			<span class="app-display text-lg tracking-wide md:text-xl" style="color: var(--app-text);">GYMBO</span>
		</div>
	</header>

	<main class="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-4 py-6 md:px-6 md:py-10">
		<div class="grid gap-8 md:grid-cols-[minmax(0,240px)_minmax(0,1fr)] md:gap-10">
			<aside class="hidden md:block">
				<OnboardingTimeline steps={ONBOARDING_STEPS} {currentStepIndex} />
			</aside>

			<section class="app-card flex flex-col p-6 md:p-8">
				<div class="mb-6 md:hidden">
					<p class="text-xs font-medium uppercase tracking-wider" style="color: var(--app-muted);">
						Step {currentStepIndex + 1} of {ONBOARDING_STEPS.length}
					</p>
					<div class="mt-2 flex gap-1.5" aria-hidden="true">
						{#each ONBOARDING_STEPS as _, index (index)}
							<span
								class="h-1.5 flex-1 rounded-full {index <= currentStepIndex
									? 'bg-[var(--app-accent)]'
									: 'bg-zinc-700'}"
							></span>
						{/each}
					</div>
				</div>

				<h1 class="app-display text-2xl md:text-3xl" style="color: var(--app-text);">
					{currentStep.title}
				</h1>
				{#if currentStep.description}
					<p class="mt-2 text-sm md:text-base" style="color: var(--app-muted);">
						{currentStep.description}
					</p>
				{/if}

				<fieldset class="mt-6 space-y-3 border-0 p-0">
					<legend class="sr-only">{currentStep.title}</legend>
					{#each currentStep.options as option (option.value)}
						{@const selected = answers[currentStep.id] === option.value}
						<label
							class="flex min-h-12 cursor-pointer items-center rounded-lg border px-4 py-3 transition-colors {selected
								? 'border-[var(--color-accent)] bg-[var(--color-accent)]/10 ring-1 ring-[var(--color-accent)]/35'
								: 'border-zinc-600 bg-zinc-900/50 hover:border-zinc-500'}"
						>
							<input
								type="radio"
								class="sr-only"
								name={currentStep.id}
								value={option.value}
								checked={selected}
								onchange={() => selectOption(currentStep.id, option.value)}
							/>
							<span class="text-sm font-medium md:text-base" style="color: var(--app-text);">
								{option.label}
							</span>
						</label>
					{/each}
				</fieldset>

				{#if fieldError}
					<p class="mt-4 text-sm text-red-400" role="alert">{fieldError}</p>
				{/if}
				{#if onboardingMutation.isError}
					<p class="mt-4 text-sm text-red-400" role="alert">
						Failed to save your answers. Please try again.
					</p>
				{/if}

				<div class="mt-8 flex flex-wrap gap-3">
					{#if currentStepIndex > 0}
						<Button
							type="button"
							variant="outline"
							class="min-h-11"
							disabled={onboardingMutation.isPending}
							onclick={goBack}
						>
							Back
						</Button>
					{/if}
					<Button
						type="button"
						class="min-h-11"
						disabled={onboardingMutation.isPending}
						onclick={goNext}
					>
						{#if onboardingMutation.isPending}
							Saving…
						{:else if isLastStep}
							Get started
						{:else}
							Continue
						{/if}
					</Button>
				</div>
			</section>
		</div>
	</main>
</div>
