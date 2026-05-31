from typing import Dict, Any, List
from orix.sdk.base import FrameworkPlugin

class FastAPIPlugin(FrameworkPlugin):
    @property
    def name(self) -> str:
        return "fastapi"

    def get_template_name(self) -> str:
        return "fastapi"

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
                "message": "Include JWT Authentication?",
                "default": False
            }
        ]

    def get_context(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "use_docker": answers.get("docker", False),
            "use_auth": answers.get("auth", False),
            "fastapi_version": "0.95.0"
        }
