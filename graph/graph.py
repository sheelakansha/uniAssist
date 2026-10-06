from langgraph.graph import StateGraph, START, END
from .state import AssistantState
from .nodes import (
    route_node,
    tool_node,
    policy_node,
    decision_node,
    llm_response_node
)

def route_after_classifier(state: AssistantState):
    if state.get("intent") in {
        "university_policy",
        "attendance_eligibility"
    }:
        return "policy"
    return "tool"

def build_graph():
    builder = StateGraph(AssistantState)

    builder.add_node("router", route_node)
    builder.add_node("tool", tool_node)
    builder.add_node("policy", policy_node)
    builder.add_node("decision", decision_node)
    builder.add_node("llm_response", llm_response_node)

    builder.add_edge(START, "router")

    builder.add_conditional_edges(
        "router",
        route_after_classifier,
        {
            "tool": "tool",
            "policy": "policy"
        }
    )

    builder.add_edge("tool", "llm_response")
    builder.add_edge("policy", "decision")
    builder.add_edge("decision", "llm_response")
    builder.add_edge("llm_response", END)

    return builder.compile()

assistant_graph = build_graph()
