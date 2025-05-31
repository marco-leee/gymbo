import { z } from "zod/v4";

export const Gender = z.enum(["male", "female", "other"]);

export const Client = z.object({
  id: z.ulid(),
  email: z.email(),
  first_name: z.string(),
  last_name: z.string(),
  gender: Gender.nullable(),
  height: z.number().nullable(),
  weight: z.number().nullable(),
  updated_at: z.coerce.date().nullable(),
  created_at: z.coerce.date().nullable(),
});

export type Gender = z.infer<typeof Gender>;

export type Client = z.infer<typeof Client>;

