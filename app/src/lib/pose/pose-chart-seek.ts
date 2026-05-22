/** Extract chart row time (seconds) for video seek. */
export function timestampSecFromChartRow(row: unknown): number | null {
	if (!row || typeof row !== 'object') return null;
	const t = Number((row as Record<string, unknown>).timestampSec);
	return Number.isFinite(t) ? t : null;
}

export function seekVideoToTimestamp(
	video: HTMLVideoElement | null | undefined,
	timestampSec: number
): void {
	if (!video || !Number.isFinite(timestampSec)) return;
	const duration = video.duration;
	const clamped =
		Number.isFinite(duration) && duration > 0
			? Math.max(0, Math.min(timestampSec, duration - 0.05))
			: Math.max(0, timestampSec);
	video.currentTime = clamped;
	void video.play().catch(() => {});
}

export function createChartSeekHandlers(
	video: HTMLVideoElement | null | undefined,
	onSeek?: (timestampSec: number) => void
): {
	onTooltipClick: (e: MouseEvent, details: { data: unknown }) => void;
	onPointClick: (e: MouseEvent, details: { data: unknown }) => void;
} {
	function seekFromRow(row: unknown) {
		const t = timestampSecFromChartRow(row);
		if (t == null) return;
		seekVideoToTimestamp(video, t);
		onSeek?.(t);
	}

	return {
		onTooltipClick: (_e, details) => seekFromRow(details.data),
		onPointClick: (_e, details) => seekFromRow(details.data)
	};
}
