from .state import AssistantState
from .router import route_query
from tools.student import get_student
from tools.attendance import get_attendance
from tools.results import get_results
from tools.backlog import get_backlogs
from tools.course import get_course
from tools.eligibility import check_attendance_threshold
from rag.policy_rules import extract_attendance_rule
from llm.local_llm import LocalLLM
from llm.prompt import SYSTEM_PROMPT, build_user_prompt
from llm.formatter import format_policy_sources, format_tool_result

local_llm = LocalLLM()

def route_node(state: AssistantState):
    return route_query(state["user_query"])

def policy_node(state: AssistantState):
    query = state["user_query"]

    if state.get("intent") == "attendance_eligibility":
        query = (
            "NSUT B.Tech regulation minimum required attendance percentage "
            "eligibility examination attendance"
        )

    # PolicyEngine selects Chroma only after a document has completed vector
    # indexing; otherwise it safely retrieves from registered source text.
    from rag.policy_engine import PolicyEngine
    result = {"sources": PolicyEngine().retrieve(query, top_k=8)}
    sources = result.get("sources", [])

    return {
        "policy_context": sources,
        "sources": sources
    }

def tool_node(state: AssistantState):
    intent = state.get("intent")
    student_id = state.get("student_id")
    course_code = state.get("course_code")

    if intent in {
        "attendance", "attendance_eligibility", "backlogs", "results"
    } and not student_id:
        return {"error": "Please provide a student ID, for example S1001."}

    if intent == "student":
        return {"tool_result": get_student(student_id)}

    if intent == "attendance":
        return {"tool_result": get_attendance(student_id, course_code)}

    if intent == "results":
        return {"tool_result": get_results(student_id, course_code)}

    if intent == "backlogs":
        return {"tool_result": get_backlogs(student_id)}

    if intent == "course":
        if not course_code:
            return {"error": "Please provide a course code, for example CS201."}
        return {"tool_result": get_course(course_code)}

    if intent == "attendance_eligibility":
        # Policy value is resolved in decision_node.
        return {}

    return {
        "error": (
            "I could not identify the request. Try asking about "
            "attendance, results, backlogs, courses, student details, "
            "or university policies."
        )
    }

def decision_node(state: AssistantState):
    intent = state.get("intent")
    policies = state.get("policy_context") or []

    if intent == "attendance_eligibility":
        if not policies:
            return {
                "error": "No active authoritative attendance policy retrieved."
            }

        ordered = sorted(
            policies,
            key=lambda x: int(x.get("authority_level") or 0),
            reverse=True
        )

        selected = None
        rule = None

        for source in ordered:
            candidate = extract_attendance_rule(source.get("text", ""))
            if candidate:
                selected = source
                rule = candidate
                break

        if not rule:
            return {
                "error": (
                    "An attendance policy was retrieved, but its threshold "
                    "could not be deterministically extracted."
                )
            }

        student_id = state.get("student_id")
        course_code = state.get("course_code")

        if not student_id or not course_code:
            return {
                "error": (
                    "Please provide both a student ID and course code, "
                    "for example S1001 and CS201."
                )
            }

        result = check_attendance_threshold(
            student_id,
            course_code,
            rule["required_percentage"]
        )

        if not result.get("found"):
            return {
                "error": result.get(
                    "message", "Attendance record not found."
                )
            }

        return {
            "tool_result": result,
            "policy_context": policies,
            "selected_policy": selected,
            "policy_rule": rule
        }

    return {}

def llm_response_node(state: AssistantState):
    if state.get("error"):
        return {
            "final_answer": state["error"]
        }

    question = state.get("user_query", "")
    tool_result = format_tool_result(state.get("tool_result"))
    policy_context = format_policy_sources(
        state.get("policy_context") or []
    )

    answer = local_llm.generate(
        SYSTEM_PROMPT,
        build_user_prompt(
            question,
            tool_result=tool_result,
            policy_context=policy_context
        )
    )

    return {
        "final_answer": answer
    }
