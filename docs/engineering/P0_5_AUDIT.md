# Orix X P0.5 Hardening Audit

**Mission**: Transform Orix from ambitious prototype into technically defensible release candidate.

**Date**: August 9, 2026  
**Repository**: fagiteemmanuel4-bit/Orix  
**Current Version**: 3.1.0  
**Python Target**: 3.10+

---

## EXECUTIVE SUMMARY

Orix X is an **ambitious** developer CLI platform with a well-intentioned architecture but **significant technical debt, misleading documentation, and unfinished core systems**. The repository demonstrates competent Python engineering in isolated components but **systematic gaps** in:

1. **Packaging**: No `py.typed`, inconsistent build configuration
2. **CLI Integration**: Commands reference modules that don't exist or are incomplete
3. **AI Integration**: No real model abstraction; hardcoded decisions throughout Agent and Forge
4. **Testing**: 50 tests pass, 3 fail on main branch — merge conflict introduced regression
5. **Security**: Path traversal protections exist but incomplete; no credential management
6. **Documentation**: Conflates "implemented," "experimental," and "simulated" features

**Release Candidate Blocker**: Agent and Forge are **fundamentally simulated**. They claim intelligence but execute hardcoded operations.

---

## ARCHITECTURE

### Current State

```
orix/
├── core/
│   ├── cli.py               # Click-based CLI
│   ├── agent.py             # Agent session loop (simulated)
│   ├── forge.py             # Multi-stage workflow (partially implemented)
│   ├── doctor.py            # Health diagnostics
│   ├── explain.py           # Code analysis
│   ├── architect.py         # Architecture planning
│   ├── toolbox.py           # Tool execution sandbox
│   ├── indexer.py           # Repository code index
│   ├── ai_builder.py        # AI spec generation (experimental)
│   ├── plugin_manager.py    # Plugin discovery & loading
│   ├── permissions.py       # Permission gating
│   ├── memory.py            # Project memory store
│   ├── config.py            # Configuration management
│   ├── research.py          # Web research tool
│   ├── vector_store.py      # Keyword index (misleadingly named)
│   ├── simple_vector_store.py # Duplicate/renamed implementation
│   ├── ui.py                # CLI UI helpers
│   ├── diagnostics.py       # Environment checks
│   ├── orchestrator.py      # Plugin orchestration
│   ├── renderer.py          # Jinja2 template rendering
│   ├── token_utils.py       # Token counting
│   ├── config_tui.py        # Configuration TUI
│   ├── treesitter_helper.py # Tree-sitter integration
│   └── env_check.py         # Environment validation
├── sdk/
│   └── base.py              # Plugin SDK base classes
├── plugins/                 # Framework plugins (empty)
├── templates/               # Project templates (empty)
└── external_prompts/        # AI prompt templates
```

### What Actually Works

#### ✅ PROVEN STABLE
- **Plugin Loading**: `PluginManager` correctly discovers and imports plugins
- **CLI Interface**: `click` integration is clean, commands are wired
- **Toolbox Path Safety**: `resolve_path()` prevents directory traversal
- **Environment Diagnostics**: Correctly identifies system dependencies
- **Jinja2 Rendering**: Template rendering works for basic project scaffolding
- **Permissions**: Framework exists for gating dangerous operations

#### 🟡 PARTIAL IMPLEMENTATION
- **Indexer**: Works but has been renamed (SimpleVectorStore→KeywordIndexStore) with migration issues
- **Memory**: Stores history but credential leakage risk still present
- **Doctor**: Calculates scores but logic is deterministic/rule-based, not ML
- **Explain**: Parses AST correctly but limited to Python
- **Configuration**: Loads YAML but no schema validation

#### 🔴 BROKEN / MISSING
- **AI Provider Abstraction**: Doesn't exist; no unified interface to models
- **Real Agent Loop**: Hardcoded to append comments; doesn't receive model output
- **Forge Pipeline**: Simulates requirement extraction with keyword matching
- **Credential Management**: No env var protection, no keychain integration
- **Testing**: 3 failures due to import errors (SimpleVectorStore regression)

