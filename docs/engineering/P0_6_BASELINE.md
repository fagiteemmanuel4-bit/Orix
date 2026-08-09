# Orix X P0.6 Baseline Audit & Inventory

This baseline audit inventories every non-Agent core component of Orix before Phase P0.6 foundation hardening begins.

---

## 🛠️ Sub-system Inventory Matrix

### 1. Python Packaging & Installation
- **Current State**: Packages can be installed using `pip install -e .`. The backend setuptools configuration supports clean installations.
- **Working status**: Working. Imports compile cleanly on modern environments.
- **Known bugs**: None.
- **Test coverage**: Moderate. Verified on CI pipelines.
- **Risk**: Low.
- **Recommended Action**: Assert that package-level version variables and setup entrypoints match click configurations perfectly without sys.path workarounds.

### 2. Click CLI Core Commands
- **Current State**: Entry point routes to Click options. Commands support specs and interactive TUIs.
- **Working status**: Stable. Help and version screens load successfully.
- **Known bugs**: Operational failures or missing options can sometimes bubble raw python exceptions or tracebacks to the user.
- **Test coverage**: High. Covers commands, invalid inputs, and diagnostic checks.
- **Risk**: Medium. bubbled tracebacks degrade developer trust.
- **Recommended Action**: Overhaul `cli.py` to catch operational exceptions cleanly and suppress tracebacks unless in debug mode.

### 3. Unified Config & Scoped Memory Store
- **Current State**: Active configuration manages global settings. LocalMemoryStore handles active project-level configs under `.orix/memory.json`.
- **Working status**: Stable.
- **Known bugs**: Corrupted files can bubble parsing crashes during CLI startup.
- **Test coverage**: High.
- **Risk**: Low.
- **Recommended Action**: Enforce parsing schema validation and graceful fallback defaults when reading corrupted config or memory files.

### 4. Model-Agnostic Provider & Model Registry
- **Current State**: Mapped adapters support OpenAI, Anthropic, Gemini, OpenRouter, and Ollama under a centralized `MODEL_REGISTRY` dict.
- **Working status**: Stable.
- **Known bugs**: Unknown models can trigger key/value mismatches or crash execution loops.
- **Test coverage**: High. Verified with a deterministic offline `MockProvider`.
- **Risk**: Medium.
- **Recommended Action**: Enforce robust validation fallbacks in the Model Registry to support unknown, removed, or custom endpoint model descriptions gracefully.

### 5. Workspace boundaries & Subprocess Security
- **Current State**: Toolbox resolves workspace paths relative to active project roots and checks ancestors. Subprocesses run with `shell=False`.
- **Working status**: Stable.
- **Known bugs**: None.
- **Test coverage**: Very high. Covers absolute, double dot (`../`), and trailing slash variations.
- **Risk**: High. Unchecked system escapes can compromise developer hosts.
- **Recommended Action**: Harden `resolve_path()` to handle complex variations (Windows UNC paths, non-existent targets, case-insensitive checks, and nested symlinks).

### 6. Evidence-Driven Orix Doctor
- **Current State**: Diagnostic tool runs static checks on workspace directories and lists findings.
- **Working status**: Stable.
- **Known bugs**: Scoring calculations are derived from general findings, but lacks a critical vulnerability score drop override.
- **Test coverage**: High.
- **Risk**: Low.
- **Recommended Action**: Refactor Doctor score calculations to immediately drop the overall health index to 0 if any `CRITICAL` finding (such as active committed credentials) is detected.

### 7. Scaffolding Forge Pipeline
- **Current State**: Forge executes multi-stage workflow, checkpointing checkpoints at `.orix/forge_checkpoint.json`.
- **Working status**: Working.
- **Known bugs**: None.
- **Test coverage**: High. Tested using MockProvider.
- **Risk**: Low.
- **Recommended Action**: Assert that Forge testing stage physically scans output paths for tests files and runs them under native Pytest commands, reporting exit codes and counts perfectly.
