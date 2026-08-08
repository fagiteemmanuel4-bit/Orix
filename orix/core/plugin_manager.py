import importlib.util
import inspect
import os
import shutil
import subprocess
import tempfile
from typing import List
from orix.sdk.base import BasePlugin

class PluginManager:
    def __init__(self, plugins_dir: str):
        self.plugins_dir = plugins_dir
        self.plugins: List[BasePlugin] = []

    def load_plugins(self):
        self.plugins = []
        if not os.path.isdir(self.plugins_dir):
            return
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                file_path = os.path.join(self.plugins_dir, filename)

                try:
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
                except Exception as e:
                    # Individual plugin load failure should not crash the CLI
                    from orix.core.ui import console
                    console.print(f"[bold yellow]Warning:[/bold yellow] Failed to load plugin from '{file_path}': {e}")

    def install_plugin(self, source: str) -> List[str]:
        if source.startswith(("http://", "https://")) or source.endswith(".git"):
            return self._install_from_git(source)
        return self._install_from_path(source)

    def _install_from_git(self, url: str) -> List[str]:
        temp_dir = tempfile.mkdtemp()
        try:
            subprocess.run(["git", "clone", url, temp_dir], check=True, capture_output=True, text=True)
            search_dir = os.path.join(temp_dir, "orix", "plugins")
            if not os.path.isdir(search_dir):
                search_dir = temp_dir
            return self._copy_plugins_from_directory(search_dir)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _install_from_path(self, source: str) -> List[str]:
        if not os.path.exists(source):
            raise FileNotFoundError(f"Plugin source '{source}' does not exist.")

        if os.path.isdir(source):
            return self._copy_plugins_from_directory(source)

        if source.endswith(".py"):
            dest_path = os.path.join(self.plugins_dir, os.path.basename(source))
            shutil.copy2(source, dest_path)
            return [os.path.basename(source)]

        raise ValueError("Plugin source must be a Python file or directory containing plugin modules.")

    def _copy_plugins_from_directory(self, source_dir: str) -> List[str]:
        installed = []
        for filename in os.listdir(source_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                dest_path = os.path.join(self.plugins_dir, filename)
                shutil.copy2(os.path.join(source_dir, filename), dest_path)
                installed.append(filename)

        if not installed:
            raise ValueError(f"No plugin modules were found in '{source_dir}'.")
        return installed

    def remove_plugin(self, name: str) -> str:
        plugin_path = os.path.join(self.plugins_dir, f"{name}.py")
        if not os.path.exists(plugin_path):
            raise FileNotFoundError(f"Plugin '{name}' not found.")
        os.remove(plugin_path)
        return plugin_path

    def get_plugins_by_type(self, plugin_type: str) -> List[BasePlugin]:
        return [p for p in self.plugins if p.plugin_type == plugin_type]

    def get_plugin_by_name(self, name: str) -> BasePlugin:
        for p in self.plugins:
            if p.name == name:
                return p
        return None
