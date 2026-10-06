from .db import get_connection

def get_attendance(student_id: str, course_code: str | None = None):
    conn = get_connection()
    try:
        query = """
            SELECT
                a.student_id,
                a.course_code,
                c.course_name,
                a.classes_held,
                a.classes_attended,
                ROUND(
                    CASE
                        WHEN a.classes_held = 0 THEN 0
                        ELSE 100.0 * a.classes_attended / a.classes_held
                    END, 2
                ) AS attendance_percentage
            FROM attendance a
            LEFT JOIN courses c ON c.course_code = a.course_code
            WHERE a.student_id = ?
        """
        params = [student_id]

        if course_code:
            query += " AND a.course_code = ?"
            params.append(course_code)

        query += " ORDER BY a.course_code"

        rows = conn.execute(query, params).fetchall()
        return {
            "student_id": student_id,
            "count": len(rows),
            "attendance": [dict(r) for r in rows]
        }
    finally:
        conn.close()
