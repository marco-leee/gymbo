import { z } from "zod/v4";
import { Description, Name, Timestamp, Ulid } from "./base";

export const ExerciseType = z.enum([
  'SQUAT',
]);

export const Exercise = z.object({
  id: Ulid,
  client_id: Ulid,
  name: Name,
  description: Description,
  type: ExerciseType,
  comment: z.string(),
  created_at: Timestamp,
  updated_at: Timestamp,
});