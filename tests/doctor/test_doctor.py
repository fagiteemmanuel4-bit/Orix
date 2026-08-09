import os
import pytest
from orix.core.doctor import OrixDoctor

def test_doctor_diagnose_and_scores(tmp_path):
    # Create an incomplete project workspace (lacks git, lacks lock file, lacks tests)
    doctor = OrixDoctor(str(tmp_path))
    report = doctor.run_diagnostics()

    scores = report["scores"]
    findings = report["findings"]

    # Security score should be penalized because of missing .git directory and no secrets found (starts at 100, -15 because missing .git)
    # Actually under new severity rules: missing .git is HIGH severity (-15 points). So Security score should be 85.
    assert scores["Security"] == 85
    assert len(findings) > 0

    # Testing score should be penalized for missing tests folder (HIGH severity, -15) and no test config (MEDIUM, -10). So Testing score should be 75.
    assert scores["Testing"] == 75

    # Dependencies score should be penalized for missing requirements file (HIGH severity, -15). So Dependencies score should be 85.
    assert scores["Dependencies"] == 85

    # Overall score should match unweighted mathematical average of categories
    expected_overall = round((85 + 75 + 85 + 95) / 4)
    assert scores["Overall"] == expected_overall
    assert "Scoring Model Documentation" in report["scoring_model"]

def test_doctor_critical_security_override(tmp_path):
    # Setup files with a simulated committed secret key to trigger CRITICAL override
    (tmp_path / "app.py").write_text("api_key = 'sk-1234567890abcdef'\n", encoding="utf-8")

    doctor = OrixDoctor(str(tmp_path))
    report = doctor.run_diagnostics()

    scores = report["scores"]
    # Check that any CRITICAL security finding drops Security and Overall health index directly to 0
    assert scores["Security"] == 0
    assert scores["Overall"] == 0
