from typing import Dict, Any, List
from client.backend_client import backend_client

async def list_workforce_conflicts(unresolved_only: bool = True) -> Dict[str, Any]:
    """Retrieve all current allocation conflicts (overbooking, leave clashes) from the backend."""
    conflicts = await backend_client.get_conflicts(unresolved_only=unresolved_only)
    if isinstance(conflicts, dict) and conflicts.get("error"):
        return {"success": False, "error": conflicts.get("detail")}

    formatted = []
    for c in conflicts:
        formatted.append({
            "id": c.get("id"),
            "worker_name": c.get("worker_name"),
            "type": c.get("conflict_type"),
            "severity": c.get("severity"),
            "allocated_hours": c.get("total_allocated_hours"),
            "max_capacity": c.get("max_capacity_hours"),
            "details": c.get("details"),
            "is_resolved": c.get("is_resolved")
        })

    return {
        "success": True,
        "count": len(formatted),
        "conflicts": formatted
    }

async def identify_overloaded_workers() -> Dict[str, Any]:
    """Find all employees who are overbooked (>40h/wk) or near max capacity (>90% utilization)."""
    workers = await backend_client.get_workers()
    overloaded = []
    at_risk = []

    for w in workers:
        util = float(w.get("utilization_rate", 0.0))
        allocated = float(w.get("current_allocated_hours", 0.0))
        max_cap = float(w.get("max_weekly_hours", 40.0))

        if util > 100.0 or allocated > max_cap:
            overloaded.append({
                "worker_id": w.get("id"),
                "name": w.get("name"),
                "role": w.get("role"),
                "department": w.get("department"),
                "allocated_hours": allocated,
                "max_capacity": max_cap,
                "overage_hours": round(allocated - max_cap, 1),
                "utilization_rate": f"{util}%"
            })
        elif util >= 90.0:
            at_risk.append({
                "worker_id": w.get("id"),
                "name": w.get("name"),
                "role": w.get("role"),
                "department": w.get("department"),
                "allocated_hours": allocated,
                "max_capacity": max_cap,
                "utilization_rate": f"{util}%"
            })

    return {
        "success": True,
        "overloaded_count": len(overloaded),
        "at_risk_count": len(at_risk),
        "overloaded_workers": overloaded,
        "at_risk_workers": at_risk
    }

async def check_critical_task_capacity() -> Dict[str, Any]:
    """Assess whether the workforce has enough bandwidth and matching talent for Critical and High priority tasks."""
    all_tasks = await backend_client.get_all_tasks()
    critical_tasks = [t for t in all_tasks if t.get("priority") in ["Critical", "High"]]

    assessments = []
    unstaffed_critical = 0

    for t in critical_tasks:
        is_assigned = len(t.get("allocations", [])) > 0
        if not is_assigned:
            unstaffed_critical += 1

        recs = await backend_client.get_task_recommendations(t.get("id"), limit=3)
        top_candidates = recs.get("top_candidates", [])

        viable_candidates = [
            {
                "name": c.get("worker", {}).get("name"),
                "score": c.get("match_score"),
                "available_hours": c.get("available_hours_per_week")
            }
            for c in top_candidates if not c.get("potential_conflicts")
        ]

        assessments.append({
            "task_id": t.get("id"),
            "title": t.get("title"),
            "project_name": t.get("project_name"),
            "priority": t.get("priority"),
            "status": t.get("status"),
            "needed_hours": t.get("required_hours_per_week"),
            "is_assigned": is_assigned,
            "has_viable_unconflicted_staff": len(viable_candidates) > 0,
            "viable_candidates": viable_candidates
        })

    return {
        "success": True,
        "total_critical_high_tasks": len(critical_tasks),
        "unstaffed_critical_count": unstaffed_critical,
        "has_capacity_deficit": any(not a["has_viable_unconflicted_staff"] for a in assessments if not a["is_assigned"]),
        "task_assessments": assessments
    }

async def detect_missing_skills() -> Dict[str, Any]:
    """Analyze all task skill requirements against the workforce skill directory to detect missing competencies or coverage gaps."""
    all_tasks = await backend_client.get_all_tasks()
    workers = await backend_client.get_workers()

    # Build workforce skill registry: skill_id -> max proficiency available
    worker_skill_max = {}
    skill_names = {}
    for w in workers:
        for ws in w.get("skills", []):
            sk = ws.get("skill", {})
            sk_id = sk.get("id")
            sk_name = sk.get("name")
            prof = ws.get("proficiency", 1)
            if sk_id:
                skill_names[sk_id] = sk_name
                worker_skill_max[sk_id] = max(worker_skill_max.get(sk_id, 0), prof)

    missing_skills = []
    proficiency_gaps = []

    for t in all_tasks:
        for req in t.get("skill_requirements", []):
            sk_id = req.get("skill_id")
            sk_name = req.get("skill", {}).get("name", "Unknown Skill")
            min_prof = req.get("min_proficiency", 3)

            if sk_id not in worker_skill_max:
                missing_skills.append({
                    "skill_name": sk_name,
                    "task_title": t.get("title"),
                    "project_name": t.get("project_name"),
                    "priority": t.get("priority"),
                    "required_level": min_prof,
                    "reason": "Zero active workers have this skill registered."
                })
            elif worker_skill_max[sk_id] < min_prof:
                proficiency_gaps.append({
                    "skill_name": sk_name,
                    "task_title": t.get("title"),
                    "project_name": t.get("project_name"),
                    "required_level": min_prof,
                    "max_available_level": worker_skill_max[sk_id],
                    "reason": f"Required proficiency is Lv {min_prof}, but highest employee proficiency is Lv {worker_skill_max[sk_id]}."
                })

    return {
        "success": True,
        "missing_skills_count": len(missing_skills),
        "proficiency_gaps_count": len(proficiency_gaps),
        "completely_missing_skills": missing_skills,
        "proficiency_gaps": proficiency_gaps
    }

CONFLICT_TOOL_DEFINITIONS = [
    {
        "name": "list_workforce_conflicts",
        "description": "Retrieve all active allocation conflicts, such as overbooked engineers (>40h/wk) and leave clashes.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "unresolved_only": {
                    "type": "BOOLEAN",
                    "description": "Filter to only unresolved conflicts (default true)."
                }
            },
            "required": []
        }
    },
    {
        "name": "identify_overloaded_workers",
        "description": "Identify all employees whose weekly allocated hours exceed their maximum capacity (>100% utilization).",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "check_critical_task_capacity",
        "description": "Assess if company capacity and skills are sufficient to cover all Critical and High priority tasks.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "detect_missing_skills",
        "description": "Scan task requirements and compare against workforce talent to detect unfulfilled skills or proficiency deficits.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    }
]
