# Orix Feature Status Report — Release-Candidate Version (P0.5)

This status report details the fully audited, technically defensible readiness states of Orix sub-systems.

---

## 📊 Core Component Readiness Matrix

| Feature | Stability | Primary Location | Key Audited Implementation Details |
| :--- | :--- | :--- | :--- |
| **Model-Agnostic AI Providers** | **STABLE** | `orix/core/ai_providers.py` | Full BYOK (Bring Your Own Key) architecture with centralized `MODEL_REGISTRY`. Concrete adapters handle OpenAI, Anthropic, Gemini, OpenRouter, and local Ollama APIs. Includes `MockProvider` for complete offline test repeatability. |
| **Structured Workspace Toolbox** | **STABLE** | `orix/core/toolbox.py` | Every tool specifies exact typed schemas, permission levels, validation, and structured dictionary output/error formats. Enforces sandboxed Path Traversal resolution checks. |
| **System Specifier (`orix architect`)** | **STABLE** | `orix/core/architect.py` | Parses prompting intents to produce `.orix/architecture.yaml`, `.orix/plan.yaml`, and `.orix/decisions.md` before code gets generated. |
| **Resumable Scaffolding (`orix forge`)** | **STABLE** | `orix/core/forge.py` | Structured requirement analysis. Automatically installs pip packages, physically runs generated test suites inside output folders, parses exit codes/counts, and tracks stage checkpoints via `.orix/forge_checkpoint.json`. |
| **Diagnostics (`orix doctor`)** | **STABLE** | `orix/core/doctor.py` | Strictly evidence-driven findings categorized by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`). Directly derives unweighted scores from these rules. |
| **Code Explain Analyst (`orix explain`)** | **STABLE** | `orix/core/explain.py` | Parses module docstrings, function blocks, import lists, and reports complexity/security risks. Supports full directory graphs. |
| **Release Validation Gate (`orix self-test`)** | **STABLE** | `orix/core/selftest.py` | Comprehensive click-driven diagnostic command running offline checks across all 12 key Orix subsystems. |
| **Keyword Index Store** | **STABLE** | `orix/core/keyword_store.py` | Renamed from SimpleVectorStore to truth-driven `KeywordIndexStore`. Does not pretend to do vector similarity searches; instead implements precise local index keyword matches. |
| **Automated Evaluation (`orix eval`)** | **STABLE** | `orix/core/eval.py` | Sandboxes the agent loop over 5 distinct, isolated benchmark scenarios and reports exact scorecard metrics (iterations, passes, tokens). |
| **Project-Scoped Memory** | **STABLE** | `orix/core/memory.py` | Project-isolated memory written strictly to `.orix/memory.json` in the current workspace. Automatically scrubs private API keys or credential matches before writing to disk. |
| **Autonomous Agent Loop** | **EXPERIMENTAL** | `orix/core/agent.py` | Active reasoning/action execution loops following `OBSERVE -> PLAN -> REQUEST PERMISSION -> ACT -> TEST -> OBSERVE RESULT -> FIX -> VERIFY` with auto-repair loops and retry bounds. |
