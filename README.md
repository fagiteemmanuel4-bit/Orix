# 🌌 Orix X

```
   ____         _       
  / __ \_______(_)  __  
 / / / / __/ __/ / |/_/  
/ /_/ / / / / / />  <    
\____/_/ /_/ /_/_/|_|    

⚡ UNIVERSAL DEVELOPER CLI PLATFORM ⚡
       Version 2.0.0
```

**Orix X** is an independent, plugin-driven CLI designed to bootstrap apps and infrastructure faster than traditional generators. Instead of hardcoding every stack, Orix loads framework support as plugins at runtime, renders Jinja2 templates into a target folder, and delivers production-ready boilerplate — including Docker, auth, CI, and environment diagnostics.

Orix is built for developers, automation, and AI agents. It supports interactive prompts, deterministic CLI flags, and YAML spec files, so it works like `git`, `npm`, `gh`, `cargo`, or `nx` in modern workflows.

---

## 🚀 Key Features

- **Plugin-based architecture** — Each framework (React, Django, FastAPI) is a self-contained plugin built on a shared SDK (`BasePlugin` / `FrameworkPlugin`). Adding a new framework means writing a new plugin, not touching the core.
- **Modular core engine** — Orchestration, plugin discovery, and template rendering are fully decoupled (`Orchestrator`, `PluginManager`, `TemplateRenderer`).
- **Interactive TUI** — A `rich` + `questionary` terminal experience that feels polished and approachable.
- **Deterministic CLI mode** — Every prompt option is also available as a flag, so AI agents and scripts can generate projects non-interactively.
- **Spec-driven generation** — Use YAML specs for repeatable, audit-friendly project creation.
- **Recursive Jinja2 templating** — Render placeholders in file contents, file names, and directory names across entire project trees.
- **Auto-loaded plugins** — Drop a new plugin into `orix/plugins/` and `PluginManager` discovers it automatically, with no core changes required.

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

**How it works under the hood:**
1. `PluginManager` scans `orix/plugins/`, dynamically imports every module, and registers any class that subclasses `BasePlugin`.
2. `cli.py` lists the available frameworks and, in interactive mode, prompts you to pick one and answer its `get_questions()` (e.g. "Include Docker?").
3. `Orchestrator.generate()` builds a context dict from your project name + answers + the plugin's `get_context()` output (e.g. Django gets an auto-generated `secret_key`).
4. `TemplateRenderer` walks the matching template folder under `orix/templates/`, rendering directory names, file names, and file contents through Jinja2, and writes the result to your target folder.

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

You'll get the Orix banner, a framework picker, and prompts for any options the chosen framework supports (Docker, auth, etc).

### Deterministic mode (scriptable / AI-agent-friendly)

```bash
orix create my-project --framework react --docker --auth
```

Orix is designed to be called directly from automation and AI tools. Use exact flags or a YAML spec to make scaffolding reproducible and agent-ready.

```bash
orix create --spec orix.yaml
orix plugin_install https://github.com/your-org/orix-react-plugin.git
orix diagnose
orix ai_build
```

All flags can be mixed — anything you don't pass will fall back to an interactive prompt for that option.

**Supported flags:**

| Flag | Description |
|---|---|
| `project_name` | Name of the project / output folder (positional, optional) |
| `--framework` | One of: `react`, `django`, `fastapi` |
| `--docker` / `--no-docker` | Include Docker configuration |
| `--auth` / `--no-auth` | Include auth boilerplate (JWT for FastAPI, DRF auth for Django, auth scaffolding for React) |
| `--spec` | Path to a YAML spec file, making generation repeatable |
| `--output` | Output folder / path for generated project |

---

## 🤖 AI Builder

Orix can use an AI model to generate a scaffold spec automatically. Provide an OpenRouter/OpenAI-compatible endpoint and API key, then describe the app you want to build.

```bash
orix ai_build
```

The AI builder writes `orix_ai_spec.yaml` and generates a project from the returned spec. All payment and model access is handled by the user.

---

## 🔌 Currently Supported Frameworks

| Framework | Docker | Auth |
|---|---|---|
| React | ✅ | ✅ |
| Django | ✅ | ✅ (DRF) |
| FastAPI | ✅ | ✅ (JWT) |

---

## 🧩 Writing Your Own Plugin

Orix is designed so new framework support doesn't require touching the core. To add one:

1. Create `orix/plugins/<name>.py` with a class extending `FrameworkPlugin` from `orix.sdk.base`.
2. Implement `name`, `get_template_name()`, `get_questions()`, and `get_context()`.
3. Add a matching template folder under `orix/templates/<name>/` using Jinja2 placeholders for any dynamic content, file names, or folders.
4. Drop it in — `PluginManager` will discover it automatically on the next run.

---

## 🧪 Development

```bash
pytest
```

---

## 📄 License

Orix X is open-source software licensed under the **MIT License**.
