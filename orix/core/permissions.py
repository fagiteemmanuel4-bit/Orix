import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel

console = Console()

class PermissionManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.allowlist = config.get("allowlist", [])

    def is_allowed_domain(self, url: str) -> bool:
        return any(url.startswith(domain) for domain in self.allowlist)

    def request(self, action: str, details: str, force: bool = False) -> bool:
        if force:
            return True
        prompt = (
            "≽^•⩊•^≼ ⚠️  PERMISSIONS ALERT // ACTION REQUIRED\n\n"
            f"[ SYSTEM ] AI wants to perform: {action}\n\n"
            f"{details}\n\n"
            "👉 Allow this action? [Y]es / [N]o / [P]lan-Only: "
        )
        answer = console.input(f"[bold cyan]{prompt}[/bold cyan]")
        normalized = answer.strip().lower()
        if normalized in ["y", "yes"]:
            return True
        if normalized in ["p", "plan-only", "plan"]:
            return False
        return False

    def verify_url(self, url: str, force: bool = False) -> bool:
        if self.is_allowed_domain(url):
            return True
        return self.request(
            "Access external URL",
            f"[ WEB ] AI requests permission to fetch: {url}",
            force=force,
        )

    def verify_high_risk(self, description: str, force: bool = False) -> bool:
        return self.request("High-risk operation", description, force=force)
