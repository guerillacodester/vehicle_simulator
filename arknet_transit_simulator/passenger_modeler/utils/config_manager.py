"""
Configuration Manager
====================

Handles loading and parsing of the main config.ini file that specifies
which statistical model to use and what data to apply it to.
"""

import configparser
from pathlib import Path
from typing import Dict, List, Any, Optional


class ConfigManager:
    """Manages the main configuration file (config.ini)"""
    
    def __init__(self, config_path: str):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to the config.ini file
        """
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        self.config.read(self.config_path)
        self._validate_config()
    
    def get_model_type(self) -> str:
        """Get the statistical model type to use"""
        return self.config.get('model', 'type', fallback='poisson')
    
    def get_data_files(self) -> Dict[str, str]:
        """Get dictionary of data file types and their paths"""
        data_files = {}
        
        if self.config.has_section('data'):
            for key, value in self.config.items('data'):
                # Resolve relative paths
                file_path = Path(self.config_path.parent) / value
                data_files[key] = str(file_path)
        
        return data_files
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration"""
        output_config = {}
        
        if self.config.has_section('output'):
            # Resolve relative path for model file
            model_file = self.config.get('output', 'model_file', fallback='models/generated/model.json')
            model_path = Path(self.config_path.parent) / model_file
            output_config['model_file'] = str(model_path)
            
            output_config['include_statistics'] = self.config.getboolean('output', 'include_statistics', fallback=True)
            output_config['include_validation'] = self.config.getboolean('output', 'include_validation', fallback=True)
        
        return output_config
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration"""
        processing_config = {}
        
        if self.config.has_section('processing'):
            processing_config['walking_distance_meters'] = self.config.getint('processing', 'walking_distance_meters', fallback=600)
            processing_config['generation_interval_seconds'] = self.config.getint('processing', 'generation_interval_seconds', fallback=30)
        
        return processing_config
    
    def get_environment_config(self) -> Dict[str, str]:
        """Get environment configuration"""
        env_config = {}
        
        if self.config.has_section('environment'):
            env_config['region'] = self.config.get('environment', 'region', fallback='unknown')
            env_config['timezone'] = self.config.get('environment', 'timezone', fallback='UTC')
            env_config['coordinate_system'] = self.config.get('environment', 'coordinate_system', fallback='WGS84')
        
        return env_config
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get complete configuration as dictionary"""
        return {
            'model_type': self.get_model_type(),
            'data_files': self.get_data_files(),
            'output': self.get_output_config(),
            'processing': self.get_processing_config(),
            'environment': self.get_environment_config()
        }
    
    def _validate_config(self):
        """Validate the configuration file"""
        errors = []
        
        # Check required sections
        required_sections = ['model', 'data', 'output']
        for section in required_sections:
            if not self.config.has_section(section):
                errors.append(f"Missing required section: [{section}]")
        
        # Check model type
        if self.config.has_section('model'):
            model_type = self.config.get('model', 'type', fallback=None)
            if not model_type:
                errors.append("Missing model.type in configuration")
        
        # Check data files exist
        if self.config.has_section('data'):
            for key, value in self.config.items('data'):
                file_path = Path(self.config_path.parent) / value
                if not file_path.exists():
                    errors.append(f"Data file not found: {value} ({file_path})")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ValueError(error_msg)
    
    def list_available_data_files(self) -> List[str]:
        """List all configured data files that exist"""
        available_files = []
        data_files = self.get_data_files()
        
        for data_type, file_path in data_files.items():
            if Path(file_path).exists():
                available_files.append(f"{data_type}: {file_path}")
            else:
                available_files.append(f"{data_type}: {file_path} (NOT FOUND)")
        
        return available_files
    
    def update_model_type(self, new_model_type: str):
        """Update the model type in the configuration"""
        self.config.set('model', 'type', new_model_type)
        
        # Save back to file
        with open(self.config_path, 'w') as f:
            self.config.write(f)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the configuration"""
        summary_lines = []
        summary_lines.append("📋 Passenger Modeler Configuration")
        summary_lines.append("=" * 40)
        
        summary_lines.append(f"🧠 Model Type: {self.get_model_type()}")
        
        summary_lines.append("\n📂 Data Files:")
        for data_type, file_path in self.get_data_files().items():
            exists = "✅" if Path(file_path).exists() else "❌"
            summary_lines.append(f"   {exists} {data_type}: {Path(file_path).name}")
        
        output_config = self.get_output_config()
        summary_lines.append(f"\n📊 Output: {Path(output_config['model_file']).name}")
        
        processing_config = self.get_processing_config()
        summary_lines.append(f"\n⚙️ Processing:")
        summary_lines.append(f"   Walking Distance: {processing_config.get('walking_distance_meters', 600)}m")
        summary_lines.append(f"   Generation Interval: {processing_config.get('generation_interval_seconds', 30)}s")
        
        env_config = self.get_environment_config()
        summary_lines.append(f"\n🌍 Environment: {env_config.get('region', 'unknown')} ({env_config.get('timezone', 'UTC')})")
        
        return "\n".join(summary_lines)
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get the configuration as a dictionary"""
        config_dict = {}
        
        for section_name in self.config.sections():
            config_dict[section_name] = dict(self.config.items(section_name))
        
        return config_dict
    
    def get_version(self) -> str:
        """Get the version from config.ini [version] section"""
        return self.config.get('version', 'config_version', fallback='1.0.0')
    
    def get_plugin_config_path(self, model_type: str) -> str:
        """
        Get the plugin configuration file path for a specific model type
        
        Args:
            model_type: The statistical model type (e.g., 'poisson', 'gaussian')
            
        Returns:
            Plugin config filename, defaults to {model_type}_model.json if not specified
        """
        if self.config.has_section('plugin_configs'):
            return self.config.get('plugin_configs', model_type, fallback=f'{model_type}_model.json')
        else:
            return f'{model_type}_model.json'