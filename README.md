
# 🌌 Orix

```identity
   ____         _       
  / __ \_______(_)  __  
 / / / / __/ __/ / |/_/  
/ /_/ / / / / / />  <    
\____/_/ /_/ /_/_/|_|    
                         
⚡ LIGHTWEIGHT MULTI-FRAMEWORK PROJECT SCAFFOLDER ⚡
       Engineered by Kryonara • Version 1.0.0

```

> **Orix** is a lightweight, zero-dependency multi-framework project scaffolder engineered by **Kryonara**. It generates ready-to-edit, production-grade starter templates for modern web, mobile, and backend stacks in seconds.

---

## 📋 Table of Contents

* [Overview](https://www.google.com/search?q=%23-overview)
* [Key Features](https://www.google.com/search?q=%23-key-features)
* [Quick Start](https://www.google.com/search?q=%23-quick-start)
* [Usage](https://www.google.com/search?q=%23-usage)
* [For Human Developers (Interactive UI)](https://www.google.com/search?q=%23for-human-developers-interactive-ui)
* [For AI Agents & Automation (Deterministic Flags)](https://www.google.com/search?q=%23for-ai-agents--automation-deterministic-flags)


* [Architecture & Tech Stack](https://www.google.com/search?q=%23-architecture--tech-stack)
* [Configuration](https://www.google.com/search?q=%23%25EF%25B8%258F-configuration)
* [Development & Testing](https://www.google.com/search?q=%23-development--testing)
* [Contributing](https://www.google.com/search?q=%23-contributing)
* [Security](https://www.google.com/search?q=%23-security)
* [License](https://www.google.com/search?q=%23-license)
* [Contact](https://www.google.com/search?q=%23-contact)

---

## 👁️ Overview

Setting up new projects is plagued by repetitive boilerplate configuration—wiring up database containers, configuring modern authentication layers, and setting up CI/CD pipelines. **Orix** eliminates this friction.

Built for Python 3.10+ environments, Orix instantly provisions structurally flawless workspaces for **React, Next.js, Django, FastAPI, and Flutter**. It is explicitly designed with a dual-input layer: an elegant, responsive terminal interface for human software engineers, and a strict, deterministic flag-driven interface for **autonomous AI coding agents** (e.g., Cursor, Claude Engineer, AutoGPT).

With Orix, you go from a blank directory to an isolated, dockerized, auth-ready development environment in under 5 seconds.

---

## ✨ Key Features

* ⚡ **Multi-Framework Velocity:** Instantly scaffolds production layouts for React, Next.js + Tailwind CSS, Django, FastAPI, and Flutter.
* 🐳 **Instant Containerization:** Generates custom, working `Dockerfile` and `docker-compose.yml` setups automatically mapped to persistent databases.
* 🔒 **Zero-Placeholder Auth Boilerplate:** Injects actual working authentication logic (JWT/Session states) directly into your templates out of the box.
* 🤖 **AI-Agent Determinism:** Clean, non-interactive CLI flag structures allow LLM-driven development tools to automate directory setup seamlessly.
* 🎨 **Premium TUI Experience:** Implements an incredibly clean, responsive terminal UI using `rich` and `questionary` with live operational spinners.

---

## 🚀 Quick Start

### Prerequisites

* **Python 3.10** or newer
* `pip` and `pipx` (recommended for global CLI execution)

### Installation

#### Method 1: Instant Global Run (Recommended)

Run Orix instantly without manually cloning or polluting your global package scope:

```bash
pipx run orix

```

#### Method 2: Local Development Installation

If you are building custom templates or contributing to the core engine:

```bash
# Clone the repository
git clone [https://github.com/fagiteemmanuel4-bit/Orix.git](https://github.com/fagiteemmanuel4-bit/Orix.git)
cd Orix

# Initialize an isolated environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with development configurations
pip install -e .

```

---

## 🛠️ Usage

### For Human Developers (Interactive UI)

Simply execute the root command. Orix will clear your terminal environment, render the Kryonara signature banner, and walk you through a beautifully color-coded configuration wizard:

```bash
orix

```

### For AI Agents & Automation (Deterministic Flags)

AI agents can bypass the interactive prompts entirely by passing raw explicit configuration flags. This ensures deterministic, repeatable directory outputs:

```bash
# Example: Create a production-ready Next.js frontend with a FastAPI backend, Docker setups, and Auth layers
orix create my-workspace --framework nextjs --backend fastapi --docker --auth

```

---

## 🏗️ Architecture & Tech Stack

Orix is built cleanly using a modular template-rendering design pattern. It relies on a high-performance Python micro-stack:

* **CLI Parsing & Routing:** `click`
* **Interactive Prompts:** `questionary`
* **Terminal UI/UX Rendering & Spinners:** `rich`
* **Package Management & Distribution:** `setuptools` + `pyproject.toml`

```
orix/
├── core/
│   ├── __init__.py
│   ├── cli.py            # CLI flag parsing & execution routers
│   ├── engine.py         # File IO writing and placeholder injection strings
│   └── ui.py             # Rich layout interfaces and terminal terminal controls
└── templates/            # Raw, deterministic boilerplates (React, Django, Next, etc.)

```

---

## ⚙️ Configuration

Orix evaluates both runtime flags and local shell environment variables to customize your generation engines securely.

| Environment Variable | Description | Default Value |
| --- | --- | --- |
| `ORIX_DEFAULT_AUTHOR` | Automatically seeds the `package.json` or project headers | `Kryonara Developer` |
| `ORIX_AUTO_DOCKER` | Forces container generation across all initializations | `false` |
| `ORIX_THEME_COLOR` | Tweaks the terminal output interface highlights | `purple` |

> ⚠️ **Note on Secrets:** When generating Django or FastAPI templates, Orix automatically generates cryptographically secure, randomized secret keys. These are written directly to a local, untracked `.env` file. Never commit these raw `.env` files to source control.

---

## 💻 Development & Testing

We enforce strict linting and continuous type safety to make sure Orix stays lightweight and blazing fast.

### Local Quality Controls

```bash
# Format codebase using Black
black core/ tests/

# Run static type compliance verification
mypy core/

# Execute the testing suite
pytest tests/

```

---

## 🤝 Contributing

We welcome contributions from engineers and AI automation loop builders alike. To maintain high-velocity progress:

1. Fork the repository.
2. Create a logically isolated feature branch (`git checkout -b feature/amazing-new-framework`).
3. Ensure **zero placeholders** remain in your generated boilerplates. Write robust, full-string configurations.
4. Run `pytest` to verify your changes pass local engine verification.
5. Open a Pull Request detailing your optimizations.

---

## 🔒 Security

For security vulnerabilities, please do not open public GitHub issues. Instead, reach out directly to the **Kryonara Security Team** at `security@kryonara.com`. Vulnerabilities will be triaged and patched within 24 hours.

---

## 📄 License

Orix is open-source software licensed under the **MIT License**. See the `LICENSE` file for the comprehensive legal text.

---

## 🏢 Contact

* **Maintained By:** Kryonara Engineering Team
* **GitHub Repository:** [fagiteemmanuel4-bit/Orix]()

```

```
