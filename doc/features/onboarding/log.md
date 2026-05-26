# Decision log: onboarding

| Date       | Decision | Rationale |
| ---------- | -------- | --------- |
| 2026-05-26 | Store questionnaire on `trainers` doc | One doc per user; simple layout guard check |
| 2026-05-26 | Required 4-step timeline before `/app/*` | Product requirement; separate from Shepherd UI tour |
| 2026-05-26 | Minimal onboarding shell (no sidebar/tour) | Reduce distraction per ADHD-friendly UX principles |

## Changes

- Extended `trainers` schema with `onboarding_completed_at` and `onboarding_answers`
- Added `GET`/`PUT` `/api/onboarding`
- Added `/app/onboarding` page with vertical timeline and radio option cards
- Gated `app/+layout.server.ts` to redirect incomplete trainers to onboarding
