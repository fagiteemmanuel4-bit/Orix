import json
import os
import requests
from typing import Dict, Any, Optional

class AIProvider:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "")
        self.endpoint = config.get("endpoint", "")
        self.api_key = config.get("api_key", "")
        self.temperature = config.get("temperature", 0.2)
        self.max_tokens = config.get("max_tokens", 2048)
        self.timeout = config.get("timeout", 60)

    def generate_text(self, prompt: str) -> str:
        raise NotImplementedError("Each concrete provider must implement generate_text.")

    def generate_structured_output(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates text and parses/validates it according to the schema if specified."""
        response_text = self.generate_text(prompt)

        # Clean any markdown block wrap if present
        if "```json" in response_text:
            response_text = response_text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```", 1)[1].rsplit("```", 1)[0].strip()

        try:
            parsed = json.loads(response_text)
            if schema:
                # Basic schema validation
                for req_key in schema.get("required", []):
                    if req_key not in parsed:
                        raise ValueError(f"Schema validation failed: missing required key '{req_key}'")
            return parsed
        except Exception as e:
            # Simple repair attempt: ask again or fallback
            raise ValueError(f"Failed to parse structured JSON from model: {e}. Raw content: {response_text}")

class OpenAIProvider(AIProvider):
    def generate_text(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API key is missing. Set 'api_key' in config or use OPENAI_API_KEY env var.")
        url = self.endpoint or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model or "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

class AnthropicProvider(AIProvider):
    def generate_text(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("Anthropic API key is missing.")
        url = self.endpoint or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model or "claude-3-5-sonnet-20241022",
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

class GeminiProvider(AIProvider):
    def generate_text(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key is missing.")
        url = self.endpoint or f"https://generativelanguage.googleapis.com/v1beta/models/{self.model or 'gemini-1.5-flash'}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens
            }
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

class OpenRouterProvider(AIProvider):
    def generate_text(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("OpenRouter API key is missing.")
        url = self.endpoint or "https://openrouter.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model or "meta-llama/llama-3.1-8b-instruct:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

class OllamaProvider(AIProvider):
    def is_available(self) -> bool:
        url = self.endpoint or "http://localhost:11434/api/tags"
        try:
            resp = requests.get(url, timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def generate_text(self, prompt: str) -> str:
        url = self.endpoint or "http://localhost:11434/api/generate"
        payload = {
            "model": self.model or "llama3",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()["response"]
        except Exception as e:
            raise RuntimeError(f"Ollama local API call failed. Is Ollama server running? Error: {e}")

class OpenAICompatibleProvider(AIProvider):
    def generate_text(self, prompt: str) -> str:
        if not self.endpoint:
            raise ValueError("Endpoint must be specified for OpenAI-compatible provider.")
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        headers["Content-Type"] = "application/json"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

def get_provider(config: Dict[str, Any]) -> AIProvider:
    provider_name = config.get("provider", "openai").lower()

    # Read key from env vars as fallback
    if not config.get("api_key"):
        if provider_name == "openai":
            config["api_key"] = os.getenv("OPENAI_API_KEY", "")
        elif provider_name == "anthropic":
            config["api_key"] = os.getenv("ANTHROPIC_API_KEY", "")
        elif provider_name == "gemini":
            config["api_key"] = os.getenv("GEMINI_API_KEY", "")
        elif provider_name == "openrouter":
            config["api_key"] = os.getenv("OPENROUTER_API_KEY", "")

    if provider_name == "openai":
        return OpenAIProvider(config)
    elif provider_name == "anthropic":
        return AnthropicProvider(config)
    elif provider_name == "gemini":
        return GeminiProvider(config)
    elif provider_name == "openrouter":
        return OpenRouterProvider(config)
    elif provider_name == "ollama":
        return OllamaProvider(config)
    elif provider_name == "openai-compatible":
        return OpenAICompatibleProvider(config)
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")
