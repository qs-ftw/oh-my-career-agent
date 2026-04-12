"""LangGraph graph builder for CareerAgent.

This module defines the three core agent pipelines as LangGraph StateGraph
instances. The role initialization pipeline is fully wired for Sprint 2.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agent.state import CareerAgentState
from src.agent.nodes.capability_modeling import capability_modeling
from src.agent.nodes.resume_init import resume_init
from src.agent.nodes.gap_evaluation import gap_evaluation


def build_achievement_pipeline() -> StateGraph:
    """Build the achievement-processing pipeline.

    Flow:
        achievement_raw -> Achievement Analysis -> Role Matching
          -> (parallel per role) Resume Update + Gap Evaluation
          -> Explain
    """
    graph = StateGraph(CareerAgentState)
    # Placeholder: add a no-op node so the graph compiles
    graph.add_node("__noop__", lambda state: state)
    graph.set_entry_point("__noop__")
    graph.add_edge("__noop__", END)
    return graph


def build_role_init_pipeline() -> StateGraph:
    """Build the role-initialization pipeline.

    Flow:
        role_input -> Capability Modeling -> Resume Init -> Gap Evaluation

    When a user creates a new target role, this pipeline:
    1. Analyzes the role description and builds a capability model
    2. Generates a resume skeleton tailored to the role
    3. Identifies initial skill gaps
    """
    graph = StateGraph(CareerAgentState)

    # Add nodes
    graph.add_node("capability_modeling", capability_modeling)
    graph.add_node("resume_init", resume_init)
    graph.add_node("gap_evaluation", gap_evaluation)

    # Wire the linear chain
    graph.set_entry_point("capability_modeling")
    graph.add_edge("capability_modeling", "resume_init")
    graph.add_edge("resume_init", "gap_evaluation")
    graph.add_edge("gap_evaluation", END)

    return graph


def build_jd_tailoring_pipeline() -> StateGraph:
    """Build the JD-tailoring pipeline.

    Flow:
        jd_raw -> JD Parsing -> (mode branch) JD Tailoring -> Match Scoring -> Explain
    """
    graph = StateGraph(CareerAgentState)
    graph.add_node("__noop__", lambda state: state)
    graph.set_entry_point("__noop__")
    graph.add_edge("__noop__", END)
    return graph


# Compiled graphs — these are the objects the API layer will invoke.
achievement_graph = build_achievement_pipeline().compile()
role_init_graph = build_role_init_pipeline().compile()
jd_tailoring_graph = build_jd_tailoring_pipeline().compile()

# Default export for langgraph.json entry point.
graph = achievement_graph
