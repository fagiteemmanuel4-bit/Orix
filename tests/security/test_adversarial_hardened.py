import os
import pytest
import tempfile
from pathlib import Path
from orix.core.toolbox import WorkspaceToolbox

def test_hardened_symlink_escape():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "workspace"
        root.mkdir()

        # Create a secret file outside the workspace root
        secret_file = Path(tmp_dir) / "secret.txt"
        secret_file.write_text("SUPER_SECRET_VALUE", encoding="utf-8")

        # Create a symlink inside workspace pointing to secret file outside
        escaped_symlink = root / "escaped_symlink"
        try:
            os.symlink(str(secret_file), str(escaped_symlink))
        except OSError:
            # Skip if symlink creation is not permitted on host (e.g. Windows non-admin)
            pytest.skip("Symlink creation not supported on this platform/configuration")

        toolbox = WorkspaceToolbox(str(root))

        # Try to read the symlinked target outside workspace
        with pytest.raises(ValueError, match="Path traversal detected|violates the absolute workspace sandboxed boundaries"):
            toolbox.resolve_path("escaped_symlink")

def test_hardened_command_shell_injection():
    with tempfile.TemporaryDirectory() as tmp_dir:
        toolbox = WorkspaceToolbox(tmp_dir)

        # Attempt command injection by using shell operators in command arguments
        # If shell=False is enforced correctly, it will try to execute the string literally as the binary name,
        # which will raise a FileNotFoundError instead of running the nested command.
        inject_payload = ["echo", "hello; cat /etc/passwd"]

        # Let's run a raw shell command or equivalent through run_shell or subprocess wrapper
        with pytest.raises(FileNotFoundError):
            # run_shell should fail if we attempt to pass raw un-tokenized command injection strings
            # and executing non-existent binaries literally
            toolbox.run_shell(["nonexistent_bin; rm -rf /"])
