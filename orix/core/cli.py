import os
import subprocess
import sys
import click
import yaml
from rich.panel import Panel
from rich.table import Table
from orix.core.ai_builder import AIBuilder
from orix.core.agent import AgentSession
from orix.core.diagnostics import EnvironmentDiagnostics
from orix.core.orchestrator import Orchestrator
from orix.core.plugin_manager import PluginManager
from orix.core.ui import TUI, console

# Path to the current directory where the package is installed
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
PLUGINS_DIR = os.path.join(BASE_DIR, "plugins")

@click.group(invoke_without_command=True)
@click.option("--config", is_flag=True, help="Open interactive config editor and exit.")
@click.version_option(version="3.1.0", prog_name="orix")
@click.pass_context
def cli(ctx, config):
    """Orix X: Universal Dev CLI — think git/npm/gh for app scaffolding."""
    if config:
        from orix.core.config_tui import run_config_tui

        run_config_tui()
        ctx.exit()
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

@cli.command()
@click.argument("project_name", required=False)
@click.option("--framework", help="Framework to use.")
@click.option("--docker/--no-docker", default=None, help="Include Docker setup.")
@click.option("--auth/--no-auth", default=None, help="Include Auth logic.")
@click.option("--spec", type=click.Path(exists=True), help="Path to an Orix YAML spec.")
@click.option("--output", type=click.Path(), default=None, help="Absolute or relative output path.")
def create(project_name, framework, docker, auth, spec, output):
    """Create a new project."""
    orchestrator = Orchestrator(TEMPLATES_DIR, PLUGINS_DIR)

    if spec:
        spec_data = orchestrator.load_spec(spec)
        project_name = spec_data.get("project_name")
        framework = spec_data.get("framework")
        docker = spec_data.get("docker")
        auth = spec_data.get("auth")
        output = spec_data.get("output", output)

    if not project_name:
        TUI.display_banner()
        project_name = TUI.prompt_project_name()

    available_frameworks = [p.name for p in orchestrator.plugin_manager.get_plugins_by_type("framework")]

    if not framework:
        framework = TUI.prompt_framework(available_frameworks)

    if framework not in available_frameworks:
        console.print(f"[bold red]Error:[/bold red] Framework '{framework}' is not supported.")
        return

    plugin = orchestrator.plugin_manager.get_plugin_by_name(framework)

    options = {
        "docker": docker,
        "auth": auth
    }

    if project_name and (options["docker"] is None or options["auth"] is None):
        questions = plugin.get_questions()
        remaining_questions = [q for q in questions if options.get(q['name']) is None]
        if remaining_questions:
            new_options = TUI.prompt_options(remaining_questions)
            options.update(new_options)

    if not output:
        output = project_name

    with console.status(f"[bold green]Generating {framework} project: {project_name}..."):
        try:
            path = orchestrator.generate(output, framework, options)
            console.print(f"\n[bold green]Success![/bold green] Project created at: [cyan]{path}[/cyan]")
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")

