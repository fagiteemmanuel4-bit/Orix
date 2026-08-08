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
        templates_base_path = os.path.abspath(self.env.loader.searchpath[0])
        template_path = os.path.abspath(os.path.join(templates_base_path, template_name))
        
        if not template_path.startswith(templates_base_path + os.path.sep) and template_path != templates_base_path:
            raise ValueError(f"Template path traversal detected: '{template_name}' resolves outside base templates directory.")

        for root, dirs, files in os.walk(template_path):
            # Calculate relative path from template root
            rel_path = os.path.relpath(root, template_path)

            # Render directory name if it contains placeholders
            rendered_rel_path = self._render_string(rel_path, context)
            # Treat current dir marker as root
            if rendered_rel_path in (".", os.curdir):
                rendered_rel_path = ""

            dest_dir = os.path.join(target_path, rendered_rel_path)

            # Boundary check on directory
            resolved_target = os.path.abspath(target_path)
            resolved_dest_dir = os.path.abspath(dest_dir)
            if not resolved_dest_dir.startswith(resolved_target + os.path.sep) and resolved_dest_dir != resolved_target:
                raise ValueError(f"Directory path traversal detected: '{rendered_rel_path}' resolves outside target directory.")

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            for file in files:
                # Render filename if it contains placeholders
                rendered_filename = self._render_string(file, context)
                dest_file_path = os.path.join(dest_dir, rendered_filename)

                # Boundary check on file write
                resolved_dest_file = os.path.abspath(dest_file_path)
                if not resolved_dest_file.startswith(resolved_target + os.path.sep) and resolved_dest_file != resolved_target:
                    raise ValueError(f"File path traversal detected: '{rendered_filename}' resolves outside target directory.")

                # Build template-relative path using POSIX separators for Jinja2
                if rel_path in (".", os.curdir):
                    template_file_rel_path = file
                else:
                    template_file_rel_path = os.path.join(rel_path, file).replace(os.path.sep, '/')

                template_lookup_name = f"{template_name}/{template_file_rel_path}" if template_file_rel_path else template_name
                template = self.env.get_template(template_lookup_name)
                content = template.render(context)

                with open(dest_file_path, "w") as f:
                    f.write(content)

    def _render_string(self, source: str, context: Dict[str, Any]) -> str:
        return jinja2.Template(source).render(context)
