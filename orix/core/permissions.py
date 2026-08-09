import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel

console = Console()

class PermissionManager:
    # Tier mapping
    TIERS = {
        "READ_ONLY": 1,
        "SAFE": 2,
        "INTERACTIVE": 3,
        "FULL": 4
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.allowlist = config.get("allowlist", [])
        # Default tier level is INTERACTIVE (forces prompts for write/shell actions)
        self.level = config.get("permission_level", "INTERACTIVE").upper()
        if self.level not in self.TIERS:
            self.level = "INTERACTIVE"

    def is_allowed_domain(self, url: str) -> bool:
        return any(url.startswith(domain) for domain in self.allowlist)

    def request(self, action: str, details: str, force: bool = False, tool_tier: str = "INTERACTIVE") -> bool:
        if force or self.level == "FULL":
            return True

        # Check if the requested tool tier is within the configured allowed permission level
        user_level_num = self.TIERS.get(self.level, 3)
        tool_level_num = self.TIERS.get(tool_tier, 3)

        if tool_level_num <= user_level_num and tool_level_num <= 2:
            # READ_ONLY and SAFE tools are automatically approved in SAFE/INTERACTIVE/FULL modes
            return True

        # Prompt for higher tier actions if in INTERACTIVE mode
        prompt = (
            "≽^•⩊•^≼ ⚠️  PERMISSIONS GATE ALERT // ACTION REQUIRED\n\n"
            f"[ SYSTEM ] AI wants to execute: {action} ({tool_tier} tier)\n\n"
            f"{details}\n\n"
            "👉 Allow this action? [Y]es / [N]o: "
        )
        answer = console.input(f"[bold cyan]{prompt}[/bold cyan]")
        normalized = answer.strip().lower()
        if normalized in ["y", "yes"]:
            return True
        return False

    def verify_url(self, url: str, force: bool = False) -> bool:
        if self.is_allowed_domain(url):
            return True
        return self.request(
            "Access external URL",
            f"[ WEB ] AI requests permission to fetch: {url}",
            force=force,
            tool_tier="INTERACTIVE"
        )

    def verify_high_risk(self, description: str, force: bool = False) -> bool:
        return self.request("High-risk operation", description, force=force, tool_tier="FULL")
