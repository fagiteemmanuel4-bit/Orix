import os
import json
import requests
from typing import Dict, Any, List, Optional, Generator

# Centralized Model Capability Registry
MODEL_REGISTRY = {
    "gpt-4o-mini": {
        "provider": "openai",
        "display_name": "GPT-4o Mini",
        "context_window": 128000,
        "tool_calling": True,
        "structured_output": True,
        "vision": True,
        "streaming": True,
        "reasoning": False,
        "local": False
    },
    "claude-3-5-sonnet-20241022": {
        "provider": "anthropic",
        "display_name": "Claude 3.5 Sonnet",
        "context_window": 200000,
        "tool_calling": True,
        "structured_output": True,
        "vision": True,
        "streaming": True,
        "reasoning": True,
        "local": False
    },
    "gemini-1.5-flash": {
        "provider": "gemini",
        "display_name": "Gemini 1.5 Flash",
        "context_window": 1048576,
        "tool_calling": True,
        "structured_output": True,
        "vision": True,
        "streaming": True,
        "reasoning": False,
        "local": False
    },
    "llama3": {
        "provider": "ollama",
        "display_name": "Llama 3 (Local)",
        "context_window": 8192,
        "tool_calling": False,
        "structured_output": False,
        "vision": False,
        "streaming": True,
        "reasoning": False,
        "local": True
    }
}

