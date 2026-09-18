from typing import Dict, Any, List, Optional
from client.backend_client import backend_client

async def list_unassigned_tasks() -> Dict[str, Any]:
    """List all project tasks currently in 'Unassigned' status needing staffing."""
    all_tasks = await backend_client.get_all_tasks()
    unassigned = [t for t in all_tasks if t.get("status") == "Unassigned"]

    results = []
    for t in unassigned:
        reqs = [
            f"{r.get('skill', {}).get('name', 'Skill')} (Lv {r.get('min_proficiency', 3)}+)"
            for r in t.get("skill_requirements", [])
        ]
        results.append({
            "task_id": t.get("id"),
            "title": t.get("title"),
            "project_name": t.get("project_name", "Unknown"),
            "priority": t.get("priority"),
            "required_hours_per_week": t.get("required_hours_per_week"),
            "estimated_total_hours": t.get("estimated_total_hours"),
            "required_skills": reqs,
            "timeline": f"{t.get('start_date')} to {t.get('end_date')}"
        })

    return {
        "success": True,
        "count": len(results),
        "unassigned_tasks": results
    }

async def recommend_candidates_for_task(task_id: str, limit: int = 3) -> Dict[str, Any]:
    """Get multi-factor scored candidate recommendations for a specific task."""
    res = await backend_client.get_task_recommendations(task_id, limit=limit)
    if res.get("error"):
        return {"success": False, "error": res.get("detail")}
    return {"success": True, "recommendations": res}

async def explain_worker_selection(task_id: str, worker_name: str) -> Dict[str, Any]:
    """Explain why a worker was recommended or scored for a specific task using multi-factor breakdown."""
    recs = await backend_client.get_task_recommendations(task_id, limit=10)
    if recs.get("error"):
        return {"success": False, "error": recs.get("detail")}

    candidates = recs.get("top_candidates", [])
    target = None
    for c in candidates:
        if worker_name.lower() in c.get("worker", {}).get("name", "").lower():
            target = c
            break

    if not target:
        return {
            "success": False,
            "message": f"Worker '{worker_name}' was not ranked in the top candidate pool for task {task_id}."
        }

    return {
        "success": True,
        "worker_name": target.get("worker", {}).get("name"),
        "task_id": task_id,
        "match_score": target.get("match_score"),
        "breakdown": target.get("breakdown"),
        "available_hours": target.get("available_hours_per_week"),
        "fit_summary": target.get("fit_summary"),
        "potential_conflicts": target.get("potential_conflicts", [])
    }

async def get_worker_assigned_tasks(worker_name: str) -> Dict[str, Any]:
    """Find all active project tasks allocated to a specific worker (e.g. to evaluate absence impact)."""
    worker = await backend_client.find_worker_by_name(worker_name)
    if not worker:
        return {
            "success": False,
            "worker_found": False,
            "message": f"Worker '{worker_name}' not found in workforce database."
        }

    all_tasks = await backend_client.get_all_tasks()
    affected = []
    for t in all_tasks:
        for alloc in t.get("allocations", []):
            if alloc.get("worker_id") == worker.get("id"):
                affected.append({
                    "task_id": t.get("id"),
                    "title": t.get("title"),
                    "project_name": t.get("project_name"),
                    "priority": t.get("priority"),
                    "allocated_hours_per_week": alloc.get("allocated_hours_per_week"),
                    "timeline": f"{t.get('start_date')} to {t.get('end_date')}"
                })

    return {
        "success": True,
        "worker_found": True,
        "worker_name": worker.get("name"),
        "worker_id": worker.get("id"),
        "affected_tasks_count": len(affected),
        "affected_tasks": affected
    }

