from rag.policy_rules import extract_attendance_rule

def test_extract():
    text = """
    11.2 Minimum 75% attendance in classes held in a subject
    till MSE/ESE for eligibility.
    """
    rule = extract_attendance_rule(text)
    assert rule is not None
    assert rule["required_percentage"] == 75.0

if __name__ == "__main__":
    test_extract()
    print("DYNAMIC POLICY EXTRACTION TEST PASSED")
