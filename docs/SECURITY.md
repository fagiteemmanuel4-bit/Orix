# Orix Security, Hardening & Permission Model

Orix CLI is engineered as a secure, sandboxed Developer OS CLI platform. It enforces a strict, multi-tiered security boundary to guarantee that untrusted AI outputs, malformed shell commands, or third-party templates cannot compromise the developer's system host.

---

## 🛡️ Core Hardening Defenses

### 1. Unified Permission Tiers
All toolbox operations mapped inside Orix reside under one of four explicit security permission tiers:
- **`READ_ONLY`**: Includes reading files, directory listing, index matching, and symbol/reference searching. (Approved automatically in standard runtime profiles).
- **`SAFE`**: Execution of read-only static validations, such as linter verification (`run_linter`, `run_formatter`), package manifest validation (`run_build`), and test suite verification (`run_test`).
- **`INTERACTIVE`**: File system writes, file modifications, or file deletions. Forces runtime user confirmation prompts when in `INTERACTIVE` permission levels.
- **`FULL`**: High-risk activities, such as executing ad-hoc shell commands (`run_shell`) or custom package dependency installations. Never allowed implicitly without explicit user approval.

### 2. Path Traversal & Workspace Boundary Isolation
- **Strict Resolution**: All operations resolving paths (`read_file`, `write_file`, `edit_file`, `delete_file`) route through `WorkspaceToolbox.resolve_path()`. This resolves paths fully (`Path.resolve()`), stripping any nested symlinks, absolute parameters, or parent relative path elements (`../`).
- **Ancestor Checks**: Any path resolving outside the workspace root is rejected instantly, raising a `ValueError`. This protects system directories (e.g., `/etc/passwd` or system files) from arbitrary reading or overwriting.

### 3. User Secrets & API Keys Protection
- **No Private Credentials Committed**: Orix never requires storing central developer keys. It relies entirely on standard user-level env keys (such as `OPENAI_API_KEY` or local Ollama endpoints).
- **Sensitive Key Cleansing**: Before writing project memory cache or prompt caches, the `LocalMemoryStore` actively scrubs any dictionary fields or strings matching keys like `api_key`, `password`, `token`, or `credentials`.
- **Automated Secrets Scanning**: An active regression test suite (`tests/security/test_leakage.py`) runs static scans across all source, spec, and memory files to guarantee no accidental key assignments get committed.

### 4. Malformed Response & Failure Isolation
- **Schema Validation**: Model-generated structured payloads (e.g., JSON requirements or tool calls) are validated against exact schemas. Malformed structural outputs are rejected rather than parsed blindly.
- **Subprocess Isolation**: All subprocess commands executed via the Toolbox run with `shell=False` to prevent shell injection vulnerabilities.
