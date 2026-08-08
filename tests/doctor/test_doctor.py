import pytest
import os
from orix.core.doctor import Doctor

def test_doctor_healthy_project(tmp_path):
    # Setup standard layout to be highly healthy
    os.makedirs(tmp_path / ".git", exist_ok=True)
    os.makedirs(tmp_path / "app", exist_ok=True)
    os.makedirs(tmp_path / "tests", exist_ok=True)
    (tmp_path / "requirements.txt").write_text("pytest==9.1.1\n", encoding="utf-8")

    doctor = Doctor(str(tmp_path))
    res = doctor.run_diagnostics()

    assert res["scores"]["overall"] >= 90
    assert not any("Git" in issue for issue in res["issues"])
    assert not any("tests" in issue for issue in res["issues"])

def test_doctor_broken_project(tmp_path):
    # Empty directory has multiple problems
    doctor = Doctor(str(tmp_path))
    res = doctor.run_diagnostics()

    assert res["scores"]["overall"] < 80
    assert any("Git" in issue for issue in res["issues"])
    assert any("Testing" in issue or "tests" in issue.lower() for issue in res["issues"])
    assert any("Dependencies" in issue for issue in res["issues"])
