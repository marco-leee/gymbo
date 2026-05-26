import type {
	CountRange,
	OnboardingAnswers,
	SessionDuration,
	TrainerType
} from '$lib/services/models/trainer';

export type OnboardingField = keyof OnboardingAnswers;

export type OnboardingOption<T extends string = string> = {
	value: T;
	label: string;
};

export type OnboardingStep = {
	id: OnboardingField;
	title: string;
	description?: string;
	options: OnboardingOption[];
};

export const ONBOARDING_STEPS: OnboardingStep[] = [
	{
		id: 'trainer_type',
		title: 'Which best describes you?',
		description: '4 quick questions to tailor your setup.',
		options: [
			{ value: 'freelance', label: 'Freelance trainer' },
			{ value: 'chain_gym', label: 'Trainer at a chain gym' },
			{ value: 'small_studio', label: 'Trainer at a small studio' },
			{ value: 'gym_owner', label: 'Gym owner' }
		] satisfies OnboardingOption<TrainerType>[]
	},
	{
		id: 'typical_client_count',
		title: 'Typical client count',
		options: [
			{ value: '1_5', label: '1–5' },
			{ value: '6_15', label: '6–15' },
			{ value: '16_30', label: '16–30' },
			{ value: '31_plus', label: '31+' }
		] satisfies OnboardingOption<CountRange>[]
	},
	{
		id: 'sessions_per_week',
		title: 'How many sessions do you run per week?',
		options: [
			{ value: '1_5', label: '1–5' },
			{ value: '6_15', label: '6–15' },
			{ value: '16_30', label: '16–30' },
			{ value: '31_plus', label: '31+' }
		] satisfies OnboardingOption<CountRange>[]
	},
	{
		id: 'session_duration',
		title: 'How long is a typical session?',
		options: [
			{ value: 'under_30', label: 'Under 30 min' },
			{ value: '30_45', label: '30–45 min' },
			{ value: '45_60', label: '45–60 min' },
			{ value: '60_90', label: '60–90 min' },
			{ value: '90_plus', label: '90+ min' }
		] satisfies OnboardingOption<SessionDuration>[]
	}
];

export function createEmptyOnboardingAnswers(): Partial<OnboardingAnswers> {
	return {};
}
