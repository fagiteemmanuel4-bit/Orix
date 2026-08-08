import os
import shutil
import pytest
from orix.core.plugin_manager import PluginManager

def test_plugin_manager_discovery_and_loading(tmp_path):
    # Setup dummy plugins directory
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    # Write a valid dummy framework plugin
    plugin_content = """
from orix.sdk.base import FrameworkPlugin

class DummyPlugin(FrameworkPlugin):
    @property
    def name(self) -> str:
        return "dummy"

    def get_template_name(self) -> str:
        return "dummy_template"

    def get_questions(self):
        return []

    def get_context(self, answers):
        return {}
"""
    (plugins_dir / "dummy.py").write_text(plugin_content, encoding="utf-8")

    pm = PluginManager(str(plugins_dir))
    pm.load_plugins()

    assert len(pm.plugins) == 1
    assert pm.get_plugin_by_name("dummy") is not None
    assert pm.get_plugin_by_name("dummy").get_template_name() == "dummy_template"
    assert pm.get_plugins_by_type("framework")[0].name == "dummy"

def test_plugin_manager_invalid_plugin(tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    # Write a plugin with syntax errors
    (plugins_dir / "broken.py").write_text("class BrokenPlugin: syntax_error {", encoding="utf-8")

    pm = PluginManager(str(plugins_dir))
    # This should load successfully and print a warning instead of crashing
    pm.load_plugins()
    assert len(pm.plugins) == 0

def test_plugin_manager_missing_and_removal(tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    pm = PluginManager(str(plugins_dir))

    # Non-existent plugin removal should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        pm.remove_plugin("non_existent")

    # Install local plugin file
    plugin_src = tmp_path / "my_plugin.py"
    plugin_src.write_text("""
from orix.sdk.base import FrameworkPlugin
class MyPlugin(FrameworkPlugin):
    @property
    def name(self): return "myplugin"
    def get_template_name(self): return "my_temp"
    def get_questions(self): return []
    def get_context(self, answers): return {}
""", encoding="utf-8")

    pm.install_plugin(str(plugin_src))
    assert os.path.exists(plugins_dir / "my_plugin.py")

    pm.load_plugins()
    assert pm.get_plugin_by_name("myplugin") is not None

    # Remove it
    pm.remove_plugin("my_plugin")
    assert not os.path.exists(plugins_dir / "my_plugin.py")
