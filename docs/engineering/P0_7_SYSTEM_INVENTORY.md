# Orix X P0.7 System Inventory

This document establishes the fresh, audited baseline of all features implemented across the Orix Developer OS CLI.

---

## 1. CLI Command Engine

*   **Feature**: click command group registration and execution
*   **Location**: `orix/core/cli.py`
*   **Purpose**: Exposes developer commands for scaffolding, diagnostics, agent loops, model configurations, and memory management.
*   **Dependencies**: `click`, `rich`, `yaml`
*   **Public CLI/API**: `orix <command>`
*   **Existing tests**: `tests/cli/test_cli.py`
*   **Actual test result**: PASS
*   **Working**: Yes (STABLE)
*   **Security risk**: LOW (Arguments and paths are handed off to robust sandboxed utilities)
*   **Performance risk**: LOW (Minimal startup overhead)
*   **Upgrade required**: No

---

## 2. Workspace Indexer & Keyword Index Store

*   **Feature**: AST Parsing & Reference tracking
*   **Location**: `orix/core/indexer.py` & `orix/core/keyword_store.py`
*   **Purpose**: Scans project files, builds AST parsing trees for Python, extracts classes, functions, imports, and cross-file references.
*   **Dependencies**: `tree_sitter` (optional extra), `ast`
*   **Public CLI/API**: Used programmatically in diagnostics and agent loops.
*   **Existing tests**: `tests/indexer/test_indexer.py`
*   **Actual test result**: PASS
*   **Working**: Yes (STABLE)
*   **Security risk**: LOW (Read-only static scanning)
*   **Performance risk**: MEDIUM (Scanning massive monorepos can block execution unless chunked/budgeted)
*   **Upgrade required**: Yes (Can be extended to support non-python file symbols)

---

## 3. Workspace Toolbox (Tool Execution Sandbox)

*   **Feature**: Sandboxed file mutations, searches, and test executions
*   **Location**: `orix/core/toolbox.py`
*   **Purpose**: Executes operations (read_file, write_file, edit_file, delete_file, search, find_symbol, run_test, format, lint) with explicit boundary guarantees.
*   **Dependencies**: `subprocess`, `fnmatch`, `difflib`
*   **Public CLI/API**: `orix run <command>`, and programmatically inside Agent/Forge
*   **Existing tests**: `tests/toolbox/test_toolbox.py`
*   **Actual test result**: PASS
*   **Working**: Yes (STABLE)
*   **Security risk**: HIGH (Runs file edits and shell subprocesses; requires absolute path-traversal hardening)
*   **Performance risk**: LOW
*   **Upgrade required**: Yes (Enforce stricter execution timeouts, and sandboxing fellbacks)

---

## 4. Local Memory Store

*   **Feature**: Project-isolated JSON storage
*   **Location**: `orix/core/memory.py`
*   **Purpose**: Reads and writes project-scoped session memories, preferences, and exception logs under `.orix/memory.json`.
*   **Dependencies**: `json`
*   **Public CLI/API**: `orix memory list`, `orix memory show <category>`, `orix memory remove <category>`
*   **Existing tests**: `tests/unit/test_config.py` (partially)
*   **Actual test result**: PASS
*   **Working**: Yes (STABLE)
*   **Security risk**: MEDIUM (API keys must never be logged or stored plaintext)
*   **Performance risk**: LOW
*   **Upgrade required**: No

---

## 5. Permission Manager

*   **Feature**: Security tier gating & User approval prompts
*   **Location**: `orix/core/permissions.py`
*   **Purpose**: Classifies operations into READ_ONLY, SAFE, INTERACTIVE, and FULL tiers and requests confirmation when necessary.
*   **Dependencies**: `rich`
*   **Public CLI/API**: Interactive console confirmation prompts
*   **Existing tests**: `tests/unit/test_agent_safety.py`
*   **Actual test result**: PASS
*   **Working**: Yes (STABLE)
*   **Security risk**: LOW (Highly protective barrier)
*   **Performance risk**: LOW
*   **Upgrade required**: No

---

## 6. Doctor (Workspace Diagnostics)

*   **Feature**: Score-driven project health auditor
*   **Location**: `orix/core/doctor.py`
*   **Purpose**: Audits repository structure, locks, missing test suites, monolithic patterns, and scans for potential secrets and injection vulnerabilities.
*   **Dependencies**: None
*   **Public CLI/API**: `orix doctor`
*   **Existing tests**: `tests/doctor/test_doctor.py`
*   **Actual test result**: PASS
*   **Working**: Yes (STABLE)
*   **Security risk**: LOW
*   **Performance risk**: LOW
*   **Upgrade required**: No

---

## 7. Explain System

*   **Feature**: Static analyzer of target directories/files
*   **Location**: `orix/core/explain.py`
*   **Purpose**: Inspects files or folders to explain purpose, imports, classes, functions, and flags security risks.
*   **Dependencies**: `ast`
*   **Public CLI/API**: `orix explain <target>`
*   **Existing tests**: `tests/explain/test_explain.py`
*   **Actual test result**: PASS
*   **Working**: Yes (STABLE)
*   **Security risk**: LOW
*   **Performance risk**: LOW
*   **Upgrade required**: Yes (Needs `--symbol` resolution)

---

## 8. AI Providers & Model Registry

*   **Feature**: Multi-provider LLM connector contracts
*   **Location**: `orix/core/ai_providers.py`
*   **Purpose**: Adapts OpenAI, Anthropic, Gemini, OpenRouter, local Ollama, and Mock providers to a single standardized API.
*   **Dependencies**: `requests`, `json`
*   **Public CLI/API**: `orix ai models`
*   **Existing tests**: `tests/unit/test_ai_builder.py`
*   **Actual test result**: PASS
*   **Working**: Yes (STABLE)
*   **Security risk**: MEDIUM (Protects against credential exposure and validates timeouts)
*   **Performance risk**: MEDIUM (Relies on external network/API latency)
*   **Upgrade required**: Yes (Needs local fallbacks and routing logic)

---

## 9. Forge Workflow Scaffolder

*   **Feature**: Multi-stage resumable project builder
*   **Location**: `orix/core/forge.py`
*   **Purpose**: Executes a multi-stage workflow from an idea: requirements -> architecture -> selection -> generation -> verification.
*   **Dependencies**: `orix/core/orchestrator.py`
*   **Public CLI/API**: `orix forge <idea>`
*   **Existing tests**: `tests/forge/test_forge.py`
*   **Actual test result**: PASS
*   **Working**: Yes (STABLE/EXPERIMENTAL)
*   **Security risk**: LOW
*   **Performance risk**: LOW
*   **Upgrade required**: No

---

## 10. Agent Workspace Session

*   **Feature**: Observe-Plan-Act-Test agent loops
*   **Location**: `orix/core/agent.py`
*   **Purpose**: Autonomous loop that identifies steps, calls tools, handles permissions, verifies tests, and repairs failures using configured provider logic.
*   **Dependencies**: `orix/core/ai_providers.py`, `orix/core/toolbox.py`
*   **Public CLI/API**: `orix agent`
*   **Existing tests**: `tests/agent/test_agent.py`
*   **Actual test result**: PASS
*   **Working**: Yes (EXPERIMENTAL)
*   **Security risk**: HIGH (Autonomous code alterations and command executions)
*   **Performance risk**: HIGH (Recursive loops could consume significant API tokens)
*   **Upgrade required**: Yes (Needs Token cost tracking integration)
