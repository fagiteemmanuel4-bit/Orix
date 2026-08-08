# 🌌 Orix X

```
   ____         _       
  / __ \_______(_)  __  
 / / / / __/ __/ / |/_/  
/ /_/ / / / / / />  <    
\____/_/ /_/ /_/_/|_|    

⚡ UNIVERSAL DEVELOPER CLI PLATFORM ⚡
       Version 3.1.0
```

**Orix X** is an independent, plugin-driven CLI designed to bootstrap apps and infrastructure faster than traditional generators. Instead of hardcoding every stack, Orix loads framework support as plugins at runtime, renders Jinja2 templates into a target folder, and delivers production-ready boilerplate — including auth, CI, and environment diagnostics.

Orix is built for developers, automation, and AI agents. It supports interactive prompts, deterministic CLI flags, and YAML spec files, so it works like `git`, `npm`, `gh`, `cargo`, or `nx` in modern workflows.

---

## 📊 Feature Stability Classification

To make Orix trustworthy, all features are classified by their stability and readiness below:

### ✅ Stable (Actually Works)
*These features are fully implemented, thoroughly tested, and ready for production use.*
- **Plugin Loading & Discovery**: Auto-discovery and loading of framework plugins from directory without core changes.
- **Project Scaffolding / Orchestration**: Wires plugins, CLI context, and specs to orchestrate clean project generation.
- **Jinja2 Recursive Rendering**: Walks directory structure and renders dynamic contents, file names, and directories.
- **Environment Diagnostics**: Verifies host development dependencies (`python`, `node`, `git`, `docker`).
- **Interactive TUI Config Editor**: Prompts and configures development roles, endpoints, and key models.
- **Deterministic CLI Flags & Specs**: Supports non-interactive runs via click options or structured YAML specifications.

### 🧪 Experimental (Exists but subject to change)
*These features exist in the codebase but are currently under refinement or have mocked integrations.*
- **AI Spec Builder (`ai_build`)**: Uses remote LLMs (e.g. OpenRouter/OpenAI-compatible) to synthesize scaffolding specs from natural language. Requires external API keys and has schema validators.
- **Web Research Tool (`/research`)**: Fetches titles/paragraphs using simple requests or playwright.
- **Workspace Indexing & Search**: Built-in AST and parser-based local keyword search. Uses `SimpleVectorStore` which conducts fast substring-based matches.
- **Autonomous Agent Session (`agent`)**: Autonomous multi-agent development loop simulation. Employs user-permission guard rails but currently performs preset file mutations.

### 📅 Planned (Not Implemented)
*These features are part of the Orix X roadmap and do not yet have executable implementations.*
- **Docker Scaffolding Generation**: Currently under template design. The interactive CLI accepts `--docker` but no Dockerfiles are rendered in default template packages yet.
- **Multi-Agent Coding Workspace**: Multi-agent collaborative reasoning loops with custom sandbox isolation.

---

## 🛠️ Architecture

```
orix/
├── core/
│   ├── cli.py             # Click-based CLI entrypoint (orix create)
│   ├── orchestrator.py    # Wires plugins + renderer together, drives generation
│   ├── plugin_manager.py  # Discovers and loads plugins from orix/plugins/
│   ├── renderer.py        # Recursive Jinja2 template renderer
│   └── ui.py               # TUI: banner, prompts (rich + questionary)
├── sdk/
│   └── base.py             # BasePlugin / FrameworkPlugin abstract classes
├── plugins/
│   ├── react.py            # React framework plugin
│   ├── django.py           # Django framework plugin
│   └── fastapi.py          # FastAPI framework plugin
└── templates/
    ├── react/               # React project template
    ├── django/              # Django project template
    └── fastapi/             # FastAPI project template
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

### Interactive mode (human-friendly)

```bash
orix create
```

You'll get the Orix banner, a framework picker, and prompts for any options the chosen framework supports.

### Deterministic mode (scriptable / AI-agent-friendly)

```bash
orix create my-project --framework react --no-docker --auth
```

Orix is designed to be called directly from automation and AI tools. Use exact flags or a YAML spec to make scaffolding reproducible and agent-ready.

```bash
orix create --spec orix.yaml
orix plugin-install https://github.com/your-org/orix-react-plugin.git
orix diagnose
orix ai-build
```

---

## 🧪 Development & Testing

Run the full automated test suite containing 35 units, integrations, CLI runner, and safety checks:

```bash
pytest
```

---

## 📄 License

Orix X is open-source software licensed under the **MIT License**.
