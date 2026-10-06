from .attendance import get_attendance

def check_attendance_threshold(
    student_id: str,
    course_code: str,
    required_percentage: float | None = None
):
    """
    Deterministic calculation only.

    Production callers must supply the value from the policy resolver.  The
    compatibility path reads the existing rule registry, rather than embedding
    a policy number in code, for the original deterministic-tool test.
    """
    if required_percentage is None:
        from .db import get_connection
        conn = get_connection()
        try:
            row = conn.execute("SELECT value FROM rule_registry WHERE parameter='min_attendance_pct' ORDER BY effective_from DESC LIMIT 1").fetchone()
            if not row:
                return {"student_id": student_id, "course_code": course_code, "found": False, "message": "No attendance threshold is registered"}
            required_percentage = float(row["value"])
        finally:
            conn.close()
    result = get_attendance(student_id, course_code)

    if not result["attendance"]:
        return {
            "student_id": student_id,
            "course_code": course_code,
            "found": False,
            "message": "Attendance record not found"
        }

    record = result["attendance"][0]
    actual = float(record["attendance_percentage"])

    return {
        "student_id": student_id,
        "course_code": course_code,
        "found": True,
        "actual_percentage": actual,
        "required_percentage": float(required_percentage),
        "meets_threshold": actual >= float(required_percentage),
        "difference": round(actual - float(required_percentage), 2)
    }
