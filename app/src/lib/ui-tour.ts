import { browser } from '$app/environment';
import Shepherd from 'shepherd.js';

export type TourStepId =
	| 'clients-nav'
	| 'clients-new-btn'
	| 'clients-form'
	| 'sessions-nav'
	| 'sessions-new-btn'
	| 'sessions-form'
	| 'sessions-exercise-fields'
	| 'session-hub-add-exercise'
	| 'record-start'
	| 'record-video-tip'
	| 'record-set-accordion'
	| 'record-create-set'
	| 'record-upload-video';

export type TourMilestone = 'none' | 'client_created';
export type TourStatus = 'active' | 'completed' | 'skipped';

type TourState = {
	status: TourStatus;
	step: TourStepId;
	milestone: TourMilestone;
	recordStarted?: boolean;
};

const STORAGE_KEY = 'gymbo:onboarding';

const RECORD_STEPS = new Set<TourStepId>([
	'record-start',
	'record-video-tip',
	'record-set-accordion',
	'record-create-set',
	'record-upload-video'
]);

const STEP_CONFIGS: Record<
	TourStepId,
	{
		text: string;
		attachTo: { element: string; on: 'top' | 'bottom' | 'left' | 'right' };
	}
> = {
	'clients-nav': {
		text: 'Start here — open Clients to add someone you train.',
		attachTo: { element: '[data-tour-nav="clients"]', on: 'right' }
	},
	'clients-new-btn': {
		text: 'Add your first client with this button.',
		attachTo: { element: '[data-tour="clients-new"]', on: 'bottom' }
	},
	'clients-form': {
		text: 'Fill in the details, then tap Create client.',
		attachTo: { element: '[data-tour="clients-form"]', on: 'top' }
	},
	'sessions-nav': {
		text: 'Nice work. Next, open Sessions to schedule a workout.',
		attachTo: { element: '[data-tour-nav="sessions"]', on: 'right' }
	},
	'sessions-new-btn': {
		text: 'Create a session for your client here.',
		attachTo: { element: '[data-tour="sessions-new"]', on: 'bottom' }
	},
	'sessions-form': {
		text: 'Pick a client, then tap Add exercise to plan lifts for this session.',
		attachTo: { element: '[data-tour="sessions-form"]', on: 'top' }
	},
	'sessions-exercise-fields': {
		text: `<p><strong>Exercise</strong> — choose Squat or Deadlift (the only supported lifts right now).</p>
<p><strong>Target Reps &amp; Weight Load</strong> — Amount of repetitions and weight load to lift.</p>
<p><strong>Sets &amp; rest</strong> — Number of sets and rest time between sets.</p>
<p><strong>Exercise notes</strong> — Any additional notes for this exercise.</p>
<p>When you are ready, tap Create Session.</p>`,
		attachTo: { element: '[data-tour="sessions-exercise-fields"]', on: 'top' }
	},
	'session-hub-add-exercise': {
		text: 'Add more exercises here if you need to. When you are ready, open the table recorder to continue.',
		attachTo: { element: '[data-tour="session-hub-add-exercise"]', on: 'top' }
	},
	'record-start': {
		text: 'Tap Start to begin this session.',
		attachTo: { element: '[data-tour="record-start"]', on: 'bottom' }
	},
	'record-video-tip': {
		text: `<p>Record your client performing the exercise.</p>
<p>Keep the clip <strong>under 1 minute</strong> — that is the upload limit.</p>Once you have uploaded your video, the system will automatically process the video, please wait.<p>`,
		attachTo: { element: '[data-tour="record-video-tip"]', on: 'bottom' }
	},
	'record-set-accordion': {
		text: '<p>Expand this set to log details and upload your video.</p><p>Once you have uploaded your video, the system will automatically process the video, please wait.</p>',
		attachTo: { element: '[data-tour="record-set-accordion"]', on: 'top' }
	},
	'record-create-set': {
		text: 'Create a set first, then expand it to upload your video clip.',
		attachTo: { element: '[data-tour="record-create-set"]', on: 'top' }
	},
	'record-upload-video': {
		text: 'Upload the MP4 clip here. Remember to keep it under 1 minute.',
		attachTo: { element: '[data-tour="record-upload-video"]', on: 'top' }
	}
};

const NAV_STEPS = new Set<TourStepId>(['clients-nav', 'sessions-nav']);
const RECORD_PREPARE_STEPS = new Set<TourStepId>([
	'record-set-accordion',
	'record-upload-video',
	'record-create-set'
]);

export const tour = new Shepherd.Tour({
	useModalOverlay: true,
	defaultStepOptions: {
		classes: 'gymbo-shepherd-step',
		scrollTo: { behavior: 'smooth', block: 'center' },
		modalOverlayOpeningPadding: 8,
		canClickTarget: true
	}
});

