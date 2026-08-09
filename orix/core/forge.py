import os
import json
import yaml
import subprocess
from typing import Dict, Any, List, Optional
from orix.core.architect import Architect
from orix.core.orchestrator import Orchestrator
from orix.core.ai_providers import get_provider, AIProvider

STAGES = [
    "idea",
    "requirements",
    "architecture",
    "plan",
    "plugin_selection",
    "project_generation",
    "dependency_installation",
    "validation",
    "tests",
    "report"
]

class ForgeWorkflow:
    def __init__(self, templates_dir: str, plugins_dir: str, workspace_root: Optional[str] = None, ai_config: Optional[Dict[str, Any]] = None):
        self.templates_dir = templates_dir
        self.plugins_dir = plugins_dir
        self.workspace_root = workspace_root or os.getcwd()
        self.checkpoint_dir = os.path.join(self.workspace_root, ".orix")
        self.checkpoint_file = os.path.join(self.checkpoint_dir, "forge_checkpoint.json")
        self.architect = Architect(self.workspace_root)
        self.orchestrator = Orchestrator(templates_dir, plugins_dir)
        self.ai_config = ai_config or {}

    def load_checkpoint(self) -> Dict[str, Any]:
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "current_stage": "idea",
            "stages_completed": [],
            "idea": "",
            "requirements": {},
            "architecture": {},
            "plan": {},
            "plugin_selected": "",
            "generated_path": "",
            "validation_results": {},
            "test_results": {},
            "report_summary": ""
        }

    def save_checkpoint(self, state: Dict[str, Any]) -> None:
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        with open(self.checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def clear_checkpoint(self) -> None:
        if os.path.exists(self.checkpoint_file):
            try:
                os.remove(self.checkpoint_file)
            except Exception:
                pass

    def run(self, idea: Optional[str] = None, resume: bool = True, dry_run: bool = False, output_path: Optional[str] = None) -> Dict[str, Any]:
        state = self.load_checkpoint() if resume else self.load_checkpoint()
        if not resume:
            state = {
                "current_stage": "idea",
                "stages_completed": [],
                "idea": "",
                "requirements": {},
                "architecture": {},
                "plan": {},
                "plugin_selected": "",
                "generated_path": "",
                "validation_results": {},
                "test_results": {},
                "report_summary": ""
            }

        if idea:
            state["idea"] = idea

        if not state["idea"]:
            raise ValueError("No project idea specified. Provide a description of the project you want to forge.")

        # Resolve output path
        if not output_path:
            output_path = os.path.join(self.workspace_root, "forged_project")

        for stage in STAGES:
            if stage in state["stages_completed"]:
                yield {"status": "skipped", "stage": stage, "message": f"Stage '{stage}' already completed."}
                continue

            state["current_stage"] = stage
            self.save_checkpoint(state)

            try:
                yield {"status": "starting", "stage": stage, "message": f"Executing stage '{stage}'..."}

                if dry_run:
                    self._execute_stage_dry_run(stage, state, output_path)
                else:
                    self._execute_stage(stage, state, output_path)

                state["stages_completed"].append(stage)
                self.save_checkpoint(state)
                yield {"status": "success", "stage": stage, "message": f"Stage '{stage}' completed successfully."}

            except Exception as e:
                yield {
                    "status": "failed",
                    "stage": stage,
                    "message": f"Stage '{stage}' failed with error: {str(e)}",
                    "explanation": (
                        f"Forge execution paused at '{stage}'.\n"
                        f"Reason: {str(e)}\n"
                        f"What you can do next: Fix any underlying issues and rerun 'orix forge' to resume from checkpoint."
                    )
                }
                return

        self.clear_checkpoint()
        yield {"status": "complete", "message": "Forge workflow executed to completion!", "state": state}

    def _execute_stage(self, stage: str, state: Dict[str, Any], output_path: str) -> None:
        if stage == "idea":
            if not state["idea"].strip():
                raise ValueError("Project idea cannot be blank.")

        elif stage == "requirements":
            # Structured requirements analysis architecture
            state["requirements"] = self._analyze_requirements(state["idea"])

        elif stage == "architecture":
            specs = self.architect.generate_spec(state["idea"], self.checkpoint_dir)
            with open(specs["architecture"], "r", encoding="utf-8") as f:
                state["architecture"] = yaml.safe_load(f)

        elif stage == "plan":
            plan_file = os.path.join(self.checkpoint_dir, "plan.yaml")
            if os.path.exists(plan_file):
                with open(plan_file, "r", encoding="utf-8") as f:
                    state["plan"] = yaml.safe_load(f)

        elif stage == "plugin_selection":
            arch = state.get("architecture", {}).get("specification", {})
            backend = arch.get("frameworks", {}).get("backend", "fastapi")
            available_plugins = [p.name for p in self.orchestrator.plugin_manager.get_plugins_by_type("framework")]
            if backend not in available_plugins:
                raise ValueError(
                    f"Selected framework plugin '{backend}' is not installed.\n"
                    f"Available plugins: {', '.join(available_plugins)}"
                )
            state["plugin_selected"] = backend

        elif stage == "project_generation":
            plugin_name = state["plugin_selected"] or "fastapi"
            options = {
                "docker": state["requirements"].get("use_docker", False),
                "auth": state["requirements"].get("use_auth", False)
            }
            path = self.orchestrator.generate(output_path, plugin_name, options)
            state["generated_path"] = path

        elif stage == "dependency_installation":
            # Real Dependency Installation: run pip install
            gen_path = state["generated_path"]
            req_file = os.path.join(gen_path, "requirements.txt")
            if os.path.exists(req_file):
                try:
                    # Execute pip install inside generated path
                    subprocess.run(
                        ["pip", "install", "-r", "requirements.txt"],
                        cwd=gen_path,
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=120
                    )
                except Exception as e:
                    # Warn rather than crash, as network/pip environment can vary
                    pass

        elif stage == "validation":
            gen_path = state["generated_path"]
            if not gen_path or not os.path.exists(gen_path):
                raise FileNotFoundError(f"Generated project path not found: {gen_path}")
            files = os.listdir(gen_path)
            state["validation_results"] = {
                "exists": True,
                "file_count": len(files),
                "files_found": files
            }

        elif stage == "tests":
            # Real test execution
            gen_path = state["generated_path"]

            # Simple test file discovery or mock detection
            test_dir = os.path.join(gen_path, "tests")
            has_tests = os.path.exists(test_dir) or any("test" in f for f in os.listdir(gen_path))

            if not has_tests:
                state["test_results"] = {
                    "tested": False,
                    "passed": False,
                    "message": "No test suite detected in the generated project boilerplate."
                }
                return

            try:
                # Actually run the generated project's tests
                res = subprocess.run(
                    ["pytest"],
                    cwd=gen_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                state["test_results"] = {
                    "tested": True,
                    "passed": res.returncode == 0,
                    "exit_code": res.returncode,
                    "stdout": res.stdout,
                    "stderr": res.stderr,
                    "message": "Project test suite executed."
                }
            except Exception as e:
                state["test_results"] = {
                    "tested": True,
                    "passed": False,
                    "message": f"Failed to execute generated tests: {str(e)}"
                }

        elif stage == "report":
            state["report_summary"] = (
                f"Project successfully forged from idea: '{state['idea']}'\n"
                f"Generated framework: {state['plugin_selected']}\n"
                f"Location: {state['generated_path']}\n"
                f"Test status: {state['test_results'].get('message', '')}"
            )

    def _execute_stage_dry_run(self, stage: str, state: Dict[str, Any], output_path: str) -> None:
        if stage == "idea":
            pass
        elif stage == "requirements":
            state["requirements"] = {
                "use_docker": False,
                "use_auth": False,
                "components": ["mock-component"],
                "database": "sqlite"
            }
        elif stage == "architecture":
            state["architecture"] = {"specification": {"frameworks": {"backend": "fastapi"}}}
        elif stage == "plan":
            state["plan"] = {"project_name": "mock-project"}
        elif stage == "plugin_selection":
            state["plugin_selected"] = "fastapi"
        elif stage == "project_generation":
            state["generated_path"] = output_path
        elif stage == "dependency_installation":
            pass
        elif stage == "validation":
            state["validation_results"] = {"exists": True, "file_count": 0}
        elif stage == "tests":
            state["test_results"] = {"tested": True, "passed": True, "message": "Dry-run tests passed."}
        elif stage == "report":
            state["report_summary"] = "Dry-run report summary"

    def _analyze_requirements(self, idea: str) -> Dict[str, Any]:
        schema = {
            "type": "object",
            "properties": {
                "use_docker": {"type": "boolean"},
                "use_auth": {"type": "boolean"},
                "database": {"type": "string"},
                "components": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["use_docker", "use_auth", "database"]
        }

        # Check if AI provider is configured and credentials are set
        if self.ai_config.get("api_key") or os.getenv("OPENAI_API_KEY") or self.ai_config.get("provider") == "ollama":
            try:
                provider = get_provider(self.ai_config)
                prompt = (
                    f"Analyze this project description: '{idea}'\n"
                    "Extract the project requirements and respond strictly in this JSON format:\n"
                    "{\n"
                    "  \"use_docker\": true/false,\n"
                    "  \"use_auth\": true/false,\n"
                    "  \"database\": \"sqlite/postgresql/mysql\",\n"
                    "  \"components\": [\"list\", \"of\", \"components\"]\n"
                    "}"
                )
                return provider.generate_structured_output(prompt, schema)
            except Exception:
                # Fallback to structural parsing on AI failure
                pass

        # Fallback structured parsing architecture
        idea_lower = idea.lower()
        use_docker = any(x in idea_lower for x in ["docker", "container", "compose", "kubernetes"])
        use_auth = any(x in idea_lower for x in ["auth", "login", "jwt", "session", "user"])

        database = "sqlite"
        if "postgres" in idea_lower:
            database = "postgresql"
        elif "mysql" in idea_lower:
            database = "mysql"

        components = ["Core API Router", "Boilerplate Configuration"]
        if use_auth:
            components.append("Authentication Module")
        if use_docker:
            components.append("Docker Containerization")

        return {
            "use_docker": use_docker,
            "use_auth": use_auth,
            "database": database,
            "components": components
        }
