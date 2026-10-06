import re
from typing import Any

def _number(value: str) -> float:
    return float(value.replace(",", "").strip())

def extract_attendance_rule(text: str) -> dict[str, Any] | None:
    """
    Deterministic extraction of the university attendance threshold.

    We deliberately do NOT ask the LLM to invent a policy value.
    We search retrieved regulation text for explicit attendance percentages.
    """
    patterns = [
        r'(?:minimum|required|at least|maintain)\D{0,120}'
        r'(\d{1,3}(?:\.\d+)?)\s*%\s*(?:attendance|of attendance)',
        r'(\d{1,3}(?:\.\d+)?)\s*%\s*(?:attendance|of attendance)',
        r'(?:attendance)\D{0,100}'
        r'(\d{1,3}(?:\.\d+)?)\s*%'
    ]

    candidates = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = _number(match.group(1))
            if 0 < value <= 100:
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 120)
                context = " ".join(text[start:end].split())
                candidates.append({
                    "required_percentage": value,
                    "context": context
                })

    if not candidates:
        return None

    # Prefer values occurring near "minimum/required/at least".
    preferred = [
        c for c in candidates
        if re.search(r'\b(minimum|required|at least|maintain)\b',
                     c["context"], re.IGNORECASE)
    ]

    chosen = preferred[0] if preferred else candidates[0]

    return {
        "rule_type": "attendance_minimum",
        "required_percentage": chosen["required_percentage"],
        "evidence": chosen["context"]
    }
