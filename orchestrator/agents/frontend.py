"""
Frontend Agent - Handles UI/UX code
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.base_agent import BaseAgent

class FrontendAgent(BaseAgent):
    def __init__(self):
        super().__init__("frontend", "Frontend Agent")
    
    def analyze_task(self, task: dict) -> dict:
        """Analyze frontend requirements"""
        request = task.get("description", "")
        project_structure = self.read_project_structure()
        
        existing_components = self._find_existing_components(project_structure)
        
        return {
            "summary": f"Frontend analysis complete",
            "existing_components": existing_components,
            "changes_needed": self._determine_changes(request)
        }
    
    def execute_task(self, task: dict) -> dict:
        """Execute frontend changes"""
        request = task.get("description", "")
        
        self.log("EXECUTING", "Frontend changes")
        
        result = {
            "files_modified": [],
            "components_updated": [],
            "status": "success"
        }
        
        return result
    
    def _find_existing_components(self, structure: dict) -> list:
        components = []
        for f in structure.get("files", []):
            if any(ext in f.lower() for ext in [".html", ".css", ".js", ".jsx", ".tsx"]):
                components.append(f)
        return components[:5]
    
    def _determine_changes(self, request: str) -> list:
        changes = []
        request_lower = request.lower()
        
        if "button" in request_lower or "form" in request_lower:
            changes.append("Form elements")
        if "page" in request_lower or "layout" in request_lower:
            changes.append("Page layout")
        if "style" in request_lower or "design" in request_lower:
            changes.append("Styling")
        
        return changes

frontend_agent = FrontendAgent()
