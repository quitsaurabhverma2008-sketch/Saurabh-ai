"""
Global Memory System - Central shared state for all agents
"""
import json
import os
from datetime import datetime
from pathlib import Path

MEMORY_FILE = Path(__file__).parent.parent / "shared_memory.json"

class GlobalMemory:
    def __init__(self):
        self.memory_file = MEMORY_FILE
        self.lock_file = MEMORY_FILE.with_suffix(".lock")
        self._ensure_memory_exists()
    
    def _ensure_memory_exists(self):
        if not self.memory_file.exists():
            default_memory = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "project_context": {},
                "task_queue": [],
                "agents": {},
                "execution_log": [],
                "shared_data": {}
            }
            self._write_memory(default_memory)
    
    def _read_memory(self):
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[GlobalMemory] Error reading: {e}")
            return {}
    
    def _write_memory(self, data):
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[GlobalMemory] Error writing: {e}")
    
    def read(self, key=None):
        memory = self._read_memory()
        if key is None:
            return memory
        return memory.get(key)
    
    def write(self, key, value):
        memory = self._read_memory()
        memory[key] = value
        memory["last_updated"] = datetime.now().isoformat()
        self._write_memory(memory)
    
    def update(self, updates: dict):
        memory = self._read_memory()
        memory.update(updates)
        memory["last_updated"] = datetime.now().isoformat()
        self._write_memory(memory)
    
    # Task Queue Methods
    def add_task(self, task: dict):
        memory = self._read_memory()
        task["id"] = task.get("id", f"task_{len(memory.get('task_queue', [])) + 1}")
        task["status"] = "pending"
        task["created_at"] = datetime.now().isoformat()
        memory.setdefault("task_queue", []).append(task)
        memory["last_updated"] = datetime.now().isoformat()
        self._write_memory(memory)
        return task["id"]
    
    def update_task(self, task_id: str, updates: dict):
        memory = self._read_memory()
        for task in memory.get("task_queue", []):
            if task.get("id") == task_id:
                task.update(updates)
                task["updated_at"] = datetime.now().isoformat()
                break
        memory["last_updated"] = datetime.now().isoformat()
        self._write_memory(memory)
    
    def get_task(self, task_id: str):
        memory = self._read_memory()
        for task in memory.get("task_queue", []):
            if task.get("id") == task_id:
                return task
        return None
    
    def get_all_tasks(self):
        memory = self._read_memory()
        return memory.get("task_queue", [])
    
    def get_pending_tasks(self):
        memory = self._read_memory()
        return [t for t in memory.get("task_queue", []) if t.get("status") == "pending"]
    
    # Agent Status Methods
    def register_agent(self, agent_id: str, agent_info: dict):
        memory = self._read_memory()
        memory.setdefault("agents", {})[agent_id] = {
            **agent_info,
            "registered_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
        memory["last_updated"] = datetime.now().isoformat()
        self._write_memory(memory)
    
    def update_agent_status(self, agent_id: str, status: str, details: dict = None):
        memory = self._read_memory()
        if agent_id in memory.get("agents", {}):
            memory["agents"][agent_id]["status"] = status
            memory["agents"][agent_id]["last_seen"] = datetime.now().isoformat()
            if details:
                memory["agents"][agent_id].update(details)
        memory["last_updated"] = datetime.now().isoformat()
        self._write_memory(memory)
    
    def get_agent_status(self, agent_id: str):
        memory = self._read_memory()
        return memory.get("agents", {}).get(agent_id, {})
    
    def get_all_agents(self):
        memory = self._read_memory()
        return memory.get("agents", {})
    
    # Logging
    def log(self, agent_id: str, action: str, details: str = ""):
        memory = self._read_memory()
        memory.setdefault("execution_log", []).append({
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "action": action,
            "details": details
        })
        memory["last_updated"] = datetime.now().isoformat()
        self._write_memory(memory)
    
    def get_logs(self, limit: int = 50):
        memory = self._read_memory()
        logs = memory.get("execution_log", [])
        return logs[-limit:]
    
    # Project Context
    def set_project_context(self, context: dict):
        memory = self._read_memory()
        memory["project_context"] = context
        memory["last_updated"] = datetime.now().isoformat()
        self._write_memory(memory)
    
    def get_project_context(self):
        memory = self._read_memory()
        return memory.get("project_context", {})
    
    # Shared Data between agents
    def set_shared_data(self, key: str, value):
        memory = self._read_memory()
        memory.setdefault("shared_data", {})[key] = value
        memory["last_updated"] = datetime.now().isoformat()
        self._write_memory(memory)
    
    def get_shared_data(self, key: str):
        memory = self._read_memory()
        return memory.get("shared_data", {}).get(key)
    
    def clear(self):
        self._ensure_memory_exists()
        print("[GlobalMemory] Memory cleared to default state")

# Singleton instance
global_memory = GlobalMemory()
