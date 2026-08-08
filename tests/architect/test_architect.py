import os
import pytest
from orix.core.architect import Architect

def test_architect_valid_idea(tmp_path):
    arch = Architect(str(tmp_path))
    res = arch.generate_spec("Build a FastAPI inventory management SaaS with postgres and JWT auth")

    assert os.path.exists(res["architecture"])
    assert os.path.exists(res["plan"])
    assert os.path.exists(res["decisions"])

    # Read back and assert values
    import yaml
    with open(res["architecture"], "r") as f:
        arch_data = yaml.safe_load(f)
    assert arch_data["specification"]["components"]["database"] == "postgresql"
    assert arch_data["specification"]["components"]["authentication"] == "JWT"
    assert arch_data["specification"]["frameworks"]["backend"] == "fastapi"

def test_architect_empty_idea(tmp_path):
    arch = Architect(str(tmp_path))
    with pytest.raises(ValueError, match="The project idea cannot be empty"):
        arch.generate_spec("   ")
