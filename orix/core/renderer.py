import os
import jinja2
from typing import Dict, Any

class TemplateRenderer:
    def __init__(self, templates_base_path: str):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_base_path),
            keep_trailing_newline=True,
        )

    def render_project(self, template_name: str, target_path: str, context: Dict[str, Any]):
        template_path = os.path.join(self.env.loader.searchpath[0], template_name)
        
        for root, dirs, files in os.walk(template_path):
            # Calculate relative path from template root
            rel_path = os.path.relpath(root, template_path)
            
            # Render directory name if it contains placeholders
            rendered_rel_path = self._render_string(rel_path, context)
            dest_dir = os.path.join(target_path, rendered_rel_path)
            
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            for file in files:
                # Render filename if it contains placeholders
                rendered_filename = self._render_string(file, context)
                dest_file_path = os.path.join(dest_dir, rendered_filename)
                
                template_file_rel_path = os.path.join(rel_path, file)
                if template_file_rel_path.startswith("./"):
                    template_file_rel_path = template_file_rel_path[2:]
                
                template = self.env.get_template(os.path.join(template_name, template_file_rel_path))
                content = template.render(context)
                
                with open(dest_file_path, "w") as f:
                    f.write(content)

    def _render_string(self, source: str, context: Dict[str, Any]) -> str:
        return jinja2.Template(source).render(context)
