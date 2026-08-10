import os
import shutil
import tempfile
from pathlib import Path
from orix.core.orchestrator import Orchestrator
from orix.core.doctor import OrixDoctor

def test_scaffold_fastapi_and_doctor():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    templates_dir = os.path.join(base_dir, "orix", "templates")
    plugins_dir = os.path.join(base_dir, "orix", "plugins")

    orchestrator = Orchestrator(templates_dir, plugins_dir)

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "fastapi_app"

        # Scaffold fastapi project
        orchestrator.generate(str(output_path), "fastapi", {"docker": False, "auth": False})

        assert (output_path / "app" / "main.py").exists()
        assert (output_path / "requirements.txt").exists()

        # Validate with Doctor
        doctor = OrixDoctor(str(output_path))
        report = doctor.run_diagnostics()

        assert "scores" in report
        assert report["scores"]["Overall"] > 0
        assert len(report["findings"]) > 0
