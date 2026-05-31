import os
from typing import Dict, Any, List
from orix.core.renderer import TemplateRenderer
from orix.core.plugin_manager import PluginManager

class Orchestrator:
    def __init__(self, templates_dir: str, plugins_dir: str):
        self.renderer = TemplateRenderer(templates_dir)
        self.plugin_manager = PluginManager(plugins_dir)
        self.plugin_manager.load_plugins()

    def generate(self, project_name: str, framework_name: str, options: Dict[str, Any]):
        target_path = os.path.join(os.getcwd(), project_name)
        if not os.path.exists(target_path):
            os.makedirs(target_path)

        framework_plugin = self.plugin_manager.get_plugin_by_name(framework_name)
        if not framework_plugin:
            raise ValueError(f"Framework plugin '{framework_name}' not found.")

        # Build context
        context = {
            "project_name": project_name,
            **options
        }
        
        # Get context from plugin
        plugin_context = framework_plugin.get_context(options)
        context.update(plugin_context)

        # Render framework template
        template_name = framework_plugin.get_template_name()
        self.renderer.render_project(template_name, target_path, context)
        
        return target_path
