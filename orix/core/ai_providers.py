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

    def _get_resolved_model(self) -> str:
        pname = self.config.get("provider", "openai").lower()
        if pname == "mock":
            return "mock-model"
        if pname == "openai":
            return self.model or "gpt-4o-mini"
        if pname == "anthropic":
            return self.model or "claude-3-5-sonnet-20241022"
        if pname == "gemini":
            return self.model or "gemini-1.5-flash"
        if pname == "ollama":
            return self.model or "llama3"
        return self.model or "unknown-model"

    def post_generate_log(self, messages: List[Dict[str, str]], response: str):
        from orix.core.token_utils import count_tokens
        from orix.core.cost_tracker import CostTracker

        provider_name = self.config.get("provider", "openai")
        model_name = self._get_resolved_model()

        # Concat all messages for prompt text
        prompt_text = "\n".join([m.get("content", "") for m in messages])
        in_tokens = count_tokens(prompt_text)
        out_tokens = count_tokens(response)

        tracker = CostTracker(self.config.get("workspace_root", os.getcwd()))
        tracker.log_transaction(provider_name, model_name, in_tokens, out_tokens)

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
        res_text = resp.json()["choices"][0]["message"]["content"]
        self.post_generate_log(messages, res_text)
        return res_text

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
        accumulated = []
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
                            accumulated.append(delta)
                            yield delta
                    except Exception:
                        pass
        self.post_generate_log(messages, "".join(accumulated))

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
        res_text = msg.get("content", "")
        self.post_generate_log(messages, res_text + json.dumps(tool_calls))
        return {
            "content": res_text,
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
        res_text = resp.json()["content"][0]["text"]
        self.post_generate_log(messages, res_text)
        return res_text

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        res_text = self.generate(messages, **options)
        yield res_text

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
        self.post_generate_log(messages, content + json.dumps(tool_calls))
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
        res_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        self.post_generate_log(messages, res_text)
        return res_text

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        res_text = self.generate(messages, **options)
        yield res_text

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        res_text = self.generate(messages)
        return {"content": res_text, "tool_calls": []}


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
        res_text = resp.json()["choices"][0]["message"]["content"]
        self.post_generate_log(messages, res_text)
        return res_text

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        res_text = self.generate(messages, **options)
        yield res_text

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        res_text = self.generate(messages)
        return {"content": res_text, "tool_calls": []}


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
        res_text = resp.json()["response"]
        self.post_generate_log(messages, res_text)
        return res_text

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        res_text = self.generate(messages, **options)
        yield res_text

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        res_text = self.generate(messages)
        return {"content": res_text, "tool_calls": []}


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
        res_text = resp.json()["choices"][0]["message"]["content"]
        self.post_generate_log(messages, res_text)
        return res_text

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        res_text = self.generate(messages, **options)
        yield res_text

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        res_text = self.generate(messages)
        return {"content": res_text, "tool_calls": []}


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
            response = '{"steps": ["Check assertions"], "tool_calls": [{"name": "write_file", "arguments": {"filepath": "test_runner.py", "content": "def test_assert():\\n    assert True\\n"}}]}'
        elif "endpoint" in prompt.lower() or "app.py" in prompt.lower():
            response = '{"steps": ["Add health endpoint"], "tool_calls": [{"name": "write_file", "arguments": {"filepath": "app.py", "content": "class API:\\n    @property\\n    def health(self): return True\\n"}}]}'
        elif "math" in prompt.lower() or "refactor" in prompt.lower():
            response = '{"steps": ["Refactor math_utils.py"], "tool_calls": [{"name": "write_file", "arguments": {"filepath": "math_utils.py", "content": "def calc_sum(): return 1 + 2\\n"}}]}'
        elif "buggy.py" in prompt.lower():
            response = '{"steps": ["Fix buggy syntax"], "tool_calls": [{"name": "write_file", "arguments": {"filepath": "buggy.py", "content": "def run_code():\\n    print(\'bug\')\\n"}}]}'
        else:
            response = '{"steps": ["Scanned directory"], "tool_calls": []}'

        self.post_generate_log(messages, response)
        return response

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        res_text = self.generate(messages, **options)
        yield res_text

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        response = "Mock text content"
        self.post_generate_log(messages, response)
        return {
            "content": response,
            "tool_calls": []
        }


# --- FAILOVER & HYBRID DYNAMIC ROUTING ADAPTERS ---

class RoutingProvider(AIProvider):
    def __init__(self, target_provider: AIProvider, fallback_provider: Optional[AIProvider] = None):
        super().__init__(target_provider.config)
        self.target = target_provider
        self.fallback = fallback_provider or OllamaProvider({"provider": "ollama", "model": "llama3"})

    def validate_connection(self) -> bool:
        return self.target.validate_connection()

    def list_models(self) -> List[str]:
        return self.target.list_models()

    def generate(self, messages: List[Dict[str, str]], **options) -> str:
        try:
            return self.target.generate(messages, **options)
        except Exception as e:
            # Check if local fallback is available and route
            if self.fallback.validate_connection():
                from rich.console import Console
                Console().print(f"\n[bold yellow]⚠️  Remote provider failure: {e}. Falling back to Local Ollama model (llama3)...[/bold yellow]\n")
                return self.fallback.generate(messages, **options)
            raise e

    def stream(self, messages: List[Dict[str, str]], **options) -> Generator[str, None, None]:
        try:
            yield from self.target.stream(messages, **options)
        except Exception as e:
            if self.fallback.validate_connection():
                from rich.console import Console
                Console().print(f"\n[bold yellow]⚠️  Remote provider failure: {e}. Falling back to Local Ollama model (llama3)...[/bold yellow]\n")
                yield from self.fallback.stream(messages, **options)
            else:
                raise e

    def generate_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], **options) -> Dict[str, Any]:
        try:
            return self.target.generate_with_tools(messages, tools, **options)
        except Exception as e:
            if self.fallback.validate_connection():
                from rich.console import Console
                Console().print(f"\n[bold yellow]⚠️  Remote provider failure: {e}. Falling back to Local Ollama...[/bold yellow]\n")
                return self.fallback.generate_with_tools(messages, tools, **options)
            raise e


