import pytest
import os
import yaml
from orix.core.architect import Architect

def test_architect_valid_request(tmp_path):
    arch = Architect(str(tmp_path))
    res = arch.generate_spec("Build a SaaS inventory with React and Django")

    assert os.path.exists(res["paths"]["architecture"])
    assert os.path.exists(res["paths"]["plan"])
    assert os.path.exists(res["paths"]["decisions"])

    # Load and verify specs
    with open(res["paths"]["architecture"], "r") as f:
        spec = yaml.safe_load(f)
    assert spec["frontend"] == "React"
    assert spec["backend"] == "Django"
    assert spec["database"] == "PostgreSQL"

def test_architect_empty_request(tmp_path):
    arch = Architect(str(tmp_path))
    with pytest.raises(ValueError, match="Idea prompt is empty"):
        arch.generate_spec("")
