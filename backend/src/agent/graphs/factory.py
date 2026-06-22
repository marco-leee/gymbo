"""Graph factory: wire dry-run vs live adapters and compiled LangGraph subgraphs."""

from __future__ import annotations

from dataclasses import dataclass

from langgraph.checkpoint.memory import MemorySaver

from agent.infra.llm_factory import LLMClientFactory
from agent.pipeline.cue_generator import CueGenerator
from agent.pipeline.pose.dry_run_adapter import DryRunPoseAdapter
from agent.pipeline.vlm.dry_run_adapter import DryRunVLMAdapter
from agent.pipeline.vlm.openrouter_adapter import OpenRouterVLMAdapter


@dataclass
class GraphDependencies:
    pose: DryRunPoseAdapter | object
    vlm: DryRunVLMAdapter | OpenRouterVLMAdapter
    cue_generator: CueGenerator
    llm_factory: LLMClientFactory
    dry_run: bool


def build_dependencies(*, dry_run: bool = False) -> GraphDependencies:
    llm_factory = LLMClientFactory.from_env(dry_run=dry_run)
    if dry_run:
        return GraphDependencies(
            pose=DryRunPoseAdapter(),
            vlm=DryRunVLMAdapter(),
            cue_generator=CueGenerator(llm_factory),
            llm_factory=llm_factory,
            dry_run=True,
        )
    from agent.pipeline.pose.mediapipe_adapter import MediapipePoseAdapter

    return GraphDependencies(
        pose=MediapipePoseAdapter(),
        vlm=OpenRouterVLMAdapter(llm_factory),
        cue_generator=CueGenerator(llm_factory),
        llm_factory=llm_factory,
        dry_run=False,
    )


def build_checkpointer() -> MemorySaver:
    return MemorySaver()


def build_set_subgraph():
    from agent.graphs.set_loop import build_set_subgraph as _build

    return _build()


def build_voice_graph():
    from agent.graphs.voice_out import build_voice_graph as _build

    return _build()


def build_rest_subgraph():
    from agent.graphs.rest import build_rest_subgraph as _build

    return _build()


def build_session_graph(*, checkpointer=None):
    from agent.graphs.session import build_session_graph as _build

    return _build(checkpointer=checkpointer)
