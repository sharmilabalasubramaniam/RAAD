from typing import Dict, Any, Optional
from client.backend_client import backend_client

async def get_workforce_summary() -> Dict[str, Any]:
    """Retrieve overall workforce metrics, department utilization, and headcount."""
    metrics = await backend_client.get_workforce_metrics()
    if metrics.get("error"):
        return {"success": False, "error": metrics.get("detail")}
    return {"success": True, "metrics": metrics}

async def search_workers_by_skill(skill_name: str) -> Dict[str, Any]:
    """Search for workers possessing a specific technical or domain skill."""
    workers = await backend_client.get_workers(skill=skill_name)
    results = []
    for w in workers:
        results.append({
            "id": w.get("id"),
            "name": w.get("name"),
            "role": w.get("role"),
            "department": w.get("department"),
            "seniority_level": w.get("seniority_level"),
            "current_allocated_hours": w.get("current_allocated_hours", 0.0),
            "max_weekly_hours": w.get("max_weekly_hours", 40.0),
            "utilization_rate": f"{w.get('utilization_rate', 0.0)}%",
            "available_hours": max(0.0, w.get("max_weekly_hours", 40.0) - w.get("current_allocated_hours", 0.0))
        })
    return {
        "success": True,
        "skill": skill_name,
        "count": len(results),
        "workers": results
    }

async def get_worker_profile(name: str) -> Dict[str, Any]:
    """Look up an employee by name to inspect their current utilization, skills, and capacity."""
    worker = await backend_client.find_worker_by_name(name)
    if not worker:
        return {"success": False, "message": f"Worker '{name}' not found in active workforce directory."}

    return {
        "success": True,
        "worker": {
            "id": worker.get("id"),
            "name": worker.get("name"),
            "role": worker.get("role"),
            "department": worker.get("department"),
            "seniority_level": worker.get("seniority_level"),
            "hourly_rate": worker.get("hourly_rate"),
            "max_weekly_hours": worker.get("max_weekly_hours"),
            "current_allocated_hours": worker.get("current_allocated_hours"),
            "utilization_rate": f"{worker.get('utilization_rate')}%",
            "skills": [
                {
                    "name": s.get("skill", {}).get("name") if isinstance(s.get("skill"), dict) else "Unknown",
                    "proficiency": s.get("proficiency"),
                    "years_experience": s.get("years_experience")
                }
                for s in worker.get("skills", [])
            ]
        }
    }

WORKFORCE_TOOL_DEFINITIONS = [
    {
        "name": "get_workforce_summary",
        "description": "Fetch high-level workforce metrics: headcount, average utilization %, over/under-allocated counts, and department breakdown.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "search_workers_by_skill",
        "description": "Find active workers proficient in a specific technology or domain skill (e.g., Python, React, FastAPI, Docker).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "skill_name": {
                    "type": "STRING",
                    "description": "Name of the technical or domain skill."
                }
            },
            "required": ["skill_name"]
        }
    },
    {
        "name": "get_worker_profile",
        "description": "Look up an employee's verified profile, skills, current allocation hours, and utilization rate by their name.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "name": {
                    "type": "STRING",
                    "description": "The name or first name of the employee."
                }
            },
            "required": ["name"]
        }
    }
]
