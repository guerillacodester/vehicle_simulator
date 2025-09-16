import sys
import importlib.util
import inspect
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Type

plugins_path = Path(__file__).parent.parent / 'plugins'
sys.path.insert(0, str(plugins_path))

from base_model import StatisticalModel

class PluginLoader:
    def __init__(self, plugins_dir: str, configs_dir: str, config_manager=None):
        self.plugins_dir = Path(plugins_dir)
        self.configs_dir = Path(configs_dir)
        self.config_manager = config_manager
        self.loaded_plugins: Dict[str, Type[StatisticalModel]] = {}
        self.plugin_configs: Dict[str, str] = {}
        
        self._discover_plugins()
        self._discover_configs()
    
    def _discover_plugins(self):
        plugin_files = list(self.plugins_dir.glob("*_plugin.py"))
        for plugin_file in plugin_files:
            try:
                self._load_plugin_file(plugin_file)
            except Exception as e:
                print(f"Failed to load plugin {plugin_file.name}: {e}")
    
    def _load_plugin_file(self, plugin_file: Path):
        module_name = plugin_file.stem
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (issubclass(obj, StatisticalModel) and 
                obj != StatisticalModel and 
                hasattr(obj, 'get_model_type')):
                
                try:
                    temp_instance = obj.__new__(obj)
                    model_type = temp_instance.get_model_type()
                    self.loaded_plugins[model_type] = obj
                    print(f"Loaded plugin: {name} ({model_type})")
                except Exception as e:
                    print(f"Warning: Could not determine model type for {name}: {e}")
    
    def _discover_configs(self):
        if not self.configs_dir.exists():
            raise ValueError(f"Configs directory not found: {self.configs_dir}")
        
        print(f"Discovering configs in {self.configs_dir}")
        
        if self.config_manager:
            for model_type in self.loaded_plugins.keys():
                config_filename = self.config_manager.get_plugin_config_path(model_type)
                config_file_path = self.configs_dir / config_filename
                
                if config_file_path.exists():
                    self.plugin_configs[model_type] = str(config_file_path)
                    print(f"Found config: {model_type} -> {config_filename}")
                else:
                    print(f"Warning: Config file not found: {config_filename}")
        else:
            config_files = list(self.configs_dir.glob("*_model.json"))
            for config_file in config_files:
                model_type = config_file.stem.replace('_model', '')
                if model_type in self.loaded_plugins:
                    self.plugin_configs[model_type] = str(config_file)
                    print(f"Found config: {model_type} -> {config_file.name}")
    
    def get_available_models(self) -> List[str]:
        return list(self.loaded_plugins.keys())
    
    def create_model(self, model_type: str) -> Optional[StatisticalModel]:
        if model_type not in self.loaded_plugins:
            return None
        
        config_path = self.plugin_configs.get(model_type)
        if not config_path:
            raise ValueError(f"No configuration found for model type: {model_type}")
        
        plugin_class = self.loaded_plugins[model_type]
        return plugin_class(config_path)
    
    def list_models_with_details(self) -> Dict[str, Dict[str, Any]]:
        models_info = {}
        for model_type in self.loaded_plugins.keys():
            try:
                plugin_class = self.loaded_plugins[model_type]
                config_path = self.plugin_configs.get(model_type)
                
                if config_path:
                    temp_instance = plugin_class(config_path)
                    models_info[model_type] = temp_instance.get_info()
                else:
                    models_info[model_type] = {"error": f"No config found for {model_type}"}
            except Exception as e:
                models_info[model_type] = {"error": f"Failed to get info: {e}"}
        
        return models_info
