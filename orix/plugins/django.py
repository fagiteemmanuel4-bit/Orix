import secrets
from typing import Dict, Any, List
from orix.sdk.base import FrameworkPlugin

class DjangoPlugin(FrameworkPlugin):
    @property
    def name(self) -> str:
        return "django"

    def get_template_name(self) -> str:
        return "django"

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
                "message": "Include Django Rest Framework Auth?",
                "default": False
            }
        ]

    def get_context(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "use_docker": answers.get("docker", False),
            "use_auth": answers.get("auth", False),
            "django_version": "4.2.0",
            "secret_key": secrets.token_urlsafe(50)
        }
