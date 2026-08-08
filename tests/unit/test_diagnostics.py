import platform
from orix.core.diagnostics import EnvironmentDiagnostics

def test_diagnostics_run():
    results = EnvironmentDiagnostics.run()
    assert "platform" in results
    assert results["platform"]["system"] == platform.system()
    assert results["platform"]["python_version"] == platform.python_version()

def test_diagnostics_format_report():
    results = {
        "python": {"available": True, "version": "Python 3.12.0"},
        "node": {"available": False, "error": "Not found"},
        "platform": {
            "system": "Linux",
            "release": "6.8.0",
            "python_version": "3.12.0"
        }
    }
    report = EnvironmentDiagnostics.format_report(results)
    assert "Orix environment diagnostics report:" in report
    assert "Platform: Linux 6.8.0" in report
    assert "Python: 3.12.0" in report
    assert "- python: available (Python 3.12.0)" in report
    assert "- node: unavailable (Not found)" in report