async def reassign_worker_tasks(worker_name: str, execute: bool = False) -> Dict[str, Any]:
    """
    Find alternative candidate recommendations for all tasks currently assigned to a worker,
    and optionally execute the reassignments via the backend allocation API.
    """
    tasks_res = await get_worker_assigned_tasks(worker_name)
    if not tasks_res.get("success") or not tasks_res.get("worker_found"):
        return tasks_res

    worker_id = tasks_res.get("worker_id")
    affected_tasks = tasks_res.get("affected_tasks", [])
    if not affected_tasks:
        return {
            "success": True,
            "worker_name": tasks_res.get("worker_name"),
            "message": f"No active tasks are assigned to {tasks_res.get('worker_name')}. No reassignment needed.",
            "reassignments": []
        }

    plan = []
    for task in affected_tasks:
        task_id = task.get("task_id")
        recs = await backend_client.get_task_recommendations(task_id, limit=5)
        top_candidates = recs.get("top_candidates", [])

        # Pick best alternative who is NOT the unavailable worker
        alt = None
        for c in top_candidates:
            if c.get("worker", {}).get("id") != worker_id and not c.get("potential_conflicts"):
                alt = c
                break
        if not alt:
            # Fallback to highest scoring alternative even with warnings
            for c in top_candidates:
                if c.get("worker", {}).get("id") != worker_id:
                    alt = c
                    break

        item = {
            "task_id": task_id,
            "task_title": task.get("title"),
            "project_name": task.get("project_name"),
            "required_hours": task.get("allocated_hours_per_week"),
            "previous_assignee": tasks_res.get("worker_name")
        }

        if alt:
            new_worker = alt.get("worker", {})
            item["recommended_worker"] = {
                "id": new_worker.get("id"),
                "name": new_worker.get("name"),
                "match_score": alt.get("match_score"),
                "fit_summary": alt.get("fit_summary"),
                "available_hours": alt.get("available_hours_per_week")
            }
            if execute:
                alloc_res = await backend_client.allocate_worker(
                    task_id=task_id,
                    worker_id=new_worker.get("id"),
                    allocated_hours_per_week=task.get("allocated_hours_per_week"),
                    notes=f"Reassigned from {tasks_res.get('worker_name')} by AI Agent"
                )
                item["execution_result"] = alloc_res
        else:
            item["recommended_worker"] = None
            item["warning"] = "No suitable replacement candidate found in workforce."

        plan.append(item)

    return {
        "success": True,
        "worker_name": tasks_res.get("worker_name"),
        "executed": execute,
        "reassignments_count": len(plan),
        "reassignments": plan
    }

async def allocate_worker_to_task(task_id: str, worker_id: str, hours_per_week: Optional[float] = None) -> Dict[str, Any]:
    """Assign a worker to a task via the backend Allocation Engine."""
    res = await backend_client.allocate_worker(task_id, worker_id, hours_per_week)
    if res.get("error"):
        return {"success": False, "error": res.get("detail")}
    return res

ALLOCATION_TOOL_DEFINITIONS = [
    {
        "name": "list_unassigned_tasks",
        "description": "List all unassigned project backlog tasks with priority, required weekly hours, and skills.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "recommend_candidates_for_task",
        "description": "Run the multi-factor candidate matcher to recommend top workers for a specific task.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "task_id": {
                    "type": "STRING",
                    "description": "The unique ID of the task."
                },
                "limit": {
                    "type": "INTEGER",
                    "description": "Number of candidates to recommend (default 3)."
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "explain_worker_selection",
        "description": "Explain the multi-factor score breakdown (skills, availability, seniority) for a specific worker on a task.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "task_id": {
                    "type": "STRING",
                    "description": "The unique ID of the project task."
                },
                "worker_name": {
                    "type": "STRING",
                    "description": "The name of the worker."
                }
            },
            "required": ["task_id", "worker_name"]
        }
    },
    {
        "name": "get_worker_assigned_tasks",
        "description": "Retrieve all tasks currently allocated to a specific worker to analyze the impact of their absence.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "worker_name": {
                    "type": "STRING",
                    "description": "The name of the employee."
                }
            },
            "required": ["worker_name"]
        }
    },
    {
        "name": "reassign_worker_tasks",
        "description": "Find replacements and reassign all tasks from an unavailable worker to the best conflict-free candidates.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "worker_name": {
                    "type": "STRING",
                    "description": "The name of the unavailable employee."
                },
                "execute": {
                    "type": "BOOLEAN",
                    "description": "Whether to immediately commit the reassignment in the backend (defaults to false for proposal mode)."
                }
            },
            "required": ["worker_name"]
        }
    },
    {
        "name": "allocate_worker_to_task",
        "description": "Assign a worker to a task in the backend with automatic constraint validation.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "task_id": {
                    "type": "STRING",
                    "description": "The unique ID of the task."
                },
                "worker_id": {
                    "type": "STRING",
                    "description": "The unique ID of the worker."
                },
                "hours_per_week": {
                    "type": "NUMBER",
                    "description": "Hours per week to allocate."
                }
            },
            "required": ["task_id", "worker_id"]
        }
    }
]
