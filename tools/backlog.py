from .db import get_connection

def get_backlogs(student_id: str):
    conn = get_connection()
    try:
        # Prefer the authoritative active_backlogs field for the student's
        # current backlog count, and also expose failed/absent/detained rows.
        student = conn.execute("""
            SELECT active_backlogs
            FROM students
            WHERE student_id = ?
        """, (student_id,)).fetchone()

        rows = conn.execute("""
            SELECT
                r.course_code,
                c.course_name,
                r.total_marks,
                r.result
            FROM results r
            LEFT JOIN courses c ON c.course_code = r.course_code
            WHERE r.student_id = ?
              AND UPPER(r.result) IN
                  ('FAIL','FAILED','BACKLOG','DETAINED','ABSENT')
        """, (student_id,)).fetchall()

        return {
            "student_id": student_id,
            "active_backlogs": int(student["active_backlogs"]) if student else None,
            "backlogs": [dict(r) for r in rows]
        }
    finally:
        conn.close()