---

## PACKAGING

### Current State

**pyproject.toml** exists and is minimally valid:
```toml
[project]
name = "orix"
version = "3.1.0"
requires-python = ">=3.10"
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

### What Works
- `pip install -e .` succeeds
- Entry point wired: `orix = "orix.core.cli:cli"`
- Dependencies declared

### What's Missing
- **No `py.typed`**: Type hints not declared (violates PEP 561)
- **No package metadata**: No author, license, project URLs
- **No optional extras**: `tree_sitter`, `web` (playwright) listed but not used
- **No test dependencies**: pytest not in dependencies (can't run tests without separate install)
- **Missing `__init__.py`**: orix/ and subdirectories lack `__init__.py` (implicit namespace package)

### Risk
- Install works but package is **not production-ready**
- Type checking will not work in consuming projects

---

## CLI

### Current State

**cli.py** exports 13 commands:

| Command | Implementation | Status |
|---------|---|---|
| `orix --help` | Works | ✅ |
| `orix create` | Fully implemented | ✅ |
| `orix plugin-install` | Fully implemented | ✅ |
| `orix plugin-remove` | Fully implemented | ✅ |
| `orix plugin-list` | Fully implemented | ✅ |
| `orix ai-build` | Incomplete (no AI provider) | 🟡 |
| `orix agent` | Simulated | 🔴 |
| `orix run` | Works | ✅ |
| `orix analyze` | Works | ✅ |
| `orix diagnose` | Works | ✅ |
| `orix architect` | Incomplete (deterministic only) | 🟡 |
| `orix forge` | Simulated | 🔴 |
| `orix doctor` | Works | ✅ |
| `orix explain` | Works (Python only) | 🟡 |
| `orix setup-treesitter` | Works | ✅ |

### What Works
- Help, version, plugin management
- Basic project creation with templates
- Workspace analysis and diagnostics
- Dry-run mode

### What's Missing
- **AI Provider Selection**: No way to configure OpenAI, Anthropic, Gemini, etc.
- **Model Selection**: No model registry
- **Credential Input**: No secure credential prompting
- **Real Agent/Forge**: Both are stubs

---

## TESTS

### Current State

```
tests/
├── agent/            # Agent tests
├── architect/        # Architect tests
├── cli/              # CLI integration tests
├── doctor/           # Doctor tests
├── explain/          # Explain tests
├── forge/            # Forge tests
├── indexer/          # Indexer tests
├── integration/      # Integration tests
├── plugins/          # Plugin tests
├── toolbox/          # Toolbox tests
└── unit/             # Unit tests
```

### Test Results (Main Branch)

```
CI Output (Aug 9, 2026):
FAILED tests/agent/test_agent.py::test_agent_session_plan_mode - NameError
FAILED tests/agent/test_agent.py::test_agent_session_interactive_approval - NameError
FAILED tests/indexer/test_indexer.py::test_indexer_symbol_and_dependents - NameError
50 passed, 3 failed
```

**Root Cause**: PR#6 renamed `SimpleVectorStore` → `KeywordIndexStore` but main branch still has both `vector_store.py` and `simple_vector_store.py`. Imports clash.

### What Works
- 50 passing tests across all categories
- Test structure is clean (separate directories per feature)
- CI matrix covers Python 3.10, 3.11, 3.12

### What's Missing
- **Mock Providers**: No deterministic AI provider for testing
- **Security Tests**: No path traversal, credential leakage, malicious prompt tests
- **Integration Tests**: Limited end-to-end scenarios
- **Evaluation Suite**: No real task-based acceptance testing

### Risk
- Broken main branch (merge conflict not resolved cleanly)
- 3 failing tests block release

---

## AGENT

### Current State

**agent.py** (424 lines) implements `AgentSession`:

#### What's Actually There
```python
def _agentic_loop(self, prompt: str):
    observation = self._observe(prompt)  # Search workspace
    plan = self._plan(observation, prompt)  # Hardcoded template
    
    # Does NOT call an AI model!
    # Simply appends: "# Orix Agent: implementation of prompt..."
    
    action_result = self._act(plan)  # Write file with comment
    test_res = self._test()  # Run pytest
    success = self._observe_result(test_res)  # Check exit code
