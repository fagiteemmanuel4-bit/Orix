import os
import sys
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

console = Console()

VALID_MODES = {"plan", "interactive", "force"}

class AgentSession:
    def __init__(
        self,
        root_path: str,
        mode: str = "interactive",
        guidance_path: Optional[str] = None,
        image_path: Optional[str] = None,
        initial_prompt: Optional[str] = None,
        dry_run: bool = False,
        force: bool = False,
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
        self.memory = LocalMemoryStore()
        self.permissions = PermissionManager(self.config.get_all())
        self.toolbox = WorkspaceToolbox(root_path, dry_run=dry_run, auto_approve=force)
        self.indexer = WorkspaceIndexer(root_path)
        self.research = WebResearchTool()
        self.dry_run = dry_run
        self.force = force
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
            # gracefully save state
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
        console.print(Panel("Use /help, /status, /plan, /run, /research, /memory, /review, /undo. High-risk actions require explicit approval unless in force mode.", style="cyan"))

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
            # Launch in-session config editor and reload config
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

    def _agentic_loop(self, prompt: str):
        self.sandbox_state = "thinking"
        self._render_layout()
        plan = self._plan(prompt)
        self._display_thinking_panel(plan)

        if self.mode == "plan":
            console.print(Panel("Plan mode enabled: no commands or modifications will be executed.", title="Plan Mode", border_style="yellow"))
            self.sandbox_state = "idle"
            return

        execute_result = self._execute_plan(plan)
        if execute_result.get("success"):
            reflect = self._reflect(prompt, execute_result)
            console.print(Panel(reflect, title="Reflection", border_style="green"))
        self.sandbox_state = "idle"
        self._render_layout()

    def _plan(self, prompt: str) -> Dict[str, Any]:
        return {
            "prompt": prompt,
            "steps": [
                "Analyze repository and relevant code structure.",
                "Generate a safe code edit plan or command sequence.",
                "Evaluate risk and require approval if needed.",
            ],
            "examples": self._collect_relevant_memory(prompt),
        }

    def _display_thinking_plan(self, plan: Dict[str, Any]):
        # kept for backwards compatibility
        lines = [f"{idx + 1}. {step}" for idx, step in enumerate(plan["steps"])]
        content = "\n".join(lines)
        console.print(Panel(content, title="Thinking & Planning", border_style="blue"))

    def _display_thinking_panel(self, plan: Dict[str, Any]):
        # Rich multi-column planning overview with checklist and examples
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
        console.print(Panel("Agent will attempt autonomous retries on failures; high-risk actions will ask for approval.", title="Notes", border_style="yellow"))

    def _collect_relevant_memory(self, prompt: str) -> List[str]:
        return [entry for entry in self.memory.data.get("history", []) if prompt.lower() in entry.lower()][:3]

    def _execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        self.sandbox_state = "executing"
        self._render_layout()

        files = self.toolbox.search_code(plan["prompt"])
        if not files:
            return {"success": False, "error": "No files found matching prompt."}

        target_file = files[0]
        original = self.toolbox.read_file(str(target_file))
        changed = original + "\n# Orix AI agent applied changes\n"
        diff = self.toolbox.compute_diff(original, changed, str(target_file))
        self._show_code_diff(diff)

        if self.dry_run:
            return {"success": True, "dry_run": True, "diff": diff}

        needs_approval = self.mode == "interactive" and not self.force
        can_apply = not needs_approval or self._prompt_approval(target_file, diff)
        if not can_apply:
            return {"success": False, "error": "User declined approval."}

        path, file_diff = self.toolbox.write_file(str(target_file), changed)
        self.memory.append_history(f"Applied change to {path}")
        result = self._run_safely(["python", "-m", "pytest"], cwd=self.root_path)
        return {"success": result["returncode"] == 0, "command_result": result, "diff": file_diff}

    def _reflect(self, prompt: str, execution: Dict[str, Any]) -> str:
        if execution.get("success"):
            if execution.get("dry_run"):
                return "Dry run completed successfully; no changes were written."
            return "Execution completed successfully and the agent learned from the result."

        error = execution.get("command_result", {}).get("stderr") or execution.get("error")
        self.memory.record_exception(str(error), "Agent reflection required a retry path.")
        if execution.get("command_result"):
            self._handle_execution_failure(execution["command_result"])
        return f"Execution failed. The agent captured the failure for self-correction: {error}"

    def _run_safely(self, command: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        result = self.toolbox.run_shell(command, cwd=cwd)
        if result["returncode"] != 0 and self.mode != "plan":
            self._capture_failure(result)
        return result

    def _capture_failure(self, result: Dict[str, Any]) -> None:
        summary = f"Command failed: {result['command']} | code={result['returncode']}"
        self.memory.append_history(summary)
        self.memory.record_exception(result["stderr"], "Retry path recorded")
        self.memory.append_history(prune_text_to_tokens(result["stderr"], self.config.get("context_window", 128000)))

    def _handle_execution_failure(self, result: Dict[str, Any]) -> None:
        if self.mode == "force":
            console.print(Panel("Auto-retrying failed command in force mode.", border_style="yellow"))
            self._run_safely(result["command"].split(), cwd=self.root_path)
        else:
            console.print(Panel("Execution failed and will be used to correct the next plan.", border_style="yellow"))

    def _prompt_approval(self, path: Path, diff: str) -> bool:
        if self.mode == "force":
            return True
        answer = console.input(f"[bold cyan]Apply changes to {path}? [Y/n] [/bold cyan]")
        return answer.strip().lower() in ["y", "yes", ""]

    def _run_command(self, prompt: str):
        if self.mode == "plan":
            console.print(Panel("Run commands are disabled in plan mode.", title="Plan Mode", border_style="yellow"))
            return

        command_text = prompt[len("/run"):].strip()
        if not command_text:
            console.print(Panel("Usage: /run <command>", title="Run Command", border_style="yellow"))
            return

        if self.mode == "interactive" and not self.force:
            allowed = self.permissions.verify_high_risk(f"Run shell command: {command_text}", force=self.force)
            if not allowed:
                console.print(Panel("Command blocked by user.", title="Permission Denied", border_style="red"))
                return

        result = self._run_safely(command_text.split(), cwd=self.root_path)
        self._show_command_output(result)

    def _run_research(self, prompt: str):
        query = prompt[len("/research"):].strip()
        if not query:
            console.print(Panel("Usage: /research <query>", title="Research", border_style="yellow"))
            return
        if self.mode == "plan":
            console.print(Panel("Research is disabled in plan mode.", title="Plan Mode", border_style="yellow"))
            return

        url = query if query.startswith("http") else f"https://{query}"
        if not self.permissions.verify_url(url, force=self.force):
            console.print(Panel("Web research blocked by user.", title="Permission Denied", border_style="red"))
            return

        result = self.research.fetch_url(url)
        console.print(Panel(result.get("summary", "No summary available."), title="Research Summary", border_style="green"))
        if result.get("error"):
            console.print(Panel(result["error"], title="Research Error", border_style="red"))

    def _show_live_feed(self, lines: List[str]):
        for line in lines:
            console.print(f"[bold cyan]>[/bold cyan] {line}")

    def _show_code_diff(self, diff_text: str):
        syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, title="Preview Diff", border_style="green"))

    def _show_command_output(self, result: Dict[str, Any]):
        if result["stdout"]:
            console.print(Panel(result["stdout"], title="stdout", border_style="green"))
        if result["stderr"]:
            console.print(Panel(result["stderr"], title="stderr", border_style="red"))
        console.print(Panel(f"Exit code: {result['returncode']}", title="Command Result", border_style="blue"))

    def _undo_last_action(self):
        if not self.history:
            console.print(Panel("No actions to undo.", title="Undo", border_style="red"))
            return
        last = self.history.pop()
        self.token_usage = max(0, self.token_usage - len(last.split()))
        console.print(Panel(f"Undid prompt: {last}", title="Undo", border_style="yellow"))

    def _review_history(self):
        table = Table(title="Prompt History")
        table.add_column("Prompt", overflow="fold")
        for prompt in self.history:
            table.add_row(prompt)
        console.print(table)

    def _show_plan(self, prompt: str):
        plan_text = (
            f"1. Analyze the repository for files and structure matching: {prompt}\n"
            "2. Generate a safe edit plan with approval gating.\n"
            "3. Execute changes only if approved.\n"
            "4. Run local tests and reflect on failures automatically.\n"
        )
        console.print(Panel(plan_text, title="Dry Run Plan", border_style="yellow"))
