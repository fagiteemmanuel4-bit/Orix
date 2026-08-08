import os
import yaml
from typing import Dict, Any, Optional

class Architect:
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.getcwd()

    def analyze_idea(self, idea: str) -> Dict[str, Any]:
        idea_lower = idea.lower()

        # Deterministic analysis based on prompt keywords
        # Frontend selection
        frontend = "react" if "react" in idea_lower or "frontend" in idea_lower else "none"

        # Backend selection
        backend = "django" if "django" in idea_lower else "fastapi"
        if "backend" in idea_lower and "django" not in idea_lower:
            backend = "fastapi"

        # App type
        if frontend != "none":
            app_type = "Single Page Application + API"
        elif backend == "django":
            app_type = "Fullstack MVC Application"
        else:
            app_type = "REST API Service"

        # Database selection
        database = "sqlite"
        if "postgres" in idea_lower or "postgresql" in idea_lower:
            database = "postgresql"
        elif "mysql" in idea_lower:
            database = "mysql"

        # Authentication selection
        authentication = "None"
        if "auth" in idea_lower or "login" in idea_lower or "jwt" in idea_lower:
            authentication = "JWT" if backend == "fastapi" or frontend != "none" else "Session-based"

        # Deployment selection
        deployment = "Standard"
        if "docker" in idea_lower or "kubernetes" in idea_lower:
            deployment = "Docker Compose"

        # Testing framework
        testing = "pytest"
        if frontend == "react" and backend == "none":
            testing = "jest"

        # Name heuristic
        project_name = "orix-app"
        words = [w for w in idea.split() if w.isalnum() and len(w) > 3]
        if words:
            # simple heuristic: use first 2 meaningful words joined by hyphen
            project_name = "-".join(words[:2]).lower()

        return {
            "project_name": project_name,
            "application_type": app_type,
            "frontend": frontend,
            "backend": backend,
            "database": database,
            "authentication": authentication,
            "apis": "REST APIs",
            "storage": "Local File System",
            "external_services": "None",
            "testing": testing,
            "deployment": deployment,
            "security_requirements": [
                "Workspace boundary protection",
                "Environment variable secrets management",
                "Input parameter validation"
            ]
        }

    def generate_spec(self, idea: str, target_dir: Optional[str] = None) -> Dict[str, str]:
        if not idea.strip():
            raise ValueError("The project idea cannot be empty.")

        analysis = self.analyze_idea(idea)

        # Build architecture spec
        architecture_data = {
            "specification": {
                "project_name": analysis["project_name"],
                "application_type": analysis["application_type"],
                "frameworks": {
                    "frontend": analysis["frontend"],
                    "backend": analysis["backend"]
                },
                "components": {
                    "database": analysis["database"],
                    "authentication": analysis["authentication"],
                    "apis": analysis["apis"],
                    "storage": analysis["storage"],
                    "external_services": analysis["external_services"]
                },
                "operations": {
                    "testing": analysis["testing"],
                    "deployment": analysis["deployment"]
                },
                "security": analysis["security_requirements"]
            }
        }

        # Build plan
        plan_data = {
            "project_name": analysis["project_name"],
            "framework": analysis["backend"],
            "stages": {
                "1_requirements": "Refine the functional requirements from the prompt idea.",
                "2_architecture": "Define component interaction model and DB schema.",
                "3_generation": f"Scaffold project via Orix CLI using {analysis['backend']} template.",
                "4_validation": "Check for essential boilerplate files and workspace bounds.",
                "5_testing": f"Run automated tests under {analysis['testing']}."
            }
        }

        # Build decisions markdown
        decisions_md = f"""# Architectural Decisions - {analysis['project_name'].upper()}

Based on the proposed idea: *"{idea}"*

## Chosen Stack
- **Application Type:** {analysis['application_type']}
- **Backend Framework:** {analysis['backend']}
- **Frontend Framework:** {analysis['frontend']}
- **Database:** {analysis['database']}
- **Authentication:** {analysis['authentication']}
- **Deployment Strategy:** {analysis['deployment']}

## Key Technical Decisions
1. **Framework Choice ({analysis['backend']}):** Chosen as the central application container for API routing and core logic.
2. **Database Choice ({analysis['database']}):** Standard storage layer to support transactional data integrity.
3. **Authentication Scheme ({analysis['authentication']}):** Secures endpoints against unauthorized requests.

## Deployment & Security
- Isolated workspace bounds for any runner agent actions.
- Containerization using {analysis['deployment']}.
"""

        # Write files
        out_dir = target_dir or os.path.join(self.workspace_root, ".orix")
        os.makedirs(out_dir, exist_ok=True)

        arch_file = os.path.join(out_dir, "architecture.yaml")
        plan_file = os.path.join(out_dir, "plan.yaml")
        dec_file = os.path.join(out_dir, "decisions.md")

        with open(arch_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(architecture_data, f, default_flow_style=False)

        with open(plan_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(plan_data, f, default_flow_style=False)

        with open(dec_file, "w", encoding="utf-8") as f:
            f.write(decisions_md)

        return {
            "architecture": arch_file,
            "plan": plan_file,
            "decisions": dec_file
        }
