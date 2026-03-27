"""
Master Orchestrator - Main coordinator for all agents
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from global_memory import global_memory
from task_queue import task_queue, TaskPriority
from agents.planner import planner_agent
from agents.backend import backend_agent
from agents.frontend import frontend_agent
from agents.tester import tester_agent
from agents.integrator import integrator_agent
from agents.qa import qa_agent

class MasterOrchestrator:
    def __init__(self):
        self.gm = global_memory
        self.tq = task_queue
        self.agents = {
            "planner": planner_agent,
            "backend": backend_agent,
            "frontend": frontend_agent,
            "tester": tester_agent,
            "integrator": integrator_agent,
            "qa": qa_agent
        }
        self.gm.log("MASTER", "SYSTEM_STARTED", "Master Orchestrator initialized")
    
    def create_user_task(self, description: str, project_path: str = None) -> str:
        """Create a new user task"""
        task_id = self.tq.create_task(
            title=f"User Request: {description[:50]}...",
            description=description,
            priority=TaskPriority.HIGH,
            tags=["user_request"]
        )
        self.gm.set_shared_data("current_user_task", task_id)
        return task_id
    
    def analyze_with_all_agents(self, task_id: str):
        """All agents analyze the task"""
        task = self.tq.get_task(task_id)
        
        plans = {}
        for agent_id, agent in self.agents.items():
            if agent_id == "planner":
                continue
            try:
                plan = agent.analyze_task(task)
                plans[agent_id] = plan
                agent.log("ANALYZED", f"Plan for task {task_id}")
            except Exception as e:
                plans[agent_id] = {"error": str(e)}
        
        return plans
    
    def get_combined_plan(self, task_id: str, agent_plans: dict) -> dict:
        """Combine all agent plans into one"""
        planner_plan = planner_agent.analyze_task(self.tq.get_task(task_id))
        
        combined = {
            "task_id": task_id,
            "planner": planner_plan,
            "agent_plans": agent_plans,
            "subtasks": planner_plan.get("subtasks", []),
            "estimated_time": planner_plan.get("estimated_time", "Unknown")
        }
        
        return combined
    
    def present_plan_to_user(self, combined_plan: dict) -> str:
        """Present the plan to user and wait for approval"""
        print("\n" + "="*60)
        print("COMBINED EXECUTION PLAN")
        print("="*60)
        
        print(f"\nTask: {combined_plan.get('task_id')}")
        print(f"Estimated Time: {combined_plan.get('estimated_time')}")
        
        print("\nSUBTASKS:")
        for i, subtask in enumerate(combined_plan.get("subtasks", []), 1):
            agent = subtask.get("assigned_agent", "unknown")
            deps = subtask.get("dependencies", [])
            dep_info = f" (depends on {len(deps)} tasks)" if deps else ""
            print(f"  {i}. [{agent.upper()}] {subtask.get('title')}{dep_info}")
        
        print("\nAGENT ANALYSIS:")
        for agent_id, plan in combined_plan.get("agent_plans", {}).items():
            summary = plan.get("summary", "No summary")
            print(f"  - {agent_id}: {summary}")
        
        print("\n" + "="*60)
        print("Enter 'yes' to approve and start execution")
        print("Enter 'no' to cancel")
        print("="*60)
        
        return "pending"
    
    def execute_plan(self, task_id: str) -> dict:
        """Execute the plan with all agents"""
        self.gm.log("MASTER", "EXECUTION_STARTED", f"Task: {task_id}")
        
        results = {}
        ready_tasks = self.tq.get_ready_tasks()
        
        for task in ready_tasks:
            task_obj = self.tq.get_task(task.get("id"))
            if task_obj and task_obj.get("assigned_agent") in self.agents:
                agent = self.agents[task_obj["assigned_agent"]]
                self.display_agent_progress(agent.agent_id, "started")
                result = agent.work_on_task(task.get("id"))
                results[task.get("id")] = result
                self.display_agent_progress(agent.agent_id, "completed")
        
        return results
    
    def display_agent_progress(self, agent_id: str, status: str):
        """Display agent progress"""
        icons = {
            "started": "[START]",
            "completed": "[DONE]",
            "failed": "[FAIL]",
            "working": "[WORK]"
        }
        print(f"{icons.get(status, '[LOG]')} {agent_id.upper()}: {status.upper()}")
    
    def qa_check(self) -> dict:
        """Run QA check on all agents"""
        qa_result = qa_agent.execute_task({"description": "QA Check"})
        issues = qa_agent._find_issues(
            self.gm.get_all_agents(),
            self.tq.get_all_tasks()
        )
        return {
            "qa_result": qa_result,
            "issues": issues
        }
    
    def create_final_demo(self) -> dict:
        """Create final structure and demo"""
        structure = integrator_agent.create_final_structure()
        
        print("\n" + "="*60)
        print("FINAL PROJECT STRUCTURE")
        print("="*60)
        print(f"\nTotal Files: {structure.get('total_files')}")
        print(f"Languages: {', '.join(structure.get('languages', []))}")
        print("\nSample Files:")
        for f in structure.get("files", [])[:10]:
            print(f"  - {f}")
        
        print("\n" + "="*60)
        print("INTEGRATION COMPLETE!")
        print("="*60)
        
        return structure
    
    def run_full_workflow(self, user_request: str, project_path: str = None) -> dict:
        """Run the complete orchestrator workflow"""
        print("\nMASTER ORCHESTRATOR STARTED")
        print("="*60)
        
        print("\nStep 1: Creating task...")
        task_id = self.create_user_task(user_request, project_path)
        print(f"   Task ID: {task_id}")
        
        print("\nStep 2: All agents analyzing project structure...")
        agent_plans = self.analyze_with_all_agents(task_id)
        print(f"   {len(agent_plans)} agents analyzed")
        
        print("\nStep 3: Creating combined plan...")
        combined_plan = self.get_combined_plan(task_id, agent_plans)
        
        print("\nStep 4: Presenting plan to user...")
        self.present_plan_to_user(combined_plan)
        
        return {
            "task_id": task_id,
            "combined_plan": combined_plan,
            "status": "plan_ready"
        }
    
    def get_system_status(self) -> dict:
        """Get current system status"""
        return {
            "agents": self.gm.get_all_agents(),
            "tasks": self.tq.get_summary(),
            "memory": {
                "project_context": self.gm.get_project_context(),
                "last_updated": self.gm.read("last_updated")
            }
        }

master_orchestrator = MasterOrchestrator()
