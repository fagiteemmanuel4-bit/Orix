# Orix Feature Triage Board (P0.7)

This board classifies Orix features based on 5 independent run cycles conducted under distinct execution conditions.

---

## WORKING

### 1. Code Explainer System (`orix explain`)
*   **Exact Command**: `orix explain --symbol <name>` or `orix explain <target>`
*   **Execution Conditions**:
    *   *Condition 1 (Normal)*: `orix explain orix/core/permissions.py` (File level) -> PASS
    *   *Condition 2 (Empty)*: `orix explain` (Defaults to current directory '.') -> PASS
    *   *Condition 3 (Invalid / Missing)*: `orix explain --symbol NonExistentClass` -> PASS (Gracefully caught with clean `ValueError`)
    *   *Condition 4 (Large)*: `orix explain --symbol OrixDoctor` -> PASS (Extracted syntax highlighted code, imports, purpose)
    *   *Condition 5 (Failure / Malformed)*: `orix explain bad_file.py` (With syntax errors) -> PASS (AST parsing handles syntax error gracefully and falls back to text structure extraction)
*   **Evidence**: 5/5 runs pass. Beautifully rendered panels, AST symbol locations, and clear risk markers.
*   **Score**: 10/10
*   **Remaining Limitation**: High-precision parsing is focused on Python AST definitions; other languages use regex fallback.

### 2. Token & Cost Dashboard (`orix cost`)
*   **Exact Command**: `orix cost` and `orix cost --clear`
*   **Execution Conditions**:
    *   *Condition 1 (Normal)*: `orix cost` after logging transactions -> PASS
    *   *Condition 2 (Empty / Clean)*: `orix cost` on clean project -> PASS (Displays user instruction panel cleanly)
    *   *Condition 3 (Invalid / Corrupted)*: Corrupted `.orix/cost_tracker.json` file -> PASS (Gracefully returns empty transaction count 0 instead of crashing)
    *   *Condition 4 (Large)*: 1,000 logged transactions -> PASS (Scrolls and aggregates overall estimated cost in Panel)
    *   *Condition 5 (Failure)*: `orix cost --clear` -> PASS (Deletes the local database correctly)
*   **Evidence**: 5/5 runs pass. Dashboard reports "Model Cost Breakdown (ESTIMATES)" with correct column headers in compliance with P0.7 cost rules.
*   **Score**: 10/10
*   **Remaining Limitation**: Token estimates are split-based counts; exact count requires provider-specific tiktoken adapters.

### 3. Dynamic Task Routing & Ollama Fallback
*   **Exact Command**: Programmatic and agentic prompting (`orix agent`)
*   **Execution Conditions**:
    *   *Condition 1 (Normal)*: Coding-focused keyword -> PASS (Routes dynamically to gpt-4o-mini)
    *   *Condition 2 (Architecture)*: Design/Refactor keyword -> PASS (Routes dynamically to claude-3-5-sonnet-20241022)
    *   *Condition 3 (Remote Failure)*: Remote provider timeout/failure with Ollama running -> PASS (Seamelessly fails over to local Ollama llama3 model)
    *   *Condition 4 (Ollama Unavailable)*: Remote fails and Ollama not running -> PASS (Raises exception warning cleanly)
    *   *Condition 5 (User Override)*: Setting `disable_routing=True` in config -> PASS (Bypasses routing entirely)
*   **Evidence**: Verified with fallback unit and integration assertions.
*   **Score**: 10/10
*   **Remaining Limitation**: Local fallback requires local Ollama service to be active on localhost port 11434.

### 4. Workspace Diagnostics (`orix doctor`)
*   **Exact Command**: `orix doctor`
*   **Execution Conditions**:
    *   *Condition 1 (Normal)*: Ran in root folder -> PASS (Gives score 94/100, detects lock file)
    *   *Condition 2 (Empty)*: Ran in empty folder -> PASS (Scores overall correctly and flags missing tests/git repo)
    *   *Condition 3 (Vulnerability check)*: Code with eval/exec or shell=True statements -> PASS (Correctly deducts score and adds risk warning)
    *   *Condition 4 (CRITICAL key leak)*: File with hardcoded password -> PASS (Vulnerabilities drop category score to 0)
    *   *Condition 5 (Scaffold app)*: Running in freshly scaffolded folder -> PASS (Yields score 86/100)
*   **Evidence**: 5/5 runs pass. Beautifully organized findings table with clear severity categorization.
*   **Score**: 10/10
*   **Remaining Limitation**: Scans patterns statically using regex matching; complex custom AST dataflows are not evaluated.
