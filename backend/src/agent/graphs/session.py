"""Session graph — top-level LangGraph orchestrator."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.graphs.nodes import session_nodes as nodes
from agent.graphs.rest import build_rest_subgraph
from agent.graphs.set_loop import build_set_subgraph
from agent.graphs.state import TrainerGraphState


def build_session_graph(*, checkpointer=None):
    set_subgraph = build_set_subgraph()
    rest_subgraph = build_rest_subgraph()

    graph = StateGraph(TrainerGraphState)

    graph.add_node("prepare", nodes.prepare)
    graph.add_node("setup", nodes.setup)
    graph.add_node("announce_set", nodes.announce_set)
    graph.add_node("run_set", set_subgraph)
    graph.add_node("after_set", nodes.after_set)
    graph.add_node("run_rest", rest_subgraph)
    graph.add_node("increment_set", nodes.increment_set)
    graph.add_node("exercise_feedback", nodes.exercise_feedback)
    graph.add_node("session_complete", nodes.session_complete)

    graph.add_edge(START, "prepare")
    graph.add_conditional_edges(
        "prepare",
        nodes.route_after_prepare,
        {"setup": "setup", "end": "session_complete"},
    )
    graph.add_conditional_edges(
        "setup",
        nodes.route_after_setup,
        {"sets": "announce_set", "end": "session_complete"},
    )
    graph.add_edge("announce_set", "run_set")
    graph.add_edge("run_set", "after_set")
    graph.add_conditional_edges(
        "after_set",
        nodes.route_after_set,
        {
            "pause": END,
            "end": "session_complete",
            "feedback": "exercise_feedback",
            "rest": "run_rest",
            "next_set": "increment_set",
        },
    )
    graph.add_conditional_edges(
        "run_rest",
        nodes.route_after_rest,
        {"pause": END, "next_set": "increment_set"},
    )
    graph.add_conditional_edges(
        "increment_set",
        nodes.route_more_sets,
        {"announce": "announce_set", "feedback": "exercise_feedback"},
    )
    graph.add_edge("exercise_feedback", "session_complete")
    graph.add_edge("session_complete", END)

    return graph.compile(checkpointer=checkpointer)
