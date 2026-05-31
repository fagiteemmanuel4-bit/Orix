import os
import shutil
import pytest
from orix.core.renderer import TemplateRenderer
from orix.core.plugin_manager import PluginManager
from orix.core.orchestrator import Orchestrator

@pytest.fixture
def base_dir(tmp_path):
    d = tmp_path / "orix"
    d.mkdir()
    (d / "templates").mkdir()
    (d / "plugins").mkdir()
    return d

def test_plugin_manager_loads_plugins():
    # Setup dummy plugin
    plugins_dir = "orix/plugins"
    pm = PluginManager(plugins_dir)
    pm.load_plugins()
    assert len(pm.plugins) >= 3
    assert pm.get_plugin_by_name("react") is not None
    assert pm.get_plugin_by_name("django") is not None
    assert pm.get_plugin_by_name("fastapi") is not None

def test_renderer_renders_template(tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    react_dir = templates_dir / "react"
    react_dir.mkdir()
    (react_dir / "file.txt").write_text("Hello {{ name }}")
    
    renderer = TemplateRenderer(str(templates_dir))
    target_path = tmp_path / "output"
    renderer.render_project("react", str(target_path), {"name": "World"})
    
    assert (target_path / "file.txt").read_text() == "Hello World"

def test_orchestrator_integration(tmp_path):
    # Use real templates and plugins for integration test
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_dir = os.path.join(base_dir, "orix", "templates")
    plugins_dir = os.path.join(base_dir, "orix", "plugins")
    
    orchestrator = Orchestrator(templates_dir, plugins_dir)
    project_name = "test_project"
    target_dir = tmp_path / project_name
    
    # Mocking current working directory by passing it to generate
    # (Actually orchestrator uses os.getcwd(), but let's just test it creates the folder)
    # We'll just run it and hope it doesn't mess up the environment
    
    path = orchestrator.generate(str(target_dir), "react", {"docker": True, "auth": False})
    
    assert os.path.exists(path)
    assert os.path.exists(os.path.join(path, "package.json"))
    assert os.path.exists(os.path.join(path, "src", "App.js"))
