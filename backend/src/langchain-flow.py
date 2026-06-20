"""POC: overhead-squat form analysis via VLM + LangGraph.

Env (see src/.env):
  OPENROUTER_API_KEY   — required unless --dry-run
  OPENROUTER_MODEL     — default nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free

Usage:
  uv run python src/langchain-flow.py --video /path/to/squat.mp4
  uv run python src/langchain-flow.py --video /path/to/squat.mp4 --dry-run
  uv run python src/langchain-flow.py --video /path/to/squat.mp4 --state-dir tmp/vlm-state
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Literal, TypedDict

import cv2
import numpy as np
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field, ValidationError

DEFAULT_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
# DEFAULT_MODEL = "nvidia/nemotron-3-nano-30b-a3b:nitro"
FRAME_HISTORY_LIMIT = 4  # prior sampled frames sent as images (plus current)
REP_PHASES = ("setup", "descending", "bottom", "ascending", "lockout", "rest")
SEVERITIES = ("none", "minor", "moderate", "critical")

SYSTEM_PROMPT = """
You are an elite-level personal trainer, biomechanics expert, and movement coach with 15+ years of experience. You specialize in incremental, real-time video form analysis for workout sessions, especially overhead squats.

You receive a chronological sequence of sampled video frames as images, oldest first.
- All frames except the last are HISTORY — use them only for motion context (tempo, direction, rep phase, drift, regressions).
- The LAST frame is the CURRENT frame — your structured output must judge THIS frame only.

Compare the current frame to prior frames to infer movement: hip/knee travel, bar path, depth, torso angle, and rep phase transitions. Do not assume perfect form. If motion is unclear, lower confidence and say so.

Use the session context JSON for exercise state and recent coaching events. Do not rely on text summaries of past frames — use the images.

