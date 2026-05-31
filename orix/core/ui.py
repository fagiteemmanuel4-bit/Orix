import questionary
from rich.console import Console
from rich.panel import Panel
from typing import Dict, Any, List

console = Console()

class TUI:
    @staticmethod
    def display_banner():
        banner = """
   ____         _       
  / __ \_______(_)  __  
 / / / / __/ __/ / |/_/  
/ /_/ / / / / / />  <    
\____/_/ /_/ /_/_/|_|    
                         
⚡ Orix X: Universal Project Generator ⚡
        """
        console.print(Panel(banner, style="bold cyan"))

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
