import { z } from "zod/v4";

export const Client = z.object({
  id: z.ulid(),
  email: z.email(),
  first_name: z.string(),
  last_name: z.string(),
  updated_at: z.coerce.date().nullable(),
  created_at: z.coerce.date().nullable(),
});

export type Client = z.infer<typeof Client>;

