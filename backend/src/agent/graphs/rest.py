"""Rest subgraph — compiled LangGraph timer."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.graphs.nodes import rest_nodes as nodes
from agent.graphs.state import TrainerGraphState


def build_rest_subgraph():
    graph = StateGraph(TrainerGraphState)

    graph.add_node("start_timer", nodes.start_timer)
    graph.add_node("during_rest_tick", nodes.during_rest_tick)
    graph.add_node("finish_rest", nodes.finish_rest)

    graph.add_edge(START, "start_timer")
    graph.add_edge("start_timer", "during_rest_tick")
    graph.add_conditional_edges(
        "during_rest_tick",
        nodes.route_rest_tick,
        {"tick": "during_rest_tick", "done": "finish_rest"},
    )
    graph.add_edge("finish_rest", END)

    return graph.compile()
