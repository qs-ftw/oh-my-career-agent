"""LangGraph graph builder for CareerAgent.

This module defines the three core agent pipelines as LangGraph StateGraph
instances.  During the stub phase the graphs are empty placeholders that will
be populated with real nodes and edges in subsequent sprints.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agent.state import CareerAgentState


def build_achievement_pipeline() -> StateGraph:
    """Build the achievement-processing pipeline.

    Flow:
        achievement_raw -> Achievement Analysis -> Role Matching
          -> (parallel per role) Resume Update + Gap Evaluation
          -> Explain
    """
    graph = StateGraph(CareerAgentState)
    # Nodes will be added in Sprint 3.
    graph.set_entry_point("__end__")
    graph.add_edge("__end__", END)
    return graph


def build_role_init_pipeline() -> StateGraph:
    """Build the role-initialization pipeline.

    Flow:
        role_input -> Capability Modeling -> Resume Init -> Gap Evaluation -> Explain
    """
    graph = StateGraph(CareerAgentState)
    graph.set_entry_point("__end__")
    graph.add_edge("__end__", END)
    return graph


def build_jd_tailoring_pipeline() -> StateGraph:
    """Build the JD-tailoring pipeline.

    Flow:
        jd_raw -> JD Parsing -> (mode branch) JD Tailoring -> Match Scoring -> Explain
    """
    graph = StateGraph(CareerAgentState)
    graph.set_entry_point("__end__")
    graph.add_edge("__end__", END)
    return graph


# Compiled graphs — these are the objects the API layer will invoke.
achievement_graph = build_achievement_pipeline().compile()
role_init_graph = build_role_init_pipeline().compile()
jd_tailoring_graph = build_jd_tailoring_pipeline().compile()

# Default export for langgraph.json entry point.
graph = achievement_graph
