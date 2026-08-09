"""
Orix X - Universal Developer OS CLI Platform

A model-agnostic developer environment CLI that decouples scaffolding,
workspace diagnostics, system blueprinting, and multi-stage generation
from underlying model instances.
"""

__version__ = "3.1.0"
__author__ = "Orix Contributors"
__license__ = "MIT"

# Expose main entry points for programmatic access
from orix.core.cli import cli
from orix.core.agent import AgentSession
from orix.core.forge import ForgeWorkflow
from orix.core.doctor import OrixDoctor
from orix.core.explain import OrixExplain
from orix.core.architect import Architect
from orix.core.toolbox import WorkspaceToolbox
from orix.core.indexer import WorkspaceIndexer
from orix.core.permissions import PermissionManager
from orix.core.memory import LocalMemoryStore
from orix.core.config import ConfigManager

__all__ = [
    "cli",
    "AgentSession",
    "ForgeWorkflow",
    "OrixDoctor",
    "OrixExplain",
    "Architect",
    "WorkspaceToolbox",
    "WorkspaceIndexer",
    "PermissionManager",
    "LocalMemoryStore",
    "ConfigManager",
]
