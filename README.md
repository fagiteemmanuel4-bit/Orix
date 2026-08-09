# 🌌 Orix X

```
   ____         _       
  / __ \_______(_)  __  
 / / / / __/ __/ / |/_/  
/ /_/ / / / / / />  <    
\____/_/ /_/ /_/_/|_|    

⚡ UNIVERSAL DEVELOPER OS CLI PLATFORM ⚡
       Version 3.1.0
```

**Orix** is an extensible developer environment CLI and model-agnostic AI-native engineering assistant. It decouples app scaffolding, local workspace diagnostics, system blueprinting, and multi-stage generation from underlying model instances.

Orix is built for engineers and AI agents. It integrates interactive prompting, automated testing, structural verification, and explicit permission boundaries.

---

## 📊 Feature Stability Classification

To make Orix trustworthy, all features are classified by their stability and readiness below:

### ✅ Stable (Actually Works)
- **Plugin Loading & Discovery**: Auto-discovery of custom plugins and frameworks at runtime.
- **System Architecture Specifier (`orix architect`)**: Designs system spec blueprints under `.orix/` (`architecture.yaml`, `plan.yaml`, and `decisions.md`).
- **Resumable Scaffold Workflow (`orix/forge`)**: Coordinates a multi-stage project generation loop with resumption capabilities (`.orix/forge_checkpoint.json`).
- **Structured Workspace Toolbox**: Standardized schemas and boundary protection checks covering reads, searches, and file creations.
- **Evidence-Driven Diagnostics (`orix doctor`)**: Transparent, severity-categorized project health scorecard mapping issues to clear scores.
- **Code Explain Analyzer (`orix explain`)**: Statically parses directory layouts or source file components, imports, and risks.
- **Model-Agnostic Providers**: Pluggable support for OpenAI, Anthropic, Gemini, OpenRouter, and local Ollama interfaces.
- **Deterministic Agent Evaluator (`orix eval`)**: Automated metrics logging (token counts, iterations, passes) across isolated test sandboxes.

### 🧪 Experimental (Subject to change)
- **Autonomous Coding Agent Session (`orix agent`)**: Active model-driven loop matching `OBSERVE -> PLAN -> REQUEST PERMISSION -> ACT -> TEST -> OBSERVE RESULT -> FIX -> VERIFY`.
- **Project Indexing & Dependents Tracking**: Parses imports and cross-module dependents using local AST logic.

---

## 🛠️ Architecture

```
orix/
├── core/
│   ├── cli.py             # Click-based CLI commands and entry points
│   ├── architect.py       # Heuristic and structural system blueprinting
│   ├── forge.py           # Multi-stage resumable project scaffolding workflow
│   ├── ai_providers.py    # Model-agnostic AI provider abstractions
│   ├── doctor.py          # Evidence-driven workspace diagnostics
│   ├── explain.py         # Static code structure and execution flow analyst
│   ├── eval.py            # Agent performance sandboxed scorecard evaluation
│   ├── indexer.py         # AST syntax and module imports analyzer
│   ├── keyword_store.py   # Truthful local workspace keyword database (was SimpleVectorStore)
│   ├── orchestrator.py    # Wires plugins + renderer together, drives generation
│   ├── plugin_manager.py  # Discovers and loads plugins from orix/plugins/
│   └── toolbox.py         # Schema-validated tools and workspace boundary protection
├── sdk/
│   └── base.py            # SDK Base classes
└── plugins/               # Framework plugins
```

---

## 📦 Installation

```bash
git clone https://github.com/fagiteemmanuel4-bit/Orix.git
cd Orix
pip install -e .
```

Requires Python 3.10+.

---

## 🚀 Usage

### Command Summary

```bash
# Generate architecture plan
orix architect "Build a FastAPI SaaS"

# Execute multi-stage resumable scaffolding
orix forge "Build an inventory app"

# Execute evidence-driven project diagnostics
orix doctor

# Graph file structure and explain flow
orix explain orix/core/cli.py

# Run sandboxed agent evaluation scorecard
orix eval

# List local Ollama and configured cloud model statuses
orix ai models
```

---

## 🧪 Development & Testing

Orix prioritizes rigorous automated verification. Run the full test suite with 50+ passing tests across indexer, toolbox, doctor, agent, and security boundaries:

```bash
pytest
```

---

## 📄 License

Orix is open-source software licensed under the **MIT License**.
