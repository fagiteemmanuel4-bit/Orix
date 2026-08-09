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
@click.argument("idea", required=True)
@click.option("--output-dir", type=click.Path(), default=None, help="Custom directory for architecture output files.")
def architect(idea, output_dir):
    """Generate architecture design and build plan from a project idea description."""
    from orix.core.architect import Architect
    try:
        arch = Architect()
        res = arch.generate_spec(idea, target_dir=output_dir)
        console.print("[bold green]Success![/bold green] Architectural specifications generated successfully:")
        console.print(f"- Architecture Spec: [cyan]{res['architecture']}[/cyan]")
        console.print(f"- Build Plan: [cyan]{res['plan']}[/cyan]")
        console.print(f"- Decisions Log: [cyan]{res['decisions']}[/cyan]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")


@cli.command()
@click.argument("idea", required=False)
@click.option("--resume/--no-resume", default=True, help="Resume from the last saved checkpoint.")
@click.option("--dry-run/--no-dry-run", default=False, help="Simulate stages without making directory edits.")
@click.option("--output", type=click.Path(), default=None, help="Output directory path.")
def forge(idea, resume, dry_run, output):
    """Execute a multi-stage resumable project scaffolding workflow."""
    from orix.core.forge import ForgeWorkflow

    workflow = ForgeWorkflow(TEMPLATES_DIR, PLUGINS_DIR)

    # If not resuming and no idea was passed, print error
    if not resume and not idea:
        console.print("[bold red]Error:[/bold red] You must provide a project idea description when starting a new forge workflow.")
        return

    checkpoint = workflow.load_checkpoint()
    if resume and not idea:
        if not checkpoint or not checkpoint.get("idea"):
            console.print("[bold red]Error:[/bold red] No saved checkpoint found to resume. Please provide a project idea.")
            return
        idea = checkpoint.get("idea")

    console.print(f"[bold green]Starting Orix Forge:[/bold green] [cyan]'{idea}'[/cyan]\n")

    for step in workflow.run(idea=idea, resume=resume, dry_run=dry_run, output_path=output):
        status = step.get("status")
        stage = step.get("stage")
        message = step.get("message")

        if status == "starting":
            console.print(f"[yellow]▶ {stage.upper()}...[/yellow] {message}")
        elif status == "success":
            console.print(f"[green]✔ {stage.upper()}:[/green] Completed.")
        elif status == "skipped":
            console.print(f"[blue]ℹ {stage.upper()}:[/blue] Already completed, skipping.")
        elif status == "failed":
            console.print(f"\n[bold red]✖ {stage.upper()} FAILED:[/bold red] {message}")
            if "explanation" in step:
                console.print(f"\n[bold yellow]Explanation & Help:[/bold yellow]\n{step['explanation']}")
            return
        elif status == "complete":
            console.print(f"\n[bold green]★ FORGE COMPLETE! ★[/bold green]\n")
            if not dry_run:
                summary = step.get("state", {}).get("report_summary", "")
                console.print(summary)
            else:
                console.print("[yellow]Dry-run finished. No project directories were created.[/yellow]")


@cli.command()
def doctor():
    """Diagnose workspace health and security configurations."""
    from orix.core.doctor import OrixDoctor

    doc = OrixDoctor(os.getcwd())
    report = doc.run_diagnostics()

    scores = report["scores"]
    findings = report["findings"]

    console.print("\n[bold green]⚕ Orix Project Health Diagnosis ⚕[/bold green]\n")

    table = Table(title="Health Scores", border_style="cyan")
    table.add_column("Category", style="cyan")
    table.add_column("Score", justify="right")

    for category, score in scores.items():
        color = "green" if score >= 80 else ("yellow" if score >= 50 else "red")
        table.add_row(category, f"[{color}]{score}/100[/{color}]")

    console.print(table)
    console.print()

    if findings:
        console.print("[bold yellow]⚠️  Diagnostics Findings:[/bold yellow]")
        for f in findings:
            color = "red" if f["severity"] == "CRITICAL" else ("orange3" if f["severity"] == "HIGH" else "yellow")
            console.print(f"  [[bold {color}]{f['severity']}[/bold {color}]] {f['category']}: {f['message']}")
        console.print()
    else:
        console.print("[bold green]✔ Excellent! No critical issues or security vulnerability patterns detected.[/bold green]\n")

    console.print(Panel(report["scoring_model"], title="Scoring Methodology Documentation", border_style="blue"))


