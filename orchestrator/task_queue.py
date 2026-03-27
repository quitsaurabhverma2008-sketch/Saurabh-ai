"""
Task Queue System - Priority-based task management
"""
from datetime import datetime
from global_memory import global_memory
from enum import IntEnum

class TaskPriority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class TaskQueue:
    def __init__(self):
        self.gm = global_memory
    
    def create_task(self, title: str, description: str = "", 
                   assigned_agent: str = None, priority: int = TaskPriority.MEDIUM,
                   dependencies: list = None, tags: list = None):
        task = {
            "title": title,
            "description": description,
            "assigned_agent": assigned_agent,
            "priority": priority,
            "status": TaskStatus.PENDING,
            "dependencies": dependencies or [],
            "tags": tags or [],
            "result": None,
            "error": None,
            "retries": 0
        }
        task_id = self.gm.add_task(task)
        return task_id
    
    def get_task(self, task_id: str):
        return self.gm.get_task(task_id)
    
    def get_all_tasks(self):
        return self.gm.get_all_tasks()
    
    def get_tasks_by_agent(self, agent_id: str):
        tasks = self.gm.get_all_tasks()
        return [t for t in tasks if t.get("assigned_agent") == agent_id]
    
    def get_tasks_by_status(self, status: str):
        tasks = self.gm.get_all_tasks()
        return [t for t in tasks if t.get("status") == status]
    
    def get_tasks_by_priority(self, min_priority: int):
        tasks = self.gm.get_all_tasks()
        return [t for t in tasks if t.get("priority", 0) >= min_priority]
    
    def get_ready_tasks(self):
        """Get tasks whose dependencies are all completed"""
        tasks = self.gm.get_all_tasks()
        ready = []
        for task in tasks:
            if task.get("status") != TaskStatus.PENDING:
                continue
            deps = task.get("dependencies", [])
            if not deps:
                ready.append(task)
            else:
                all_deps_done = all(
                    self.get_task(dep_id) and 
                    self.get_task(dep_id).get("status") == TaskStatus.COMPLETED
                    for dep_id in deps
                )
                if all_deps_done:
                    ready.append(task)
        return sorted(ready, key=lambda x: x.get("priority", 0), reverse=True)
    
    def assign_task(self, task_id: str, agent_id: str):
        self.gm.update_task(task_id, {
            "assigned_agent": agent_id,
            "status": TaskStatus.IN_PROGRESS
        })
    
    def complete_task(self, task_id: str, result: dict = None):
        self.gm.update_task(task_id, {
            "status": TaskStatus.COMPLETED,
            "completed_at": datetime.now().isoformat(),
            "result": result
        })
    
    def fail_task(self, task_id: str, error: str):
        self.gm.update_task(task_id, {
            "status": TaskStatus.FAILED,
            "error": error,
            "failed_at": datetime.now().isoformat()
        })
    
    def retry_task(self, task_id: str):
        task = self.get_task(task_id)
        if task:
            retries = task.get("retries", 0) + 1
            self.gm.update_task(task_id, {
                "status": TaskStatus.PENDING,
                "retries": retries,
                "error": None
            })
            return True
        return False
    
    def block_task(self, task_id: str, reason: str = ""):
        self.gm.update_task(task_id, {
            "status": TaskStatus.BLOCKED,
            "block_reason": reason
        })
    
    def update_progress(self, task_id: str, progress: int, message: str = ""):
        self.gm.update_task(task_id, {
            "progress": progress,
            "progress_message": message
        })
    
    def delete_task(self, task_id: str):
        tasks = self.gm.get_all_tasks()
        new_tasks = [t for t in tasks if t.get("id") != task_id]
        self.gm.write("task_queue", new_tasks)
    
    def get_summary(self):
        tasks = self.gm.get_all_tasks()
        summary = {
            "total": len(tasks),
            "pending": len([t for t in tasks if t.get("status") == TaskStatus.PENDING]),
            "in_progress": len([t for t in tasks if t.get("status") == TaskStatus.IN_PROGRESS]),
            "completed": len([t for t in tasks if t.get("status") == TaskStatus.COMPLETED]),
            "failed": len([t for t in tasks if t.get("status") == TaskStatus.FAILED]),
            "blocked": len([t for t in tasks if t.get("status") == TaskStatus.BLOCKED])
        }
        return summary

# Singleton instance
task_queue = TaskQueue()
