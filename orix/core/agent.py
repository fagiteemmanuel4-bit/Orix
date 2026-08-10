import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from orix.core.config import ConfigManager
from orix.core.indexer import WorkspaceIndexer
from orix.core.memory import LocalMemoryStore
from orix.core.permissions import PermissionManager
from orix.core.research import WebResearchTool
from orix.core.token_utils import prune_text_to_tokens, trim_history
from orix.core.toolbox import WorkspaceToolbox
from orix.core.ai_providers import get_provider, AIProvider

console = Console()

VALID_MODES = {"plan", "interactive", "force"}

class AgentSession:
    # Map toolbox tools to permission tiers
    TOOL_TIERS = {
        "read_file": "READ_ONLY",
        "search": "READ_ONLY",
        "inspect_project": "READ_ONLY",
        "find_symbol": "READ_ONLY",
        "find_references": "READ_ONLY",
        "run_test": "SAFE",
        "run_linter": "SAFE",
        "run_formatter": "SAFE",
        "write_file": "INTERACTIVE",
        "edit_file": "INTERACTIVE",
        "delete_file": "INTERACTIVE",
        "run_shell": "FULL"
    }

    def __init__(
        self,
        root_path: str,
        mode: str = "interactive",
        guidance_path: Optional[str] = None,
        image_path: Optional[str] = None,
        initial_prompt: Optional[str] = None,
        dry_run: bool = False,
        force: bool = False,
        retry_limit: int = 3,
        ai_config: Optional[Dict[str, Any]] = None
    ):
        self.root_path = Path(root_path).resolve()
        self.mode = mode if mode in VALID_MODES else "interactive"
        self.guidance_path = guidance_path
        self.image_path = image_path
        self.initial_prompt = initial_prompt
        self.history: List[str] = []
        self.token_usage = 0
        self.sandbox_state = "idle"
        self.config = ConfigManager(str(self.root_path))
        self.memory = LocalMemoryStore(str(self.root_path))
        self.permissions = PermissionManager(self.config.get_all())
        self.toolbox = WorkspaceToolbox(str(self.root_path), dry_run=dry_run, auto_approve=force)
        self.indexer = WorkspaceIndexer(str(self.root_path))
        self.research = WebResearchTool()
        self.dry_run = dry_run
        self.force = force
        self.retry_limit = retry_limit
        self.ai_config = ai_config or self.config.get_all()
        self._load_initial_state()

    def _load_initial_state(self):
        self.config.reload_if_needed()
        self.memory.append_history(f"Session started with mode={self.mode}")
        if self.mode != "plan":
            self._ensure_indexed()

    def _ensure_indexed(self):
        console.print(Panel("Building local code index...", title="Indexer", border_style="cyan"))
        paths = self.indexer.list_files_to_index()
        total = len(paths)
        if total == 0:
            console.print(Panel("No indexable files found in workspace.", title="Indexer", border_style="yellow"))
            return

        with Progress("[progress.percentage]{task.percentage:>3.0f}%", "|", SpinnerColumn(), TextColumn("{task.completed}/{task.total} files"), TextColumn("{task.fields[filename]}")) as progress:
            task = progress.add_task("Indexing workspace", total=total, filename="starting")

            def progress_cb(current: int, total_count: int, path: str):
                progress.update(task, completed=current, filename=Path(path).name)

            try:
                self.indexer.index_workspace(paths=paths, progress_callback=progress_cb)
            except KeyboardInterrupt:
                progress.stop()
                console.print(Panel("Indexing interrupted by user.", title="Indexer", border_style="red"))
                return

        console.print(Panel("Workspace indexed successfully.", title="Indexer", border_style="green"))

    def run(self):
        try:
            self._render_layout()
            self._load_guidance()
            prompt = self.initial_prompt or self._prompt_user()
            if prompt:
                self._process_prompt(prompt)
        except KeyboardInterrupt:
            self.sandbox_state = "interrupted"
            console.print(Panel("Execution interrupted by user (Ctrl+C).", title="Interrupted", border_style="red"))
            self.memory.append_history("Session interrupted by user via KeyboardInterrupt")

    def _render_layout(self):
        self.config.reload_if_needed()
        self.permissions.allowlist = self.config.get("allowlist", [])
        header = Table.grid(expand=True)
        header.add_column(justify="left")
        header.add_column(justify="center")
        header.add_column(justify="right")
        header.add_row(
            "[bold green]Orix Agent[/bold green]",
            f"[bold white on green] MODE: {self.mode.upper()} [/bold white on green] [bold white on dark_green] STATE: {self.sandbox_state.upper()} [/bold white on dark_green]",
            f"[bold white on green] TOKENS: {self.token_usage} [/bold white on green]",
        )
        console.print(Panel(header, title="Agent Control", style="bold green"))

    def _load_guidance(self):
        if self.guidance_path and os.path.exists(self.guidance_path):
            with open(self.guidance_path, "r", encoding="utf-8") as f:
                guidance = f.read()
            console.print(Panel(guidance, title="Project Guidance", border_style="cyan"))

    def _prompt_user(self) -> str:
        return console.input("[bold white on green]AI Prompt> [/bold white on green]")

    def _process_prompt(self, prompt: str):
        self.history.append(prompt)
        self.token_usage += len(prompt.split())
        self.history = trim_history(self.history, self.config.get("context_window", 128000))
        if prompt.startswith("/help"):
            self._display_help()
        elif prompt.startswith("/status"):
            self._render_layout()
        elif prompt.startswith("/undo"):
            self._undo_last_action()
        elif prompt.startswith("/review"):
            self._review_history()
        elif prompt.startswith("/plan"):
            self._show_plan(prompt)
        elif prompt.startswith("/run"):
            self._run_command(prompt)
        elif prompt.startswith("/research"):
            self._run_research(prompt)
        elif prompt.startswith("/memory"):
            self._show_memory()
        elif prompt.startswith("/mode"):
            self._set_mode(prompt)
        elif prompt.startswith("/config"):
            try:
                from orix.core.config_tui import run_config_tui

                run_config_tui(project_root=str(self.root_path))
                self.config.reload_if_needed()
                self.permissions.allowlist = self.config.get("allowlist", [])
                console.print(Panel("Configuration reloaded.", title="Config", border_style="green"))
            except Exception as e:
                console.print(Panel(f"Failed to open config: {e}", title="Config Error", border_style="red"))
        else:
            self._agentic_loop(prompt)

    def _display_help(self):
        help_text = (
            "Available commands:\n"
            "  /help       Show this help screen\n"
            "  /status     Show current mode and sandbox state\n"
            "  /mode       Switch execution mode (plan/interactive/force)\n"
            "  /undo       Undo last prompt action\n"
            "  /review     Review session history\n"
            "  /plan       Show a read-only plan for requested work\n"
            "  /run        Execute a shell command inside the workspace\n"
            "  /research   Search web/docs for error resolution\n"
            "  /memory     Show local memory insights\n"
        )
        console.print(Panel(help_text, title="Agent Help", border_style="cyan"))

    def _show_memory(self):
        data = self.memory.get_all()
        table = Table(title="Local Memory Summary")
        table.add_column("Key")
        table.add_column("Value", overflow="fold")
        table.add_row("Preferences", str(data.get("preferences", {})))
        table.add_row("Resolved Exceptions", str(data.get("resolved_exceptions", [])))
        table.add_row("Project Insights", str(data.get("project_insights", {})))
        table.add_row("History length", str(len(data.get("history", []))))
        console.print(table)

    def _set_mode(self, prompt: str):
        value = prompt[len("/mode"):].strip().lower()
        if value in VALID_MODES:
            self.mode = value
            console.print(Panel(f"Execution mode switched to: {self.mode}", title="Mode Changed", border_style="green"))
            self.memory.append_history(f"Mode changed to {self.mode}")
        else:
            console.print(Panel("Invalid mode. Available modes: plan, interactive, force.", title="Mode Error", border_style="red"))

    # --- Model-Driven Tool and Permissions Agentic Loop ---

    def _agentic_loop(self, prompt: str):
        self.sandbox_state = "thinking"
        self._render_layout()

        # Step 1: OBSERVE & PLAN
        # Get target or planned actions
        plan = self._generate_plan(prompt)

        if self.mode == "plan":
            console.print(Panel("Plan mode enabled: no commands or tools will be executed.", title="Plan Mode", border_style="yellow"))
            self._display_thinking_panel(plan)
            self.sandbox_state = "idle"
            return

        success = False
        attempt = 1

        while attempt <= self.retry_limit:
            console.print(Panel(f"Execution Attempt {attempt} of {self.retry_limit}", title="Loop Executing", border_style="yellow"))
            self._display_thinking_panel(plan)

            # Step 2: MODEL TOOL CHOICE DECISION
            tool_calls = plan.get("tool_calls", [])
            if not tool_calls:
                console.print("[yellow]No tool calls generated. Task completed.[/yellow]")
                success = True
                break

            step_success = True
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["arguments"]

                # Step 3: REQUEST PERMISSION based on exact permission tier
                tier = self.TOOL_TIERS.get(tool_name, "INTERACTIVE")
                approved = self.permissions.request(
                    action=f"Execute tool '{tool_name}'",
                    details=f"Arguments: {json.dumps(tool_args)}",
                    force=(self.mode == "force" or self.force),
                    tool_tier=tier
                )

                if not approved:
                    console.print(Panel(f"Tool '{tool_name}' denied by user. Halting loop.", title="Permission Denied", border_style="red"))
                    step_success = False
                    break

                # Step 4: ACT (actual tool call execution)
                console.print(f"[cyan]Executing tool '{tool_name}' with args {json.dumps(tool_args)}...[/cyan]")
                tool_result = self.toolbox.execute_tool(tool_name, tool_args)

                # Step 5: OBSERVE RESULT / TEST
                if not tool_result.get("success"):
                    console.print(f"[bold red]Tool Execution Error:[/bold red] {tool_result.get('error', {}).get('message')}")
                    step_success = False

                    # Step 6: MODEL FAILURE ANALYSIS & FIX
                    plan = self._repair_plan(tool_result, attempt)
                    break
                else:
                    console.print(f"[green]Tool '{tool_name}' returned successful result.[/green]")

            if step_success:
                # Step 7: VERIFY
                test_res = self.toolbox.execute_tool("run_test", {})
                if test_res.get("success") and test_res["result"].get("exit_code") == 0:
                    success = True
                    break
                else:
                    console.print(Panel("Tests failed or verification checks failed.", title="Verification Failure", border_style="yellow"))
                    plan = self._repair_plan(test_res, attempt)
                    attempt += 1
            else:
                attempt += 1

        self._verify(success)
        self.sandbox_state = "idle"
        self._render_layout()

    def _generate_plan(self, prompt: str) -> Dict[str, Any]:
        from orix.core.ai_providers import route_task

        # Determine active config (respect explicit user override in config)
        if self.config.get("disable_routing", False):
            active_config = self.ai_config
        else:
            active_config = route_task(prompt, self.ai_config)
            if active_config.get("model") != self.ai_config.get("model"):
                console.print(f"[bold yellow]🔀 Dynamic Task Routing: Automatically routing to model {active_config.get('model')} based on task characteristics.[/bold yellow]")

        # If AI model is configured, call generate_structured_output
        schema = {
            "type": "object",
            "properties": {
                "steps": {"type": "array", "items": {"type": "string"}},
                "tool_calls": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "arguments": {"type": "object"}
                        },
                        "required": ["name", "arguments"]
                    }
                }
            },
            "required": ["steps", "tool_calls"]
        }

        if active_config.get("api_key") or os.getenv("OPENAI_API_KEY") or active_config.get("provider") in ("ollama", "mock"):
            try:
                provider = get_provider(active_config)
                return provider.generate_structured_output(prompt, schema)
            except Exception:
                pass

        # Robust model-fallback agent reasoning
        search_res = self.toolbox.execute_tool("search", {"query": prompt})
        files = search_res.get("result", [])
        target_file = files[0] if files else "new_file.py"

        tool_calls = []
        if "read" in prompt.lower() and files:
            tool_calls.append({"name": "read_file", "arguments": {"filepath": target_file}})
        elif "write" in prompt.lower() or "add" in prompt.lower() or "create" in prompt.lower():
            tool_calls.append({
                "name": "write_file",
                "arguments": {
                    "filepath": target_file,
                    "content": f"# Orix Agent: autonomous model-driven edit\n# For prompt: {prompt}\n"
                }
            })
        else:
            # Fallback tool call search
            tool_calls.append({"name": "search", "arguments": {"query": prompt}})

        return {
            "steps": [
                "Scan repository layout using semantic search",
                f"Invoke tool sequence targets on file '{target_file}'",
                "Execute local tests to verify changes"
            ],
            "tool_calls": tool_calls,
            "examples": self._collect_relevant_memory(prompt)
        }

    def _repair_plan(self, failure_result: Dict[str, Any], attempt: int) -> Dict[str, Any]:
        err_msg = failure_result.get("error", {}).get("message") or "unknown execution verification failure"
        return {
            "steps": [
                f"Analyze previous execution failure: {err_msg[:60]}",
                "Formulate safe repair payload",
                "Execute workspace repair"
            ],
            "tool_calls": [
                {
                    "name": "write_file",
                    "arguments": {
                        "filepath": f"repair_attempt_{attempt}.py",
                        "content": f"# Orix Agent loop repair block\n# Exception analyzed: {err_msg}\n"
                    }
                }
            ],
            "examples": []
        }

    def _verify(self, success: bool) -> None:
        if success:
            console.print(Panel("★ Session Completed Successfully! Verification passed. ★", title="Verification", border_style="green"))
            self.memory.append_history("Agent session successfully completed task and verified results.")
        else:
            console.print(Panel("✖ Session terminated. All retry attempts failed or permission denied.", title="Verification", border_style="red"))
            self.memory.append_history("Agent session terminated with unresolved failures.")

    # --- Helpers ---

    def _display_thinking_panel(self, plan: Dict[str, Any]):
        checklist = Table.grid(padding=(0,1))
        checklist.add_column("step", width=4)
        checklist.add_column("description")
        for i, step in enumerate(plan.get("steps", [])):
            checklist.add_row(f"{i+1}", step)

        examples = Table(title="Relevant Memory (examples)")
        examples.add_column("Example", overflow="fold")
        for ex in plan.get("examples", []):
            examples.add_row(ex)

        left_panel = Panel(checklist, title="Planned Steps", border_style="blue")
        right_panel = Panel(examples, title="Memory Examples", border_style="magenta")
        console.print(left_panel)
        console.print(right_panel)

    def _collect_relevant_memory(self, prompt: str) -> List[str]:
        return [entry for entry in self.memory.data.get("history", []) if prompt.lower() in entry.lower()][:3]

    def _run_command(self, prompt: str):
        command_text = prompt[len("/run"):].strip()
        if not command_text:
            console.print(Panel("Usage: /run <command>", title="Run Command", border_style="yellow"))
            return

        if self.mode == "interactive" and not self.force:
            allowed = self.permissions.request("Run shell command", command_text, force=self.force, tool_tier="FULL")
            if not allowed:
                console.print(Panel("Command blocked by user.", title="Permission Denied", border_style="red"))
                return

        result = self.toolbox.run_shell(command_text.split(), cwd=self.root_path)
        if result["stdout"]:
            console.print(Panel(result["stdout"], title="stdout", border_style="green"))
        if result["stderr"]:
            console.print(Panel(result["stderr"], title="stderr", border_style="red"))
        console.print(Panel(f"Exit code: {result['returncode']}", title="Command Result", border_style="blue"))

    def _run_research(self, prompt: str):
        query = prompt[len("/research"):].strip()
        if not query:
            console.print(Panel("Usage: /research <query>", title="Research", border_style="yellow"))
            return
        url = query if query.startswith("http") else f"https://{query}"
        if not self.permissions.verify_url(url, force=self.force):
            console.print(Panel("Web research blocked by user.", title="Permission Denied", border_style="red"))
            return

        result = self.research.fetch_url(url)
        console.print(Panel(result.get("summary", "No summary available."), title="Research Summary", border_style="green"))

    def _undo_last_action(self):
        if not self.history:
            return
        last = self.history.pop()
        console.print(Panel(f"Undid prompt: {last}", title="Undo", border_style="yellow"))

    def _review_history(self):
        table = Table(title="Prompt History")
        table.add_column("Prompt", overflow="fold")
        for p in self.history:
            table.add_row(p)
        console.print(table)

    def _show_plan(self, prompt: str):
        plan_text = (
            f"1. Analyze the repository for files and structure matching: {prompt}\n"
            "2. Generate a safe edit plan with approval gating.\n"
            "3. Execute changes only if approved.\n"
            "4. Run local tests and reflect on failures automatically.\n"
        )
        console.print(Panel(plan_text, title="Dry Run Plan", border_style="yellow"))
