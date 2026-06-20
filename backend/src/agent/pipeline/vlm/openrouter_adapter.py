"""OpenRouter VLM adapter (migrated from langchain-flow.py)."""

from __future__ import annotations

import json
import re
from typing import Any, Sequence

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from agent.domain.models import FrameSnapshot, MergedObservationState, VLMFrameResult
from agent.exercises.registry import get_profile
from agent.infra.llm_factory import LLMClientFactory


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


class VLMContextAdapter:
    def __init__(
        self,
        *,
        merged_state: MergedObservationState,
        set_number: int,
        exercise_type: str,
        recent_coaching: list[dict] | None = None,
    ) -> None:
        self.merged_state = merged_state
        self.set_number = set_number
        self.exercise_type = exercise_type
        self.recent_coaching = recent_coaching or []


class OpenRouterVLMAdapter:
    def __init__(self, llm_factory: LLMClientFactory) -> None:
        self._llm_factory = llm_factory

    def analyze(
        self,
        *,
        frames: Sequence[FrameSnapshot],
        context: VLMContextAdapter,
    ) -> VLMFrameResult:
        if not frames:
            raise ValueError("At least one frame required for VLM analysis")
        current = frames[-1]
        profile = get_profile(context.exercise_type)
        messages = self._build_messages(
            frames=frames,
            context=context,
            system_prompt=profile.vlm_system_prompt,
        )
        llm = self._llm_factory.get_client()
        assert llm is not None
        return self._invoke_structured(
            llm,
            messages,
            frame_index=current.frame_index,
            timestamp_sec=current.timestamp_sec,
        )

    def _build_messages(
        self,
        *,
        frames: Sequence[FrameSnapshot],
        context: VLMContextAdapter,
        system_prompt: str,
    ) -> list[SystemMessage | HumanMessage]:
        exercise_state = {
            "exercise_type": context.exercise_type,
            "in_rep": context.merged_state.in_rep,
            "rep_phase": context.merged_state.rep_phase,
            "rep_count": context.merged_state.completed_reps,
            "active_issues": context.merged_state.active_issues,
        }
        ctx = {
            "exercise_state": exercise_state,
            "recent_coaching_events": context.recent_coaching[-3:],
            "prior_frame_count": len(frames) - 1,
            "current_frame_index": frames[-1].frame_index,
            "current_timestamp_sec": frames[-1].timestamp_sec,
            "set_number": context.set_number,
        }
        total = len(frames)
        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    f"Session context JSON:\n{json.dumps(ctx, indent=2)}\n\n"
                    f"Frame sequence ({total} images, oldest first). "
                    f"Judge frame {total} of {total} (CURRENT)."
                ),
            }
        ]
        for i, frame in enumerate(frames):
            is_current = i == total - 1
            role = "CURRENT — judge this frame" if is_current else "history"
            content.append(
                {
                    "type": "text",
                    "text": (
                        f"Frame {i + 1} of {total} — index={frame.frame_index} "
                        f"t={frame.timestamp_sec:.2f}s ({role})"
                    ),
                }
            )
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{frame.frame_b64}"},
                }
            )
        return [SystemMessage(content=system_prompt), HumanMessage(content=content)]

    def _invoke_structured(
        self,
        llm,
        messages: list,
        *,
        frame_index: int,
        timestamp_sec: float,
    ) -> VLMFrameResult:
        try:
            structured = llm.with_structured_output(VLMFrameResult)
            result = structured.invoke(messages)
            if isinstance(result, VLMFrameResult):
                result.frame_index = frame_index
                result.timestamp_sec = timestamp_sec
                return result
        except Exception:
            pass

        json_messages = list(messages) + [
            HumanMessage(
                content=(
                    "Respond with ONLY valid JSON matching the schema fields: "
                    "frame_index, timestamp_sec, in_rep, rep_phase, observations, issues, "
                    "severity, confidence, rep_completed, action, voice_reason, focus_issue."
                )
            )
        ]

        def invoke(err_msg: str | None = None):
            if err_msg:
                json_messages.append(HumanMessage(content=f"previous error: {err_msg}"))
            raw = llm.invoke(json_messages)
            content = raw.content if isinstance(raw.content, str) else str(raw.content)
            data = _extract_json(content)
            data["frame_index"] = frame_index
            data["timestamp_sec"] = timestamp_sec
            return VLMFrameResult.model_validate(data)

        try:
            return invoke()
        except ValidationError as e:
            return invoke(str(e))