@cli.command()
@click.argument("target", type=click.Path(exists=True), required=True)
def explain(target):
    """Generate professional explanation of a file or directory based on source code analysis."""
    from orix.core.explain import OrixExplain

    explainer = OrixExplain(os.getcwd())
    try:
        report = explainer.explain_path(target)

        console.print(f"\n[bold green]✦ Orix Code Explanation: {report['path']} ✦[/bold green]\n")

        console.print(f"[bold cyan]● Purpose:[/bold cyan]\n  {report['purpose']}")
        console.print()

        if report["type"] in ("file", "binary_file"):
            if "dependencies" in report and report["dependencies"]:
                console.print("[bold cyan]● Dependencies & Imports:[/bold cyan]")
                for dep in report["dependencies"]:
                    console.print(f"  - {dep}")
                console.print()

            if "important_functions" in report and report["important_functions"]:
                console.print("[bold cyan]● Important Functions & Classes:[/bold cyan]")
                for fn in report["important_functions"]:
                    console.print(f"  - {fn}")
                console.print()

        elif report["type"] == "directory":
            if "subdirectories" in report and report["subdirectories"]:
                console.print("[bold cyan]● Subdirectories:[/bold cyan]")
                for sd in report["subdirectories"]:
                    console.print(f"  - {sd}/")
                console.print()

            if "files" in report and report["files"]:
                console.print("[bold cyan]● Top-level Files:[/bold cyan]")
                for f in report["files"]:
                    console.print(f"  - {f}")
                console.print()

        console.print(f"[bold cyan]● Execution Flow:[/bold cyan]\n  {report['execution_flow']}")
        console.print()

        if "risks" in report and report["risks"]:
            console.print("[bold red]● Potential Risks & Recommendations:[/bold red]")
            for risk in report["risks"]:
                console.print(f"  - {risk}")
            console.print()

        if report.get("warning"):
            console.print(f"[bold yellow]⚠️  Warning:[/bold yellow] {report['warning']}\n")

    except Exception as e:
        console.print(f"[bold red]Error explaining target:[/bold red] {str(e)}")


@cli.group()
def ai():
    """Manage and query Orix's intelligence layer and models."""
    pass


@ai.command(name="models")
def ai_models():
    """Detect and list status of available AI models and local providers."""
    from orix.core.ai_providers import OllamaProvider

    ollama = OllamaProvider({"provider": "ollama"})
    ollama_avail = "Available" if ollama.is_available() else "Unavailable / Not Running"

    openai_avail = "Configured" if os.getenv("OPENAI_API_KEY") else "Not configured"
    anthropic_avail = "Configured" if os.getenv("ANTHROPIC_API_KEY") else "Not configured"
    gemini_avail = "Configured" if os.getenv("GEMINI_API_KEY") else "Not configured"
    openrouter_avail = "Configured" if os.getenv("OPENROUTER_API_KEY") else "Not configured"

    table = Table(title="Orix Intelligence Layer Providers", border_style="cyan")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", justify="left")

    table.add_row("Ollama (Local)", f"[green]{ollama_avail}[/green]" if "Available" in ollama_avail else f"[yellow]{ollama_avail}[/yellow]")
    table.add_row("OpenAI (Cloud)", f"[green]{openai_avail}[/green]" if "Configured" in openai_avail else f"[yellow]{openai_avail}[/yellow]")
    table.add_row("Anthropic (Cloud)", f"[green]{anthropic_avail}[/green]" if "Configured" in anthropic_avail else f"[yellow]{anthropic_avail}[/yellow]")
    table.add_row("Gemini (Cloud)", f"[green]{gemini_avail}[/green]" if "Configured" in gemini_avail else f"[yellow]{gemini_avail}[/yellow]")
    table.add_row("OpenRouter (Cloud)", f"[green]{openrouter_avail}[/green]" if "Configured" in openrouter_avail else f"[yellow]{openrouter_avail}[/yellow]")

    console.print(table)