let currentShownStepId: TourStepId | null = null;
let prepareMobileNav: (() => void | Promise<void>) | null = null;
let prepareRecordStep: ((stepId: TourStepId) => void | Promise<void>) | null = null;

export function setTourMobileNavHandler(handler: (() => void | Promise<void>) | null) {
	prepareMobileNav = handler;
}

export function setTourRecordPrepareHandler(
	handler: ((stepId: TourStepId) => void | Promise<void>) | null
) {
	prepareRecordStep = handler;
}

function readState(): TourState | null {
	if (!browser) return null;
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (!raw) return null;
		return JSON.parse(raw) as TourState;
	} catch {
		return null;
	}
}

function writeState(state: TourState) {
	if (!browser) return;
	localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function clearShownStep() {
	currentShownStepId = null;
	tour.cancel();
}

function isActiveTour(): boolean {
	const state = readState();
	return Boolean(state && state.status === 'active');
}

type SessionRoute =
	| { kind: 'hub'; sessionId: string }
	| { kind: 'record'; sessionId: string };

function parseSessionRoute(pathname: string): SessionRoute | null {
	const recordMatch = pathname.match(/^\/app\/sessions\/([^/]+)\/record$/);
	if (recordMatch) return { kind: 'record', sessionId: recordMatch[1] };
	const hubMatch = pathname.match(/^\/app\/sessions\/([^/]+)$/);
	if (hubMatch && hubMatch[1] !== 'new') return { kind: 'hub', sessionId: hubMatch[1] };
	return null;
}

function targetExists(stepId: TourStepId): boolean {
	const selector = STEP_CONFIGS[stepId].attachTo.element;
	return Boolean(document.querySelector(selector));
}

function resolveRecordStep(storedStep: TourStepId, recordStarted: boolean): TourStepId | null {
	if (storedStep === 'record-upload-video') return 'record-upload-video';
	if (storedStep === 'record-set-accordion' || storedStep === 'record-create-set') {
		if (targetExists('record-set-accordion')) return 'record-set-accordion';
		if (targetExists('record-create-set')) return 'record-create-set';
		return storedStep;
	}
	if (storedStep === 'record-video-tip' && recordStarted) return 'record-video-tip';
	if (storedStep === 'record-start' || !recordStarted) {
		if (targetExists('record-start')) return 'record-start';
		return recordStarted ? 'record-video-tip' : null;
	}
	if (recordStarted) return 'record-video-tip';
	return 'record-start';
}

function resolveStepForPath(
	pathname: string,
	state: TourState,
	searchParams?: URLSearchParams
): TourStepId | null {
	if (!pathname.startsWith('/app')) return null;

	const { milestone, step: storedStep, recordStarted = false } = state;

	if (milestone === 'none') {
		if (pathname === '/app/clients/new') return 'clients-form';
		if (pathname === '/app/clients') return 'clients-new-btn';
		return 'clients-nav';
	}

	const sessionRoute = parseSessionRoute(pathname);

	if (sessionRoute?.kind === 'hub') {
		const view = searchParams?.get('view') ?? 'session';
		if (view !== 'session') return null;
		if (RECORD_STEPS.has(storedStep)) return null;
		return 'session-hub-add-exercise';
	}

	if (sessionRoute?.kind === 'record') {
		if (RECORD_STEPS.has(storedStep) || storedStep === 'session-hub-add-exercise') {
			return resolveRecordStep(
				storedStep === 'session-hub-add-exercise' ? 'record-start' : storedStep,
				recordStarted
			);
		}
		return 'record-start';
	}

	if (pathname === '/app/sessions/new') {
		if (storedStep === 'sessions-exercise-fields') return 'sessions-exercise-fields';
		return 'sessions-form';
	}
	if (pathname === '/app/sessions') return 'sessions-new-btn';
	if (pathname.startsWith('/app/sessions/')) return null;
	return 'sessions-nav';
}

async function waitForTarget(stepId: TourStepId, attempts = 20): Promise<boolean> {
	for (let i = 0; i < attempts; i++) {
		if (targetExists(stepId)) return true;
		await new Promise((resolve) => setTimeout(resolve, 50));
	}
	return false;
}

function removeAllSteps() {
	for (const step of [...tour.steps]) {
		tour.removeStep(step.id);
	}
}

async function handleGotIt(stepId: TourStepId) {
	tour.cancel();
	currentShownStepId = null;

	if (stepId === 'session-hub-add-exercise') {
		const state = readState();
		if (state?.status === 'active') {
			writeState({ ...state, step: 'record-start' });
		}
		return;
	}

	if (stepId === 'record-video-tip') {
		await advanceTourToSetAccordion();
		return;
	}

	if (stepId === 'record-upload-video') {
		completeTour();
	}
}

async function showTourStep(stepId: TourStepId) {
	if (currentShownStepId === stepId && tour.getCurrentStep()?.id === stepId) return;

	if (NAV_STEPS.has(stepId)) {
		await prepareMobileNav?.();
	}

	if (RECORD_PREPARE_STEPS.has(stepId)) {
		await prepareRecordStep?.(stepId);
	}

	let showStepId = stepId;
	if (stepId === 'record-set-accordion' && !targetExists('record-set-accordion')) {
		if (targetExists('record-create-set')) showStepId = 'record-create-set';
	}

	if (!(await waitForTarget(showStepId))) return;

	tour.cancel();
	removeAllSteps();
	currentShownStepId = null;

	const config = STEP_CONFIGS[showStepId];

	tour.addStep({
		id: showStepId,
		text: config.text,
		attachTo: config.attachTo,
		buttons: [
			{
				text: 'Skip tour',
				secondary: true,
				action() {
					skipTour();
				}
			},
			{
				text: 'Got it',
				action() {
					void handleGotIt(showStepId);
				}
			}
		]
	});

	tour.start();
	currentShownStepId = showStepId;
}

export function shouldAutoStartTour(): boolean {
	if (!browser) return false;
	return readState() === null;
}

export function startTour() {
	if (!browser) return;
	writeState({ status: 'active', step: 'clients-nav', milestone: 'none' });
}

export function skipTour() {
	if (!browser) return;
	const state = readState();
	writeState({
		status: 'skipped',
		step: state?.step ?? 'clients-nav',
		milestone: state?.milestone ?? 'none',
		recordStarted: state?.recordStarted
	});
	clearShownStep();
}

export function completeTour() {
	if (!browser) return;
	writeState({
		status: 'completed',
		step: 'record-upload-video',
		milestone: 'client_created',
		recordStarted: true
	});
	clearShownStep();
}

export async function advanceTourToExerciseFields() {
	if (!browser) return;
	const state = readState();
	if (!state || state.status !== 'active') return;
	writeState({ ...state, step: 'sessions-exercise-fields' });
	clearShownStep();
	await showTourStep('sessions-exercise-fields');
}

export function advanceTourAfterClientCreated() {
	if (!browser) return;
	const state = readState();
	if (!state || state.status !== 'active') return;
	writeState({
		status: 'active',
		step: 'sessions-nav',
		milestone: 'client_created'
	});
	clearShownStep();
}

export function advanceTourAfterSessionCreated() {
	if (!browser) return;
	const state = readState();
	if (!state || state.status !== 'active') return;
	writeState({
		status: 'active',
		step: 'session-hub-add-exercise',
		milestone: 'client_created',
		recordStarted: false
	});
	clearShownStep();
}

export async function advanceTourToRecordVideoTip() {
	if (!browser) return;
	const state = readState();
	if (!state || state.status !== 'active') return;
	writeState({ ...state, recordStarted: true, step: 'record-video-tip' });
	clearShownStep();
	await showTourStep('record-video-tip');
}

export async function advanceTourToSetAccordion() {
	if (!browser) return;
	const state = readState();
	if (!state || state.status !== 'active') return;

	await prepareRecordStep?.('record-set-accordion');

	const stepId: TourStepId = targetExists('record-set-accordion')
		? 'record-set-accordion'
		: 'record-create-set';

	writeState({ ...state, step: stepId });
	clearShownStep();
	await showTourStep(stepId);
}

export async function advanceTourAfterSetCreated() {
	if (!browser) return;
	const state = readState();
	if (!state || state.status !== 'active') return;

	await prepareRecordStep?.('record-upload-video');
	writeState({ ...state, step: 'record-upload-video' });
	clearShownStep();
	await showTourStep('record-upload-video');
}

export async function markClientCreated(pathname = '/app/clients') {
	advanceTourAfterClientCreated();
	await resumeTourForPath(pathname);
}

export async function resumeTourForPath(pathname: string, searchParams?: URLSearchParams) {
	if (!browser) return;

	const state = readState();
	if (!state || state.status !== 'active') {
		if (currentShownStepId) clearShownStep();
		return;
	}

	const step = resolveStepForPath(pathname, state, searchParams);
	if (!step) {
		clearShownStep();
		return;
	}

	if (state.step !== step) {
		writeState({ ...state, step });
	}

	await showTourStep(step);
}

export function isTourActive(): boolean {
	return isActiveTour();
}

export function getActiveTourStep(): TourStepId | null {
	const state = readState();
	if (!state || state.status !== 'active') return null;
	return state.step;
}
