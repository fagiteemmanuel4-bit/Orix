import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

# Initialize the global Kryonara rich console
console = Console()

def clear_terminal() -> None:
    """Clears the terminal screen completely for a clean UI environment."""
    os.system("cls" if os.name == "nt" else "clear")

def display_welcome_banner() -> None:
    """
    Renders the premium Kryonara-themed Orix ASCII welcome banner.
    Designed with precise string escapes to prevent alignment drifting.
    """
    clear_terminal()

    # Highly stable stylized ASCII art block
    ascii_art = (
        r"   ____         _       " "\n"
        r"  / __ \_______(_)  __  " "\n"
        r" / / / / __/ __/ / |/_/  " "\n"
        r"/ /_/ / / / / / />  <    " "\n"
        r"\____/_/ /_/ /_/_/|_|    " "\n"
    )

    # Apply a sleek deep-purple to magenta gradient to the ASCII branding
    banner_text = Text(ascii_art, style="bold matrix")
    banner_text.stylize_gradient("bright_purple", "magenta")

    # Taglines and metadata
    tagline = Text("\n⚡ LIGHTWEIGHT MULTI-FRAMEWORK PROJECT SCAFFOLDER ⚡", style="bold white")
    meta_info = Text("Engineered by Kryonara • Version 1.0.0", style="dim italic cyan")

    # Combine text items vertically
    combined_content = Text.assemble(banner_text, tagline, "\n", meta_info)
    
    # Align content to the center of the panel
    centered_content = Align.center(combined_content)

    # Render a clean, heavy-bordered panel to act as the viewport frame
    viewport_panel = Panel(
        centered_content,
        border_style="bright_purple",
        padding=(1, 4),
        subtitle="[bold reverse white] HUMAN & AI CHANNELS ACTIVE [/bold reverse white]",
        subtitle_align="right"
    )

    console.print(viewport_panel)
    console.print("\n")

def display_success_message(project_name: str, path: str) -> None:
    """Prints a beautiful, structural success report when a project finishes scaffolding."""
    success_text = Text()
    success_text.append("\n✨ Project Scaffolding Complete!\n\n", style="bold green")
    success_text.append("🚀 Project Name: ", style="bold white")
    success_text.append(f"{project_name}\n", style="cyan")
    success_text.append("📂 Location:     ", style="bold white")
    success_text.append(f"{path}\n\n", style="cyan")
    success_text.append("To get started, execute the following commands:\n", style="dim white")
    
    # Render the copy-paste action block
    console.print(Panel(success_text, border_style="green", title="[bold green]SUCCESS[/bold green]", title_align="left"))
    
    action_panel = Panel(
        f"[bold magenta]cd[/bold magenta] {project_name}\n"
        f"[bold magenta]docker-compose[/bold magenta] up --build",
        border_style="dim white",
        title="[dim]Quickstart Command[/dim]",
        title_align="left"
    )
    console.print(action_panel)

if __name__ == "__main__":
    # Test execution layout locally
    display_welcome_banner()
    display_success_message("my-premium-app", "./workspaces/my-premium-app")
