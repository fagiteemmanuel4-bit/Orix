from typing import Dict, Any, List
from orix.sdk.base import FrameworkPlugin

class ReactPlugin(FrameworkPlugin):
    @property
    def name(self) -> str:
        return "react"

    def get_template_name(self) -> str:
        return "react"

    def get_questions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "confirm",
                "name": "docker",
                "message": "Include Docker configuration?",
                "default": False
            },
            {
                "type": "confirm",
                "name": "auth",
                "message": "Include Authentication boilerplate?",
                "default": False
            }
        ]

    def get_context(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "use_docker": answers.get("docker", False),
            "use_auth": answers.get("auth", False),
            "react_version": "18.2.0"
        }