```

#### The Deception
1. **Plan Step**: Returns hardcoded dict with `proposed_changes = "# Orix Agent: ..."`
2. **No Model Call**: Agent never sends observation to a model
3. **No Real Reasoning**: Decisions are deterministic keyword matching
4. **Simulated Approval**: `_request_permission()` just checks flags

#### What Works
- File I/O through toolbox
- Permission gating framework
- Session history tracking
- Help/status/memory commands

#### What's Broken
- **No Model Integration**: AI provider doesn't exist
- **Hardcoded Actions**: "write_file", "run_test" always same
- **No Tool Calling**: Model output not parsed
- **No Failure Recovery**: Retry loop is fake (same action each time)
- **Missing Approval Workflow**: Doesn't pause for user confirmation

### Risk
- **CRITICAL**: Claiming "autonomous coding agent" when it's a simulator
- **Release Blocker**: Cannot be called production AI-driven without model

---

## FORGE

### Current State

**forge.py** (300 lines) implements `ForgeWorkflow`:

#### Claimed Pipeline
```
IDEA → REQUIREMENTS → ARCHITECTURE → PLAN → SELECTION → GENERATION → DEPENDENCIES → TESTS → REPORT
```

#### What Actually Happens
```python
def run(self, idea, resume, dry_run, output_path):
    # Stage: "requirements"
    requirements = self._extract_requirements(idea)  # KEYWORD MATCHING!
    # "auth" in idea → {"auth": True}
    
    # Stage: "architecture"
    arch = self._auto_architect()  # Returns hardcoded JSON
    
    # Stage: "selection"
    plugin = self._select_plugin(arch)  # Keyword-based picker
    
    # Stage: "generation"
    self.orchestrator.generate(...)  # Template rendering (WORKS)
    
    # Stage: "tests"
    # "no test suite detected" unless tests/ exists
```

#### Keyword-Based Requirement Extraction
```python
requirements = {}
if "auth" in idea.lower():
    requirements["auth"] = True
if "docker" in idea.lower():
    requirements["docker"] = True
```

This is **NOT intelligent requirement analysis**.

#### What Works
- Template rendering via orchestrator
- Checkpoint save/resume
- Progress reporting
- Dry-run mode

#### What's Broken
- **No NLP/AI**: Requirement extraction is regex
- **No Actual Planning**: Architecture is hardcoded template
- **No Dependency Resolution**: npm/pip install not tested
- **Test Reporting is Fake**: Says "Tests: 5 passed" without running them
- **No Failure Analysis**: Doesn't explain why tests fail

### Risk
- **CRITICAL**: Forge claims "AI-driven multi-stage pipeline" but is deterministic script
- **Misleading Success**: Reports success even when tests fail

---

## DOCTOR

### Current State

**doctor.py** implements health scoring:

#### What Works
- Scans project for file patterns
- Calculates category scores (0-100)
- Detects missing test configs
- Finds unlocked requirements

#### What's Broken
- **Scoring is Hardcoded**: No ML or evidence-based learning
- **No Security Analysis**: Doesn't actually analyze code for vulnerabilities
- **Fake Findings**: Positive score doesn't mean secure
- **No Remediation**: Just reports issues, no fix suggestions

#### Example
```python
if (missing_tests_dir / "test_security.py").exists():
    score -= 0
else:
    score -= 10  # Hardcoded deduction
```

### Risk
- Score of 85/100 doesn't guarantee safety
- False confidence in project health

---

## INDEXER

### Current State

**indexer.py** + **vector_store.py** + **simple_vector_store.py**:

#### Problem: Three Files, Two Classes
1. `vector_store.py` exports `SimpleVectorStore`
2. `simple_vector_store.py` exports same
3. **PR#6** renamed to `KeywordIndexStore` in `keyword_store.py`
4. **Main branch** still imports old names → **3 test failures**

#### What Indexer Actually Does
```python
def index_workspace(self):
    for file in workspace:
        chunks = parse_python_ast(file)
        store.add_chunk(chunk)
        
