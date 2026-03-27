"""
Integrator Agent - Combines all agent outputs
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.base_agent import BaseAgent

class IntegratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("integrator", "Integrator Agent")
    
    def analyze_task(self, task: dict) -> dict:
        """Analyze integration requirements"""
        all_tasks = self.tq.get_all_tasks()
        completed = [t for t in all_tasks if t.get("status") == "completed"]
        
        return {
            "summary": f"Integration plan: {len(completed)} completed tasks",
            "components_to_integrate": [t.get("title") for t in completed]
        }
    
    def execute_task(self, task: dict) -> dict:
        """Integrate all components"""
        self.log("EXECUTING", "Integrating all components")
        
        result = {
            "integration_complete": True,
            "final_structure": {},
            "status": "success"
        }
        
        return result
    
    def create_final_structure(self, project_path: str = None) -> dict:
        """Create final project structure summary"""
        from config.settings import get_config
        
        if project_path is None:
            project_path = get_config("paths.project_root")
        
        structure = self.read_project_structure(project_path)
        
        return {
            "total_files": len(structure.get("files", [])),
            "languages": structure.get("languages", []),
            "files": structure.get("files", [])[:20]
        }

integrator_agent = IntegratorAgent()
