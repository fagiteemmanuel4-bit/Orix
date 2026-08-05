import platform
import shutil
import subprocess
from typing import Dict, List

class EnvironmentDiagnostics:
    TOOLS = [
        {"name": "python", "cmd": ["python", "--version"]},
        {"name": "node", "cmd": ["node", "--version"]},
        {"name": "git", "cmd": ["git", "--version"]},
        {"name": "docker", "cmd": ["docker", "--version"]},
    ]

    @staticmethod
    def check_command(command: List[str]) -> Dict[str, str]:
        try:
            output = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )
            version = output.stdout.strip() or output.stderr.strip()
            return {"available": True, "version": version}
        except Exception as exc:
            return {"available": False, "error": str(exc)}

    @classmethod
    def run(cls) -> Dict[str, Dict[str, str]]:
        results: Dict[str, Dict[str, str]] = {}
        for tool in cls.TOOLS:
            results[tool["name"]] = cls.check_command(tool["cmd"])
        results["platform"] = {
            "system": platform.system(),
            "release": platform.release(),
            "python_version": platform.python_version(),
        }
        return results

    @classmethod
    def format_report(cls, results: Dict[str, Dict[str, str]]) -> str:
        lines = ["Orix environment diagnostics report:"]
        lines.append(f"Platform: {results['platform']['system']} {results['platform']['release']}")
        lines.append(f"Python: {results['platform']['python_version']}")
        for tool, status in results.items():
            if tool == "platform":
                continue
            if status.get("available"):
                lines.append(f"- {tool}: available ({status.get('version')})")
            else:
                lines.append(f"- {tool}: unavailable ({status.get('error')})")
        return "\n".join(lines)
