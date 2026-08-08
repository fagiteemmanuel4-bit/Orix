import os
import fnmatch
import subprocess
import difflib
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class WorkspaceToolbox:
    SCHEMAS = {
        "read_file": {"filepath": str},
        "write_file": {"filepath": str, "content": str},
        "edit_file": {"filepath": str, "old_content": str, "new_content": str},
        "delete_file": {"filepath": str},
        "search": {"query": str},
        "find_symbol": {"symbol": str},
        "find_references": {"symbol": str},
        "run_test": {},
        "run_linter": {},
        "run_formatter": {},
        "inspect_project": {}
    }

    PERMISSIONS = {
        "read_file": "read",
        "write_file": "write",
        "edit_file": "write",
        "delete_file": "write",
        "search": "read",
        "find_symbol": "read",
        "find_references": "read",
        "run_test": "high_risk",
        "run_linter": "high_risk",
        "run_formatter": "high_risk",
        "inspect_project": "read"
    }

    def __init__(self, root_path: str, dry_run: bool = False, auto_approve: bool = False):
        self.root_path = Path(root_path).resolve()
        self.dry_run = dry_run
        self.auto_approve = auto_approve

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

    def validate_args(self, tool_name: str, args: Dict[str, Any]) -> None:
        if tool_name not in self.SCHEMAS:
            raise ValueError(f"Unknown tool '{tool_name}'")
        schema = self.SCHEMAS[tool_name]
        for key, expected_type in schema.items():
            if key not in args:
                raise TypeError(f"Missing required argument '{key}' for tool '{tool_name}'")
            if not isinstance(args[key], expected_type):
                raise TypeError(f"Invalid type for argument '{key}': expected {expected_type.__name__}, got {type(args[key]).__name__}")

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.validate_args(tool_name, args)
            method = getattr(self, f"_tool_{tool_name}", None)
            if not method:
                raise NotImplementedError(f"Tool '{tool_name}' method is not implemented.")

            result = method(args)
            return {"success": True, "result": result}
        except Exception as e:
            # Structured error
            why = "An error occurred during tool execution"
            next_action = "Check input parameters, path boundaries, or file status."
            if isinstance(e, ValueError) and "Path traversal" in str(e):
                why = "The requested file path points outside the secure workspace boundaries."
                next_action = "Provide a path that resolves within the repository root."
            elif isinstance(e, FileNotFoundError):
                why = "The target file could not be located in the workspace."
                next_action = "Verify the file path is correct and the file exists."
            elif isinstance(e, TypeError):
                why = "The arguments provided to the tool do not match the expected schema or types."
                next_action = "Refer to the tool's parameter schemas and correct the argument types."

            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "why": why,
                    "next_action": next_action
                }
            }

    # --- Tool Implementations ---

    def _tool_read_file(self, args: Dict[str, Any]) -> str:
        path = self.resolve_path(args["filepath"])
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File not found: {args['filepath']}")
        return path.read_text(encoding="utf-8")

    def _tool_write_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        path = self.resolve_path(args["filepath"])
        content = args["content"]
        old_content = path.read_text(encoding="utf-8") if path.exists() else ""
        diff = self.compute_diff(old_content, content, str(path))
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return {"filepath": str(path), "diff": diff}

    def _tool_edit_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        path = self.resolve_path(args["filepath"])
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File not found for editing: {args['filepath']}")

        old_text = path.read_text(encoding="utf-8")
        search_block = args["old_content"]
        replace_block = args["new_content"]

        if search_block not in old_text:
            raise ValueError(f"Search block not found in the file '{args['filepath']}'. Exact match required.")

        new_text = old_text.replace(search_block, replace_block, 1)
        diff = self.compute_diff(old_text, new_text, str(path))

        if not self.dry_run:
            path.write_text(new_text, encoding="utf-8")
        return {"filepath": str(path), "diff": diff}

    def _tool_delete_file(self, args: Dict[str, Any]) -> str:
        path = self.resolve_path(args["filepath"])
        if not self.dry_run and path.exists():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)
        return str(path)

    def _tool_search(self, args: Dict[str, Any]) -> List[str]:
        query = args["query"]
        patterns = ["*.py", "*.js", "*.ts", "*.json", "*.html", "*.css", "*.md", "*.txt", "*.ini", "*.toml", "*.yaml", "*.yml"]
        matches = []
        for root, _, files in os.walk(self.root_path):
            for pattern in patterns:
                for filename in fnmatch.filter(files, pattern):
                    path = Path(root) / filename
                    try:
                        text = path.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue
                    if query.lower() in text.lower() or query.lower() in filename.lower():
                        matches.append(str(path.relative_to(self.root_path)))
        return list(set(matches))

    def _tool_find_symbol(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        symbol = args["symbol"]
        results = []
        for root, _, files in os.walk(self.root_path):
            for filename in fnmatch.filter(files, "*.py"):
                path = Path(root) / filename
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                            if symbol.lower() == node.name.lower():
                                results.append({
                                    "file": str(path.relative_to(self.root_path)),
                                    "type": "class" if isinstance(node, ast.ClassDef) else "function",
                                    "name": node.name,
                                    "lineno": node.lineno
                                })
                except Exception:
                    continue
        return results

    def _tool_find_references(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        symbol = args["symbol"]
        results = []
        for root, _, files in os.walk(self.root_path):
            for filename in fnmatch.filter(files, "*.py"):
                path = Path(root) / filename
                try:
                    source = path.read_text(encoding="utf-8", errors="ignore")
                    tree = ast.parse(source)
                    for node in ast.walk(tree):
                        # check imports
                        if isinstance(node, ast.ImportFrom):
                            for name in node.names:
                                if name.name == symbol:
                                    results.append({
                                        "file": str(path.relative_to(self.root_path)),
                                        "type": "import",
                                        "lineno": node.lineno
                                    })
                        elif isinstance(node, ast.Name):
                            if node.id == symbol and not isinstance(node.ctx, ast.Store):
                                results.append({
                                    "file": str(path.relative_to(self.root_path)),
                                    "type": "reference",
                                    "lineno": node.lineno
                                })
                except Exception:
                    continue
        return results

    def _tool_run_test(self, args: Dict[str, Any]) -> Dict[str, Any]:
        # Framework detection
        framework = "pytest"
        if os.path.exists(self.root_path / "package.json"):
            framework = "npm test"

        cmd = ["pytest"] if framework == "pytest" else ["npm", "test"]
        res = self.run_shell(cmd)
        return {
            "framework_detected": framework,
            "exit_code": res["returncode"],
            "stdout": res["stdout"],
            "stderr": res["stderr"]
        }

    def _tool_run_linter(self, args: Dict[str, Any]) -> Dict[str, Any]:
        # Use flake8 or fallback black check
        cmd = ["black", "--check", "."]
        res = self.run_shell(cmd)
        return {
            "linter_detected": "black",
            "exit_code": res["returncode"],
            "stdout": res["stdout"],
            "stderr": res["stderr"]
        }

    def _tool_run_formatter(self, args: Dict[str, Any]) -> Dict[str, Any]:
        cmd = ["black", "."]
        res = self.run_shell(cmd)
        return {
            "formatter_detected": "black",
            "exit_code": res["returncode"],
            "stdout": res["stdout"],
            "stderr": res["stderr"]
        }

    def _tool_inspect_project(self, args: Dict[str, Any]) -> List[str]:
        relative_path = args.get("path", "")
        target_dir = self.resolve_path(relative_path) if relative_path else self.root_path

        results = []
        for item in target_dir.iterdir():
            suffix = "/" if item.is_dir() else ""
            results.append(f"{item.name}{suffix}")
        return results

    # --- Original methods kept for backwards compatibility ---

    def delete_file(self, relative_path: str) -> Path:
        return self._tool_delete_file({"filepath": relative_path})

    def read_file(self, relative_path: str) -> str:
        return self._tool_read_file({"filepath": relative_path})

    def write_file(self, relative_path: str, content: str) -> Tuple[Path, str]:
        res = self._tool_write_file({"filepath": relative_path, "content": content})
        return Path(res["filepath"]), res["diff"]

    def search_code(self, query: str, patterns: Optional[List[str]] = None) -> List[Path]:
        res = self._tool_search({"query": query})
        return [self.root_path / p for p in res]

    def list_files(self, patterns: Optional[List[str]] = None) -> List[Path]:
        patterns = patterns or ["*"]
        files: List[Path] = []
        for root, _, filenames in os.walk(self.root_path):
            for pattern in patterns:
                for filename in fnmatch.filter(filenames, pattern):
                    files.append(Path(root) / filename)
        return files

    def run_shell(self, command: List[str], cwd: Optional[str] = None) -> Dict[str, str]:
        if self.dry_run:
            return {"command": " ".join(command), "stdout": "[dry run]", "stderr": "", "returncode": 0}
        cwd_path = self.resolve_path(cwd) if cwd else self.root_path
        process = subprocess.run(command, capture_output=True, text=True, cwd=str(cwd_path), shell=False)
        return {
            "command": " ".join(command),
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "returncode": process.returncode,
        }

    def git_status(self) -> str:
        result = self.run_shell(["git", "status", "--short"])
        return result["stdout"]

    def git_diff(self, args: Optional[List[str]] = None) -> str:
        args = args or ["--stat"]
        result = self.run_shell(["git", "diff"] + args)
        return result["stdout"]

    def git_current_branch(self) -> str:
        result = self.run_shell(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return result["stdout"].strip()

    def compute_diff(self, old: str, new: str, filename: str) -> str:
        return "\n".join(difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile=f"{filename}.old", tofile=filename, lineterm=""))
