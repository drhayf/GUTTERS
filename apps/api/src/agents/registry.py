import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Optional
from .base import BaseAgent
from ..core.schemas import AgentManifest

class AgentRegistry:
    _instance: Optional["AgentRegistry"] = None
    _agents: dict[str, BaseAgent] = {}
    
    def __new__(cls) -> "AgentRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents = {}
        return cls._instance
    
    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name.lower().replace(" ", "_")] = agent
        print(f"[AgentRegistry] Registered agent: {agent.name}")
    
    def get(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name.lower().replace(" ", "_"))
    
    def list_agents(self) -> list[AgentManifest]:
        return [agent.get_manifest() for agent in self._agents.values()]
    
    def get_agent_names(self) -> list[str]:
        return list(self._agents.keys())
    
    @classmethod
    def get_instance(cls) -> "AgentRegistry":
        return cls()

def register_agents(agents_dir: Optional[Path] = None) -> AgentRegistry:
    registry = AgentRegistry.get_instance()
    
    if agents_dir is None:
        agents_dir = Path(__file__).parent
    
    for item in agents_dir.iterdir():
        if item.is_dir() and (item / "manifest.json").exists():
            _load_plugin_agent(item, registry)
        elif item.is_file() and item.suffix == ".py":
            if item.name not in ("__init__.py", "base.py", "registry.py"):
                _load_module_agent(item, registry)
    
    return registry

def _load_plugin_agent(plugin_dir: Path, registry: AgentRegistry) -> None:
    import json
    
    manifest_path = plugin_dir / "manifest.json"
    workflow_path = plugin_dir / "workflow.py"
    
    if not workflow_path.exists():
        print(f"[AgentRegistry] Skipping {plugin_dir.name}: no workflow.py found")
        return
    
    try:
        with open(manifest_path) as f:
            manifest_data = json.load(f)
        
        spec = importlib.util.spec_from_file_location(
            f"plugins.{plugin_dir.name}",
            workflow_path
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseAgent)
                    and attr is not BaseAgent
                ):
                    agent_instance = attr()
                    registry.register(agent_instance)
                    print(f"[AgentRegistry] Loaded plugin: {manifest_data.get('name', plugin_dir.name)}")
                    return
            
            print(f"[AgentRegistry] No agent class found in {workflow_path}")
    
    except Exception as e:
        print(f"[AgentRegistry] Error loading plugin {plugin_dir.name}: {e}")

def _load_module_agent(module_path: Path, registry: AgentRegistry) -> None:
    """Load an agent from a Python module file."""
    try:
        # Use direct import instead of spec_from_file_location
        # This preserves relative imports
        module_name = module_path.stem
        
        # Import relative to the agents package
        import importlib
        full_module_name = f"src.agents.{module_name}"
        module = importlib.import_module(full_module_name)
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseAgent)
                and attr is not BaseAgent
            ):
                agent_instance = attr()
                registry.register(agent_instance)
    
    except Exception as e:
        print(f"[AgentRegistry] Error loading module {module_path.name}: {e}")
