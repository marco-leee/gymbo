"""Safety evaluation from VLM severity and global monitor."""

from __future__ import annotations

from dataclasses import dataclass

from agent.domain.models import VLMFrameResult


@dataclass(frozen=True, slots=True)
class SafetyOutcome:
    safe: bool
    severity: str
    description: str
    source: str = "set_check"


def evaluate_set_safety(vlm: VLMFrameResult) -> SafetyOutcome:
    if vlm.severity == "critical":
        desc = ", ".join(vlm.issues) if vlm.issues else "Critical form issue detected"
        return SafetyOutcome(safe=False, severity="critical", description=desc)
    return SafetyOutcome(safe=True, severity=vlm.severity, description="")


def evaluate_global_safety(*, force_unsafe: bool = False) -> SafetyOutcome | None:
    """Hook for global safety monitor; returns None when no trigger."""
    if force_unsafe:
        return SafetyOutcome(
            safe=False,
            severity="critical",
            description="Global safety monitor triggered",
            source="global_monitor",
        )
    return None
