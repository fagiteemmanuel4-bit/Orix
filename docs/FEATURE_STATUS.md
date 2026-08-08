# Feature Status Report - Orix X (Phase P0)

This report details the stability, location, test coverage, and security audit of every significant feature in the Orix codebase as of Phase P0.

---

## Overview

| Feature | Status | Implementation Location | Entry Point | Primary Dependencies | Known Issues | Test Coverage | Recommended Next Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Plugin Loading & Discovery** | **WORKING** | `orix/core/plugin_manager.py` | `PluginManager.load_plugins()` | `importlib.util`, `inspect`, `os` | A syntax/import error in any plugin will crash the entire application on startup. No duplicate checking. | `tests/test_core.py` (basic load check) | Protect load sequence against individual plugin import failures; prevent duplicate plugin names. |
| **Project Scaffolding / Orchestration** | **WORKING** | `orix/core/orchestrator.py` | `Orchestrator.generate()` | `TemplateRenderer`, `PluginManager`, `PyYAML` | Docker option is offered/validated but no Dockerfiles exist in templates. Spec resolution accepts paths with potential traversal. | `tests/test_core.py` (integration) | Add validation to spec paths and implement missing Dockerfile templates. |
| **Recursive Jinja2 Rendering** | **WORKING** | `orix/core/renderer.py` | `TemplateRenderer.render_project()` | `jinja2`, `os` | Allows path traversal write if template names are manipulated. Unconditionally renders all files regardless of boolean flag context. | `tests/test_core.py` (unit) | Enforce template boundary checks; sanitize output filenames and directory paths. |
| **AI Spec Builder** | **PARTIALLY_WORKING** | `orix/core/ai_builder.py` | `AIBuilder.build_spec()` | `requests`, `PyYAML`, OpenRouter/OpenAI API | Brittle markdown-extraction code (regex split of backticks). Prone to crashing on malformed YAML or API failures. | None | Add robust YAML parsing, schema validation, HTTP error/timeout handling, and full mock tests. |
| **Agent Session Loop (Natural Language Coding)** | **EXPERIMENTAL** | `orix/core/agent.py` | `AgentSession.run()` | `ConfigManager`, `WorkspaceIndexer`, `WorkspaceToolbox`, `PermissionManager` | The AI generation/edits are simulated/hardcoded to append a static comment to the first matched file. Stdin prompts block when run non-interactively. | None | Ensure paths are relative and bounded to workspace. Enforce prompt validation. Add safety unit tests. |
| **Workspace Indexing & Search** | **EXPERIMENTAL** | `orix/core/indexer.py`, `orix/core/vector_store.py` | `WorkspaceIndexer.index_workspace()` | `tree_sitter`, `ast`, `json` | "SimpleVectorStore" is actually a substring/keyword store, not a vector store. Highly dependent on local tree-sitter binary files. | None | Document as substring indexer rather than vector store to avoid false claims; add basic test suite. |
| **Config TUI Editor** | **WORKING** | `orix/core/config_tui.py` | `run_config_tui()` | `questionary`, `ConfigManager` | TUI is fully interactive and blocks if standard input is unavailable. No schema validation of models or API endpoints. | None | Add unit test verifying that configuration values can be set and saved. |
| **Environment Diagnostics** | **WORKING** | `orix/core/diagnostics.py` | `EnvironmentDiagnostics.run()` | `platform`, `shutil`, `subprocess` | None. | None | Add unit tests to verify tool checking behavior. |
| **Web Research Tool** | **EXPERIMENTAL** | `orix/core/research.py` | `WebResearchTool.fetch_url()` | `requests`, `playwright` (optional), `re` | Simple regex parsing of title and paragraphs can fail on complex/malformed HTML pages. | None | Document limitations and mock network calls in tests. |

---

## Detailed Audit & Brutal Honesty

1. **Docker Scaffold Option Claim**: The interactive prompts and YAML specs support `--docker`. However, looking closely at the `templates/` folder, **no template contains actual Docker files (`Dockerfile` or `docker-compose.yml`)**. Thus, choosing Docker has zero impact on the rendered project files.
2. **"Vector Store" Claim**: The implementation of `SimpleVectorStore` uses basic case-insensitive substring search: `lower in chunk["text"].lower()`. There are no embeddings, vector metrics (such as cosine similarity), or actual vector search algorithms. This is a keyword search engine.
3. **Agent Implementation**: The agent session is a skeleton that mimics agentic workflow but lacks live LLM integration for editing. High-risk operations (such as command execution) require approval, but file writes and reads lack robust verification against path traversal.
4. **Security Vulnerabilities**:
   - `WorkspaceToolbox` and `TemplateRenderer` do not validate workspace boundaries, making Orix vulnerable to Path Traversal (`../../etc/passwd`).
   - `orix run` takes arbitrary arguments and executes them via `subprocess.run(..., shell=False)`. While `shell=False` limits shell injection, it still allows execution of any binary available in path.
