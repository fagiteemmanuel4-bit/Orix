import shutil
from typing import Dict, List

COMMON_CHECKS = {
    "xcodebuild": "macOS (Xcode) builds",
    "gradle": "Android/Gradle builds",
    "javac": "Java compiler",
    "node": "Node.js and npm",
    "docker": "Docker for sandboxed execution",
    "cargo": "Rust toolchain (cargo)",
}


def run_environment_checks() -> Dict[str, bool]:
    results = {}
    for cmd, desc in COMMON_CHECKS.items():
        path = shutil.which(cmd)
        results[cmd] = bool(path)
    return results


def format_report(results: Dict[str, bool]) -> str:
    lines: List[str] = []
    for cmd, ok in results.items():
        status = "FOUND" if ok else "MISSING"
        lines.append(f"{cmd}: {status}")
    return "\n".join(lines)

if __name__ == "__main__":
    res = run_environment_checks()
    print(format_report(res))
