import type { OnboardingAnswers } from '$lib/services/models/trainer';

export type OnboardingStatusResponse = {
	completed: boolean;
	answers?: OnboardingAnswers;
};

export async function getOnboarding(): Promise<OnboardingStatusResponse> {
	const response = await fetch('/api/onboarding');
	if (!response.ok) {
		throw new Error(`Failed to get onboarding status: ${response.statusText}`);
	}
	return response.json();
}

export async function submitOnboarding(answers: OnboardingAnswers): Promise<OnboardingStatusResponse> {
	const response = await fetch('/api/onboarding', {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(answers)
	});
	if (!response.ok) {
		const message = response.status === 409 ? 'Onboarding already completed' : response.statusText;
		throw new Error(`Failed to submit onboarding: ${message}`);
	}
	return response.json();
}
