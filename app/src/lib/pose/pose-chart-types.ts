import { z } from 'zod';

export type KipName =
	| 'INSIDE_KNEE'
	| 'OUTSIDE_HIP'
	| 'HIP_HINGE'
	| 'FRONT_KNEE';

export const KIP_NAMES: readonly KipName[] = [
	'INSIDE_KNEE',
	'OUTSIDE_HIP',
	'HIP_HINGE',
	'FRONT_KNEE'
] as const;

export type PoseChartPoint = {
	frame: number;
	timestampSec: number;
} & Partial<Record<KipName, number | null>>;

export type SquatPoseChartPoint = PoseChartPoint &
	Required<Pick<PoseChartPoint, 'INSIDE_KNEE' | 'OUTSIDE_HIP'>>;

export type DeadliftPoseChartPoint = PoseChartPoint &
	Required<Pick<PoseChartPoint, 'HIP_HINGE'>>;

export type LungePoseChartPoint = PoseChartPoint &
	Required<Pick<PoseChartPoint, 'FRONT_KNEE'>>;

export const KipNameSchema = z.enum(KIP_NAMES);

export const PoseChartPointSchema = z.object({
	frame: z.number().int().nonnegative(),
	timestampSec: z.number().nonnegative(),
	INSIDE_KNEE: z.number().nullable().optional(),
	OUTSIDE_HIP: z.number().nullable().optional(),
	HIP_HINGE: z.number().nullable().optional(),
	FRONT_KNEE: z.number().nullable().optional()
});
