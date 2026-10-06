from .db import get_connection

def get_student(student_id: str):
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT student_id, full_name, programme, batch_year,
                   current_semester, cgpa, active_backlogs
            FROM students
            WHERE student_id = ?
        """, (student_id,)).fetchone()

        if not row:
            return {"found": False, "student_id": student_id,
                    "message": "Student not found"}

        return {"found": True, **dict(row)}
    finally:
        conn.close()