@cli.command()
@click.argument("source", required=True)
def plugin_install(source):
    """Install a plugin from a local path or git repository."""
    manager = PluginManager(PLUGINS_DIR)
    try:
        installed = manager.install_plugin(source)
        manager.load_plugins()
        console.print(f"[bold green]Installed plugins:[/bold green] {', '.join(installed)}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

@cli.command()
@click.argument("name", required=True)
def plugin_remove(name):
    """Remove a plugin by name."""
    manager = PluginManager(PLUGINS_DIR)
    try:
        path = manager.remove_plugin(name)
        manager.load_plugins()
        console.print(f"[bold green]Removed plugin:[/bold green] {path}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

@cli.command()
def plugin_list():
    """List installed framework plugins."""
    manager = PluginManager(PLUGINS_DIR)
    manager.load_plugins()
    frameworks = [p.name for p in manager.get_plugins_by_type("framework")]
    if not frameworks:
        console.print("[bold yellow]No framework plugins installed.[/bold yellow]")
        return
    console.print("[bold green]Installed frameworks:[/bold green]")
    for framework in frameworks:
        console.print(f"- {framework}")

@cli.command()
def ai_build():
    """Use an AI model to generate an Orix YAML spec and scaffold a project."""
    TUI.display_ai_builder_banner()
    endpoint = TUI.prompt_ai_endpoint()
    api_key = TUI.prompt_api_key()
    model = TUI.prompt_ai_model()
    prompt_text = TUI.prompt_ai_prompt()

    builder = AIBuilder(endpoint, api_key, model)
    try:
        spec_data = builder.build_spec(prompt_text)
        if not spec_data:
            raise ValueError("AI did not return a valid spec.")

        yaml_path = os.path.join(os.getcwd(), "orix_ai_spec.yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(spec_data, f)

        console.print(f"[bold green]AI spec written to:[/bold green] {yaml_path}")
        console.print("[bold green]Generating project from AI spec...[/bold green]")

        orchestrator = Orchestrator(TEMPLATES_DIR, PLUGINS_DIR)
        project_name = spec_data.get("project_name") or "ai-project"
        output = spec_data.get("output", project_name)
        framework = spec_data.get("framework")

        if not framework:
            raise ValueError("AI spec must include a framework.")

        orchestrator.generate(output, framework, {
            "docker": spec_data.get("docker"),
            "auth": spec_data.get("auth"),
        })
        console.print(f"[bold green]Success![/bold green] Project generated at: [cyan]{output}[/cyan]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

@cli.command()
@click.option("--mode", default="interactive", type=click.Choice(["plan", "interactive", "force"]), help="Agent mode to use: plan, interactive, force.")
@click.option("--prompt", default=None, help="Initial prompt for the agent.")
@click.option("--image", default=None, help="Optional image guidance path.")
@click.option("--dry-run/--no-dry-run", default=False, help="Preview edits without applying them.")
@click.option("--force/--no-force", default=False, help="Auto-approve edits without confirmation.")
@click.option("--guidance", type=click.Path(exists=True), default=None, help="Optional guidance file path.")
def agent(mode: str, prompt: str, image: str, dry_run: bool, force: bool, guidance: str):
    """Enter the Orix agent workspace for natural language coding."""
    guidance_path = guidance or (
        os.path.join(BASE_DIR, "../AGENTS.md")
        if os.path.exists(os.path.join(BASE_DIR, "../AGENTS.md"))
        else os.path.join(os.getcwd(), "AGENTS.md")
    )
    session = AgentSession(
        root_path=os.getcwd(),
        mode=mode,
        guidance_path=guidance_path,
        image_path=image,
        initial_prompt=prompt,
        dry_run=dry_run,
        force=force,
    )
    session.run()

@cli.command()
@click.argument("command", nargs=-1, required=True)
def run(command):
    """Run a shell command and display output."""
    try:
        result = subprocess.run(list(command), capture_output=True, text=True, shell=False)
        console.print(f"[bold green]Exit code:[/bold green] {result.returncode}")
        if result.stdout:
            console.print(Panel(result.stdout, title="stdout", border_style="green"))
        if result.stderr:
            console.print(Panel(result.stderr, title="stderr", border_style="red"))
    except Exception as e:
        console.print(f"[bold red]Error running command:[/bold red] {e}")

@cli.command()
def analyze():
    """Analyze piped stdin content such as diffs or logs."""
    if sys.stdin.isatty():
        console.print("[bold yellow]No stdin detected. Pipe content into orix analyze.[/bold yellow]")
        return
    content = sys.stdin.read()
    lines = content.splitlines()
    additions = [l for l in lines if l.startswith("+") and not l.startswith("+++")]
    deletions = [l for l in lines if l.startswith("-") and not l.startswith("---")]
    errors = [l for l in lines if "error" in l.lower() or "exception" in l.lower()]
    table = Table(title="Analysis Summary")
    table.add_column("Metric")
    table.add_column("Count", justify="right")
    table.add_row("Lines", str(len(lines)))
    table.add_row("Additions", str(len(additions)))
    table.add_row("Deletions", str(len(deletions)))
    table.add_row("Errors/Exceptions", str(len(errors)))
    console.print(table)
    if additions:
        console.print(Panel("\n".join(additions[:20]), title="Additions (sample)", border_style="green"))
    if deletions:
        console.print(Panel("\n".join(deletions[:20]), title="Deletions (sample)", border_style="red"))
    if errors:
        console.print(Panel("\n".join(errors[:20]), title="Errors (sample)", border_style="yellow"))

@cli.command()
def diagnose():
    """Run environment diagnostics."""
    results = EnvironmentDiagnostics.run()
    console.print(EnvironmentDiagnostics.format_report(results))


@cli.command()
@click.option("--bundle", type=click.Path(), default=None, help="Path to output bundle (.so)")
@click.option("--langs", multiple=True, help="Language=git_repo pairs, e.g. python=https://... (can repeat)")
def setup_treesitter(bundle: str, langs: tuple):
    """Build or update the tree-sitter language bundle used by Orix.

    Example: orix setup-treesitter --langs python=https://github.com/tree-sitter/tree-sitter-python.git
    """
    from orix.core.treesitter_helper import build_language_bundle, get_default_bundle_path

    repo_map = {}
    for entry in langs:
        if "=" in entry:
            k, v = entry.split("=", 1)
            repo_map[k.strip()] = v.strip()

    bundle_path = bundle or str(get_default_bundle_path())
    try:
        path = build_language_bundle(bundle_path, repo_map or None)
        console.print(f"[bold green]Tree-sitter bundle built at:[/bold green] {path}")
    except Exception as e:
        console.print(f"[bold red]Failed to build tree-sitter bundle:[/bold red] {e}")

@cli.command()
@click.argument("idea", required=False)
def architect(idea):
    """Transform an idea prompt into architectural specifications."""
    if not idea:
        import questionary
        idea = questionary.text("Describe the application or SaaS idea you want to design:").ask()

    if not idea:
        console.print("[bold red]Error:[/bold red] An idea description is required.")
        return

    from orix.core.architect import Architect
    with console.status("[bold green]Architecting project design specifications..."):
        try:
            arch = Architect(os.getcwd())
            res = arch.generate_spec(idea)
            console.print("\n[bold green]Success![/bold green] Architecture generated under [cyan].orix/[/cyan]")
            console.print(f"- Architecture: [cyan]{res['paths']['architecture']}[/cyan]")
            console.print(f"- Plan: [cyan]{res['paths']['plan']}[/cyan]")
            console.print(f"- Decisions: [cyan]{res['paths']['decisions']}[/cyan]")
        except Exception as e:
            console.print(f"\n[bold red]Error architecting idea:[/bold red] {e}")

@cli.command()
@click.argument("idea", required=False)
@click.option("--resume", is_flag=True, help="Resume project generation from last checkpoint.")
def forge(idea, resume):
    """Orchestrate the end-to-end forging of an application from idea to validated code."""
    if not idea and not resume:
        import questionary
        idea = questionary.text("Describe the application you want Orix to Forge:").ask()

    if not idea and not resume:
        console.print("[bold red]Error:[/bold red] Either an idea prompt or --resume is required.")
        return

    from orix.core.forge import Forge
    try:
        forge_engine = Forge(os.getcwd(), TEMPLATES_DIR, PLUGINS_DIR)
        forge_engine.run_forge(idea=idea, resume=resume)
        console.print("\n[bold green]Success![/bold green] App forging completed.")
    except Exception as e:
        console.print(f"\n[bold red]Error forging application:[/bold red]\n{e}")

@cli.command()
def doctor():
    """Diagnose the workspace health, structure, and configurations."""
    from orix.core.doctor import Doctor
    with console.status("[bold green]Running workspace health diagnostics..."):
        try:
            doc = Doctor(os.getcwd())
            report = doc.run_diagnostics()

            console.print("\n[bold green]=== Orix Project Health Report ===[/bold green]")
            scores = report["scores"]
            console.print(f"Security:     [bold cyan]{scores['security']}/100[/bold cyan]")
            console.print(f"Testing:      [bold cyan]{scores['testing']}/100[/bold cyan]")
            console.print(f"Dependencies: [bold cyan]{scores['dependencies']}/100[/bold cyan]")
            console.print(f"Architecture: [bold cyan]{scores['architecture']}/100[/bold cyan]")
            console.print("-" * 30)
            console.print(f"Overall:      [bold green]{scores['overall']}/100[/bold green]\n")

            if report["issues"]:
                console.print("[bold yellow]Discovered Issues:[/bold yellow]")
                for issue in report["issues"]:
                    console.print(f"- {issue}")
            else:
                console.print("[bold green]All checks passed cleanly! Absolute clean health.[/bold green]")
        except Exception as e:
            console.print(f"\n[bold red]Error running diagnostics:[/bold red] {e}")

@cli.command()
@click.argument("target_path", type=click.Path(exists=True), required=True)
def explain(target_path):
    """Explain the purpose, dependencies, functions, and risks of a file or folder."""
    from orix.core.explain import Explainer
    with console.status(f"[bold green]Analyzing target code path: '{target_path}'..."):
        try:
            exp = Explainer(os.getcwd())
            res = exp.explain_path(target_path)

            console.print(f"\n[bold green]=== Code Explanation: {target_path} ===[/bold green]")
            console.print(f"[bold yellow]Purpose:[/bold yellow]\n{res['purpose']}\n")
            if res["dependencies"]:
                console.print(f"[bold yellow]Dependencies:[/bold yellow]\n{', '.join(res['dependencies'])}\n")
            if res["important_functions"]:
                console.print(f"[bold yellow]Exposed Symbols:[/bold yellow]\n{', '.join(res['important_functions'][:10])}\n")
            console.print(f"[bold yellow]Execution Flow:[/bold yellow]\n{res['execution_flow']}\n")
            console.print("[bold yellow]Potential Security & Safety Risks:[/bold yellow]")
            for risk in res["potential_risks"]:
                console.print(f"- {risk}")
        except Exception as e:
            console.print(f"\n[bold red]Error explaining target path:[/bold red] {e}")

if __name__ == "__main__":
    cli()
