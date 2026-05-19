/** JSON job envelope for Redis LPUSH and RunPod POST (doc/features/async-video-processing/plan.md §4.1). */
export type VideoProcessingJob = {
	session_id: string;
	exercise_id: string;
	set_id: string;
	r2_key: string;
	job_id: string;
	exercise_key?: string;
	/** Optional flat metadata for workers (e.g. camera_view, dimensions). */
	metadata?: Record<string, string>;
};
