"""LangGraph graph builder for CareerAgent.

This module defines the three core agent pipelines as LangGraph StateGraph
instances. The role initialization pipeline is fully wired for Sprint 2.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agent.nodes.achievement_analysis import achievement_analysis
from src.agent.nodes.capability_modeling import capability_modeling
from src.agent.nodes.explain import explain
from src.agent.nodes.gap_evaluation import gap_evaluation
from src.agent.nodes.jd_parsing import jd_parsing
from src.agent.nodes.jd_review import jd_review
# from src.agent.nodes.jd_tailoring import jd_tailoring  # Replaced by 4-step pipeline
from src.agent.nodes.jd_keyword_extract import jd_keyword_extract
from src.agent.nodes.project_selection import project_selection
from src.agent.nodes.resume_generation import resume_generation
from src.agent.nodes.keyword_verification import keyword_verification
from src.agent.nodes.resume_init import resume_init
from src.agent.nodes.resume_update import resume_update
from src.agent.nodes.role_matching import role_matching
from src.agent.state import CareerAgentState


def build_achievement_pipeline() -> StateGraph:
    """Build the achievement-processing pipeline.

    Flow:
        achievement_raw -> Achievement Analysis -> Role Matching
          -> Resume Update -> Gap Evaluation -> Explain

    Each of resume_update and gap_evaluation iterates over all matched
    roles internally, producing suggestions/gap_updates per role.
    """
    graph = StateGraph(CareerAgentState)

    graph.add_node("achievement_analysis", achievement_analysis)
    graph.add_node("role_matching", role_matching)
    graph.add_node("resume_update", resume_update)
    graph.add_node("gap_evaluation", gap_evaluation)
    graph.add_node("explain", explain)

    graph.set_entry_point("achievement_analysis")
    graph.add_edge("achievement_analysis", "role_matching")
    graph.add_edge("role_matching", "resume_update")
    graph.add_edge("resume_update", "gap_evaluation")
    graph.add_edge("gap_evaluation", "explain")
    graph.add_edge("explain", END)

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
    """Build the JD-tailoring pipeline (Phase 3: 4-step deep customization).

    Flow (default, skip_review=False):
        jd_raw -> JD Parsing -> JD Review -> JD Keyword Extract
          -> Project Selection -> Resume Generation -> Keyword Verification -> Explain -> END

    Flow (skip_review=True):
        jd_raw -> JD Parsing -> JD Keyword Extract
          -> Project Selection -> Resume Generation -> Keyword Verification -> Explain -> END
    """
    graph = StateGraph(CareerAgentState)

    graph.add_node("jd_parsing", jd_parsing)
    graph.add_node("jd_review", jd_review)
    graph.add_node("jd_keyword_extract", jd_keyword_extract)
    graph.add_node("project_selection", project_selection)
    graph.add_node("resume_generation", resume_generation)
    graph.add_node("keyword_verification", keyword_verification)
    graph.add_node("explain", explain)

    graph.set_entry_point("jd_parsing")

    def should_review(state: dict) -> str:
        """Skip review node if flag is set."""
        if state.get("skip_review"):
            return "jd_keyword_extract"
        return "jd_review"

    graph.add_conditional_edges("jd_parsing", should_review)
    graph.add_edge("jd_review", "jd_keyword_extract")
    graph.add_edge("jd_keyword_extract", "project_selection")
    graph.add_edge("project_selection", "resume_generation")
    graph.add_edge("resume_generation", "keyword_verification")
    graph.add_edge("keyword_verification", "explain")
    graph.add_edge("explain", END)

    return graph


# Compiled graphs — these are the objects the API layer will invoke.
achievement_graph = build_achievement_pipeline().compile()
role_init_graph = build_role_init_pipeline().compile()
jd_tailoring_graph = build_jd_tailoring_pipeline().compile()

# Default export for langgraph.json entry point.
graph = achievement_graph
