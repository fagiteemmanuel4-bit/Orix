import os
import click
from orix.core.orchestrator import Orchestrator
from orix.core.ui import TUI, console

# Path to the current directory where the package is installed
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
PLUGINS_DIR = os.path.join(BASE_DIR, "plugins")

@click.group()
def cli():
    """Orix X: Universal Project Scaffolding Platform."""
    pass

@cli.command(name="list")
def list_plugins():
    """List all dynamically discovered framework plugins."""
    orchestrator = Orchestrator(TEMPLATES_DIR, PLUGINS_DIR)
    plugins = orchestrator.plugin_manager.get_plugins_by_type("framework")

    console.print("\n[bold cyan]🌌 Available Scaffolding Plugins:[/bold cyan]")
    for p in plugins:
        console.print(f"  • [bold green]{p.name}[/bold green] (type: {p.plugin_type})")
    console.print("")

@cli.command()
@click.argument("project_name", required=False)
@click.option("--framework", help="Framework to use.")
@click.option("--docker/--no-docker", default=None, help="Include Docker setup.")
@click.option("--auth/--no-auth", default=None, help="Include Auth logic.")
@click.option("--dry-run", is_flag=True, help="Simulate execution without writing files to disk.")
@click.option("--silent", is_flag=True, help="Disable interactive TUI prompts and use secure default parameters.")
def create(project_name, framework, docker, auth, dry_run, silent):
    """Create a new project."""
    orchestrator = Orchestrator(TEMPLATES_DIR, PLUGINS_DIR)
    
    available_frameworks = [p.name for p in orchestrator.plugin_manager.get_plugins_by_type("framework")]

    # Handle Silent Mode Defaults
    if silent:
        if not project_name:
            project_name = "orix-generated-project"
        if not framework:
            framework = "react" # Default safe framework
        if docker is None:
            docker = False
        if auth is None:
            auth = False

    if not project_name:
        TUI.display_banner()
        project_name = TUI.prompt_project_name()
    
    if not framework:
        framework = TUI.prompt_framework(available_frameworks)

    if framework not in available_frameworks:
        console.print(f"[bold red]Error:[/bold red] Framework '{framework}' is not supported.")
        return

    plugin = orchestrator.plugin_manager.get_plugin_by_name(framework)
    
    options = {
        "docker": docker if docker is not None else False,
        "auth": auth if auth is not None else False
    }
    
    # If interactive (not silent) and options not provided via flags, prompt for them
    if not silent and project_name and (docker is None or auth is None):
        questions = plugin.get_questions()
        # Filter questions for options already provided
        remaining_questions = []
        if docker is None:
            remaining_questions.append([q for q in questions if q['name'] == 'docker'][0])
        if auth is None:
            remaining_questions.append([q for q in questions if q['name'] == 'auth'][0])

        if remaining_questions:
            new_options = TUI.prompt_options(remaining_questions)
            options.update(new_options)

    if dry_run:
        console.print(f"\n[bold yellow][DRY-RUN][/bold yellow] Simulating generation of framework [cyan]{framework}[/cyan] inside folder: [cyan]{project_name}[/cyan]")
        console.print(f"[bold yellow][DRY-RUN][/bold yellow] Parameters: Docker={options['docker']}, Auth={options['auth']}\n")
        console.print("[bold green]Dry-run dry run simulation completed successfully (No files written to disk).[/bold green]")
        return

    with console.status(f"[bold green]Generating {framework} project: {project_name}..."):
        try:
            path = orchestrator.generate(project_name, framework, options)
            console.print(f"\n[bold green]Success![/bold green] Project created at: [cyan]{path}[/cyan]")
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    cli()
