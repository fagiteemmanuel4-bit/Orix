import pytest
import os
import json
from orix.core.forge import Forge

@pytest.fixture
def base_dirs(tmp_path):
    # Retrieve real templates and plugins path
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    templates_dir = os.path.join(base, "orix", "templates")
    plugins_dir = os.path.join(base, "orix", "plugins")
    return {
        "templates": templates_dir,
        "plugins": plugins_dir,
        "root": str(tmp_path)
    }

def test_forge_successful_project(base_dirs):
    forge = Forge(base_dirs["root"], base_dirs["templates"], base_dirs["plugins"])
    state = forge.run_forge(idea="Build a FastAPI service with docker")

    # Assert generated project files
    project_path = os.path.join(base_dirs["root"], "generated-project")
    assert os.path.exists(project_path)
    assert os.path.exists(os.path.join(project_path, "requirements.txt"))

def test_forge_plugin_unavailable(base_dirs):
    forge = Forge(base_dirs["root"], base_dirs["templates"], base_dirs["plugins"])
    # Mocking plan spec with unsupported plugin framework
    forge.state["idea"] = "Build something"
    forge.state["current_stage"] = "plugin_selection"
    forge.state["plan_spec"] = {"framework": "unsupported-framework-name"}
    forge.save_state()

    with pytest.raises(RuntimeError, match="Selected framework plugin 'unsupported-framework-name' is not supported"):
        forge.run_forge(resume=True)

def test_forge_generation_failure(base_dirs):
    forge = Forge(base_dirs["root"], base_dirs["templates"], base_dirs["plugins"])
    # Provide an idea but simulate missing inputs or invalid setup
    with pytest.raises(ValueError, match="An idea description is required"):
        forge.run_forge(idea="")
