# Competitor Red Flags & Orix Solutions

This document details developer complaints and structural weaknesses of existing AI coding tools and outlines the technical solutions built directly into Orix.

---

## 1. Context Overflows and Runaway API Costs
*   **The Problem**: Many tools (such as Claude Code, OpenHands, and various VS Code extensions) pass the entire repository or massive multi-file trees to the LLM on every single prompt. This results in context window limits being breached rapidly and runs up hundreds of dollars in API bills.
*   **Why it happens**: Lack of local context slicing or intelligence about file structure before querying the model.
*   **Orix Solution**:
    *   **Dynamic Task Routing**: Automatically routes simpler prompts to cheap models (like `gpt-4o-mini`) and keeps highly complex architectural prompts for reasoning models (like `claude-3-5-sonnet`).
    *   **Local Code Slicing**: Uses AST parsing in `WorkspaceIndexer` to locate precisely the target function/class block and only injects the relevant code slices instead of whole files.

---

## 2. Destructive Commands and Security Violations
*   **The Problem**: AI agents sometimes execute runaway shell commands (like `rm -rf`, raw database truncations, or package installations that conflict with host environments) or access credentials and keys stored on disk.
*   **Why it happens**: Standard tool execution runs with raw shell access (`shell=True`) and has no path-traversal boundaries or permission tier classifications.
*   **Orix Solution**:
    *   **Tool Gating Tiers**: Classes operations into distinct permission levels (READ_ONLY, SAFE, INTERACTIVE, FULL).
    *   **Hardened Boundaries**: Strictly rejects double-dots, symlinks pointing outside the workspace, absolute path escapes, and runs all shell commands with `shell=False` to neutralize shell injections.

---

## 3. Network Failures and Complete Lock-in
*   **The Problem**: Developers lose access to cloud-based agent platforms when remote APIs experience downtime, connection timeouts, or rate limits.
*   **Why it happens**: Proprietary tools are hardcoded to a single provider and have no local failover modes.
*   **Orix Solution**:
    *   **Local Ollama Fallback**: If a cloud connection fails or times out, the `RoutingProvider` automatically detects if a local Ollama instance is running on port 11434, seamlessly redirects the task, and notifies the developer.