class AIProvider:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "")
        self.endpoint = config.get("endpoint", "")
        self.api_key = config.get("api_key", "")
        self.temperature = config.get("temperature", 0.2)
        self.max_tokens = config.get("max_tokens", 2048)
        self.timeout = config.get("timeout", 60)

    def validate_connection(self) -> bool:
        raise NotImplementedError()

    def list_models(self) -> List[str]:
        raise NotImplementedError()

    def generate(self, messages: List[Dict[str, str]], **options) -> str:
        raise NotImplementedError()

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        raise NotImplementedError()

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        raise NotImplementedError()

    def generate_text(self, prompt: str) -> str:
        # Backward-compatible convenience wrapper
        return self.generate([{"role": "user", "content": prompt}])

    def generate_structured_output(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Clean helper for JSON outputs with optional validation
        resp_text = self.generate([{"role": "user", "content": prompt}])
        if "```json" in resp_text:
            resp_text = resp_text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
        elif "```" in resp_text:
            resp_text = resp_text.split("```", 1)[1].rsplit("```", 1)[0].strip()

        try:
            parsed = json.loads(resp_text)
            if schema:
                for req_key in schema.get("required", []):
                    if req_key not in parsed:
                        raise ValueError(f"Schema validation failed: missing required key '{req_key}'")
            return parsed
        except Exception as e:
            raise ValueError(f"Failed to parse structured JSON from model: {e}. Raw content: {resp_text}")


class OpenAIProvider(AIProvider):
    def validate_connection(self) -> bool:
        if not self.api_key:
            return False
        url = self.endpoint or "https://api.openai.com/v1/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        return [k for k, v in MODEL_REGISTRY.items() if v["provider"] == "openai"]

    def generate(self, messages: List[Dict[str, str]], **options) -> str:
        url = self.endpoint or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model or "gpt-4o-mini",
            "messages": messages,
            "temperature": options.get("temperature", self.temperature),
            "max_tokens": options.get("max_tokens", self.max_tokens)
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        url = self.endpoint or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model or "gpt-4o-mini",
            "messages": messages,
            "temperature": options.get("temperature", self.temperature),
            "max_tokens": options.get("max_tokens", self.max_tokens),
            "stream": True
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout, stream=True)
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                decoded = line.decode("utf-8").strip()
                if decoded.startswith("data: "):
                    data_str = decoded[len("data: "):]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except Exception:
                        pass

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        url = self.endpoint or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        formatted_tools = []
        for t in tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"]
                }
            })
        payload = {
            "model": self.model or "gpt-4o-mini",
            "messages": messages,
            "tools": formatted_tools,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        msg = resp.json()["choices"][0]["message"]

        tool_calls = []
        if "tool_calls" in msg and msg["tool_calls"]:
            for tc in msg["tool_calls"]:
                tool_calls.append({
                    "name": tc["function"]["name"],
                    "arguments": json.loads(tc["function"]["arguments"])
                })
        return {
            "content": msg.get("content", ""),
            "tool_calls": tool_calls
        }


class AnthropicProvider(AIProvider):
    def validate_connection(self) -> bool:
        return bool(self.api_key)

    def list_models(self) -> List[str]:
        return [k for k, v in MODEL_REGISTRY.items() if v["provider"] == "anthropic"]

    def generate(self, messages: List[Dict[str, str]], **options) -> str:
        url = self.endpoint or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model or "claude-3-5-sonnet-20241022",
            "max_tokens": self.max_tokens,
            "messages": messages,
            "temperature": self.temperature
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        # Anthropic streaming fallback
        yield self.generate(messages, **options)

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        # Convert schemas to Anthropic style
        url = self.endpoint or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        formatted_tools = []
        for t in tools:
            formatted_tools.append({
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["parameters"]
            })
        payload = {
            "model": self.model or "claude-3-5-sonnet-20241022",
            "max_tokens": self.max_tokens,
            "messages": messages,
            "tools": formatted_tools,
            "temperature": self.temperature
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        tool_calls = []
        content = ""
        for content_block in data.get("content", []):
            if content_block.get("type") == "text":
                content += content_block.get("text", "")
            elif content_block.get("type") == "tool_use":
                tool_calls.append({
                    "name": content_block["name"],
                    "arguments": content_block["input"]
                })
        return {
            "content": content,
            "tool_calls": tool_calls
        }


class GeminiProvider(AIProvider):
    def validate_connection(self) -> bool:
        return bool(self.api_key)

    def list_models(self) -> List[str]:
        return [k for k, v in MODEL_REGISTRY.items() if v["provider"] == "gemini"]

    def generate(self, messages: List[Dict[str, str]], **options) -> str:
        model_name = self.model or "gemini-1.5-flash"
        url = self.endpoint or f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        parts = []
        for m in messages:
            parts.append({"text": m["content"]})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens
            }
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        yield self.generate(messages, **options)

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        # Simple tools fallback via text mapping
        return {"content": self.generate(messages), "tool_calls": []}


class OpenRouterProvider(AIProvider):
    def validate_connection(self) -> bool:
        return bool(self.api_key)

    def list_models(self) -> List[str]:
        return ["meta-llama/llama-3.1-8b-instruct:free"]

    def generate(self, messages: List[Dict[str, str]], **options) -> str:
        url = self.endpoint or "https://openrouter.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model or "meta-llama/llama-3.1-8b-instruct:free",
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        yield self.generate(messages, **options)

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        return {"content": self.generate(messages), "tool_calls": []}


class OllamaProvider(AIProvider):
    def validate_connection(self) -> bool:
        url = self.endpoint or "http://localhost:11434/api/tags"
        try:
            resp = requests.get(url, timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def is_available(self) -> bool:
        return self.validate_connection()

    def list_models(self) -> List[str]:
        return ["llama3"]

    def generate(self, messages: List[Dict[str, str]], **options) -> str:
        url = self.endpoint or "http://localhost:11434/api/generate"
        prompt = "\n".join([m["content"] for m in messages])
        payload = {
            "model": self.model or "llama3",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        resp = requests.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["response"]

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        yield self.generate(messages, **options)

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        return {"content": self.generate(messages), "tool_calls": []}


class OpenAICompatibleProvider(AIProvider):
    def validate_connection(self) -> bool:
        return bool(self.endpoint)

    def list_models(self) -> List[str]:
        return []

    def generate(self, messages: List[Dict[str, str]], **options) -> str:
        if not self.endpoint:
            raise ValueError("Endpoint must be specified for OpenAI-compatible provider.")
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        headers["Content-Type"] = "application/json"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        yield self.generate(messages, **options)

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        return {"content": self.generate(messages), "tool_calls": []}


# --- MOCK PROVIDER FOR DETERMINISTIC OFFLINE TESTING ---

class MockProvider(AIProvider):
    def validate_connection(self) -> bool:
        return True

    def list_models(self) -> List[str]:
        return ["mock-model"]

    def generate(self, messages: List[Dict[str, str]], **options) -> str:
        # Check for predictable mock failures
        if self.config.get("mock_failure") == "timeout":
            raise requests.exceptions.Timeout("Mock API request timed out.")
        if self.config.get("mock_failure") == "rate_limit":
            raise RuntimeError("Mock API rate limit exceeded.")
        if self.config.get("mock_failure") == "auth":
            raise ValueError("Mock API invalid key.")

        prompt = messages[-1]["content"] if messages else ""
        if "failing test" in prompt.lower() or "test_runner.py" in prompt.lower():
            return '{"steps": ["Check assertions"], "tool_calls": [{"name": "write_file", "arguments": {"filepath": "test_runner.py", "content": "def test_assert():\\n    assert True\\n"}}]}'
        if "endpoint" in prompt.lower() or "app.py" in prompt.lower():
            return '{"steps": ["Add health endpoint"], "tool_calls": [{"name": "write_file", "arguments": {"filepath": "app.py", "content": "class API:\\n    @property\\n    def health(self): return True\\n"}}]}'
        if "math" in prompt.lower() or "refactor" in prompt.lower():
            return '{"steps": ["Refactor math_utils.py"], "tool_calls": [{"name": "write_file", "arguments": {"filepath": "math_utils.py", "content": "def calc_sum(): return 1 + 2\\n"}}]}'
        if "buggy.py" in prompt.lower():
            return '{"steps": ["Fix buggy syntax"], "tool_calls": [{"name": "write_file", "arguments": {"filepath": "buggy.py", "content": "def run_code():\\n    print(\'bug\')\\n"}}]}'

        return '{"steps": ["Scanned directory"], "tool_calls": []}'

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        yield self.generate(messages, **options)

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        return {
            "content": "Mock text content",
            "tool_calls": []
        }


def get_provider(config: Dict[str, Any]) -> AIProvider:
    model_name = config.get("model", "")
    provider_name = config.get("provider", "").lower()

    # Derive provider from MODEL_REGISTRY if not explicitly specified
    if not provider_name and model_name in MODEL_REGISTRY:
        provider_name = MODEL_REGISTRY[model_name]["provider"]
    if not provider_name:
        provider_name = "openai"

    # Read keys from environment
    if not config.get("api_key"):
        if provider_name == "openai":
            config["api_key"] = os.getenv("OPENAI_API_KEY", "")
        elif provider_name == "anthropic":
            config["api_key"] = os.getenv("ANTHROPIC_API_KEY", "")
        elif provider_name == "gemini":
            config["api_key"] = os.getenv("GEMINI_API_KEY", "")
        elif provider_name == "openrouter":
            config["api_key"] = os.getenv("OPENROUTER_API_KEY", "")

    if provider_name == "mock" or config.get("provider") == "mock":
        return MockProvider(config)
    elif provider_name == "openai":
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
        # Graceful fallback to OpenAICompatibleProvider for unknown custom providers
        return OpenAICompatibleProvider(config)