@cli.group()
def memory():
    """Inspect and manage project-scoped memory store."""
    pass


@memory.command(name="list")
def memory_list():
    """List all categories and entries in project memory."""
    from orix.core.memory import LocalMemoryStore
    store = LocalMemoryStore()
    data = store.get_all()

    table = Table(title="Orix Project Memory Storage", border_style="magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Size / Count", justify="right")

    for key, val in data.items():
        count = len(val) if isinstance(val, (list, dict)) else 1
        table.add_row(key, str(count))

    console.print(table)


@memory.command(name="show")
@click.argument("category", required=True)
def memory_show(category):
    """Show details of a specific memory category."""
    from orix.core.memory import LocalMemoryStore
    store = LocalMemoryStore()
    data = store.query(category)

    if data is None:
        console.print(f"[bold red]Error:[/bold red] Category '{category}' not found in memory.")
        return

    console.print(f"\n[bold magenta]✦ Project Memory Category: {category} ✦[/bold magenta]\n")
    console.print_json(data=data)


@memory.command(name="remove")
@click.argument("category", required=True)
@click.option("--key", help="Specific nested key to remove within the category.")
def memory_remove(category, key):
    """Remove an entire memory category or a specific nested key."""
    from orix.core.memory import LocalMemoryStore
    store = LocalMemoryStore()

    success = store.delete_key(category, key)
    if success:
        target = f"nested key '{key}' from category '{category}'" if key else f"category '{category}'"
        console.print(f"[bold green]Success![/bold green] Removed {target} from project memory.")
    else:
        console.print(f"[bold red]Error:[/bold red] Failed to locate category or sub-key.")


@cli.command(name="eval")
def run_eval():
    """Run the deterministic AI agent evaluation suite."""
    from orix.core.eval import OrixEvaluationSuite

    console.print("\n[bold green]📊 Orix Developer OS Agent Evaluation Suite 📊[/bold green]\n")
    with console.status("[bold cyan]Running evaluations inside isolated sandboxes..."):
        suite = OrixEvaluationSuite()
        results = suite.run_evaluations()

    table = Table(title="Agent Scorecard Metrics", border_style="cyan")
    table.add_column("Task ID", style="cyan")
    table.add_column("Evaluation Scenario")
    table.add_column("Task Completion", justify="center")
    table.add_column("Iterations", justify="right")
    table.add_column("Approx Tokens", justify="right")
    table.add_column("Notes")

    total_completed = 0
    for r in results:
        status_str = "[green]PASS[/green]" if r["completed"] else "[red]FAIL[/red]"
        if r["completed"]:
            total_completed += 1
        table.add_row(
            r["id"],
            r["name"],
            status_str,
            str(r["iterations"]),
            str(r["tokens_approx"]),
            r["notes"]
        )

    console.print(table)
    console.print(f"\n[bold green]Final Evaluation Score: {total_completed}/{len(results)} Tasks Passed[/bold green]\n")


@cli.command(name="self-test")
def self_test():
    """Execute Orix's automated production release gate check."""
    from orix.core.selftest import OrixSelfTest

    console.print("\n[bold green]⚙ Orix Release Gate: Running self-test ⚙[/bold green]\n")

    tester = OrixSelfTest(os.getcwd())
    with console.status("[bold cyan]Executing comprehensive diagnostics..."):
        results = tester.run_all_checks()

    table = Table(title="Orix Component Readiness Matrix", border_style="cyan")
    table.add_column("Component", style="cyan")
    table.add_column("Readiness Status", justify="center")
    table.add_column("Diagnostics Detail / Info")

    all_passed = True
    for r in results:
        status_str = "[green]✓ PASS[/green]" if r["status"] else "[red]✗ FAIL[/red]"
        if not r["status"]:
            all_passed = False
        table.add_row(r["name"], status_str, r["details"])

    console.print(table)
    if all_passed:
        console.print("\n[bold green]★ PRODUCTION RELEASE CANDIDATE VALIDATED SUCCESSFULLY! ★[/bold green]\n")
    else:
        console.print("\n[bold red]✖ RELEASE CANDIDATE REJECTED: Minor component errors detected. ✖[/bold red]\n")
        sys.exit(1)


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

if __name__ == "__main__":
    cli()
