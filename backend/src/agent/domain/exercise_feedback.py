"""Build per-exercise feedback summary (SC-005 fields)."""

from __future__ import annotations

from collections import Counter

from agent.domain.models import CoachingEventRecord, MergedObservationState


def build_feedback_summary(
    *,
    merged: MergedObservationState,
    coaching_events: list[CoachingEventRecord],
    planned_sets: int,
    target_reps: int,
) -> dict[str, str | int | list[str]]:
    issue_counts = Counter(merged.recurring_issues)
    top_issues = [issue for issue, _ in issue_counts.most_common(3)]

    improvements: list[str] = []
    if merged.total_session_reps > 0:
        improvements.append(f"Completed {merged.total_session_reps} total reps across sets")

    next_focus = top_issues[0] if top_issues else "Maintain consistent form through full range"

    return {
        "total_reps": merged.total_session_reps,
        "top_recurring_issues": top_issues,
        "observed_improvement": improvements[0] if improvements else "Consistent effort throughout",
        "next_session_focus": next_focus,
        "coaching_event_count": len(coaching_events),
        "planned_sets": planned_sets,
        "target_reps_per_set": target_reps,
    }


def format_feedback_text(summary: dict[str, str | int | list[str]]) -> str:
    issues = summary.get("top_recurring_issues") or []
    issues_str = ", ".join(issues) if issues else "none noted"
    return (
        f"Session complete — {summary['total_reps']} reps total.\n"
        f"Top issues: {issues_str}.\n"
        f"Improvement: {summary['observed_improvement']}.\n"
        f"Next focus: {summary['next_session_focus']}."
    )
