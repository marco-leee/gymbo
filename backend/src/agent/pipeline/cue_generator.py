"""Coaching cue generation via LLM."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from agent.domain.models import MergedObservationState, VoiceOutEvent
from agent.infra.llm_factory import LLMClientFactory


class CueGenerator:
    def __init__(self, llm_factory: LLMClientFactory) -> None:
        self._llm_factory = llm_factory

    def generate(
        self,
        *,
        event: VoiceOutEvent,
        state: MergedObservationState,
    ) -> str:
        llm = self._llm_factory.get_client()
        if llm is None:
            return event.focus_issue or "Keep your form tight."
        prompt = (
            f"Generate one short coaching cue (max 20 words) for the athlete.\n"
            f"Focus issue: {event.focus_issue}\n"
            f"Reason: {event.reason}\n"
            f"Active issues: {state.active_issues}\n"
            "Be direct and encouraging. No markdown."
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content if isinstance(response.content, str) else str(response.content)
        return content.strip()
