# Contributing to Orix X

We are thrilled that you are interested in contributing to Orix X! Whether you are writing code, designing templates, reporting bugs, or improving documentation, your support is vital to making Orix X the premier universal scaffolding tool.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please report any violations or unacceptable behavior to `security@kryonara.com`.

---

## How to Contribute

### 1. Reporting Bugs & Suggesting Features
- Please search open issues before creating a new one to ensure it hasn't already been reported.
- Use our issue templates to provide clear instructions for reproduction, logs, or detailed feature designs.

### 2. Developing Plugins or Templates
- Create a new plugin inside `orix/plugins/` extending `FrameworkPlugin`.
- Create the matching templates directory under `orix/templates/<plugin_name>/`.
- Test your templates with variable replacements and conditional structures to ensure robust rendering.

### 3. Submitting Pull Requests
- Fork the repository and create your branch from `main`.
- Install dependencies and development packages: `pip install -e .[dev]`
- Write tests in `tests/` covering your changes.
- Ensure all tests pass: `pytest`
- Use the validation script in `/home/jules/self_created_tools/validate_orix.py` if available to quickly run checks.
- Keep your commits atomic, and use clear, descriptive commit messages.

---

## Development Guidelines

- We maintain strong typing where possible. Use type annotations on all new functions.
- Keep dependency count minimal to preserve rapid load times.
- Avoid modifying core orchestrator files unless designing wide plugin SDK features.
- If you change files in `orix/templates`, ensure no hardcoded environment values are included directly.