Output rules:
- Classify rep_phase (setup, descending, bottom, ascending, lockout, rest) for the CURRENT frame using motion vs prior frames.
- Set in_rep true when the athlete is actively performing a rep (not standing/resting between reps).
- Note form issues: knee valgus, bar path, torso lean, depth, elbow lockout.
- Set severity (none, minor, moderate, critical).
- Decide action: observe (default) or voice_out when the athlete should hear a cue now — new moderate/critical issue, rep milestone, or repeated issue across recent frames.
- Minimize chatter; avoid repeating recent coaching events.
- When action is voice_out, set voice_reason and focus_issue.
"""


class ExerciseState(BaseModel):
    exercise_type: Literal["overhead_squat"] = "overhead_squat"
    in_rep: bool = False
    rep_phase: Literal[
        "setup", "descending", "bottom", "ascending", "lockout", "rest"
    ] = "setup"
    rep_count: int = 0
    active_issues: list[str] = Field(default_factory=list)


class VLMFrameResult(BaseModel):
    frame_index: int
    timestamp_sec: float
    in_rep: bool
    rep_phase: str
    observations: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    severity: Literal["none", "minor", "moderate", "critical"] = "none"
    confidence: float = 0.0
    rep_completed: bool = False
    action: Literal["observe", "voice_out"] = "observe"
    voice_reason: str | None = None
    focus_issue: str | None = None


class SessionState(BaseModel):
    frame_results: list[VLMFrameResult] = Field(default_factory=list)
    coaching_events: list[dict[str, Any]] = Field(default_factory=list)
    completed_reps: int = 0


class FrameSnapshot(TypedDict):
    frame_index: int
    timestamp_sec: float
    frame_b64: str


class GraphState(TypedDict):
    video_path: str
    dry_run: bool
    state_dir: str
    iteration: int
    fps: float
    sample_interval_frames: int
    next_sample_frame: int
    frame_b64: str | None
    frame_history: list[FrameSnapshot]
    current_index: int
    current_timestamp: float
    exercise: dict[str, Any]
    session: dict[str, Any]
    latest_vlm: dict[str, Any] | None
    done: bool
    video_cap: Any


def _env_path() -> Path:
    return Path(__file__).resolve().parent / ".env"


def make_llm(*, dry_run: bool) -> ChatOpenAI | None:
    if dry_run:
        return None
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required (set in src/.env or env)")
    return ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL),
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        temperature=0.2,
    )


def encode_frame_b64(frame_bgr) -> str:
    ok, buf = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise RuntimeError("Failed to encode frame as JPEG")
    return base64.b64encode(buf.tobytes()).decode("ascii")


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def invoke_structured_vlm(
    llm: ChatOpenAI,
    messages: list[SystemMessage | HumanMessage],
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

    json_messages = messages + [
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
        return invoke(e.error_message)


def build_vlm_messages(
    *,
    exercise: ExerciseState,
    session: SessionState,
    prior_frames: list[FrameSnapshot],
    frame_index: int,
    timestamp_sec: float,
    frame_b64: str,
) -> list[SystemMessage | HumanMessage]:
    recent_coaching = session.coaching_events[-3:]
    context = {
        "exercise_state": exercise.model_dump(),
        "recent_coaching_events": recent_coaching,
        "prior_frame_count": len(prior_frames),
        "current_frame_index": frame_index,
        "current_timestamp_sec": timestamp_sec,
    }

    sequence: list[FrameSnapshot] = [
        *prior_frames,
        {
            "frame_index": frame_index,
            "timestamp_sec": timestamp_sec,
            "frame_b64": frame_b64,
        },
    ]
    total = len(sequence)

    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                f"Session context JSON:\n{json.dumps(context, indent=2)}\n\n"
                f"Frame sequence ({total} images, oldest first). "
                f"Judge frame {total} of {total} (CURRENT)."
            ),
        }
    ]
    for i, frame in enumerate(sequence):
        is_current = i == total - 1
        role = "CURRENT — judge this frame" if is_current else "history"
        content.append(
            {
                "type": "text",
                "text": (
                    f"Frame {i + 1} of {total} — index={frame['frame_index']} "
                    f"t={frame['timestamp_sec']:.2f}s ({role})"
                ),
            }
        )
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{frame['frame_b64']}"},
            }
        )

    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=content)]


def mock_vlm_result(frame_index: int, timestamp_sec: float) -> VLMFrameResult:
    phase = REP_PHASES[frame_index % len(REP_PHASES)]
    voice = frame_index > 0 and frame_index % 5 == 0
    return VLMFrameResult(
        frame_index=frame_index,
        timestamp_sec=timestamp_sec,
        in_rep=phase not in ("setup", "rest"),
        rep_phase=phase,
        observations=[f"Frame {frame_index}: athlete in {phase} phase"],
        issues=(
            ["slight forward lean"] if frame_index > 0 and frame_index % 7 == 0 else []
        ),
        severity="moderate" if frame_index > 0 and frame_index % 7 == 0 else "none",
        confidence=0.85,
        rep_completed=phase == "lockout",
        action="voice_out" if voice else "observe",
        voice_reason="Repeated forward lean detected" if voice else None,
        focus_issue="Keep chest up and core braced" if voice else None,
    )


def merge_states(
    exercise: ExerciseState, session: SessionState, vlm: VLMFrameResult
) -> tuple[ExerciseState, SessionState]:
    exercise.in_rep = vlm.in_rep
    if vlm.rep_phase in REP_PHASES:
        exercise.rep_phase = vlm.rep_phase  # type: ignore[assignment]
    if vlm.rep_completed:
        exercise.rep_count += 1
        session.completed_reps += 1
    if vlm.issues:
        exercise.active_issues = vlm.issues
    session.frame_results.append(vlm)
    return exercise, session


def append_frame_history(state: GraphState) -> list[FrameSnapshot]:
    history = list(state.get("frame_history", []))
    frame_b64 = state.get("frame_b64")
    if frame_b64 is None:
        return history
    history.append(
        {
            "frame_index": state["current_index"],
            "timestamp_sec": state["current_timestamp"],
            "frame_b64": frame_b64,
        }
    )
    return history[-FRAME_HISTORY_LIMIT:]


def state_to_json_dict(state: GraphState) -> dict[str, Any]:
    frame_history = state.get("frame_history", [])
    return {
        "video_path": state["video_path"],
        "dry_run": state["dry_run"],
        "iteration": state["iteration"],
        "fps": state["fps"],
        "sample_interval_frames": state["sample_interval_frames"],
        "next_sample_frame": state["next_sample_frame"],
        "current_index": state["current_index"],
        "current_timestamp": state["current_timestamp"],
        "frame_history_indices": [f["frame_index"] for f in frame_history],
        "exercise": state["exercise"],
        "session": state["session"],
        "latest_vlm": state["latest_vlm"],
        "done": state["done"],
    }


def persist_state(state: GraphState, *, step: str) -> None:
    state_dir = Path(state["state_dir"])
    state_dir.mkdir(parents=True, exist_ok=True)
    frame_idx = state["current_index"]
    iteration = state["iteration"]
    path = state_dir / f"iter_{iteration:04d}_frame_{frame_idx:06d}_{step}.json"
    payload = state_to_json_dict(state)
    payload["step"] = step
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[state] saved {path}")


def sample_frame(state: GraphState) -> dict[str, Any]:
    cap = state["video_cap"]
    if cap is None or not cap.isOpened():
        return {"done": True}

    target = state["next_sample_frame"]
    cap.set(cv2.CAP_PROP_POS_FRAMES, target)
    ok, frame = cap.read()
    if not ok or frame is None:
        cap.release()
        return {"done": True, "video_cap": None}

    fps = state["fps"]
    timestamp = target / fps if fps else 0.0
    print(f"[sample] frame={target} t={timestamp:.1f}s")

    return {
        "current_index": target,
        "current_timestamp": timestamp,
        "frame_b64": encode_frame_b64(frame),
        "next_sample_frame": target + state["sample_interval_frames"],
        "done": False,
    }


def vlm_analyze(state: GraphState) -> dict[str, Any]:
    exercise = ExerciseState.model_validate(state["exercise"])
    session = SessionState.model_validate(state["session"])
    frame_index = state["current_index"]
    timestamp = state["current_timestamp"]
    frame_b64 = state["frame_b64"]
    assert frame_b64 is not None

    if state["dry_run"]:
        result = mock_vlm_result(frame_index, timestamp)
    else:
        llm = make_llm(dry_run=False)
        assert llm is not None
        prior_frames = state.get("frame_history", [])
        messages = build_vlm_messages(
            exercise=exercise,
            session=session,
            prior_frames=prior_frames,
            frame_index=frame_index,
            timestamp_sec=timestamp,
            frame_b64=frame_b64,
        )
        image_count = len(prior_frames) + 1
        print(
            f"[vlm] analyzing frame={frame_index} "
            f"prior_images={len(prior_frames)} total_images={image_count}"
        )
        result = invoke_structured_vlm(
            llm,
            messages,
            frame_index=frame_index,
            timestamp_sec=timestamp,
        )

    print(
        f"[vlm] frame={frame_index} action={result.action} "
        f"phase={result.rep_phase} severity={result.severity}"
    )
    updates = {"latest_vlm": result.model_dump()}
    persist_state({**state, **updates}, step="vlm_analyze")
    return updates


def observe_update(state: GraphState) -> dict[str, Any]:
    exercise = ExerciseState.model_validate(state["exercise"])
    session = SessionState.model_validate(state["session"])
    vlm = VLMFrameResult.model_validate(state["latest_vlm"])
    exercise, session = merge_states(exercise, session, vlm)
    print(f"[observe] frame={vlm.frame_index} phase={exercise.rep_phase}")
    iteration = state["iteration"] + 1
    updates = {
        "exercise": exercise.model_dump(),
        "session": session.model_dump(),
        "iteration": iteration,
        "frame_history": append_frame_history(state),
    }
    persist_state({**state, **updates}, step="observe_update")
    return updates


def voice_out(state: GraphState) -> dict[str, Any]:
    exercise = ExerciseState.model_validate(state["exercise"])
    session = SessionState.model_validate(state["session"])
    vlm = VLMFrameResult.model_validate(state["latest_vlm"])
    timestamp = state["current_timestamp"]

    if state["dry_run"]:
        message = vlm.focus_issue or "Keep your form tight."
    else:
        llm = make_llm(dry_run=False)
        assert llm is not None
        prompt = (
            f"Generate one short coaching cue (max 20 words) for the athlete.\n"
            f"Focus issue: {vlm.focus_issue}\n"
            f"Reason: {vlm.voice_reason}\n"
            f"Observations: {vlm.observations}\n"
            f"Active issues: {exercise.active_issues}\n"
            "Be direct and encouraging. No markdown."
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        message = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )

    print(f"[coach @ {timestamp:.1f}s] {message}")
    session.coaching_events.append(
        {
            "timestamp": timestamp,
            "frame_index": vlm.frame_index,
            "message": message,
            "trigger_issue": vlm.focus_issue,
        }
    )
    exercise, session = merge_states(exercise, session, vlm)
    iteration = state["iteration"] + 1
    updates = {
        "exercise": exercise.model_dump(),
        "session": session.model_dump(),
        "iteration": iteration,
        "frame_history": append_frame_history(state),
    }
    persist_state({**state, **updates}, step="voice_out")
    return updates


def finalize_summary(state: GraphState) -> dict[str, Any]:
    exercise = ExerciseState.model_validate(state["exercise"])
    session = SessionState.model_validate(state["session"])
    cap = state.get("video_cap")
    if cap is not None and cap.isOpened():
        cap.release()

    all_issues: list[str] = []
    for r in session.frame_results:
        all_issues.extend(r.issues)
    unique_issues = list(dict.fromkeys(all_issues))

    if state["dry_run"]:
        summary = (
            f"Session complete.\n"
            f"- Reps completed: {session.completed_reps}\n"
            f"- Frames analyzed: {len(session.frame_results)}\n"
            f"- Coaching events: {len(session.coaching_events)}\n"
            f"- Top issues: {', '.join(unique_issues) or 'none detected'}\n"
            f"- Next focus: maintain upright torso through the squat"
        )
    else:
        llm = make_llm(dry_run=False)
        assert llm is not None
        payload = {
            "rep_count": exercise.rep_count,
            "completed_reps": session.completed_reps,
            "unique_issues": unique_issues,
            "coaching_events": session.coaching_events,
            "frame_count": len(session.frame_results),
        }
        prompt = (
            "Summarize this overhead-squat coaching session in 3-5 bullet points: "
            "reps, top 2 issues, what improved, one next focus.\n"
            f"Data:\n{json.dumps(payload, indent=2)}"
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        summary = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )

    print(f"\n=== SESSION SUMMARY ===\n{summary}")
    final_payload = state_to_json_dict(state)
    final_payload["step"] = "finalize_summary"
    final_payload["summary"] = summary
    final_path = Path(state["state_dir"]) / "final_state.json"
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(json.dumps(final_payload, indent=2), encoding="utf-8")
    print(f"[state] saved {final_path}")
    return {}


def route_after_sample(state: GraphState) -> Literal["continue", "done"]:
    return "done" if state.get("done") else "continue"


def route_after_vlm(state: GraphState) -> Literal["observe", "voice_out"]:
    vlm = state.get("latest_vlm")
    if not vlm:
        return "observe"
    return vlm.get("action", "observe")


def build_graph() -> Any:
    graph = StateGraph(GraphState)
    graph.add_node("sample_frame", sample_frame)
    graph.add_node("vlm_analyze", vlm_analyze)
    graph.add_node("observe_update", observe_update)
    graph.add_node("voice_out", voice_out)
    graph.add_node("finalize_summary", finalize_summary)

    graph.add_edge(START, "sample_frame")
    graph.add_conditional_edges(
        "sample_frame",
        route_after_sample,
        {"continue": "vlm_analyze", "done": "finalize_summary"},
    )
    graph.add_conditional_edges(
        "vlm_analyze",
        route_after_vlm,
        {"observe": "observe_update", "voice_out": "voice_out"},
    )
    graph.add_edge("observe_update", "sample_frame")
    graph.add_edge("voice_out", "sample_frame")
    graph.add_edge("finalize_summary", END)
    return graph.compile()


def initial_state(video_path: str, *, dry_run: bool, state_dir: str) -> GraphState:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    interval = max(1, round(fps / 2))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(
        f"[init] video={video_path} fps={fps:.1f} interval={interval} frames total={total}"
    )
    print(f"[init] state_dir={state_dir}")

    return GraphState(
        video_path=video_path,
        dry_run=dry_run,
        state_dir=state_dir,
        iteration=0,
        fps=fps,
        sample_interval_frames=interval,
        next_sample_frame=0,
        frame_b64=None,
        frame_history=[],
        current_index=0,
        current_timestamp=0.0,
        exercise=ExerciseState().model_dump(),
        session=SessionState().model_dump(),
        latest_vlm=None,
        done=False,
        video_cap=cap,
    )


def create_test_video(path: Path, *, fps: float = 30.0, seconds: float = 3.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    w, h = 320, 240
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (w, h),
    )
    frames = int(fps * seconds)
    for i in range(frames):
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        cv2.rectangle(frame, (80, 60 + i % 40), (240, 200), (200, 200, 200), -1)
        writer.write(frame)
    writer.release()


def main(argv: list[str] | None = None) -> int:
    load_dotenv(_env_path())

    parser = argparse.ArgumentParser(description="Overhead squat VLM form POC")
    parser.add_argument(
        "--video", type=str, default=os.getenv("VIDEO_PATH"), help="Path to squat video"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Skip API calls; validate graph wiring"
    )
    parser.add_argument(
        "--generate-test-video",
        type=str,
        default=None,
        help="Write a short synthetic mp4 to this path and use it",
    )
    parser.add_argument(
        "--state-dir",
        type=str,
        default=None,
        help="Directory for intermediate JSON state snapshots (default: tmp/vlm-state/<video_stem>)",
    )
    args = parser.parse_args(argv)

    video_path = args.video
    if args.generate_test_video:
        out = Path(args.generate_test_video)
        create_test_video(out)
        video_path = str(out)

    if not video_path:
        parser.error("--video or --generate-test-video or VIDEO_PATH env is required")

    if not Path(video_path).is_file():
        print(f"Video not found: {video_path}", file=sys.stderr)
        return 1

    state_dir = args.state_dir or str(Path("tmp/vlm-state") / Path(video_path).stem)

    app = build_graph()
    state = initial_state(video_path, dry_run=args.dry_run, state_dir=state_dir)
    app.invoke(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
