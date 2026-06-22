"""Set observation subgraph — compiled LangGraph cycle."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.graphs.nodes import set_nodes as nodes
from agent.graphs.state import TrainerGraphState


def build_set_subgraph():
    graph = StateGraph(TrainerGraphState)

    graph.add_node("begin_set", nodes.begin_set)
    graph.add_node("grab_frame", nodes.grab_frame)
    graph.add_node("preprocess_pose", nodes.preprocess_pose)
    graph.add_node("vlm_analyze", nodes.vlm_analyze)
    graph.add_node("observe_update", nodes.observe_update)
    graph.add_node("emit_voice", nodes.emit_voice)
    graph.add_node("safety_check", nodes.safety_check)
    graph.add_node("wait_cycle", nodes.wait_cycle)

    graph.add_edge(START, "begin_set")
    graph.add_edge("begin_set", "grab_frame")
    graph.add_conditional_edges(
        "grab_frame",
        nodes.route_after_grab,
        {"preprocess": "preprocess_pose", "wait": "wait_cycle", "done": END},
    )
    graph.add_edge("preprocess_pose", "vlm_analyze")
    graph.add_conditional_edges(
        "vlm_analyze",
        nodes.route_after_vlm,
        {"observe": "observe_update", "voice": "emit_voice", "safety": "safety_check"},
    )
    graph.add_edge("observe_update", "safety_check")
    graph.add_edge("emit_voice", "safety_check")
    graph.add_conditional_edges(
        "safety_check",
        nodes.route_after_safety,
        {"wait": "wait_cycle", "done": END},
    )
    graph.add_edge("wait_cycle", "grab_frame")

    return graph.compile()
