"""Runtime helpers for LangGraph node configurable injection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.runnables import RunnableConfig

if TYPE_CHECKING:
    from agent.app.event_publisher import RunEventPublisher
    from agent.app.run_context import RunContext
    from agent.graphs.factory import GraphDependencies
    from agent.infra.run_repository import RunRepository


def get_configurable(config: RunnableConfig) -> dict[str, Any]:
    return config.get("configurable") or {}


def get_run_context(config: RunnableConfig) -> RunContext:
    return get_configurable(config)["run_context"]


def get_deps(config: RunnableConfig) -> GraphDependencies:
    return get_configurable(config)["deps"]


def get_publisher(config: RunnableConfig) -> RunEventPublisher:
    return get_configurable(config)["publisher"]


def get_repository(config: RunnableConfig) -> RunRepository:
    return get_configurable(config)["repository"]


def build_graph_config(
    *,
    ctx: RunContext,
    deps: GraphDependencies,
    publisher: RunEventPublisher,
    repository: RunRepository,
) -> RunnableConfig:
    return {
        "configurable": {
            "run_context": ctx,
            "deps": deps,
            "publisher": publisher,
            "repository": repository,
            "thread_id": ctx.run.id,
        },
    }
