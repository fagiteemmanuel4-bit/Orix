import os
import yaml
from typing import Dict, Any

class Architect:
    def __init__(self, workspace_root: str):
        self.workspace_root = os.path.abspath(workspace_root)
        self.orix_dir = os.path.join(self.workspace_root, ".orix")

    def generate_spec(self, idea: str) -> Dict[str, Any]:
        if not idea or not idea.strip():
            raise ValueError(
                "Idea prompt is empty.\n"
                "Details: Orix Architect requires a non-empty description of your project.\n"
                "What to do next: Please run 'orix architect' with a descriptive idea prompt."
            )

        # Intelligently analyze the idea prompt to determine frameworks/technologies
        idea_lower = idea.lower()

        frontend = "React" if "react" in idea_lower else "Jinja2 Templates"
        backend = "FastAPI" if "fastapi" in idea_lower else ("Django" if "django" in idea_lower else "FastAPI")
        database = "PostgreSQL" if ("postgres" in idea_lower or "saas" in idea_lower) else "SQLite"
        auth = "JWT" if "jwt" in idea_lower else ("Django Auth" if "django" in idea_lower else "Token Auth")

        architecture = {
            "application_type": "SaaS Web Application" if "saas" in idea_lower else "Web Service",
            "frontend": frontend,
            "backend": backend,
            "database": database,
            "authentication": auth,
            "apis": ["RESTful JSON API"],
            "storage": "Local Filesystem" if "local" in idea_lower else "S3 Compatible Object Storage",
            "external_services": ["Email Service"] if "saas" in idea_lower else [],
            "testing": "Pytest" if backend != "Django" else "Django TestCase",
            "deployment": "Docker / AWS ECS" if "docker" in idea_lower else "Local / VPS",
            "security_requirements": [
                "Strict boundary file access control",
                "Hashed password storage",
                "HTTPS-only communication"
            ]
        }

        # Step-by-step Forge generation plan
        plan = {
            "project_name": "generated-project",
            "framework": backend.lower(),
            "docker": "docker" in idea_lower,
            "auth": True,
            "steps": [
                {"id": 1, "name": "Initialize state", "status": "pending"},
                {"id": 2, "name": "Generate project structure", "status": "pending"},
                {"id": 3, "name": "Configure settings", "status": "pending"},
                {"id": 4, "name": "Run initial validation", "status": "pending"},
                {"id": 5, "name": "Execute test suite", "status": "pending"}
            ]
        }

        # Decisions markdown document
        decisions_md = f"""# Orix Architectural Decisions

## Project Idea
"{idea}"

## Chosen Architecture Summary
- **Backend Framework**: {backend}
- **Frontend Layer**: {frontend}
- **Database System**: {database}
- **Auth Strategy**: {auth}

## Detailed Rationale
1. **Framework Choice ({backend})**: Based on the project prompt analysis, {backend} is best suited for handling rapid, modular code scaffolding.
2. **Database Choice ({database})**: selected to provide reliable schema management and easy integration.
3. **Authentication Strategy ({auth})**: standard authentication was chosen for security and stateless scalability.

## Security Controls
- Restrict file and path resolutions strictly inside the workspace boundary.
- Enforce permission gating for high-risk operations.
"""

        # Ensure .orix directory exists
        os.makedirs(self.orix_dir, exist_ok=True)

        # Write files
        arch_path = os.path.join(self.orix_dir, "architecture.yaml")
        plan_path = os.path.join(self.orix_dir, "plan.yaml")
        decisions_path = os.path.join(self.orix_dir, "decisions.md")

        with open(arch_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(architecture, f, default_flow_style=False)

        with open(plan_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(plan, f, default_flow_style=False)

        with open(decisions_path, "w", encoding="utf-8") as f:
            f.write(decisions_md)

        return {
            "architecture": architecture,
            "plan": plan,
            "decisions_md": decisions_md,
            "paths": {
                "architecture": arch_path,
                "plan": plan_path,
                "decisions": decisions_path
            }
        }
