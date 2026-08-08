import os
import shutil
import pytest
from click.testing import CliRunner
from orix.core.cli import cli

def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Orix X: Universal Dev CLI" in result.output

def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "orix, version 3.1.0" in result.output

def test_cli_invalid_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["invalid_command_here"])
    assert result.exit_code != 0
    assert "No such command" in result.output

def test_cli_create_invalid_framework():
    runner = CliRunner()
    result = runner.invoke(cli, ["create", "my_project", "--framework", "non_existent_framework"])
    # Framework validation should output Error
    assert "is not supported." in result.output

def test_cli_diagnose():
    runner = CliRunner()
    result = runner.invoke(cli, ["diagnose"])
    assert result.exit_code == 0
    assert "Orix environment diagnostics report" in result.output

def test_cli_analyze_with_input():
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze"], input="+\n-\nerror\n")
    assert result.exit_code == 0
    assert "Analysis Summary" in result.output
    assert "Lines" in result.output
    assert "Additions" in result.output

def test_cli_run_invalid_binary():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "some_completely_fake_binary"])
    assert "Error running command" in result.output

def test_cli_create_with_spec_missing_file():
    runner = CliRunner()
    result = runner.invoke(cli, ["create", "--spec", "missing_spec.yaml"])
    assert result.exit_code != 0
    assert "does not exist" in result.output

def test_cli_create_success(tmp_path):
    runner = CliRunner()
    # Create project using FastAPI framework deterministically
    target_dir = tmp_path / "fastapi_project"
    result = runner.invoke(cli, ["create", "fastapi_project", "--framework", "fastapi", "--no-docker", "--no-auth", "--output", str(target_dir)])
    assert result.exit_code == 0
    assert "Success! Project created" in result.output
    assert os.path.exists(target_dir / "requirements.txt")
