import os
import pytest
from orix.core.forge import Forge

def test_e2e_fastapi_with_auth(tmp_path):
    # Retrieve real path configuration
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    templates_dir = os.path.join(base, "orix", "templates")
    plugins_dir = os.path.join(base, "orix", "plugins")

    forge = Forge(str(tmp_path), templates_dir, plugins_dir)

    # Run the full end-to-end forge loop on a realistic FastAPI prompt with auth
    state = forge.run_forge(idea="Create a FastAPI service with authentication.")

    generated_path = os.path.join(str(tmp_path), "generated-project")

    # Verify physical file existence
    assert os.path.exists(generated_path), "E2E: Generated project directory does not exist!"
    assert os.path.exists(os.path.join(generated_path, "requirements.txt")), "E2E: requirements.txt is missing!"
    assert os.path.exists(os.path.join(generated_path, "app", "main.py")), "E2E: main.py is missing!"

    # Verify rendering contents
    with open(os.path.join(generated_path, "app", "main.py"), "r", encoding="utf-8") as f:
        content = f.read()
    assert 'app = FastAPI' in content, "E2E: App title / FastAPI initialize not rendered correctly!"
    assert 'login' in content, "E2E: Auth/login endpoint was not rendered in main.py!"
