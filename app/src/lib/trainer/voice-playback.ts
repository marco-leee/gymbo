/** Client-side voice cue playback queue (no interrupt policy). */

export type VoiceCue = {
	cueId: string;
	message: string;
	focusIssue?: string;
};

export class VoicePlaybackQueue {
	private queue: VoiceCue[] = [];
	private playing = false;

	enqueue(cue: VoiceCue): void {
		this.queue.push(cue);
		void this.drain();
	}

	private async drain(): Promise<void> {
		if (this.playing || this.queue.length === 0) return;
		if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;

		this.playing = true;
		while (this.queue.length > 0) {
			const cue = this.queue.shift()!;
			await this.speak(cue.message);
		}
		this.playing = false;
	}

	private speak(text: string): Promise<void> {
		return new Promise((resolve) => {
			const utter = new SpeechSynthesisUtterance(text);
			utter.onend = () => resolve();
			utter.onerror = () => resolve();
			window.speechSynthesis.speak(utter);
		});
	}

	get isPlaying(): boolean {
		return this.playing;
	}

	clear(): void {
		this.queue = [];
		if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
			window.speechSynthesis.cancel();
		}
		this.playing = false;
	}
}
