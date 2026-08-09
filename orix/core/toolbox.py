import os
import fnmatch
import subprocess
import difflib
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Robust, standardized Tool Contract Schemas as recommended in Phase 12
TOOL_CONTRACTS = {
    "read_file": {
        "name": "read_file",
        "description": "Reads the complete UTF-8 contents of a specified workspace file.",
        "permission_tier": "READ_ONLY",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Relative workspace file path."}
            },
            "required": ["filepath"]
        }
    },
    "write_file": {
        "name": "write_file",
        "description": "Overwrites or creates a file in the workspace with new text content.",
        "permission_tier": "INTERACTIVE",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Relative workspace file path."},
                "content": {"type": "string", "description": "Raw string contents to write."}
            },
            "required": ["filepath", "content"]
        }
    },
    "edit_file": {
        "name": "edit_file",
        "description": "Performs targeted search-and-replace block edits on an existing workspace file.",
        "permission_tier": "INTERACTIVE",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Relative workspace file path."},
                "old_content": {"type": "string", "description": "Specific search text block."},
                "new_content": {"type": "string", "description": "Replacement text block."}
            },
            "required": ["filepath", "old_content", "new_content"]
        }
    },
    "delete_file": {
        "name": "delete_file",
        "description": "Safely removes a file or directory inside the workspace boundary.",
        "permission_tier": "INTERACTIVE",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Relative workspace path to unlink."}
            },
            "required": ["filepath"]
        }
    },
    "search": {
        "name": "search",
        "description": "Performs case-insensitive keyword search matching code files across the workspace.",
        "permission_tier": "READ_ONLY",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Substring text to match."}
            },
            "required": ["query"]
        }
    },
    "list_directory": {
        "name": "list_directory",
        "description": "Lists the directory contents of a specified sub-folder.",
        "permission_tier": "READ_ONLY",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Sub-folder relative path."}
            },
            "required": []
        }
    },
    "find_symbol": {
        "name": "find_symbol",
        "description": "Locates the function or class definition matching the symbol identifier in python files.",
        "permission_tier": "READ_ONLY",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Name of function or class."}
            },
            "required": ["symbol"]
        }
    },
    "find_references": {
        "name": "find_references",
        "description": "Locates imports and references of a symbol across python files.",
        "permission_tier": "READ_ONLY",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name."}
            },
            "required": ["symbol"]
        }
    },
    "run_test": {
        "name": "run_test",
        "description": "Runs the local workspace test framework suites and returns exit codes and stdout.",
        "permission_tier": "SAFE",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "run_linter": {
        "name": "run_linter",
        "description": "Runs black validation checks on the local code files.",
        "permission_tier": "SAFE",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "run_formatter": {
        "name": "run_formatter",
        "description": "Formative auto-styling run of python code files.",
        "permission_tier": "SAFE",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "run_build": {
        "name": "run_build",
        "description": "Executes building script pipelines in python setup directories.",
        "permission_tier": "SAFE",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "git_status": {
        "name": "git_status",
        "description": "Retrieves active untracked or dirty state listings from git.",
        "permission_tier": "READ_ONLY",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "git_diff": {
        "name": "git_diff",
        "description": "Retrieves diff states from current unstaged or committed lines.",
        "permission_tier": "READ_ONLY",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

class WorkspaceToolbox:
    def __init__(self, root_path: str, dry_run: bool = False, auto_approve: bool = False):
        self.root_path = Path(root_path).resolve()
        self.dry_run = dry_run
        self.auto_approve = auto_approve

    def resolve_path(self, relative_path: str) -> Path:
        # Standardize separator variations (Windows style backslashes)
        clean_path_str = str(relative_path).replace("\\", "/")
        path = Path(clean_path_str)

        if not path.is_absolute():
            path = self.root_path / path

        # Try fully resolving the path to handle symlinks and double-dots
        try:
            resolved = path.resolve()
        except Exception:
            # Handle non-existent paths gracefully: resolve parent folder recursively
            parent_resolved = path.parent.resolve()
            resolved = parent_resolved / path.name

        # Prevent case-insensitive variation escapes and absolute path breaks
        resolved_str = str(resolved).lower().replace("\\", "/")
        root_str = str(self.root_path).lower().replace("\\", "/")

        if resolved_str != root_str and not resolved_str.startswith(root_str + "/"):
            raise ValueError(f"Path traversal detected: '{relative_path}' is outside workspace boundary '{self.root_path}'")

        return resolved

    def validate_args(self, tool_name: str, args: Dict[str, Any]) -> None:
        if tool_name not in TOOL_CONTRACTS:
            raise ValueError(f"Unknown tool name: {tool_name}")

        contract = TOOL_CONTRACTS[tool_name]
        schema = contract["parameters"]

        # Verify required keys
        for req in schema.get("required", []):
            if req not in args:
                raise TypeError(f"Missing required parameter '{req}' for tool '{tool_name}'")

        # Verify parameter types
        props = schema.get("properties", {})
        for k, v in args.items():
            if k in props:
                expected_type_str = props[k]["type"]
                if expected_type_str == "string" and not isinstance(v, str):
                    raise TypeError(f"Parameter '{k}' must be a string, got {type(v).__name__}")
                elif expected_type_str == "boolean" and not isinstance(v, bool):
                    raise TypeError(f"Parameter '{k}' must be a boolean, got {type(v).__name__}")

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Unified, schema-validated execution dispatch point returning structured outputs and errors."""
        try:
            self.validate_args(tool_name, args)
            method = getattr(self, f"_tool_{tool_name}", None)
            if not method:
                raise NotImplementedError(f"Execution method for tool '{tool_name}' is not registered.")

            res = method(args)
            return {"success": True, "result": res}
        except Exception as e:
            why = "An execution error occurred in the workspace tools handler."
            next_action = "Please check inputs, parameters, and workspace files."

            if isinstance(e, ValueError) and "traversal" in str(e):
                why = "The target path violates the absolute workspace sandboxed boundaries."
                next_action = "Specify filepaths that resolve strictly under the workspace repository root."
            elif isinstance(e, FileNotFoundError):
                why = "The specified file path could not be located in the workspace filesystem."
                next_action = "Confirm the target file exists or has been scaffolded first."
            elif isinstance(e, TypeError):
                why = "The provided parameters violate the tool's JSON Schema types contract."
                next_action = "Refer to Orix tool contracts and supply the correct parameter types."

            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "why": why,
                    "next_action": next_action
                }
            }

    # --- Tool Execution Backends ---

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

    def _tool_list_directory(self, args: Dict[str, Any]) -> List[str]:
        relative_path = args.get("path", "")
        target_dir = self.resolve_path(relative_path) if relative_path else self.root_path
        results = []
        for item in target_dir.iterdir():
            suffix = "/" if item.is_dir() else ""
            results.append(f"{item.name}{suffix}")
        return results

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
        cmd = ["pytest"]
        res = self.run_shell(cmd)
        return {
            "framework_detected": "pytest",
            "exit_code": res["returncode"],
            "stdout": res["stdout"],
            "stderr": res["stderr"]
        }

    def _tool_run_linter(self, args: Dict[str, Any]) -> Dict[str, Any]:
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

    def _tool_run_build(self, args: Dict[str, Any]) -> Dict[str, Any]:
        cmd = ["python", "-m", "pip", "show", "orix"]
        res = self.run_shell(cmd)
        return {
            "build_stage": "pip show",
            "exit_code": res["returncode"],
            "stdout": res["stdout"],
            "stderr": res["stderr"]
        }

    def _tool_git_status(self, args: Dict[str, Any]) -> str:
        return self.git_status()

    def _tool_git_diff(self, args: Dict[str, Any]) -> str:
        return self.git_diff()

    # --- Standard compatibility methods ---

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
        # Enforce shell=False for all executions as part of adversarial security audit
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
