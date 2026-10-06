from .db import get_connection

def get_course(course_code: str):
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT course_code, course_name, programme, semester, credits
            FROM courses
            WHERE course_code = ?
        """, (course_code,)).fetchone()

        if not row:
            return {"found": False, "course_code": course_code}

        return {"found": True, **dict(row)}
    finally:
        conn.close()
