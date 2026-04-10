import { BasePoseEngine } from "./base-pose-engine";
import {
	calculateSquatInterestPoints,
	type PoseEngineIteration,
	type PoseFrame,
	type SquatChartPoint,
	type SquatFrameAnalysis,
} from "./types";

export class SquatPoseEngine extends BasePoseEngine<
	SquatFrameAnalysis,
	SquatChartPoint
> {
	protected analyzeFrame(frame: PoseFrame): SquatFrameAnalysis | null {
		if (!frame.pose) {
			return null;
		}

		return calculateSquatInterestPoints(frame.pose, {
			modelInputSize: this.deps.modelInputSize,
			poseConfidenceThreshold: 0.25,
			sourceWidth: frame.sourceWidth,
			sourceHeight: frame.sourceHeight,
		});
	}

	chartPointFromIteration(
		iteration: PoseEngineIteration<SquatFrameAnalysis>,
	): SquatChartPoint | null {
		if (!iteration.analysis) {
			return null;
		}

		return {
			frame: iteration.frameIndex,
			timestampSec: iteration.timestampSec,
			insideKnee: iteration.analysis.INSIDE_KNEE.angle,
			outsideHip: iteration.analysis.OUTSIDE_HIP.angle,
		};
	}

	protected logIteration(
		iteration: PoseEngineIteration<SquatFrameAnalysis>,
	): void {
		if (!iteration.pose || !iteration.analysis) {
			console.log(`Squat frame ${iteration.frameIndex}`, {
				timestampSec: iteration.timestampSec,
				poseDetected: false,
			});
			return;
		}

		console.log(`Squat frame ${iteration.frameIndex}`, {
			timestampSec: iteration.timestampSec,
			poseConfidence: iteration.pose.confidence,
			insideKnee: iteration.analysis.INSIDE_KNEE,
			outsideHip: iteration.analysis.OUTSIDE_HIP,
		});
	}
}
