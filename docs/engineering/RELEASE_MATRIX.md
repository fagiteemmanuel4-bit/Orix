# Orix X P0.6 Release Matrix

This matrix lists the verified verification tests, expected results, and statuses for the Orix foundation sub-systems.

| Sub-system | Verification Suite | Expected Result | Actual Behavior | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Package** | `pytest tests/unit` | Installs under non-editable modes without import hacks. | Verified successfully on clean checks. | **STABLE** |
| **CLI** | `orix self-test` | Intercepts click group exception failures cleanly. | Suppresses raw tracebacks. | **STABLE** |
| **Toolbox** | `tests/toolbox` | Enforces contract-schema typed arguments. | Parameter checks fully pass. | **STABLE** |
| **Permissions** | `tests/unit/test_agent_safety.py` | Restricts INTERACTIVE/FULL tiers and allows SAFE. | Mapped security gates are honored. | **STABLE** |
| **Indexer** | `tests/indexer` | Tracks imports and python class definitions. | dependency mappings resolved accurately. | **STABLE** |
| **Memory** | `tests/unit` | Isolation under active project `.orix/memory.json`. | Saves configurations safely without key leakages. | **STABLE** |
| **Forge** | `orix forge --dry-run` | Executes scaffolding and true tests counts. | Tracks and reports stages accurately. | **STABLE** |
| **Doctor** | `orix doctor` | Overrides and drops overall score to 0 on CRITICAL findings. | Correctly overrides health index on credentials. | **STABLE** |
| **Explain** | `orix explain <target>` | Parses docstring purpose, execution flow, and risks. | Generated professional code summaries. | **STABLE** |
| **AI Providers** | `orix ai models` | central model capability registry checks. | Lists local/cloud statuses cleanly. | **STABLE** |
| **Agent** | `pytest tests/agent` | OBSERVE-ACT execution mock loop. | Runs and corrects edits using MockProvider. | **EXPERIMENTAL** |
