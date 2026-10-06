import re

def extract_student_id(query: str) -> str | None:
    m = re.search(r"\bS\d{4}\b", query.upper())
    return m.group(0) if m else None

def extract_course_code(query: str) -> str | None:
    # Current synthetic courses use codes such as CS201, EC201, etc.
    m = re.search(r"\b[A-Z]{2,4}\d{3}\b", query.upper())
    return m.group(0) if m else None

def classify_intent(query: str) -> str:
    q = query.lower()

    # Deterministic high-confidence patterns are deliberately handled before
    # broad words such as "course", "attendance", or "eligible".
    if re.search(r"\b[a-z]{2,4}\d{3}\b", q) and q.strip().startswith("what is") and "attendance" not in q and "result" not in q:
        return "course"
    if "cgpa" in q and "degree" not in q:
        return "student"
    if any(x in q for x in ["fail a course", "failed course", "re-registration", "grading rule"]):
        return "university_policy"
    if any(x in q for x in ["ese", "mse", "examination", "supplementary"]):
        if "eligibility rule" in q and not re.search(r"\bs\d{4}\b",q):
            return "university_policy"
        return "examination"
    if any(x in q for x in ["odd to even", "even to odd", "promotion", "promote"]):
        return "promotion"
    if any(x in q for x in ["maximum duration", "regular semesters", "programme duration"]):
        return "university_policy"
    if "semester begin" in q or "semester start" in q:
        return "academic_calendar"
    if "attendance" in q and any(x in q for x in ["policy", "rule", "minimum", "relaxation", "below"]):
        return "university_policy"

    if any(x in q for x in [
        "eligible", "eligibility", "attendance requirement",
        "attendance required", "minimum attendance"
    ]):
        if "attendance requirement" in q or "minimum attendance" in q:
            return "university_policy"
        if "eligible" in q or "eligibility" in q:
            return "attendance_eligibility"

    if any(x in q for x in ["degree requirement", "degree credits", "earned credits", "b.tech degree", "cgpa is needed for a degree"]):
        return "degree_requirement"
    if "promotion" in q or "promote" in q:
        return "promotion"
    if "supplementary" in q or "exam" in q or "examination" in q:
        return "examination"
    if "calendar" in q:
        return "academic_calendar"
    if "fee" in q:
        return "fees"
    if "syllabus" in q:
        return "syllabus"
    if "backlog" in q or "backlogs" in q:
        return "backlogs"

    if "attendance" in q:
        return "attendance"

    if any(x in q for x in ["result", "results", "marks", "grade"]):
        return "results"

    if "course" in q or "credits" in q or "subject" in q:
        return "course"

    if any(x in q for x in [
        "regulation", "policy", "rule", "syllabus",
        "calendar", "fee", "notice", "university requirement"
    ]):
        return "university_policy"

    if "student" in q or "profile" in q or ("who is" in q and extract_student_id(query)):
        return "student"

    return "unknown"

def route_query(query: str) -> dict:
    return {
        "intent": classify_intent(query),
        "student_id": extract_student_id(query),
        "course_code": extract_course_code(query)
    }