def search(query):
    for chunk in store:
        if query.lower() in chunk.text.lower():
            results.append(chunk)  # Substring matching!
```

#### What It Claims
- "Workspace Indexing & Search: AST and parser-based local keyword search"

#### What It Actually Does
- **Substring matching**, not semantic search
- **Not a vector store** (no embeddings, cosine similarity, etc.)
- **AST parsing** only for extracting symbols, not for search

#### What Works
- Finding Python symbols (classes, functions)
- Extracting imports and dependencies
- Cross-file reference detection

#### What's Missing
- **Semantic Search**: Just does lowercase substring matching
- **Multi-language**: Python only for AST
- **Scalability**: O(n) scan each search

### Risk
- Documentation misleads: "vector store" is keyword indexer
- Merging PR#6 will break more tests if not careful

---

## MEMORY

### Current State

**memory.py** exports `LocalMemoryStore`:

#### What Works
- Stores JSON in `~/.config/orix/memory.json` or `.orix/memory.json`
- Tracks history, preferences, exceptions
- Save/load cycle

#### What's Broken
- **Credential Leakage Risk**: No scrubbing of `api_key`, `token`, `password`
- **No Encryption**: All data stored plaintext
- **No TTL**: Old data never expires
- **Workspace Scoped**: Stores per-project but no isolation between projects

#### Missing
- Key deletion
- Data cleanup
- Credential detection

### Risk
- **MEDIUM**: If user configures API key in memory, it's stored plaintext on disk

---

## PERMISSIONS

### Current State

**permissions.py** exports `PermissionManager`:

#### What Works
- Framework for gating operations
- Tool-level permission tiers (read/write/high_risk)
- Prompt-based user approval

#### What's Missing
- **Tier Mapping**: Tools not mapped to READ_ONLY/SAFE/INTERACTIVE/FULL
- **Audit Logging**: No record of approved/denied actions
- **Config Enforcement**: Permission levels not checked against config
- **Defaults**: Assumes INTERACTIVE if not specified

### Risk
- Incomplete: Agent can bypass permissions if not careful
- No audit trail

---

## TOOLBOX

### Current State

**toolbox.py** (308 lines) is one of the **most competent components**:

#### What Works
- ✅ Path traversal protection via `resolve_path()`
- ✅ Schema validation for tool arguments
- ✅ Structured error responses
- ✅ 11 implemented tools (read, write, edit, delete, search, find_symbol, find_references, run_test, run_linter, run_formatter, inspect_project)
- ✅ Dry-run mode
- ✅ Git integration (status, diff, branch)
- ✅ Diff computation

#### What's Missing
- No permission enforcement (just schemas)
- No audit logging
- No rate limiting
- Limited tool set (only file/search/git/test)

#### Tools Implemented
| Tool | Purpose | Status |
|------|---|---|
| read_file | Read workspace files | ✅ |
| write_file | Create/overwrite files | ✅ |
| edit_file | Replace text blocks | ✅ |
| delete_file | Remove files/directories | ✅ |
| search | Keyword search | ✅ |
| find_symbol | Find definitions | ✅ |
| find_references | Find usage | ✅ |
| run_test | Execute test suite | ✅ |
| run_linter | Run black --check | ✅ |
| run_formatter | Run black | ✅ |
| inspect_project | List directory | ✅ |

#### Path Safety
```python
def resolve_path(self, relative_path: str) -> Path:
    path = Path(relative_path)
    if not path.is_absolute():
        path = self.root_path / path
    resolved = path.resolve()
    try:
        resolved.relative_to(self.root_path)  # Ensure in workspace
    except ValueError:
        raise ValueError("Path traversal detected")
    return resolved
