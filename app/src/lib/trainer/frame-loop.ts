/** Camera frame capture loop for trainer WS. */

export type FrameLoopOptions = {
	video: HTMLVideoElement;
	canvas: HTMLCanvasElement;
	fps?: number;
	onFrame: (payload: { jpegBase64: string; seq: number; timestampSec: number }) => void;
};

export class FrameLoop {
	private intervalId: ReturnType<typeof setInterval> | null = null;
	private seq = 0;
	private running = false;

	start(options: FrameLoopOptions): void {
		if (this.running) return;
		this.running = true;
		const fps = options.fps ?? 1;
		const ms = Math.max(200, Math.round(1000 / fps));
		const ctx = options.canvas.getContext('2d');
		if (!ctx) throw new Error('Canvas 2d context unavailable');

		this.intervalId = setInterval(() => {
			if (!this.running) return;
			const { video, canvas } = options;
			if (video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) return;
			canvas.width = video.videoWidth || 640;
			canvas.height = video.videoHeight || 480;
			ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
			const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
			const jpegBase64 = dataUrl.split(',')[1] ?? '';
			this.seq += 1;
			options.onFrame({
				jpegBase64,
				seq: this.seq,
				timestampSec: performance.now() / 1000
			});
		}, ms);
	}

	stop(): void {
		this.running = false;
		if (this.intervalId !== null) {
			clearInterval(this.intervalId);
			this.intervalId = null;
		}
	}

	get isRunning(): boolean {
		return this.running;
	}
}
