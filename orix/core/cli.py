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
    """Orix X: Universal Project Generator."""
    pass

@cli.command()
@click.argument("project_name", required=False)
@click.option("--framework", help="Framework to use.")
@click.option("--docker/--no-docker", default=None, help="Include Docker setup.")
@click.option("--auth/--no-auth", default=None, help="Include Auth logic.")
def create(project_name, framework, docker, auth):
    """Create a new project."""
    orchestrator = Orchestrator(TEMPLATES_DIR, PLUGINS_DIR)
    
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
    
    # If interactive and options not provided via flags, prompt for them
    if project_name and (options["docker"] is None or options["auth"] is None):
        questions = plugin.get_questions()
        # Filter questions for options already provided
        remaining_questions = [q for q in questions if options.get(q['name']) is None]
        if remaining_questions:
            new_options = TUI.prompt_options(remaining_questions)
            options.update(new_options)

    with console.status(f"[bold green]Generating {framework} project: {project_name}..."):
        try:
            path = orchestrator.generate(project_name, framework, options)
            console.print(f"\n[bold green]Success![/bold green] Project created at: [cyan]{path}[/cyan]")
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    cli()
