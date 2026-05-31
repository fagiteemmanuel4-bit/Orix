import importlib.util
import os
import inspect
from typing import List, Type
from orix.sdk.base import BasePlugin

class PluginManager:
    def __init__(self, plugins_dir: str):
        self.plugins_dir = plugins_dir
        self.plugins: List[BasePlugin] = []

    def load_plugins(self):
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                file_path = os.path.join(self.plugins_dir, filename)
                
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BasePlugin) and 
                            obj is not BasePlugin and
                            not inspect.isabstract(obj)):
                            self.plugins.append(obj())

    def get_plugins_by_type(self, plugin_type: str) -> List[BasePlugin]:
        return [p for p in self.plugins if p.plugin_type == plugin_type]

    def get_plugin_by_name(self, name: str) -> BasePlugin:
        for p in self.plugins:
            if p.name == name:
                return p
        return None
