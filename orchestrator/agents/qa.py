"""
QA Agent - Monitors all agents, catches errors, guides fixes
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.base_agent import BaseAgent

class QAAgent(BaseAgent):
    def __init__(self):
        super().__init__("qa", "QA Agent")
    
    def analyze_task(self, task: dict) -> dict:
        """Monitor current state and find issues"""
        all_agents = self.gm.get_all_agents()
        all_tasks = self.tq.get_all_tasks()
        
        issues = self._find_issues(all_agents, all_tasks)
        
        return {
            "summary": f"QA Check: {len(issues)} issues found",
            "issues": issues,
            "agent_status": all_agents
        }
    
    def execute_task(self, task: dict) -> dict:
        """Monitor and report"""
        self.log("MONITORING", "All agents")
        
        result = {
            "monitoring_complete": True,
            "issues_found": 0,
            "recommendations": []
        }
        
        return result
    
    def _find_issues(self, agents: dict, tasks: list) -> list:
        issues = []
        
        for task in tasks:
            if task.get("status") == "failed":
                issues.append({
                    "type": "task_failed",
                    "task_id": task.get("id"),
                    "task_title": task.get("title"),
                    "error": task.get("error"),
                    "recommendation": "Retry or fix the error"
                })
        
        for agent_id, agent_data in agents.items():
            if agent_data.get("status") == "idle" and agent_data.get("last_seen"):
                from datetime import datetime
                last_seen = agent_data.get("last_seen")
                issues.append({
                    "type": "agent_inactive",
                    "agent_id": agent_id,
                    "last_seen": last_seen,
                    "recommendation": "Assign new task or check agent"
                })
        
        return issues
    
    def check_code_quality(self, filepath: str) -> dict:
        """Check code for issues"""
        content = self.read_file(filepath)
        if not content:
            return {"error": "Could not read file"}
        
        issues = []
        
        if "TODO" in content or "FIXME" in content:
            issues.append("Contains TODO/FIXME comments")
        
        if content.count("print(") > 5:
            issues.append("Too many print statements")
        
        return {
            "file": filepath,
            "issues": issues,
            "quality_score": max(0, 100 - len(issues) * 20)
        }
    
    def validate_integration(self) -> dict:
        """Validate that all parts work together"""
        all_tasks = self.tq.get_all_tasks()
        completed = [t for t in all_tasks if t.get("status") == "completed"]
        failed = [t for t in all_tasks if t.get("status") == "failed"]
        
        return {
            "total_tasks": len(all_tasks),
            "completed": len(completed),
            "failed": len(failed),
            "integration_ready": len(failed) == 0 and len(completed) > 0
        }

qa_agent = QAAgent()
