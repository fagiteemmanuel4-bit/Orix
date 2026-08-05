import os
from typing import Dict, Any
from pathlib import Path
import questionary
from orix.core.config import ConfigManager


DEFAULT_ROLES = [
    ("MANAGER", "Manager"),
    ("DEV_1", "Dev_1"),
    ("DEV_2", "Dev_2"),
    ("TESTER", "Tester"),
    ("SECURITY", "Security"),
]


def run_config_tui(project_root: str = None) -> Dict[str, Any]:
    project_root = project_root or os.getcwd()
    cfg = ConfigManager(project_root)
    existing = cfg.get_all()

    print("\n=== Orix CLI Team Configuration ===\n")
    agents = {}
    for key, label in DEFAULT_ROLES:
        use = questionary.confirm(f"Configure role {label}?", default=True).ask()
        if not use:
            continue
        provider = questionary.select(
            f"{label} provider:",
            choices=["Anthropic", "OpenAI", "OpenRouter", "DeepSeek", "Groq", "Local-Ollama", "Other"],
            default=(existing.get("agents", {}).get(key, {}).get("provider") if existing.get("agents") else None),
        ).ask()
        model = questionary.text(f"{label} model id:", default=(existing.get("agents", {}).get(key, {}).get("model") if existing.get("agents") else "")).ask()
        api_key = questionary.text(f"{label} API key (leave blank to skip):", default="").ask()
        base_url = None
        if provider and provider.lower().startswith("local") or provider.lower().startswith("openrouter") or provider.lower().startswith("other"):
            base_url = questionary.text(f"{label} base URL (optional):", default=(existing.get("agents", {}).get(key, {}).get("base_url") if existing.get("agents") else "")).ask()

        agents[key] = {
            "label": label,
            "provider": provider,
            "model": model,
        }
        if api_key:
            agents[key]["api_key"] = api_key
        if base_url:
            agents[key]["base_url"] = base_url

    cfg_data = existing.copy()
    cfg_data["agents"] = agents
    confirm = questionary.confirm("Save configurations & launch?", default=True).ask()
    if confirm:
        cfg.save(cfg_data)
        print("Configuration saved to:", cfg.user_config)
    else:
        print("Configuration not saved.")

    return cfg_data
