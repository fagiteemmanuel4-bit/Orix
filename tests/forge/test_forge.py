import os
import pytest
from orix.core.forge import ForgeWorkflow

def test_forge_dry_run(tmp_path):
    templates_dir = os.path.join(os.path.dirname(__file__), "../../orix/templates")
    plugins_dir = os.path.join(os.path.dirname(__file__), "../../orix/plugins")

    workflow = ForgeWorkflow(templates_dir, plugins_dir, str(tmp_path))
    steps = list(workflow.run(idea="Build a React frontend", resume=False, dry_run=True))

    # Assert successful dry run execution
    assert steps[-1]["status"] == "complete"
    assert steps[-1]["state"]["plugin_selected"] == "fastapi"  # fallback default or select fastapi

def test_forge_plugin_unavailable(tmp_path):
    templates_dir = os.path.join(os.path.dirname(__file__), "../../orix/templates")
    plugins_dir = os.path.join(os.path.dirname(__file__), "../../orix/plugins")

    workflow = ForgeWorkflow(templates_dir, plugins_dir, str(tmp_path))

    # Inject a non-existent backend to force plugin_selection failure
    state = workflow.load_checkpoint()
    state["idea"] = "Build a custom app"
    state["architecture"] = {"specification": {"frameworks": {"backend": "non_existent_framework"}}}
    state["stages_completed"] = ["idea", "requirements", "architecture", "plan"]
    workflow.save_checkpoint(state)

    steps = list(workflow.run(resume=True, dry_run=False))

    # Selection should fail and explain
    failed_step = [s for s in steps if s.get("status") == "failed"]
    assert len(failed_step) > 0
    assert "non_existent_framework" in failed_step[0]["message"]
    assert "explanation" in failed_step[0]
