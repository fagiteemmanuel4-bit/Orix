import os
import requests
from typing import Dict, Any

class AIBuilder:
    OPENROUTER_DEFAULT = "https://openrouter.ai/v1/chat/completions"

    def __init__(self, endpoint: str, api_key: str, model: str):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model

    def build_spec(self, prompt: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an AI assistant that generates Orix YAML specs for scaffold generation."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
        }
        response = requests.post(self.endpoint, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        text = self._extract_text(data)
        return self._parse_spec(text)

    def _extract_text(self, data: Dict[str, Any]) -> str:
        if "choices" in data and data["choices"]:
            choice = data["choices"][0]
            return choice.get("message", {}).get("content", "")
        return data.get("output", "")

    def _parse_spec(self, text: str) -> Dict[str, Any]:
        import yaml

        if "```yaml" in text:
            text = text.split("```yaml", 1)[1].rsplit("```", 1)[0].strip()
        elif "```" in text:
            text = text.split("```", 1)[1].rsplit("```", 1)[0].strip()

        return yaml.safe_load(text)
