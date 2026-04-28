# Plan: session-workout-plan

> Execution notes for implementers. Update as the feature evolves.

## Approach

- **Persistence:** MongoDB **`sessions`** document with embedded **`exercises[]`**, each with **`sets[]`** and nested set **`status`** enum (`pending` | `completed` | `processing`). Optional **`target_sets`** field records planning intent when provided.
- **Set materialization:** Shared **`buildPendingSetsForExercise(count, now)`** returns placeholder **`pending`** **`ExerciseSetDoc`** rows (capped, ordered **`set_number`**).
- **API surface:**
  - **`POST …/sessions/[id]/exercises`** — append exercise (payload parsed with **`SessionExercisePayloadSchema`**).
  - **`DELETE …/sessions/[id]/exercises/[exerciseId]`** — remove iff server-side validation agrees all sets **`pending`**.
- **UI entrypoint:** **`workout-plan-section.svelte`** on session detail (**`/app-v2/sessions/(session)/[id]/`** route tree): collapsible (**`Collapsible`**) rows, **`SessionV2ExerciseFields`** for draft append, **`invalidateAll()`** after mutations.
- **Client-only rule duplication:** **`exerciseDeletionAllowed`** in **`$lib/exercise-plan.ts`** to hide delete affordances; server remains authoritative (**409** on violation).

## Session recording (`/app-v2/sessions/[id]/record`)

- **Shell:** **`app-v2-run`** layout (same visual family as **Run**); single-column main with **Card**-wrapped **`SessionExerciseTimeline`**.
- **Timeline strip:** **Reps/Duration**, **Load**, **Rest** (no separate “goal sets · rest” caption line). Log/Add hidden from **Record** via **`hideExerciseActions`**; optional outer chrome strip via **`omitOuterTimelineChrome`**.
- **Sets:** Per-set **`Collapsible`** accordions; inline fields sync to **`recordSet`**; targets shown as muted second line where applicable.
- **Video:** Sign → PUT → **`recordSet`** with **`video_url`**; **View** opens dialog with **`getMediaPlayUrl`** (not part of initial session JSON).
- **Load:** **`getSession`** in **`record/+page.ts`** passes **`includePoseChartData: false`** and **`includeVideoPlayUrl: false`** to keep responses small for this route.

## Steps

1. Confirm session editability mirrors API (scheduled / in-progress, no uploaded session videos per product rules coded in guards).
2. Verify optional sets: omit **`target_sets`** in JSON ⇒ empty **`sets`** array persisted.
3. Verify positive **`target_sets`**: N **`pending`** rows with sequential **`set_number`**.
4. Complete one set ⇒ delete button hidden ⇒ **DELETE** returns **409**.
5. All sets **pending** (or zero sets) ⇒ **DELETE** succeeds; list refreshes.

## Verification

- [ ] **`bun run check`** under **`app-v2`** where project already green aside from unrelated pre-existing diagnostics.
- [ ] Manual: create session exercise without sets count ⇒ DB document shows **`sets: []`**, **`target_sets`** absent unless sent.
- [ ] Manual: specify sets count ⇒ N pending rows server-side after add/create path.
- [ ] Manual: delete trash only appears when **`exerciseDeletionAllowed`**; **`confirm`** completes remove; accordion open state cleared.

## Risks / notes

- **Race:** Rare concurrent PATCH on same exercise could theoretically change status between read and `$pull`; acceptable for MVP; stronger approach would combine filter on array predicates in Mongo.
- Legacy sessions without **`status`** on old sets treated as failing **`pending`** check (**strict**) — remediation would be migration or lax read.
