# Feature: session-workout-plan

> Scoped to **app-v2** trainer session detail: editable workout plan embedded on the session screen (collapsible exercises, POST add/remove, persistence in Mongo).

## Summary

Trainers manage the session workout plan inline: presets or custom exercises, targets and optional preset set rows, accordion headers summarizing the plan row, and safe removal before any logged work progresses beyond pending placeholder sets. **Recording** (`/app-v2/sessions/[id]/record`) is the execution surface for logging sets against that plan (timeline + per-set accordions, optional video per set).

## Scope boundaries

- **In scope:** Mongo session `exercises` embedded docs; Zod payload validation; REST `POST/PATCH`/note updates as implemented; **`/app-v2/sessions/[id]`** workout plan accordion UI; catalogue-driven fields; optional `target_sets` and server-side pending set materialization when that count is set; delete exercise when deletion rules apply; UX copy surfaced in accordion header (excluding notes — notes remain in-collapsible UI); **`/app-v2/sessions/[id]/record`** screen reusing **`SessionExerciseTimeline`** with record-specific props, set-level logging, and performance-conscious session load (no pose chart data / no video play URLs in initial fetch).
- **Out of scope:** Video analysis pipelines, unrelated legacy `/app/` routes unless shared types only, renaming global product spec narrative in `exercise.md` wholesale (linked as reference).

## Requirements

- [x] Planner can append an exercise via API and reload session data (`invalidateAll` pattern on success).
- [x] Planner can leave **Sets** blank: stored exercise has **`sets: []`** and **`target_sets` omitted** (no inferred default row count client or server).
- [x] When **Sets > 0**, server initializes that many **`pending`** placeholder rows (`buildPendingSetsForExercise`).
- [x] Accordion row shows **compact meta** left of type badge (targets, optional weight / set goal / rest); **does not surface exercise notes** in the header strip.
- [x] Accordion strip layout preserves **title (chevron + name)** on the leading side; trailing cluster **justify-end**: meta summary, badge, conditional delete affordance when allowed.
- [x] **Delete exercise** only when **every** embedded set status is **`pending`** (vacuous truth for zero sets). Any **`completed`** or **`processing`** set blocks deletion; API returns **409** if rule violated server-side.
- [x] **Record** route loads session with **`includePoseChartData: false`** and **`includeVideoPlayUrl: false`** (no pose charts or signed play URLs in page data for this view).
- [x] **Record** set logging: **Save** persists via **`recordSet`**; optional **video** upload then **View** in dialog (signed URL on demand); **Mark done** / RPE not required on this screen in current product pass.

## Non-goals

- Reordering exercises by drag-and-drop in this iteration (order uses `order_index` from append semantics).
- Editing fully generic exercise payloads through the accordion header (beyond remove + flows already on other screens).
- Client-facing UX outside app-v2.

## References

- [requirements template](../template/requirements.md)
- [product spec](../../PRODUCT_SPEC.md)
- [exercise.md](../exercise.md) (legacy product/strategy overlay)
- [PRINCIPLES.md](../../../PRINCIPLES.md)
- [ARCHITECTURE.md](../../../ARCHITECTURE.md)
