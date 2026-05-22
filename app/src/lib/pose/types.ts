export type PoseKeypoint = {
	x: number;
	y: number;
	confidence: number;
};

export type PoseDetection = {
	confidence: number;
	classId: number;
	box: {
		x: number;
		y: number;
		width: number;
		height: number;
	};
	keypoints: PoseKeypoint[];
};

export type PoseEngineExerciseKey = "squat" | "push_up";

export type PoseFrame = {
	frameIndex: number;
	timestampSec: number;
	sourceWidth: number;
	sourceHeight: number;
	pose: PoseDetection | null;
};

export type PoseEngineIteration<TAnalysis> = PoseFrame & {
	analysis: TAnalysis | null;
};

export type VideoAnalysisInput = {
	file: File;
};

export type PoseVideoSource = {
	duration: number;
	videoWidth: number;
	videoHeight: number;
	currentTime: number;
	seekTo: (time: number) => Promise<void>;
	drawFrame: (ctx: CanvasRenderingContext2D, modelInputSize: number) => void;
	dispose: () => void;
};

export type PoseEngineDeps = {
	modelInputSize: number;
	analysisFps: number;
	videoSeekEpsilonSec: number;
	createVideoSource: (file: File) => Promise<PoseVideoSource>;
	createCanvasContext?: (
		modelInputSize: number,
	) => CanvasRenderingContext2D;
	createModelInput: (ctx: CanvasRenderingContext2D, modelInputSize: number) => Float32Array;
	ensureWorkerReady: () => Promise<Worker>;
	runPoseInference: (
		worker: Worker,
		input: Float32Array,
	) => Promise<PoseDetection | null>;
};

export type SquatInterestPoint = {
	idxToCoordinates: Record<number, [number, number]>;
	angle: number;
	rotationAngle: number;
	comment: "GOOD" | "TOO LOW" | "LOWER" | null;
};

export type SquatFrameAnalysis = Record<
	"INSIDE_KNEE" | "OUTSIDE_HIP",
	SquatInterestPoint
>;

export type { SquatPoseChartPoint as SquatChartPoint } from './pose-chart-types';

export function scaleKeypointToSource(
	keypoint: PoseKeypoint,
	sourceWidth: number,
	sourceHeight: number,
	modelInputSize: number,
): [number, number] {
	return [
		(keypoint.x / modelInputSize) * sourceWidth,
		(keypoint.y / modelInputSize) * sourceHeight,
	];
}

export function calculateAngle(
	a: [number, number],
	b: [number, number],
	c: [number, number],
	outer = false,
) {
	const radians =
		Math.atan2(c[1] - b[1], c[0] - b[0]) -
		Math.atan2(a[1] - b[1], a[0] - b[0]);
	let angle = Math.abs((radians * 180) / Math.PI);
	if (outer || angle > 180) {
		angle = 360 - angle;
	}

	return Math.trunc(angle);
}

export function classifySquatAngle(
	angle: number,
): "GOOD" | "TOO LOW" | "LOWER" | null {
	if (angle >= 90 && angle < 120) return "GOOD";
	if (angle < 90) return "TOO LOW";
	if (angle >= 120 && angle < 150) return "LOWER";
	return null;
}

export function hasConfidentKeypoint(
	keypoint: PoseKeypoint | undefined,
	poseConfidenceThreshold: number,
) {
	return (keypoint?.confidence ?? 0) >= poseConfidenceThreshold;
}

export function calculateSquatInterestPoints(
	pose: PoseDetection,
	options: {
		modelInputSize: number;
		poseConfidenceThreshold: number;
		sourceWidth: number;
		sourceHeight: number;
	},
): SquatFrameAnalysis | null {
	const RIGHT_SHOULDER_IDX = 6;
	const RIGHT_HIP_IDX = 12;
	const RIGHT_KNEE_IDX = 14;
	const RIGHT_ANKLE_IDX = 16;

	const shoulder = pose.keypoints[RIGHT_SHOULDER_IDX];
	const hip = pose.keypoints[RIGHT_HIP_IDX];
	const knee = pose.keypoints[RIGHT_KNEE_IDX];
	const ankle = pose.keypoints[RIGHT_ANKLE_IDX];

	if (
		!hasConfidentKeypoint(shoulder, options.poseConfidenceThreshold) ||
		!hasConfidentKeypoint(hip, options.poseConfidenceThreshold) ||
		!hasConfidentKeypoint(knee, options.poseConfidenceThreshold) ||
		!hasConfidentKeypoint(ankle, options.poseConfidenceThreshold)
	) {
		return null;
	}

	const shoulderCoord = scaleKeypointToSource(
		shoulder,
		options.sourceWidth,
		options.sourceHeight,
		options.modelInputSize,
	);
	const hipCoord = scaleKeypointToSource(
		hip,
		options.sourceWidth,
		options.sourceHeight,
		options.modelInputSize,
	);
	const kneeCoord = scaleKeypointToSource(
		knee,
		options.sourceWidth,
		options.sourceHeight,
		options.modelInputSize,
	);
	const ankleCoord = scaleKeypointToSource(
		ankle,
		options.sourceWidth,
		options.sourceHeight,
		options.modelInputSize,
	);

	const insideKneeAngle = calculateAngle(hipCoord, kneeCoord, ankleCoord);
	const outsideHipAngle = calculateAngle(
		shoulderCoord,
		hipCoord,
		kneeCoord,
		true,
	);

	return {
		INSIDE_KNEE: {
			idxToCoordinates: {
				[RIGHT_HIP_IDX]: hipCoord,
				[RIGHT_KNEE_IDX]: kneeCoord,
				[RIGHT_ANKLE_IDX]: ankleCoord,
			},
			angle: insideKneeAngle,
			rotationAngle: calculateAngle(
				[kneeCoord[0] + 90, kneeCoord[1]],
				kneeCoord,
				ankleCoord,
			),
			comment: classifySquatAngle(insideKneeAngle),
		},
		OUTSIDE_HIP: {
			idxToCoordinates: {
				[RIGHT_SHOULDER_IDX]: shoulderCoord,
				[RIGHT_HIP_IDX]: hipCoord,
				[RIGHT_KNEE_IDX]: kneeCoord,
			},
			angle: outsideHipAngle,
			rotationAngle: calculateAngle(
				[hipCoord[0] + 90, hipCoord[1]],
				hipCoord,
				kneeCoord,
			),
			comment: classifySquatAngle(outsideHipAngle),
		},
	};
}
