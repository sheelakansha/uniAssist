import os
from typing import Optional

class LocalLLM:
    """
    OpenAI-compatible local LLM client.

    Recommended local server:
      Ollama
      model: qwen2.5:7b-instruct

    The application never sends private student data to a cloud LLM.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 120
    ):
        self.base_url = (
            base_url
            or os.getenv("LOCAL_LLM_BASE_URL")
            or "http://localhost:11434/v1"
        ).rstrip("/")
        self.model = (
            model
            or os.getenv("LOCAL_LLM_MODEL")
            or "qwen2.5:7b-instruct"
        )
        self.timeout = timeout

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if os.getenv("LLM_MODE", "mock").lower() == "mock":
            # CI-safe explanation mode. It receives the exact same verified
            # evidence as the local model but performs no inference.
            import re
            attendance = re.search(r"attendance_percentage['\"]:\s*([0-9.]+)", user_prompt)
            if attendance:
                return f"Verified attendance: {attendance.group(1)}%. Source: SQLite / Student Academic Database."
            return "Verified evidence: " + user_prompt.replace("_", " ")
        try:
            import requests
        except ImportError:
            return (
                "Local LLM client requires the requests package. "
                "Install the project requirements first."
            )

        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            return (
                f"Local LLM is unavailable. Verified data is still available. "
                f"Error: {exc}"
            )
