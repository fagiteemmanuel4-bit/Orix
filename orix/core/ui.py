import questionary
from rich.console import Console
from rich.panel import Panel
from typing import Dict, Any, List

console = Console()

class TUI:
    @staticmethod
    def display_banner():
        banner = (
            "   ____         _       \n"
            "  / __ \\_______(_)  __  \n"
            " / / / / __/ __/ / |/_/  \n"
            "/ /_/ / / / / / />  <    \n"
            "\\____/_/ /_/ /_/_/|_|    \n"
            "                         \n"
            "⚡ Orix X: Universal Dev CLI ⚡\n"
            "  Built for dev teams, automation, and AI agents\n"
            "  Think git / npm / gh / cargo for app scaffolding"
        )
        console.print(Panel(banner, style="bold cyan"))

    @staticmethod
    def display_ai_builder_banner():
        bird_banner = (
            "   ___      ___   \n"
            "  (  (\\    /)  )  \n"
            "   \\  \\  //  /   \n"
            "    `-.__\\/.--'    \n"
            "      /  \\  \n"
            "     / /\\_\\         White + Green AI Builder\n"
            "    /_/    \\\n"
        )
        console.print(Panel(bird_banner, title="AI Builder", style="bold green", subtitle="OpenRouter/OpenAI-compatible model support"))

    @staticmethod
    def prompt_project_name() -> str:
        return questionary.text("What is your project name?", default="my-awesome-project").ask()

    @staticmethod
    def prompt_framework(frameworks: List[str]) -> str:
        return questionary.select(
            "Select a framework:",
            choices=frameworks
        ).ask()

    @staticmethod
    def prompt_options(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        return questionary.form(**{q['name']: questionary.select(q['message'], choices=q['choices']) if q['type'] == 'select' else questionary.confirm(q['message']) for q in questions}).ask()
        # Simplified for now, real implementation would handle different question types better

    @staticmethod
    def prompt_ai_endpoint(default: str = "https://openrouter.ai/v1/chat/completions") -> str:
        return questionary.text("AI model endpoint:", default=default).ask()

    @staticmethod
    def prompt_api_key() -> str:
        return questionary.password("AI model API key:").ask()

    @staticmethod
    def prompt_ai_model(default: str = "gpt-4o-mini") -> str:
        return questionary.text("AI model name:", default=default).ask()

    @staticmethod
    def prompt_ai_prompt() -> str:
        return questionary.text("Describe the project you want Orix to build:").ask()
