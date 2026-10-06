from graph.graph import assistant_graph

def run(q):
    return assistant_graph.invoke({"user_query": q})

def test_attendance():
    x = run("What is S1001's attendance for CS201?")
    assert x["intent"] == "attendance"
    assert "75.0%" in x["final_answer"]

def test_backlog():
    x = run("What are S1001's backlogs?")
    assert x["intent"] == "backlogs"
    assert "active backlog" in x["final_answer"]

def test_results():
    x = run("What are S1001's results?")
    assert x["intent"] == "results"
    assert "CS201" in x["final_answer"]

def test_student():
    x = run("Tell me about student S1001")
    assert x["intent"] == "student"
    assert "Aarav Sharma" in x["final_answer"]

def test_course():
    x = run("What is CS201 course?")
    assert x["intent"] == "course"
    assert "CS201" in x["final_answer"]

def test_policy():
    x = run("What is the minimum attendance requirement at NSUT?")
    assert x["intent"] == "university_policy"

if __name__ == "__main__":
    test_attendance()
    test_backlog()
    test_results()
    test_student()
    test_course()
    test_policy()
    print("ALL LANGGRAPH TESTS PASSED")
