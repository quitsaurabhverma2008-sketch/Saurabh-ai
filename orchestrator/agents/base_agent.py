"""
Base Agent Class - Template for all worker agents
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod

sys.path.insert(0, str(Path(__file__).parent.parent))
from global_memory import global_memory
from task_queue import task_queue, TaskStatus

class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str = None):
        self.agent_id = agent_id
        self.name = name or agent_id
        self.gm = global_memory
        self.tq = task_queue
        self.status = "idle"
        self.current_task_id = None
        self._register()
    
    def _register(self):
        self.gm.register_agent(self.agent_id, {
            "name": self.name,
            "status": self.status,
            "type": self.__class__.__name__
        })
        self.gm.log(self.agent_id, "REGISTERED", f"Agent {self.name} registered")
    
    def update_status(self, status: str, details: dict = None):
        self.status = status
        self.gm.update_agent_status(self.agent_id, status, details)
    
    def log(self, action: str, details: str = ""):
        self.gm.log(self.agent_id, action, details)
        print(f"[{self.name}] {action}: {details}")
    
    @abstractmethod
    def analyze_task(self, task: dict) -> dict:
        """Analyze task and return plan"""
        pass
    
    @abstractmethod
    def execute_task(self, task: dict) -> dict:
        """Execute the task and return result"""
        pass
    
    def work_on_task(self, task_id: str):
        """Main work loop for a task"""
        task = self.tq.get_task(task_id)
        if not task:
            self.log("ERROR", f"Task {task_id} not found")
            return {"error": "Task not found"}
        
        self.current_task_id = task_id
        self.update_status("working", {"task_id": task_id})
        self.log("STARTED", f"Working on: {task.get('title')}")
        
        try:
            plan = self.analyze_task(task)
            self.tq.update_progress(task_id, 30, f"Plan: {plan.get('summary', 'OK')}")
            self.log("ANALYZED", f"Plan created")
            
            result = self.execute_task(task)
            self.tq.complete_task(task_id, result)
            self.update_status("completed")
            self.log("COMPLETED", f"Task done: {task.get('title')}")
            
            return result
            
        except Exception as e:
            self.log("ERROR", str(e))
            task_obj = self.tq.get_task(task_id)
            retries = task_obj.get("retries", 0) if task_obj else 0
            
            if retries < 3:
                self.tq.retry_task(task_id)
                self.update_status("retrying")
                self.log("RETRY", f"Will retry (attempt {retries + 1})")
            else:
                self.tq.fail_task(task_id, str(e))
                self.update_status("failed")
                self.log("FAILED", f"Task failed after {retries} retries")
            
            return {"error": str(e)}
        
        finally:
            self.current_task_id = None
    
    def read_project_structure(self, project_path: str = None):
        """Read project structure for context"""
        from config.settings import get_config
        
        if project_path is None:
            project_path = get_config("paths.project_root")
        
        structure = {
            "files": [],
            "directories": [],
            "languages": set()
        }
        
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, project_path)
                structure["files"].append(relpath)
                
                ext = os.path.splitext(file)[1].lower()
                if ext:
                    structure["languages"].add(ext)
        
        structure["languages"] = list(structure["languages"])
        self.log("READ_STRUCTURE", f"Found {len(structure['files'])} files")
        
        return structure
    
    def read_file(self, filepath: str):
        """Read a file's content"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.log("READ_ERROR", f"Could not read {filepath}: {e}")
            return None
    
    def write_file(self, filepath: str, content: str):
        """Write content to a file"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.log("WROTE", filepath)
            return True
        except Exception as e:
            self.log("WRITE_ERROR", f"Could not write {filepath}: {e}")
            return False
    
    def run_command(self, command: str, cwd: str = None):
        """Run a shell command"""
        import subprocess
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=cwd
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
