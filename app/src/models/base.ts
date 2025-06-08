import { z } from "zod/v4";

export const Ulid = z.ulid();

export const Timestamp = z.coerce.date();

export const Email = z.email();

export const Name = z.string();

export const Description = z.string();