"""Graph factory: wire dry-run vs live adapters."""

from __future__ import annotations

from dataclasses import dataclass

from agent.app.event_publisher import RunEventPublisher
from agent.app.run_context import RunContext
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


def build_session_runner(
    ctx: RunContext,
    deps: GraphDependencies,
    publisher: RunEventPublisher,
    repository,
):
    from agent.graphs.session import SessionRunner

    return SessionRunner(ctx, deps, publisher, repository)
