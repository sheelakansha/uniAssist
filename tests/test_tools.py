from tools.student import get_student
from tools.attendance import get_attendance
from tools.results import get_results
from tools.backlog import get_backlogs
from tools.eligibility import check_attendance_threshold

def test_student():
    x = get_student("S1001")
    assert x["found"] is True
    assert x["full_name"] == "Aarav Sharma"

def test_attendance():
    x = get_attendance("S1001", "CS201")
    assert x["count"] == 1
    assert x["attendance"][0]["attendance_percentage"] == 75.0

def test_results():
    x = get_results("S1001", "CS201")
    assert x["count"] == 1
    assert x["results"][0]["total_marks"] == 65

def test_backlogs():
    x = get_backlogs("S1001")
    assert "active_backlogs" in x
    assert "backlogs" in x

def test_eligibility():
    x = check_attendance_threshold("S1001", "CS201")
    assert x["meets_threshold"] is True

if __name__ == "__main__":
    test_student()
    test_attendance()
    test_results()
    test_backlogs()
    test_eligibility()
    print("ALL TOOL TESTS PASSED")
