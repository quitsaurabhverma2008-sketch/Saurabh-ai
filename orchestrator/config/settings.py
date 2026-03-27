"""
Settings Configuration
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
PROJECT_ROOT = BASE_DIR

CONFIG = {
    "orchestrator": {
        "name": "Master Orchestrator",
        "version": "1.0.0",
        "max_retries": 3,
        "retry_delay": 2
    },
    "paths": {
        "base_dir": str(BASE_DIR),
        "project_root": str(PROJECT_ROOT),
        "orchestrator_dir": str(Path(__file__).parent),
        "agents_dir": str(Path(__file__).parent / "agents"),
        "shared_memory": str(BASE_DIR / "shared_memory.json")
    },
    "agents": {
        "planner": {"name": "Planner Agent", "enabled": True},
        "backend": {"name": "Backend Agent", "enabled": True},
        "frontend": {"name": "Frontend Agent", "enabled": True},
        "tester": {"name": "Tester Agent", "enabled": True},
        "integrator": {"name": "Integrator Agent", "enabled": True},
        "qa": {"name": "QA Agent", "enabled": True}
    },
    "context7": {
        "enabled": True,
        "auto_read_project": True
    }
}

def get_config(key: str = None):
    if key is None:
        return CONFIG
    keys = key.split(".")
    value = CONFIG
    for k in keys:
        value = value.get(k)
    return value
