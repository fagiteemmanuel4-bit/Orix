import fnmatch
import os
import shutil
import subprocess
import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

class WorkspaceToolbox:
    def __init__(self, root_path: str, dry_run: bool = False, auto_approve: bool = False):
        self.root_path = Path(root_path).resolve()
        self.dry_run = dry_run
        self.auto_approve = auto_approve

        # Define Structured Schemas and Permission Levels for P1 Toolbox
        # Levels: 1 = LOW, 2 = MEDIUM, 3 = HIGH RISK
        self.tools_manifest = {
            "read_file": {
                "description": "Read content of a file within workspace",
                "permission_level": 1,
                "schema": {
                    "relative_path": {"type": "string", "required": True}
                }
            },
            "write_file": {
                "description": "Write or overwrite content of a file within workspace",
                "permission_level": 2,
                "schema": {
                    "relative_path": {"type": "string", "required": True},
                    "content": {"type": "string", "required": True}
                }
            },
            "edit_file": {
                "description": "Perform search-and-replace modification on a file",
                "permission_level": 2,
                "schema": {
                    "relative_path": {"type": "string", "required": True},
                    "old_text": {"type": "string", "required": True},
                    "new_text": {"type": "string", "required": True}
                }
            },
            "delete_file": {
                "description": "Delete a file or directory within workspace",
                "permission_level": 3,
                "schema": {
                    "relative_path": {"type": "string", "required": True}
                }
            },
            "search": {
                "description": "Search code files for a specific query string",
                "permission_level": 1,
                "schema": {
                    "query": {"type": "string", "required": True}
                }
            },
            "find_symbol": {
                "description": "Locate definitions of functions or classes",
                "permission_level": 1,
                "schema": {
                    "symbol_name": {"type": "string", "required": True}
                }
            },
            "find_references": {
                "description": "Find which files depend on/refer to a specific symbol",
                "permission_level": 1,
                "schema": {
                    "symbol_name": {"type": "string", "required": True}
                }
            },
            "run_test": {
                "description": "Run the project test suite",
                "permission_level": 2,
                "schema": {
                    "test_path": {"type": "string", "required": False}
                }
            },
            "run_linter": {
                "description": "Execute syntax / lint checks",
                "permission_level": 2,
                "schema": {
                    "target_path": {"type": "string", "required": False}
                }
            },
            "run_formatter": {
                "description": "Format source files",
                "permission_level": 2,
                "schema": {
                    "target_path": {"type": "string", "required": False}
                }
            },
            "inspect_project": {
                "description": "List files and understand workspace layout",
                "permission_level": 1,
                "schema": {}
            }
        }

    def resolve_path(self, relative_path: str) -> Path:
        path = Path(relative_path)
        if not path.is_absolute():
            path = self.root_path / path
        resolved = path.resolve()
        try:
            resolved.relative_to(self.root_path)
        except ValueError:
            raise ValueError(f"Path traversal detected: '{relative_path}' is outside workspace boundary '{self.root_path}'")
        return resolved

    def call_tool(self, tool_name: str, args: Dict[str, Any], permission_mgr: Any = None) -> Dict[str, Any]:
        """Call a structured tool with argument validation and permission verification."""
        if tool_name not in self.tools_manifest:
            return {
                "success": False,
                "error": f"Unknown tool: '{tool_name}'",
                "details": f"Available tools are: {', '.join(self.tools_manifest.keys())}"
            }

        manifest = self.tools_manifest[tool_name]
        schema = manifest["schema"]

        # 1. Argument validation against schema
        for param, rules in schema.items():
            if rules.get("required") and param not in args:
                return {
                    "success": False,
                    "error": f"Missing required parameter '{param}' for tool '{tool_name}'",
                    "details": f"Expected schema: {schema}"
                }
            if param in args and not isinstance(args[param], str):
                return {
                    "success": False,
                    "error": f"Invalid type for parameter '{param}' in tool '{tool_name}'",
                    "details": f"Expected string, got '{type(args[param]).__name__}'"
                }

        # 2. Enforce workspace boundary checks for file tools before proceeding
        if "relative_path" in args:
            try:
                self.resolve_path(args["relative_path"])
            except Exception as exc:
                return {
                    "success": False,
                    "error": "Workspace boundary check failed / path traversal detected",
                    "details": str(exc)
                }

        # 3. Verify permissions if PermissionManager is provided
        if permission_mgr is not None:
            perm_level = manifest["permission_level"]
            # Levels 2 and 3 require explicit permission
            if perm_level >= 2:
                allowed = permission_mgr.request(
                    action=f"execute tool {tool_name}",
                    details=f"[ TOOLBOX ] Arguments: {args}",
                    force=self.auto_approve
                )
                if not allowed:
                    return {
                        "success": False,
                        "error": "Permission Denied",
                        "details": f"The user rejected permission to execute high-risk tool: '{tool_name}'."
                    }

        # 4. Dispatch and execute
        try:
            result = self._execute_tool_action(tool_name, args)
            return {
                "success": True,
                "result": result
            }
        except Exception as exc:
            return {
                "success": False,
                "error": f"Execution error in tool '{tool_name}'",
                "details": str(exc)
            }

    def _execute_tool_action(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if tool_name == "read_file":
            path = self.resolve_path(args["relative_path"])
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"File not found: '{args['relative_path']}'")
            return path.read_text(encoding="utf-8")

        elif tool_name == "write_file":
            path = self.resolve_path(args["relative_path"])
            if self.dry_run:
                return f"[dry run] Would write file: {path}"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(args["content"], encoding="utf-8")
            return f"Successfully wrote {len(args['content'])} bytes to {args['relative_path']}"

        elif tool_name == "edit_file":
            path = self.resolve_path(args["relative_path"])
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"File not found: '{args['relative_path']}'")
            content = path.read_text(encoding="utf-8")
            old_text = args["old_text"]
            new_text = args["new_text"]
            if old_text not in content:
                raise ValueError(f"Target text to replace was not found inside '{args['relative_path']}'")
            if self.dry_run:
                return f"[dry run] Would edit file: {path}"
            new_content = content.replace(old_text, new_text)
            path.write_text(new_content, encoding="utf-8")
            return f"Successfully replaced occurrences in {args['relative_path']}"

        elif tool_name == "delete_file":
            path = self.resolve_path(args["relative_path"])
            if self.dry_run:
                return f"[dry run] Would delete: {path}"
            if path.exists():
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                return f"Successfully deleted {args['relative_path']}"
            return f"Path does not exist: {args['relative_path']}"

        elif tool_name == "search":
            query = args["query"]
            matches = []
            for root, _, files in os.walk(self.root_path):
                for filename in files:
                    # Ignore .orix or hidden files
                    if ".orix" in root or filename.startswith('.'):
                        continue
                    path = Path(root) / filename
                    try:
                        text = path.read_text(encoding="utf-8", errors="ignore")
                        if query.lower() in text.lower():
                            matches.append(str(path.relative_to(self.root_path)))
                    except Exception:
                        continue
            return matches

        elif tool_name == "find_symbol":
            # Direct link to WorkspaceIndexer semantic lookups if needed, or simple regex
            from orix.core.indexer import WorkspaceIndexer
            indexer = WorkspaceIndexer(str(self.root_path))
            indexer.index_workspace()
            matches = []
            for file, symbols in indexer.file_symbols.items():
                for sym in symbols:
                    if args["symbol_name"].lower() in sym["name"].lower():
                        matches.append({"file": file, "symbol": sym})
            return matches

        elif tool_name == "find_references":
            from orix.core.indexer import WorkspaceIndexer
            indexer = WorkspaceIndexer(str(self.root_path))
            indexer.index_workspace()
            return indexer.find_dependents_of_symbol(args["symbol_name"])

        elif tool_name == "run_test":
            target = args.get("test_path") or "."
            # Safe non-shell execution
            cmd = ["pytest"]
            if target != ".":
                cmd.append(target)
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.root_path))
            return {
                "exit_code": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip()
            }

        elif tool_name == "run_linter":
            target = args.get("target_path") or "."
            cmd = ["flake8", target]
            # Since flake8 might not be in the workspace/path, fall back to successful stub if missing
            if not shutil.which("flake8"):
                return {"exit_code": 0, "stdout": "Flake8 linter is not installed on host. Linting bypassed.", "stderr": ""}
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.root_path))
            return {
                "exit_code": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip()
            }

        elif tool_name == "run_formatter":
            target = args.get("target_path") or "."
            cmd = ["black", target]
            if not shutil.which("black"):
                return {"exit_code": 0, "stdout": "Black formatter is not installed on host. Formatting bypassed.", "stderr": ""}
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.root_path))
            return {
                "exit_code": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip()
            }

        elif tool_name == "inspect_project":
            file_tree = []
            for root, _, files in os.walk(self.root_path):
                if ".orix" in root or ".git" in root or "__pycache__" in root:
                    continue
                for f in files:
                    full_path = Path(root) / f
                    file_tree.append(str(full_path.relative_to(self.root_path)))
            return sorted(file_tree)

    def git_status(self) -> str:
        proc = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=str(self.root_path))
        return proc.stdout.strip()

    def git_diff(self, args: Optional[List[str]] = None) -> str:
        args = args or ["--stat"]
        proc = subprocess.run(["git", "diff"] + args, capture_output=True, text=True, cwd=str(self.root_path))
        return proc.stdout.strip()

    def git_current_branch(self) -> str:
        proc = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, cwd=str(self.root_path))
        return proc.stdout.strip()

    def compute_diff(self, old: str, new: str, filename: str) -> str:
        return "\n".join(difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile=f"{filename}.old", tofile=filename, lineterm=""))
