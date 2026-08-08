# Orix Security & Hardening Model

Orix CLI employs a multi-tiered security and hardening model designed to protect the developer's system from path traversal, arbitrary file writes, and uncontrolled AI agent execution.

---

## 🛡️ Key Hardening Defenses

### 1. Path Traversal & Workspace Boundary Protection
All file operations performed by the workspace toolbox (`WorkspaceToolbox`) are validated against a strict workspace root constraint.
- **Defense**: In `resolve_path()`, any relative or absolute path is fully resolved (`Path.resolve()`). The resolved path must have the workspace directory as its ancestor:
  ```python
  try:
      resolved.relative_to(self.root_path)
  except ValueError:
      raise ValueError("Path traversal detected: outside workspace boundary")
  ```
- **Scope**: Protects reading, writing, searching, and deleting operations from escaping the workspace boundary.

### 2. Secure Template Rendering
The template renderer (`TemplateRenderer`) ensures that template and destination paths are rigorously checked.
- **Defense**:
  - Validates that requested templates resolve inside the base template directory.
  - Validates that rendered filenames and directories do not resolve outside the specified target directory.
- **Scope**: Prevents template injection or malicious templates from writing files outside the generated project directory.

### 3. AI Builder Validation
The AI Builder parses specs with strict error handling and payload checking.
- **Defense**:
  - Restricts spec keys and checks for required structural fields (`project_name`, `framework`).
  - Gracefully handles timeout errors, API auth/HTTP errors, and unexpected payload shapes from remote models.

### 4. Interactive Permissions Gate
The permission manager (`PermissionManager`) allows users to monitor and control AI agent actions.
- **Defense**: High-risk activities like command execution, internet requests, or file manipulation require explicit runtime approval in interactive mode unless explicitly bypassed via `--force` or configuration.

---

## ⚠️ Security Assumptions

- **Host Privilege**: Orix assumes that the host environment running the CLI is owned and secured by the developer. It does not run with root permissions by default.
- **API Keys**: Users must handle AI model API keys securely (using environment variables or local git-ignored user configuration files with safe file permissions `0o600`).
