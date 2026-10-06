from typing import Any, TypedDict

class AssistantState(TypedDict, total=False):
    user_query: str
    student_id: str | None
    course_code: str | None
    intent: str
    tool_result: dict[str, Any] | None
    policy_context: list[dict[str, Any]]
    selected_policy: dict[str, Any] | None
    policy_rule: dict[str, Any] | None
    final_answer: str
    sources: list[dict[str, Any]]
    error: str | None
