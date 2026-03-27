"""
Planner Agent - Task analysis and breakdown
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("planner", "Planner Agent")
    
    def analyze_task(self, task: dict) -> dict:
        """Break down task into subtasks and assign to agents"""
        user_request = task.get("description", "")
        project_path = task.get("project_path")
        
        subtasks = []
        
        if self._needs_backend(user_request):
            subtasks.append({
                "title": "Backend Development",
                "description": f"Backend changes for: {user_request}",
                "assigned_agent": "backend",
                "priority": 2
            })
        
        if self._needs_frontend(user_request):
            subtasks.append({
                "title": "Frontend Development",
                "description": f"Frontend changes for: {user_request}",
                "assigned_agent": "frontend",
                "priority": 2
            })
        
        if self._needs_testing(user_request):
            subtasks.append({
                "title": "Testing",
                "description": f"Test for: {user_request}",
                "assigned_agent": "tester",
                "priority": 1
            })
        
        if self._needs_integration(user_request):
            subtasks.append({
                "title": "Integration",
                "description": f"Integrate all changes",
                "assigned_agent": "integrator",
                "priority": 1,
                "dependencies": [s.get("id") for s in subtasks if s.get("assigned_agent") != "integrator"]
            })
        
        return {
            "summary": f"Created {len(subtasks)} subtasks",
            "subtasks": subtasks,
            "estimated_time": self._estimate_time(user_request)
        }
    
    def execute_task(self, task: dict) -> dict:
        """Execute the planning"""
        plan = self.analyze_task(task)
        
        created_tasks = []
        for subtask in plan.get("subtasks", []):
            task_id = self.tq.create_task(
                title=subtask["title"],
                description=subtask["description"],
                assigned_agent=subtask["assigned_agent"],
                priority=subtask.get("priority", 2),
                dependencies=subtask.get("dependencies", [])
            )
            created_tasks.append(task_id)
        
        return {
            "plan_created": True,
            "subtasks_count": len(created_tasks),
            "task_ids": created_tasks,
            "estimated_time": plan.get("estimated_time")
        }
    
    def _needs_backend(self, request: str) -> bool:
        keywords = ["api", "backend", "database", "server", "model", "auth", "login", 
                   "register", "query", "database", "sql", "fastapi", "flask", "django"]
        request_lower = request.lower()
        return any(kw in request_lower for kw in keywords)
    
    def _needs_frontend(self, request: str) -> bool:
        keywords = ["ui", "frontend", "design", "page", "component", "button", "form",
                   "html", "css", "javascript", "react", "interface", "visual"]
        request_lower = request.lower()
        return any(kw in request_lower for kw in keywords)
    
    def _needs_testing(self, request: str) -> bool:
        keywords = ["test", "verify", "check", "debug", "error", "bug"]
        request_lower = request.lower()
        return any(kw in request_lower for kw in keywords)
    
    def _needs_integration(self, request: str) -> bool:
        return True
    
    def _estimate_time(self, request: str) -> str:
        words = len(request.split())
        if words < 10:
            return "15-30 minutes"
        elif words < 30:
            return "30-60 minutes"
        else:
            return "1-2 hours"

planner_agent = PlannerAgent()
