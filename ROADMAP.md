# Orix X Product & Feature Roadmap

This roadmap outlines the planned development path for Orix X, categorizing features by execution priority and complexity.

---

## Phase 1: Local Engine Core & TUI Upgrades (Near-Term)
- **Extensible Schema Definition**: Build JSON-Schema-based templates definition files to allow plugins to load automatically without Python glue files.
- **Enhanced TUI UX**: Build progress bars for multi-file writing and validation checks.
- **Diagnostic Mode**: Validate local workspace environments (node, docker, python) before generation.

## Phase 2: Local AI Integrations & Agents (Mid-Term)
- **Local LLM Providers**: Seamless integration with Ollama and Llamafile to customize generated templates on the fly via local LLMs.
- **Interactive Prompts via LLM**: Generate schema-based custom plugins using plain-English prompts (e.g., `orix generate-plugin "Express App with Prisma and JWT"`).
- **Security Guardrails**: Automated prompt-injection filtering and safety sandbox checking for any shell-command generation.

## Phase 3: Desktop Ecosystem & Collaboration (Long-Term)
- **Orix Desktop UI**: Cross-platform desktop interface (Electron/Tauri) for scaffold selection, config workspace management, and visual template marketplace.
- **Orix Hub (Cloud Sync)**: Securely sync enterprise template configurations and sharing rules within organizations.
