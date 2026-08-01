# 🌌 Orix X

```
   ____         _       
  / __ \_______(_)  __  
 / / / / __/ __/ / |/_/  
/ /_/ / / / / / />  <    
\____/_/ /_/ /_/_/|_|    

⚡ UNIVERSAL PROJECT GENERATION ENGINE & SCAFFOLDING PLATFORM ⚡
            Engineered by Kryonara • Version 2.0.0
```

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Testing](https://img.shields.io/badge/Tests-Passing-green.svg)](tests/)

**Orix X** is an enterprise-grade, plugin-driven CLI application designed to scaffold modern, production-ready, security-hardened project structures in seconds. By decoupling the core generation engine from framework templates, Orix X operates on a runtime plugin architecture that dynamically detects, registers, and loads framework generation logic without requiring manual changes to the core system.

Orix X is optimized for both human development workflows (using rich, interactive Terminal User Interfaces) and automated/AI agentic pipelines (utilizing deterministic, non-interactive CLI flags).

---

## 🚀 Key Features

* **🔌 Decoupled Plugin Architecture**: Dynamically registers framework plugins (`React`, `Django`, `FastAPI`) via standard class inspection. Adding support for a new framework requires no changes to core logic.
* **⚡ Interactive TUI & Non-Interactive CLI**: Seamlessly switches between a gorgeous TUI powered by `rich` and `questionary`, and a fast, scriptable, agent-friendly deterministic mode.
* **🔧 Recursive Jinja2 Template Engine**: Supports variable replacement inside file contents, filenames, and nested directory paths.
* **🛡️ Security-First Defaults**: Standard generation includes secure-entropy secret keys and robust, isolated Docker configurations.
* **🧪 Test-Driven & Standardized**: Features high-fidelity unit and integration test suites, alongside comprehensive open-source contributing, security, and governance models.

---

## 🛠️ Architecture Overview

```
orix/
├── core/
│   ├── cli.py             # Click CLI commands (orix create, list)
│   ├── orchestrator.py    # Main orchestration pipeline
│   ├── plugin_manager.py  # Runtime dynamic plugin discovery & introspection
│   ├── renderer.py        # Recursive Jinja2 template renderer
│   └── ui.py              # High-fidelity TUI prompts (rich + questionary)
├── sdk/
│   └── base.py            # BasePlugin & FrameworkPlugin SDK contracts
├── plugins/
│   ├── react.py           # React template plugin module
│   ├── django.py          # Django template plugin module
│   └── fastapi.py         # FastAPI template plugin module
└── templates/
    ├── react/             # React boilerplate files & configs
    ├── django/            # Django project structure & configuration
    └── fastapi/           # FastAPI app setup & requirements
```

---

## 📦 Installation & Setup

Ensure you have **Python 3.10+** installed on your system.

### Install from Source (Development Mode)

```bash
git clone https://github.com/fagiteemmanuel4-bit/Orix.git
cd Orix
pip install -e .
```

### Running Tests

To verify your installation and environment, run the standard test suite:

```bash
python3 -m pytest
```

---

## 🚀 Usage Guide

Orix X can be run in **interactive mode** for humans or **deterministic mode** for scripts and AI agents.

### 1. Interactive Mode (TUI)

Simply type `orix create` without any positional arguments to trigger the high-fidelity wizard:

```bash
orix create
```

This will display the official Orix X banner, prompt you for a project name, show an interactive framework selector, and display multi-select configuration options (e.g. including Docker, enabling Authentication).

### 2. Deterministic Mode (Script / AI Agent)

Pass configuration options as standard CLI arguments to bypass prompts:

```bash
orix create my-enterprise-api --framework fastapi --docker --auth
```

All flags are fully decoupled and can be combined:

| Flag / Option | Type | Description |
|---|---|---|
| `project_name` | Positional | The output directory name |
| `--framework` | Option | Framework plugin to load (`react`, `django`, `fastapi`) |
| `--docker` / `--no-docker` | Flag | Toggle multi-stage Docker environment configurations |
| `--auth` / `--no-auth` | Flag | Toggle framework-specific authentication boilerplate |
| `--dry-run` | Flag | Print generation paths and variables without writing to disk |

---

## 🔌 Currently Supported Scaffolds

| Scaffold Plugin | Docker Setup | Auth Boilerplate | Features Included |
|---|---|---|---|
| **React** | ✅ Included | ✅ Ready | Standard setup, modern React Router structure |
| **Django** | ✅ Included | ✅ Rest Framework | Auto-generated secure tokens, ready-to-run settings |
| **FastAPI** | ✅ Included | ✅ JWT-based | Standard dependency injection, routers, requirements |

---

## 🧩 Writing Your Own Plugin

Orix X's plugin-loader automatically discovers and integrates custom plugins without editing any central configuration files.

1. **Create Python Plugin**: Create `orix/plugins/<your_framework>.py` inheriting from `FrameworkPlugin`:
   ```python
   from orix.sdk.base import FrameworkPlugin

   class MyFrameworkPlugin(FrameworkPlugin):
       @property
       def name(self): return "custom-fw"
       def get_template_name(self): return "custom-fw"
       def get_questions(self): return []
       def get_context(self, answers): return {}
   ```
2. **Add Templates**: Create a matching folder inside `orix/templates/custom-fw/`. Use standard `{{ project_name }}` placeholders in folder/file names and file contents.
3. **Execute**: Run `orix create` and your custom scaffold will be dynamically loaded and listed inside the TUI selection list.

---

## 🤝 Contributing, Governance & Code of Conduct

We welcome all community contributions. Please refer to our core open-source documents:
- **[Contributing Guidelines](CONTRIBUTING.md)**: Steps to write tests, design plugins, and submit PRs.
- **[Code of Conduct](CODE_OF_CONDUCT.md)**: Core community rules.
- **[Security Policy](SECURITY.md)**: Standard security reporting guidelines.
- **[Governance Model](GOVERNANCE.md)**: Decision-making roles and steer committee paths.
- **[Changelog](CHANGELOG.md)**: Full release and update history.

---

## 📄 License

Orix X is open-source software distributed under the **MIT License**.