def route_task(prompt: str, ai_config: Dict[str, Any]) -> Dict[str, Any]:
    """Dynamically route task to cheap vs reasoning models based on complexity.

    - Complexity-focused keywords ('architect', 'refactor', 'design') route to claude-3-5-sonnet.
    - Coding/Syntactic keywords route to gpt-4o-mini.
    - Fallback defaults to gpt-4o-mini or configured provider.
    """
    config_copy = ai_config.copy()
    prompt_lower = prompt.lower()

    if any(k in prompt_lower for k in ["architect", "design", "refactor structure", "security"]):
        config_copy["provider"] = "anthropic"
        config_copy["model"] = "claude-3-5-sonnet-20241022"
    elif any(k in prompt_lower for k in ["write", "syntax", "add test", "mock", "fix"]):
        config_copy["provider"] = "openai"
        config_copy["model"] = "gpt-4o-mini"

    return config_copy


def get_provider(config: Dict[str, Any]) -> AIProvider:
    provider_name = config.get("provider", "openai").lower()

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

    if config.get("provider") == "mock":
        raw_provider = MockProvider(config)
    elif provider_name == "openai":
        raw_provider = OpenAIProvider(config)
    elif provider_name == "anthropic":
        raw_provider = AnthropicProvider(config)
    elif provider_name == "gemini":
        raw_provider = GeminiProvider(config)
    elif provider_name == "openrouter":
        raw_provider = OpenRouterProvider(config)
    elif provider_name == "ollama":
        raw_provider = OllamaProvider(config)
    elif provider_name == "openai-compatible":
        raw_provider = OpenAICompatibleProvider(config)
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")

    # Wrap remote cloud providers in RoutingProvider fallback handler
    if provider_name not in ("mock", "ollama"):
        return RoutingProvider(raw_provider)
    return raw_provider
