import os
import pytest
from orix.core.doctor import OrixDoctor

def test_doctor_diagnose_and_scores(tmp_path):
    # Create an incomplete project workspace (lacks git, lacks lock file, lacks tests)
    doctor = OrixDoctor(str(tmp_path))
    report = doctor.run_diagnostics()

    scores = report["scores"]
    issues = report["issues"]

    # Security score should be penalized because of missing .git directory (starts at 100, -20)
    assert scores["Security"] == 80
    assert len(issues["Security"]) == 1

    # Testing score should be penalized for missing tests folder and pytest config
    assert scores["Testing"] == 30

    # Dependencies score should be penalized for missing requirements file
    assert scores["Dependencies"] == 60

    # Overall score should match unweighted mathematical average
    expected_overall = round((80 + 30 + 60 + 80) / 4)
    assert scores["Overall"] == expected_overall
    assert "Scoring Model Documentation" in report["scoring_model"]
