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
        retry_limit: int = 3
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
        self.toolbox = WorkspaceToolbox(str(self.root_path), dry_run=dry_run, auto_approve=force)
        self.indexer = WorkspaceIndexer(str(self.root_path))
        self.research = WebResearchTool()
        self.dry_run = dry_run
        self.force = force
        self.retry_limit = retry_limit
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

    # --- Improved Agent Loop: OBSERVE -> PLAN -> REQUEST PERMISSION -> ACT -> TEST -> OBSERVE RESULT -> FIX -> VERIFY ---

    def _agentic_loop(self, prompt: str):
        self.sandbox_state = "thinking"
        self._render_layout()

        # Step 1: OBSERVE
        observation = self._observe(prompt)

        # Step 2: PLAN
        plan = self._plan(observation, prompt)

        if self.mode == "plan":
            console.print(Panel("Plan mode enabled: no changes will be executed.", title="Plan Mode", border_style="yellow"))
            self._display_thinking_panel(plan)
            self.sandbox_state = "idle"
            return

        # Execute Loop
        success = False
        attempt = 1

        while attempt <= self.retry_limit:
            console.print(Panel(f"Execution Attempt {attempt} of {self.retry_limit}", title="Loop Executing", border_style="yellow"))
            self._display_thinking_panel(plan)

            # Step 3: REQUEST PERMISSION
            approved = self._request_permission(plan)
            if not approved:
                console.print(Panel("Operation denied by user. Halting loop.", title="Permission Denied", border_style="red"))
                break

            # Step 4: ACT
            action_result = self._act(plan)
            if not action_result.get("success"):
                console.print(Panel(f"Action failed: {action_result.get('error')}", title="Action Failed", border_style="red"))
                # Go to fix step
                plan = self._fix(action_result)
                attempt += 1
                continue

            # Step 5: TEST
            test_res = self._test()

            # Step 6: OBSERVE RESULT
            test_passed = self._observe_result(test_res)
            if test_passed:
                success = True
                break
            else:
                # Step 7: FIX
                console.print(Panel("Test failures detected. Invoking FIX step...", title="Self-Correction", border_style="yellow"))
                plan = self._fix(test_res)
                attempt += 1

        # Step 8: VERIFY
        self._verify(success)
        self.sandbox_state = "idle"
        self._render_layout()

    def _observe(self, prompt: str) -> Dict[str, Any]:
        # Search workspace for matching code files
        search_res = self.toolbox.execute_tool("search", {"query": prompt})
        files = search_res.get("result", [])
        return {
            "query": prompt,
            "relevant_files": files,
            "system_info": {
                "cwd": str(self.root_path),
                "mode": self.mode
            }
        }

    def _plan(self, observation: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        files = observation.get("relevant_files", [])
        target_file = files[0] if files else "new_file.py"

        return {
            "prompt": prompt,
            "target_file": target_file,
            "action_type": "write_file",
            "proposed_changes": f"# Orix Agent: implementation of prompt: {prompt}\n",
            "steps": [
                f"Observe project environment (Relevant files: {', '.join(files[:3]) if files else 'none'})",
                f"Apply target modification on '{target_file}'",
                "Execute workspace test suites",
                "Verify correctness and correct if necessary"
            ],
            "examples": self._collect_relevant_memory(prompt)
        }

    def _request_permission(self, plan: Dict[str, Any]) -> bool:
        if self.mode == "force" or self.force:
            return True
        target = plan.get("target_file", "workspace")
        action = plan.get("action_type", "modification")
        return self.permissions.request(
            f"{action} on {target}",
            f"Agent proposes '{action}' to implement technical solution."
        )

    def _act(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        self.sandbox_state = "executing"
        target_file = plan["target_file"]
        proposed = plan["proposed_changes"]

        # Safe read existing content to preserve or append
        existing = ""
        try:
            read_res = self.toolbox.execute_tool("read_file", {"filepath": target_file})
            if read_res.get("success"):
                existing = read_res["result"]
        except Exception:
            pass

        full_content = existing + "\n" + proposed if existing else proposed

        # Execute tool write_file
        res = self.toolbox.execute_tool("write_file", {
            "filepath": target_file,
            "content": full_content
        })
        return res

    def _test(self) -> Dict[str, Any]:
        # Execute run_test tool
        res = self.toolbox.execute_tool("run_test", {})
        return res

    def _observe_result(self, test_res: Dict[str, Any]) -> bool:
        if not test_res.get("success"):
            return False
        res_data = test_res.get("result", {})
        exit_code = res_data.get("exit_code", 1)
        return exit_code == 0

    def _fix(self, failure_details: Dict[str, Any]) -> Dict[str, Any]:
        err_msg = failure_details.get("error", {}).get("message") or failure_details.get("result", {}).get("stderr") or "unknown execution failure"
        self.memory.record_exception(str(err_msg), "Agent session failed a step and initiated fix sequence.")

        # Produce a corrected plan
        return {
            "prompt": "Fix previous execution failure",
            "target_file": "agent_session_fix.py",
            "action_type": "write_file",
            "proposed_changes": f"# Orix Agent: Auto-fix attempt for error: {err_msg[:60]}\n",
            "steps": [
                "Re-analyze files",
                "Apply correction payload",
                "Re-run test suite"
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

    # --- Backwards Compatibility & Helpers ---

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
            allowed = self.permissions.verify_high_risk(f"Run shell command: {command_text}", force=self.force)
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
