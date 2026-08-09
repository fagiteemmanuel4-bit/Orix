# Orix Release Test & Verification Matrix

This matrix lists the verification test suites, observed outcomes, and release stability classifications for all major Orix sub-systems.

| Sub-system | Verification Method | Expected Behavior | Actual Behavior | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Package** | `pytest tests/unit` | Imports `orix` securely under production environments. | Imports correctly and installs in editable modes. | **STABLE** |
| **CLI** | `orix self-test` | Runs a complete, automated validation gate. | Successfully ran all 12 key checks. | **STABLE** |
| **Toolbox** | `tests/toolbox` | Enforces JSON-schema parameter validation and outputs structured messages. | Passed 4/4 assertions. | **STABLE** |
| **Permissions** | `tests/unit/test_agent_safety.py` | Automatically grants READ_ONLY/SAFE tiers and prompts for INTERACTIVE/FULL. | Restricts file edits and shell executions dynamically. | **STABLE** |
| **Indexer & Store** | `tests/indexer` | Extracts python functions, classes, module imports, and cross-file dependents. | Tracked file dependencies accurately without fake vector labels. | **STABLE** |
| **Memory** | `tests/unit` | Isolation under active project `.orix/memory.json`. | Saves configurations safely without credential leakages. | **STABLE** |
| **Forge Scaffolder** | `orix forge --dry-run` | Runs full model-based analysis, validated outputs, and actual pytest suites inside generated directories. | Checks stage checkpoints correctly. | **STABLE** |
| **Doctor Diagnostics** | `orix doctor` | Displays severities (CRITICAL/HIGH/MEDIUM/LOW) and transparent unweighted health scores. | Prints structured health metrics flawlessly. | **STABLE** |
| **Explain Analyzer** | `orix explain <target>` | Graph module definitions, docstring purposes, and security patterns. | Generated professional code summaries successfully. | **STABLE** |
| **AI Providers** | `orix ai models` | Model-agnostic adapters (OpenAI, Anthropic, Gemini, OpenRouter, Ollama) with a centralized Model Registry. | Lists local/cloud statuses cleanly. | **STABLE** |
| **Agent Workspace** | `pytest tests/agent` | Runs task loop (`OBSERVE -> PLAN -> APPROVE -> ACT -> TEST -> FIX -> VERIFY`) with limits. | Completes tasks cleanly using the deterministic MockProvider. | **EXPERIMENTAL** |
