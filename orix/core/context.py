import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from orix.core.toolbox import WorkspaceToolbox
from orix.core.indexer import WorkspaceIndexer
from orix.core.memory import LocalMemoryStore

class ContextEngine:
    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root).resolve()
        self.toolbox = WorkspaceToolbox(str(self.root))
        self.indexer = WorkspaceIndexer(str(self.root))
        self.memory = LocalMemoryStore(str(self.root))

    def detect_project_type(self) -> str:
        if (self.root / "requirements.txt").exists() or (self.root / "pyproject.toml").exists():
            return "Python"
        if (self.root / "package.json").exists():
            return "NodeJS/Frontend"
        return "Generic Workspace"

    def gather_git_state(self) -> Dict[str, Any]:
        try:
            branch = self.toolbox.git_current_branch()
            status = self.toolbox.git_status()
            return {
                "branch": branch,
                "status": status,
                "clean": len(status.strip()) == 0
            }
        except Exception:
            return {"branch": "unknown", "status": "", "clean": True}

    def gather_memory_insights(self) -> Dict[str, Any]:
        # Incorporate local preferences or architectural constraints from memory.json
        data = self.memory.get_all()
        return {
            "preferences": data.get("preferences", {}),
            "project_insights": data.get("project_insights", {})
        }

    def build_context_package(self, task_prompt: str, max_chars_budget: int = 30000) -> Dict[str, Any]:
        """Dynamically packages the relevant workspace context boundedly under the max character budget."""
        context_files: List[Dict[str, Any]] = []
        total_size = 0

        # 1. Project Detection
        project_type = self.detect_project_type()

        # 2. Search relevant source code files matching task keywords
        matches = self.toolbox.execute_tool("search", {"query": task_prompt})
        relevant_filepaths = matches.get("result", [])

        # 3. Compile file content, symbols, and references boundedly
        for rel_path in relevant_filepaths[:5]:  # bound to top 5 files to avoid overload
            abs_path = self.root / rel_path
            if not abs_path.exists() or abs_path.is_dir():
                continue

            try:
                content = abs_path.read_text(encoding="utf-8", errors="ignore")

                # Check character budget before adding file
                file_size = len(content)
                if total_size + file_size > max_chars_budget:
                    # Truncate if partially fitting, then break
                    allowed_chars = max_chars_budget - total_size
                    if allowed_chars > 500:
                        context_files.append({
                            "filepath": rel_path,
                            "content": content[:allowed_chars] + "\n... [TRUNCATED DUE TO BUDGET LIMITS]",
                            "truncated": True
                        })
                    break

                # Extract file AST symbol info using toolbox
                symbol_res = self.toolbox.execute_tool("find_symbol", {"symbol": abs_path.stem})
                symbols = symbol_res.get("result", [])

                context_files.append({
                    "filepath": rel_path,
                    "content": content,
                    "symbols": symbols,
                    "truncated": False
                })
                total_size += file_size
            except Exception:
                continue

        # 4. Git State
        git_state = self.gather_git_state()

        # 5. Memory
        memory_insights = self.gather_memory_insights()

        return {
            "project_type": project_type,
            "git_state": git_state,
            "memory_insights": memory_insights,
            "relevant_files": context_files,
            "total_character_size": total_size,
            "budget_limit": max_chars_budget
        }

    def format_as_prompt_section(self, context_pkg: Dict[str, Any]) -> str:
        """Formats the unified context package into a clear instruction section for model consumption."""
        sections = [
            "=== WORKSPACE CONTEXT ===",
            f"Project Stack: {context_pkg['project_type']}",
            f"Git Branch: {context_pkg['git_state']['branch']}",
            f"Git Status clean: {context_pkg['git_state']['clean']}",
            f"Local Preferences: {json.dumps(context_pkg['memory_insights']['preferences'])}"
        ]

        if context_pkg["relevant_files"]:
            sections.append("\n--- RELEVANT FILES ---")
            for f in context_pkg["relevant_files"]:
                sections.append(f"File: {f['filepath']}")
                if "symbols" in f and f["symbols"]:
                    sections.append(f"Symbols: {', '.join([s['name'] for s in f['symbols']])}")
                sections.append("```")
                sections.append(f["content"])
                sections.append("```\n")

        sections.append(f"Total compiled context character size: {context_pkg['total_character_size']} chars (Budget: {context_pkg['budget_limit']})")
        return "\n".join(sections)
