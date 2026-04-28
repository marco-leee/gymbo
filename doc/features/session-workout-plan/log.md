# Decision log: session-workout-plan

> Append-only style: newest decisions at the bottom.

| Date       | Decision | Rationale |
| ---------- | -------- | --------- |
| 2026-04-28 | **Optional `target_sets`** with **no inferred default**: omitting yields **zero** placeholder rows and omission of **`target_sets`** on document when unspecified on add vs explicit **0** stored when user submits **0**. | Matches trainer mental model (“blank sets = fill in later”; avoids silent N placeholder rows). |
| 2026-04-28 | Deletion gated by **`sets.every(status === 'pending')`** server-side (**409** payload). Empty **`sets`** array allowed (**vacuous**). | Prevents ripping out exercise after reps/video pipeline attached to any non-pending slot. |
| 2026-04-28 | Header strip shows **targets / weight / set goal / rest**, **excluding notes**, to reduce duplicate noise; notes kept in collapsible body near **`SessionExerciseNotes`**. | Supports quick scan ADHD-friendly hierarchy; avoids duplicating prose in summary row. |
| 2026-04-28 | Shared **`buildPendingSetsForExercise`** for **create session** mapping and **`addExerciseToSession`** to avoid divergent placeholders. | Single source for pending row shape (**ObjectId**, timestamps). |
| 2026-04-28 | **`SessionExerciseTimeline`** exposes **`hideExerciseActions`** + **`omitOuterTimelineChrome`** so **Record** reuses timeline without duplicate plan actions / outer chrome. | Shared component between **Run** and **Record** without copy-paste forks. |
| 2026-04-28 | Record accordions omit **Mark done** / RPE; **Save** + optional **video** upload/view only. | Product choice for this pass: simplifies logging flow; completion semantics can live elsewhere (e.g. session **Done**, analysis). |
| 2026-04-28 | **`/record`** page loads session with **`includePoseChartData: false`** and **`includeVideoPlayUrl: false`**. | Recording UI does not render pose charts or inline play URLs; default API flags would inflate JSON and serialization work unnecessarily. |
