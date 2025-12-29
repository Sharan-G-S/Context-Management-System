"""
Configuration management for CMS.
"""

from typing import Dict, Any, Optional
import yaml
import os
from pathlib import Path


class Config:
    """Configuration manager for CMS."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self.config = config_dict or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports nested keys with dots)."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """Set configuration value by key."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.config.get(section, {})
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Config":
        """Load configuration from YAML file."""
        with open(yaml_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls(config_dict)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create configuration from dictionary."""
        return cls(config_dict)
    
    def to_yaml(self, yaml_path: str):
        """Save configuration to YAML file."""
        with open(yaml_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.config.copy()


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from file or use defaults.
    
    Search order:
    1. Provided path
    2. ./config/config.yaml
    3. ./config/default_config.yaml
    4. Built-in defaults
    """
    
    if config_path and os.path.exists(config_path):
        return Config.from_yaml(config_path)
    
    # Try standard locations
    search_paths = [
        "config/config.yaml",
        "config/default_config.yaml",
        str(Path(__file__).parent.parent.parent / "config" / "config.yaml"),
        str(Path(__file__).parent.parent.parent / "config" / "default_config.yaml"),
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            return Config.from_yaml(path)
    
    # Return default configuration
    return get_default_config()


def get_default_config() -> Config:
    """Get default configuration."""
    
    default_config = {
        "model": {
            "name": "gpt-4",
            "provider": "openai",
            "max_tokens": 8192,
            "context_window": 8192,
            "tokenizer": "cl100k_base",
        },
        "memory": {
            "core": {
                "max_tokens": 1000,
                "importance_threshold": 0.9,
                "immutable": True,
            },
            "long_term": {
                "semantic": {
                    "max_entries": 1000,
                    "embedding_model": "all-MiniLM-L6-v2",
                    "similarity_threshold": 0.7,
                    "max_tokens": 2000,
                },
                "episodic": {
                    "max_entries": 500,
                    "retention_days": 30,
                    "max_tokens": 1500,
                },
            },
            "working": {
                "max_turns": 10,
                "max_tokens": 3000,
                "compression_threshold": 0.8,
            },
        },
        "token_budget": {
            "system": 0.10,
            "core": 0.12,
            "semantic": 0.25,
            "episodic": 0.18,
            "working": 0.30,
            "reserve": 0.05,
        },
        "summarization": {
            "enabled": True,
            "model": "gpt-3.5-turbo",
            "strategy": "extractive",
            "compression_ratio": 0.3,
            "min_length": 100,
            "max_length": 500,
            "batch_size": 5,
        },
        "assembly": {
            "section_order": [
                "system",
                "core_memory",
                "semantic_memory",
                "episodic_memory",
                "working_memory",
                "current_task",
            ],
            "importance_weights": {
                "recency": 0.3,
                "relevance": 0.4,
                "importance": 0.3,
            },
            "position_bias_mitigation": True,
            "deduplication": True,
        },
        "optimization": {
            "enabled": True,
            "strategies": [
                "relevance_ranking",
                "temporal_decay",
                "importance_pruning",
                "semantic_clustering",
            ],
            "auto_prune": {
                "enabled": True,
                "interval_hours": 24,
                "threshold": 0.4,
            },
        },
        "policies": {
            "strict_budget": True,
            "allow_overflow": False,
            "overflow_strategy": "compress",
            "importance_scoring": {
                "user_explicit": 1.0,
                "system_critical": 0.95,
                "task_relevant": 0.8,
                "recent_interaction": 0.7,
                "background_info": 0.5,
            },
        },
        "observability": {
            "logging": {
                "level": "INFO",
                "format": "json",
                "output": "logs/cms.log",
            },
            "metrics": {
                "enabled": True,
                "track_token_usage": True,
                "track_latency": True,
                "track_memory_stats": True,
            },
        },
        "storage": {
            "backend": "local",
            "path": "data/cms_storage",
            "persistence": {
                "enabled": True,
                "auto_save": True,
                "save_interval": 300,
            },
        },
    }
    
    return Config(default_config)
