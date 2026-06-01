import type { KipName } from '$lib/pose/pose-chart-types';

/**
 * Canonical KIP palette for charts and video overlay.
 * Keep in sync with backend/src/pipeline/kip_colors.py (light-theme --chart-* tokens).
 */
export const KIP_COLORS_HEX: Record<KipName, string> = {
	INSIDE_KNEE: '#F54900',
	OUTSIDE_HIP: '#009689',
	HIP_HINGE: '#104E64',
	FRONT_KNEE: '#FFB900'
};

export function hexColorForKipName(key: KipName): string {
	return KIP_COLORS_HEX[key];
}
