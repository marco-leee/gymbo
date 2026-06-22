"""VoiceOut subgraph — compiled LangGraph per event."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.graphs.nodes import voice_nodes as nodes
from agent.graphs.state import TrainerGraphState


def build_voice_graph():
    graph = StateGraph(TrainerGraphState)

    graph.add_node("dedup_check", nodes.dedup_check)
    graph.add_node("generate_cue", nodes.generate_cue)
    graph.add_node("log_coaching", nodes.log_coaching)

    graph.add_edge(START, "dedup_check")
    graph.add_conditional_edges(
        "dedup_check",
        nodes.route_after_dedup,
        {"skip": END, "speak": "generate_cue"},
    )
    graph.add_edge("generate_cue", "log_coaching")
    graph.add_edge("log_coaching", END)

    return graph.compile()
