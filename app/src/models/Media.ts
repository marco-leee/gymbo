import { z } from "zod/v4";
import { Ulid, Timestamp } from "./base";

export const MediaCameraView = z.enum([
  'FRONT',
  'BACK',
  'LEFT',
  'RIGHT',
  'TOP',
  'BOTTOM',
]);

export const MediaMetadata = z.record(z.string(), z.string());

export const MediaStep = z.enum([
  'QUEUING',
  'VIDEO_FETCHING',
  'PRE_PROCESSING',
  'POSE_DETECTING',
  'POST_PROCESSING',
  'FINALIZING',
  'COMPLETED',
]);

const Error = z.object({
  message: z.string(),
  timestamp: Timestamp,
});

export const MediaErrors = z.array(Error);

export const Media = z.object({
  id: Ulid,
  exercise_id: Ulid,
  step: MediaStep,
  camera_view: MediaCameraView,
  original_video_location: z.string(),
  processed_video_location: z.string(),
  pose_detection_model_name: z.string(),
  metadata: MediaMetadata,
  errors: MediaErrors,
  created_at: Timestamp,
  updated_at: Timestamp,
  completed_at: Timestamp,
});