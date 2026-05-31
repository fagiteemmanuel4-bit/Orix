from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BasePlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def plugin_type(self) -> str:
        pass

    @abstractmethod
    def get_questions(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_context(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        pass

class FrameworkPlugin(BasePlugin):
    @property
    def plugin_type(self) -> str:
        return "framework"

    @abstractmethod
    def get_template_name(self) -> str:
        pass
