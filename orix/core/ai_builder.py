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
        if not self.api_key:
            raise ValueError(
                "API key is missing.\n"
                "Details: The required API key was empty or not provided.\n"
                "What to do next: Please provide a valid API key to use the AI Builder."
            )

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

        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
        except requests.exceptions.Timeout as e:
            raise RuntimeError(
                f"The AI model request timed out.\n"
                f"Details: {str(e)}\n"
                f"What to do next: Check your internet connection, verify the model endpoint '{self.endpoint}', or try again later."
            )
        except requests.exceptions.HTTPError as e:
            status_code = response.status_code if 'response' in locals() else "unknown"
            raise RuntimeError(
                f"The AI provider returned an HTTP error (Status Code: {status_code}).\n"
                f"Details: {str(e)}\n"
                f"What to do next: Verify your API key is correct and has sufficient credits, and that your selected model '{self.model}' is correct."
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to communicate with the AI provider.\n"
                f"Details: {str(e)}\n"
                f"What to do next: Ensure your network is active and the endpoint URL '{self.endpoint}' is correct."
            )

        try:
            data = response.json()
        except Exception as e:
            raise RuntimeError(
                f"Received an invalid JSON response from the AI provider.\n"
                f"Details: {str(e)}\n"
                f"What to do next: Check if the API endpoint returned an unexpected error page or HTML instead of JSON."
            )

        text = self._extract_text(data)
        if not text or not text.strip():
            raise ValueError(
                "The AI model returned an empty response.\n"
                "Details: The response JSON succeeded but 'choices' or 'output' content was empty.\n"
                "What to do next: Rephrase your prompt or try a different AI model."
            )

        return self._parse_spec(text)

    def _extract_text(self, data: Dict[str, Any]) -> str:
        if "choices" in data and data["choices"]:
            choice = data["choices"][0]
            if isinstance(choice, dict):
                return choice.get("message", {}).get("content", "")
        return data.get("output", "") if isinstance(data, dict) else ""

    def _parse_spec(self, text: str) -> Dict[str, Any]:
        import yaml

        if "```yaml" in text:
            text = text.split("```yaml", 1)[1].rsplit("```", 1)[0].strip()
        elif "```" in text:
            text = text.split("```", 1)[1].rsplit("```", 1)[0].strip()

        try:
            parsed = yaml.safe_load(text)
        except yaml.YAMLError as e:
            raise ValueError(
                f"Failed to parse the AI response as a valid YAML specification.\n"
                f"Details: {str(e)}\n"
                f"AI Output: {text}\n"
                f"What to do next: Try again with a clearer prompt, or manually create your specification YAML file."
            )

        if not isinstance(parsed, dict):
            raise ValueError(
                f"AI specification did not evaluate to a YAML dictionary/object.\n"
                f"Details: Expected a YAML dictionary, got {type(parsed).__name__}.\n"
                f"What to do next: Re-run with a prompt specifically asking for a structured YAML document."
            )

        # Validate required fields
        required_fields = ["project_name", "framework"]
        missing = [f for f in required_fields if f not in parsed]
        if missing:
            raise ValueError(
                f"The generated AI specification is invalid.\n"
                f"Details: Missing required field(s): {', '.join(missing)}.\n"
                f"What to do next: Ask the AI model specifically to include these fields, or edit the spec file manually."
            )

        return parsed
