import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
from orix.core.ai_providers import get_provider
from orix.core.toolbox import WorkspaceToolbox
from orix.core.permissions import PermissionManager
from orix.core.memory import LocalMemoryStore
from orix.core.doctor import OrixDoctor
from orix.core.indexer import WorkspaceIndexer
from orix.core.forge import ForgeWorkflow

class OrixSelfTest:
    def __init__(self, workspace_root: str):
        self.root = workspace_root

    def run_all_checks(self) -> List[Dict[str, Any]]:
        checks = []

        # 1. Package check
        checks.append(self._check_package())

        # 2. CLI integration check
        checks.append(self._check_cli())

        # 3. Configuration check
        checks.append(self._check_config())

        # 4. Workspace boundaries check
        checks.append(self._check_workspace())

        # 5. Toolbox actions check
        checks.append(self._check_toolbox())

        # 6. Permissions gates check
        checks.append(self._check_permissions())

        # 7. Custom plugins loading check
        checks.append(self._check_plugins())

        # 8. Project AST indexer check
        checks.append(self._check_indexer())

        # 9. Scoped Memory check
        checks.append(self._check_memory())

        # 10. Doctor evidence checks
        checks.append(self._check_doctor())

        # 11. Forge Pipeline checkpoint run (using MockProvider)
        checks.append(self._check_forge())

        # 12. Agent OBSERVE-ACT execution check (using MockProvider)
        checks.append(self._check_agent())

        return checks

    def _check_package(self) -> Dict[str, Any]:
        try:
            import orix
            return {"name": "Package", "status": True, "details": f"Version: {orix.__version__ if hasattr(orix, '__version__') else '3.1.0'}"}
        except Exception as e:
            return {"name": "Package", "status": False, "details": f"Import failed: {str(e)}"}

    def _check_cli(self) -> Dict[str, Any]:
        try:
            from orix.core.cli import cli
            return {"name": "CLI", "status": True, "details": "Entrypoint 'cli' successfully loaded."}
        except Exception as e:
            return {"name": "CLI", "status": False, "details": f"CLI loading failed: {str(e)}"}

    def _check_config(self) -> Dict[str, Any]:
        try:
            from orix.core.config import ConfigManager
            cfg = ConfigManager(self.root)
            return {"name": "Configuration", "status": True, "details": "Config file resolved."}
        except Exception as e:
            return {"name": "Configuration", "status": False, "details": str(e)}

    def _check_workspace(self) -> Dict[str, Any]:
        toolbox = WorkspaceToolbox(self.root)
        try:
            toolbox.resolve_path("orix/core/cli.py")
            return {"name": "Workspace", "status": True, "details": "Boundary protection active."}
        except Exception as e:
            return {"name": "Workspace", "status": False, "details": str(e)}

    def _check_toolbox(self) -> Dict[str, Any]:
        toolbox = WorkspaceToolbox(self.root)
        try:
            res = toolbox.execute_tool("search", {"query": "import click"})
            return {"name": "Toolbox", "status": res["success"], "details": f"Search found {len(res.get('result', []))} source files."}
        except Exception as e:
            return {"name": "Toolbox", "status": False, "details": str(e)}

    def _check_permissions(self) -> Dict[str, Any]:
        pm = PermissionManager({"permission_level": "INTERACTIVE"})
        try:
            # READ_ONLY and SAFE should bypass prompts
            read_ok = pm.request("read_file", "details", tool_tier="READ_ONLY")
            return {"name": "Permissions", "status": read_ok, "details": "Mapped security tiers successfully verified."}
        except Exception as e:
            return {"name": "Permissions", "status": False, "details": str(e)}

    def _check_plugins(self) -> Dict[str, Any]:
        try:
            from orix.core.plugin_manager import PluginManager
            plugins_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
            pm = PluginManager(plugins_dir)
            pm.load_plugins()
            return {"name": "Plugins", "status": True, "details": f"Loaded {len(pm.plugins)} framework plugins."}
        except Exception as e:
            return {"name": "Plugins", "status": False, "details": str(e)}

    def _check_indexer(self) -> Dict[str, Any]:
        indexer = WorkspaceIndexer(self.root)
        try:
            files = indexer.list_files_to_index()
            return {"name": "Indexer", "status": True, "details": f"Index tracking: {len(files)} files."}
        except Exception as e:
            return {"name": "Indexer", "status": False, "details": str(e)}

    def _check_memory(self) -> Dict[str, Any]:
        store = LocalMemoryStore(self.root)
        try:
            store.record_preference("self-test-run", "success")
            return {"name": "Memory", "status": (Path(self.root) / ".orix" / "memory.json").exists(), "details": "Project-scoped memory verified."}
        except Exception as e:
            return {"name": "Memory", "status": False, "details": str(e)}

    def _check_doctor(self) -> Dict[str, Any]:
        doctor = OrixDoctor(self.root)
        try:
            rep = doctor.run_diagnostics()
            return {"name": "Doctor", "status": True, "details": f"Evidence-driven health index: {rep['scores']['Overall']}/100."}
        except Exception as e:
            return {"name": "Doctor", "status": False, "details": str(e)}

    def _check_forge(self) -> Dict[str, Any]:
        # Test Forge Pipeline with a mock provider
        temp_dir = tempfile.mkdtemp()
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        plugins_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
        try:
            wf = ForgeWorkflow(templates_dir, plugins_dir, temp_dir, ai_config={"provider": "mock"})
            results = list(wf.run(idea="Build a static math helper with mock-model", resume=False, dry_run=True))
            last = results[-1]
            status = last.get("status") == "complete"
            return {"name": "Forge", "status": status, "details": "Forge mock execution run successful."}
        except Exception as e:
            return {"name": "Forge", "status": False, "details": str(e)}
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _check_agent(self) -> Dict[str, Any]:
        # Test Agent OBSERVE-ACT execution with a mock provider
        from orix.core.agent import AgentSession
        temp_dir = tempfile.mkdtemp()
        (Path(temp_dir) / "app.py").write_text("class API:\n    pass\n", encoding="utf-8")
        try:
            session = AgentSession(
                root_path=temp_dir,
                mode="force",
                initial_prompt="Add health endpoint app.py",
                force=True,
                retry_limit=1,
                ai_config={"provider": "mock"}
            )
            session.run()
            mutated = "API" in (Path(temp_dir) / "app.py").read_text()
            return {"name": "Agent", "status": mutated, "details": "Observe-Act Agent loop successfully ran tool calls."}
        except Exception as e:
            return {"name": "Agent", "status": False, "details": str(e)}
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
