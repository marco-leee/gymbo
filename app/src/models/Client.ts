import { z } from "zod/v4";
import { Email, Name, Timestamp, Ulid } from "./base";

export const Gender = z.enum(["male", "female", "other"]);

export const Client = z.object({
  id: Ulid,
  email: Email,
  first_name: Name,
  last_name: Name,
  gender: Gender.nullable(),
  height: z.number().nullable(),
  weight: z.number().nullable(),
  created_at: Timestamp.nullable(),
  updated_at: Timestamp.nullable(),
});

export type Gender = z.infer<typeof Gender>;

export type Client = z.infer<typeof Client>;

