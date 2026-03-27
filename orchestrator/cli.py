"""
Orchestrator CLI - Command line interface
Usage: python orchestrator/cli.py "your task description"
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from master import master_orchestrator
from task_queue import task_queue

def main():
    if len(sys.argv) < 2:
        print("Usage: python cli.py \"your task description\"")
        print("Example: python cli.py \"add user login page\"")
        sys.exit(1)
    
    task_description = " ".join(sys.argv[1:])
    
    print("\n" + "="*60)
    print("MASTER ORCHESTRATOR v1.0")
    print("="*60)
    print(f"\nTask: {task_description}")
    
    result = master_orchestrator.run_full_workflow(task_description)
    
    if result.get("status") == "plan_ready":
        print("\nPlan is ready for review!")
        
        response = input("\nProceed with execution? (yes/no): ").strip().lower()
        
        if response == "yes":
            print("\nExecuting plan...")
            exec_result = master_orchestrator.execute_plan(result["task_id"])
            
            print("\nRunning QA checks...")
            qa_result = master_orchestrator.qa_check()
            
            if qa_result.get("issues"):
                print(f"\nFound {len(qa_result['issues'])} issues")
                for issue in qa_result["issues"]:
                    print(f"   - {issue.get('type')}: {issue.get('recommendation')}")
            else:
                print("\nNo issues found!")
            
            print("\nFinal Demo:")
            final = master_orchestrator.create_final_demo()
            
            print("\n" + "="*60)
            print("WORKFLOW COMPLETE!")
            print("="*60)
        else:
            print("\nExecution cancelled by user")

if __name__ == "__main__":
    main()
