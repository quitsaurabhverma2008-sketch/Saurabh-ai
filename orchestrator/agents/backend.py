"""
Backend Agent - Handles server-side code
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.base_agent import BaseAgent

class BackendAgent(BaseAgent):
    def __init__(self):
        super().__init__("backend", "Backend Agent")
    
    def analyze_task(self, task: dict) -> dict:
        """Analyze backend requirements"""
        request = task.get("description", "")
        project_structure = self.read_project_structure()
        
        existing_apis = self._find_existing_apis(project_structure)
        
        return {
            "summary": f"Backend analysis complete",
            "existing_apis": existing_apis,
            "changes_needed": self._determine_changes(request)
        }
    
    def execute_task(self, task: dict) -> dict:
        """Execute backend changes"""
        request = task.get("description", "")
        project_path = task.get("project_path")
        
        self.log("EXECUTING", "Backend changes")
        
        result = {
            "files_modified": [],
            "apis_added": [],
            "status": "success"
        }
        
        if "api" in request.lower() or "endpoint" in request.lower():
            result["apis_added"].append("API endpoint created")
        
        return result
    
    def _find_existing_apis(self, structure: dict) -> list:
        apis = []
        for f in structure.get("files", []):
            if "api" in f.lower() or "route" in f.lower() or f.endswith(".py"):
                apis.append(f)
        return apis[:5]
    
    def _determine_changes(self, request: str) -> list:
        changes = []
        request_lower = request.lower()
        
        if "database" in request_lower or "model" in request_lower:
            changes.append("Database models")
        if "auth" in request_lower or "login" in request_lower:
            changes.append("Authentication")
        if "api" in request_lower:
            changes.append("API endpoints")
        
        return changes

backend_agent = BackendAgent()
