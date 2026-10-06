from .db import get_connection

def get_results(student_id: str, course_code: str | None = None):
    conn = get_connection()
    try:
        query = """
            SELECT
                r.student_id,
                r.course_code,
                c.course_name,
                r.exam_session,
                r.exam_type,
                r.internal_marks,
                r.external_marks,
                r.total_marks,
                r.max_marks,
                r.result
            FROM results r
            LEFT JOIN courses c ON c.course_code = r.course_code
            WHERE r.student_id = ?
        """
        params = [student_id]

        if course_code:
            query += " AND r.course_code = ?"
            params.append(course_code)

        query += " ORDER BY r.course_code"

        rows = conn.execute(query, params).fetchall()
        return {
            "student_id": student_id,
            "count": len(rows),
            "results": [dict(r) for r in rows]
        }
    finally:
        conn.close()