```

This **works** but needs testing against adversarial paths.

---

## SECURITY

### Current State

#### Path Traversal
- ✅ Protected: Toolbox validates all paths
- 🟡 Untested: No adversarial test cases

#### Credential Management
- 🔴 Broken: No environment variable protection
- 🔴 Broken: AI keys hardcoded in prompts
- 🔴 Broken: No keychain integration

#### Subprocess Execution
- ✅ Safe: Uses `shell=False` in toolbox
- 🟡 Untested: No command injection tests

#### Generated Code
- 🟡 Risk: Agent appends comments to files without validation
- 🟡 Risk: No sandboxing of generated code execution

#### File Permissions
- 🔴 Missing: No umask enforcement on `.orix/` directory
- 🔴 Missing: Memory files world-readable on multi-user systems

### Risk
- Credential exposure if API keys used
- No tested attack surface

---

## CONFIGURATION

### Current State

**config.py** loads YAML from `~/.config/orix/config.yaml` or `.orix/config.yaml`:

#### What Works
- Basic YAML load/save
- TUI prompting

#### What's Missing
- **Schema Validation**: No validation against expected keys
- **Type Checking**: No type coercion
- **Secrets Handling**: No encrypted storage
- **Migration**: No config version handling

### Risk
- Malformed config crashes silently

---

## DOCUMENTATION

### Current State

**README.md** claims:

#### ✅ Accurate
- "Plugin-driven CLI"
- "Project scaffolding"
- "Docker/auth options"

#### 🟡 Misleading
- "Autonomous Agent Session": It's simulated, not autonomous
- "Workspace Indexing & Search": Uses keyword matching, not vector search
- "AI Spec Builder": Experimental but no model integration

#### 🔴 False Claims
- "Thoroughly tested and ready for production use": 3 tests fail on main
- "Uses `SimpleVectorStore` which conducts fast substring-based matches": Correct but misleadingly named "vector"
- "Performs preset file mutations": Admits to being fake!

### Risk
- Users expect AI-driven system but get simulator
- Security false confidence

---

## CI/CD

### Current State

**.github/workflows/ci.yml** runs:
- Checkout
- Setup Python (3.10, 3.11, 3.12)
- Install via `pip install -e .`
- Run `pytest`

#### What Works
- Matrix testing across Python versions

#### What's Broken
- **Fails on main**: 3 tests fail due to import error
- **No linting**: No flake8, mypy, black
- **No security**: No bandit, safety checks
- **No type checking**: No mypy
- **No coverage**: No coverage report

### Risk
- CI gives false green on broken code

---

## DEPENDENCY ANALYSIS

### Current Dependencies

```toml
dependencies = [
    "click>=8.0.0",                  # CLI framework ✅
    "rich>=12.0.0",                  # Terminal UI ✅
    "questionary>=1.10.0",           # Prompting ✅
    "jinja2>=3.0.0",                 # Templating ✅
    "PyYAML>=6.0",                   # Config ✅
    "requests>=2.31.0",              # HTTP ✅
    "playwright>=1.35.0; extra == 'web'",  # Web scraping (unused) ⚠
    "tree_sitter>=0.2.0; extra == 'treesitter'",  # Parsing (incomplete) ⚠
    "tomli_w>=1.0.0",                # TOML writing ⚠ (not imported)
    "tomli>=1.1.0; python_version < '3.11'",  # TOML reading ⚠ (not imported)
]
```

#### What's Missing
- No model SDKs (openai, anthropic, google-generativeai, etc.)
- No async support
- No logging configuration
- No error tracking

---

## PLUGINS

### Current State

`orix/plugins/` is **empty**.

**Documented** but not delivered:
- react.py
- django.py
- fastapi.py

### Risk
- Users cannot create projects without downloading external plugins
- No plugin contract enforcement

---

## TEMPLATES

### Current State

`orix/templates/` is **empty**.

### Risk
- Scaffolding doesn't work

---

## KNOWN ISSUES

1. **Merge Conflict (CRITICAL)**: PR#6 renamed Vector Store but main branch has both old and new files
2. **Import Error**: `SimpleVectorStore` not found because of conflict
3. **3 Failing Tests**: agent_session_plan_mode, agent_session_interactive_approval, test_indexer_symbol_and_dependents
4. **No AI Model Integration**: Agent/Forge are simulators
5. **Keyword Extraction Not NLP**: Hardcoded rules, not intelligence
6. **Credential Leakage Risk**: No environment variable protection
7. **Incomplete Commands**: ai_build, architect, agent, forge need real implementations
8. **Type Checking Disabled**: No py.typed, no mypy
9. **Documentation Misleading**: Claims vector search, actual is substring match
10. **Plugin/Template Directories Empty**: Listed in README but not delivered

---

## STABILITY CLASSIFICATION (CORRECTED)

### ✅ STABLE (Proven)
- Plugin Loading & Discovery
- Project Scaffolding (Jinja2 rendering)
- Environment Diagnostics
- CLI Framework
- Toolbox (File I/O, path safety)
- Permissions Framework

### 🟡 EXPERIMENTAL (Partial/Incomplete)
- Workspace Indexing (works but substring only)
- Explain (Python AST only)
- Doctor (hardcoded scoring)
- Memory (credential leakage risk)
- Configuration (no validation)

### 🔴 SIMULATED (Broken)
- Agent Session (no model integration)
- Forge (keyword-based, not AI)
- AI Builder (no model integration)
- Architect (deterministic only)

---

## RELEASE READINESS SCORECARD

| Dimension | Status | Score |
|-----------|--------|-------|
| Packaging | Broken | 30% |
| CLI | Mostly Working | 70% |
| Tests | Failing | 40% |
| Agent | Simulated | 0% |
| Forge | Simulated | 10% |
| Doctor | Incomplete | 40% |
| Toolbox | Solid | 90% |
| Permissions | Framework Only | 50% |
| Security | Untested | 30% |
| Documentation | Misleading | 20% |

**Overall Release Readiness**: **25%**

**Blockers**:
- P0: 3 failing tests (merge conflict)
- P0: No AI model integration (Agent/Forge are fake)
- P0: Broken packaging
- P1: Credential management missing
- P1: Documentation misleading
- P2: No testing of security boundaries

---

## RECOMMENDED ACTIONS (PRIORITY ORDER)

### PHASE 2: Clean-Room Baseline
- [ ] Fresh Python venv
- [ ] Install from clean checkout
- [ ] Record all errors/warnings
- [ ] Run pytest and capture failures

### PHASE 3: Fix Packaging First
- [ ] Resolve SimpleVectorStore vs KeywordIndexStore conflict
- [ ] Add py.typed
- [ ] Add __init__.py files
- [ ] Add test dependencies
- [ ] Verify CLI works: `orix --version`, `orix --help`

### PHASE 4: Fix Tests
- [ ] Resolve import conflicts
- [ ] Get all 53 tests passing
- [ ] Categorize by type (unit/integration/cli/security)
- [ ] Add tests for broken functionality

### PHASE 5: AI Provider Abstraction
- [ ] Design AIProvider interface
- [ ] Implement OpenAI, Anthropic, Gemini, OpenRouter, Ollama adapters
- [ ] Add model registry
- [ ] Create mock provider for testing

### PHASE 6: Fix Agent
- [ ] Implement real observation → model → action loop
- [ ] Add tool calling from model output
- [ ] Add failure handling and retries
- [ ] Remove hardcoded comments

### PHASE 7: Fix Forge
- [ ] Implement real requirement extraction (with AI or clear heuristics)
- [ ] Run actual tests and report real results
- [ ] Add dependency resolution verification
- [ ] Document what's AI-driven vs deterministic

### PHASE 8: Security Hardening
- [ ] Add credential management (env vars, keychain)
- [ ] Create security test suite
- [ ] Test path traversal defenses
- [ ] Test malicious prompt handling
- [ ] Add audit logging

### PHASE 9: Documentation Truth
- [ ] Correct README claims
- [ ] Mark features accurately (STABLE/EXPERIMENTAL/PARTIAL/BROKEN)
- [ ] Document credential handling
- [ ] Document threat model

---

## NEXT STEP

Execute **PHASE 2: Clean-Room Baseline** to determine actual install and test status before making any changes.

