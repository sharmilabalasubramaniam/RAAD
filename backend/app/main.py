from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from datetime import datetime
from .database import Base, engine, SessionLocal, get_db
from .models import Employee, Task, AuditEvent
from .schemas import EmployeeCreate, TaskCreate
from .allocation import find_best_employee, calculate_assignment_score, generate_explanation, calculate_skill_match

# Create database tables
Base.metadata.create_all(bind=engine)

def _record_audit_event(
    db: Session,
    action: str,
    task_id: Optional[str] = None,
    task_title: Optional[str] = None,
    previous_employee_name: Optional[str] = None,
    new_employee_name: Optional[str] = None,
    reason: Optional[str] = None,
    trigger: Optional[str] = None
):
    try:
        event = AuditEvent(
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            action=action,
            task_id=str(task_id) if task_id else None,
            task_title=task_title,
            previous_employee_name=previous_employee_name,
            new_employee_name=new_employee_name,
            reason=reason or "Automated RAAD Optimization Engine",
            trigger=trigger or "Manager Interactive Reallocation",
            status="Completed"
        )
        db.add(event)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Audit] Failed to record audit event: {e}")

app = FastAPI(
    title="AI Workforce Decision & Resource Allocation Agent API",
    description="AI-powered workforce allocation, real-time precision telemetry, and reallocation system",
    version="1.0.0"
)

@app.on_event("startup")
def auto_seed_on_startup():
    db = SessionLocal()
    try:
        if db.query(Employee).count() == 0:
            print("[Startup] Empty DB detected. Seeding demo dataset...")
            import subprocess, sys, os
            seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seed.py")
            if os.path.exists(seed_path):
                subprocess.run([sys.executable, seed_path], check=False)
    except Exception as e:
        print(f"[Startup] Auto-seed check error: {e}")
    finally:
        db.close()

# CORS configuration for frontend (http://localhost:5173) and agent (http://localhost:8001)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "AI Workforce API is running 🚀",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/health")
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "workforce-backend",
        "database": "sqlite_connected"
    }

# ==================================================
# EMPLOYEES & WORKERS
# ==================================================

def _format_employee(emp: Employee) -> Dict[str, Any]:
    skills_list = [s.strip() for s in emp.skills.split(",")] if emp.skills else []
    max_hours = 40.0
    current_hours = round((emp.workload / 100.0) * max_hours, 1)
    
    return {
        "id": emp.id,
        "name": emp.name,
        "initials": "".join([part[0] for part in emp.name.split()[:2]]).upper() if emp.name else "EMP",
        "role": emp.role,
        "department": emp.department,
        "team": emp.department,
        "skills": skills_list,
        "workload": emp.workload,
        "capacity": max_hours,
        "utilization": emp.workload,
        "utilization_rate": emp.workload,
        "availability": emp.availability,
        "location": emp.location or "Stockholm, Sweden",
        "performance_score": emp.performance_score,
        "seniority_level": "Senior" if emp.performance_score >= 85 else "Mid",
        "max_weekly_hours": max_hours,
        "current_allocated_hours": current_hours,
        "status": "Overloaded" if emp.workload >= 85 else "Steady Load" if emp.workload >= 65 else "Balanced" if emp.workload >= 50 else "Optimal Available",
        "avatarColor": "bg-rose-500" if emp.workload >= 85 else "bg-blue-600" if emp.workload < 50 else "bg-amber-600"
    }

@app.post("/employees")
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    new_employee = Employee(
        name=employee.name,
        role=employee.role,
        department=employee.department,
        skills=",".join(employee.skills),
        workload=employee.workload,
        availability=employee.availability,
        location=employee.location,
        performance_score=employee.performance_score
    )
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    return _format_employee(new_employee)

@app.get("/employees")
@app.get("/workforce/workers")
@app.get("/api/v1/employees")
@app.get("/api/v1/workforce/workers")
def get_employees(
    department: Optional[str] = None,
    skill: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    query = db.query(Employee)
    if department:
        query = query.filter(Employee.department.ilike(f"%{department}%"))
    if not is_active:
        query = query.filter(Employee.availability == False)
    
    employees = query.all()
    formatted = [_format_employee(e) for e in employees]
    
    if skill:
        skill_lower = skill.lower()
        formatted = [e for e in formatted if any(skill_lower in s.lower() for s in e["skills"])]
        
    return formatted

@app.get("/employees/{employee_id}")
@app.get("/workforce/workers/{employee_id}")
@app.get("/api/v1/employees/{employee_id}")
@app.get("/api/v1/workforce/workers/{employee_id}")
def get_employee_by_id(employee_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return _format_employee(emp)

@app.put("/employees/{employee_id}/availability")
@app.put("/api/v1/employees/{employee_id}/availability")
def update_employee_availability(employee_id: int, availability: bool, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    emp.availability = availability
    db.commit()
    db.refresh(emp)
    return {
        "success": True,
        "employee_id": emp.id,
        "employee_name": emp.name,
        "availability": emp.availability
    }

# ==================================================
# TASKS & ALLOCATIONS
# ==================================================

def _format_task(task: Task, db: Session) -> Dict[str, Any]:
    skills_list = [s.strip() for s in task.required_skills.split(",")] if task.required_skills else []
    assigned_emp = None
    if task.assigned_employee_id:
        assigned_emp = db.query(Employee).filter(Employee.id == task.assigned_employee_id).first()
        
    assigned_info = _format_employee(assigned_emp) if assigned_emp else None
    
    sla_status = "On Track"
    if task.sla_hours <= 4:
        sla_status = "Critical Breach"
    elif task.sla_hours <= 12:
        sla_status = "Approaching"
        
    hours = int(task.sla_hours)
    mins = int((task.sla_hours - hours) * 60)
    remaining_sla_str = f"{hours}h {mins:02d}m"
    
    ai_match = 90
    if assigned_emp and skills_list:
        match_ratio = calculate_skill_match(assigned_emp.skills.split(","), skills_list)
        ai_match = int(round(match_ratio * 100))

    return {
        "id": str(task.id),
        "task_id": str(task.id),
        "taskCode": f"TASK-{task.id:03d}",
        "taskName": task.title,
        "title": task.title,
        "workstream": f"{task.location or 'Core'} • Priority {task.priority}",
        "priority": task.priority,
        "required_skills": skills_list,
        "skill_requirements": [{"skill": {"name": s}, "min_proficiency": 3} for s in skills_list],
        "assignedEmployeeId": str(task.assigned_employee_id) if task.assigned_employee_id else None,
        "assignedEmployeeName": assigned_info["name"] if assigned_info else "Unassigned",
        "assignedEmployeeInitials": assigned_info["initials"] if assigned_info else "UN",
        "assignedEmployeeRole": assigned_info["role"] if assigned_info else "Unassigned",
        "assignedEmployeeAvatarColor": assigned_info["avatarColor"] if assigned_info else "bg-slate-400",
        "team": assigned_info["department"] if assigned_info else "Operations",
        "effort": f"{int(task.estimated_hours)}h",
        "dueDate": "2026-10-25T18:00:00Z",
        "remainingSla": remaining_sla_str,
        "remaining_sla": remaining_sla_str,
        "remainingSlaHours": task.sla_hours,
        "sla_hours": task.sla_hours,
        "estimated_hours": task.estimated_hours,
        "required_hours_per_week": task.estimated_hours,
        "aiSkillMatch": ai_match,
        "status": task.status if task.status != "Unassigned" else sla_status if task.assigned_employee_id else "Unassigned",
        "description": f"Execute {task.title} requiring {', '.join(skills_list)} under {remaining_sla_str} SLA window.",
        "allocations": [{
            "worker_id": task.assigned_employee_id,
            "allocated_hours_per_week": task.estimated_hours
        }] if task.assigned_employee_id else []
    }

@app.post("/tasks")
@app.post("/api/v1/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(
        title=task.title,
        priority=task.priority,
        required_skills=",".join(task.required_skills),
        sla_hours=task.sla_hours,
        estimated_hours=task.estimated_hours,
        location=task.location,
        status="Unassigned"
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return _format_task(new_task, db)

@app.get("/tasks")
@app.get("/api/v1/tasks")
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return [_format_task(t, db) for t in tasks]

@app.get("/tasks/{task_id}")
@app.get("/api/v1/tasks/{task_id}")
def get_task_by_id(task_id: int, db: Session = Depends(get_db)):
    t = db.query(Task).filter(Task.id == task_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return _format_task(t, db)

# ==================================================
# ALLOCATION & RECOMMENDATION ENGINE
# ==================================================

@app.get("/tasks/{task_id}/recommendations")
@app.get("/allocation/tasks/{task_id}/recommendations")
@app.get("/api/v1/tasks/{task_id}/recommendations")
@app.get("/api/v1/allocation/tasks/{task_id}/recommendations")
def get_task_recommendations(task_id: int, limit: int = Query(default=3), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    employees = db.query(Employee).filter(Employee.availability == True).all()
    candidates = []
    
    for emp in employees:
        score = calculate_assignment_score(emp, task)
        match_ratio = calculate_skill_match(emp.skills.split(","), task.required_skills.split(","))
        explanation = generate_explanation(emp, task)
        
        candidates.append({
            "worker": _format_employee(emp),
            "match_score": score,
            "available_hours_per_week": max(0.0, 40.0 - (emp.workload / 100.0 * 40.0)),
            "fit_summary": explanation,
            "breakdown": {
                "skill_score": int(round(match_ratio * 100)),
                "availability_score": int(round(max(0, 100 - emp.workload))),
                "experience_score": int(emp.performance_score)
            },
            "potential_conflicts": ["Overloaded (>80%)"] if emp.workload >= 80 else []
        })
        
    candidates.sort(key=lambda c: c["match_score"], reverse=True)
    top = candidates[:limit]
    
    return {
        "task_id": task.id,
        "task_title": task.title,
        "top_candidates": top
    }

@app.post("/tasks/{task_id}/allocate")
@app.post("/allocation/allocate")
@app.post("/api/v1/tasks/{task_id}/allocate")
@app.post("/api/v1/allocation/allocate")
def allocate_task(task_id: int, worker_id: Optional[int] = None, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if worker_id:
        employee = db.query(Employee).filter(Employee.id == worker_id).first()
    else:
        employees = db.query(Employee).filter(Employee.availability == True).all()
        best = find_best_employee(employees, task)
        employee = best["employee"] if best else None

    if not employee:
        return {"success": False, "message": "No available employee found"}

    prev_emp = db.query(Employee).filter(Employee.id == task.assigned_employee_id).first() if task.assigned_employee_id else None

    task.assigned_employee_id = employee.id
    task.status = "Assigned"
    employee.workload = min(100.0, employee.workload + (task.estimated_hours / 40.0 * 100.0))

    db.commit()

    _record_audit_event(
        db=db,
        action="REALLOCATE",
        task_id=str(task.id),
        task_title=task.title,
        previous_employee_name=prev_emp.name if prev_emp else "Unassigned",
        new_employee_name=employee.name,
        reason=f"Skill match & SLA protection allocation to {employee.name}",
        trigger="Manager Interactive Request"
    )

    return {
        "success": True,
        "task_id": task.id,
        "task_title": task.title,
        "employee_id": employee.id,
        "employee_name": employee.name,
        "assignment_score": 94.0,
        "explanation": f"Successfully allocated {task.title} to {employee.name}."
    }

@app.post("/employees/{employee_id}/unavailable")
@app.post("/api/v1/employees/{employee_id}/unavailable")
def employee_unavailable(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.availability = False
    affected_tasks = db.query(Task).filter(Task.assigned_employee_id == employee_id).all()
    available_employees = db.query(Employee).filter(Employee.availability == True, Employee.id != employee_id).all()
    
    reallocated = []
    for task in affected_tasks:
        result = find_best_employee(available_employees, task)
        if result:
            new_emp = result["employee"]
            task.assigned_employee_id = new_emp.id
            task.status = "Reassigned"
            new_emp.workload = min(100.0, new_emp.workload + (task.estimated_hours / 40.0 * 100.0))
            
            reallocated.append({
                "task_id": task.id,
                "task_title": task.title,
                "new_employee_id": new_emp.id,
                "new_employee_name": new_emp.name,
                "assignment_score": result["score"],
                "explanation": result["explanation"],
                "status": "Reassigned"
            })
        else:
            task.assigned_employee_id = None
            task.status = "Unassigned"
            reallocated.append({
                "task_id": task.id,
                "task_title": task.title,
                "status": "Unassigned",
                "reason": "No suitable replacement candidate found"
            })

    db.commit()
    return {
        "success": True,
        "unavailable_employee": employee.name,
        "affected_tasks": len(affected_tasks),
        "reallocated_tasks": reallocated
    }

# ==================================================
# WORKFORCE METRICS & CONFLICTS
# ==================================================

@app.get("/workforce/overview")
@app.get("/workforce/metrics")
@app.get("/api/v1/workforce/overview")
@app.get("/api/v1/workforce/metrics")
def workforce_overview(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    tasks = db.query(Task).all()

    total_emp = len(employees)
    available_emp = sum(1 for e in employees if e.availability)
    assigned_tasks = sum(1 for t in tasks if t.assigned_employee_id is not None)
    overloaded_emp = sum(1 for e in employees if e.workload >= 80)
    avg_util = round(sum(e.workload for e in employees) / max(1, total_emp), 1)

    return {
        "total_employees": total_emp,
        "total_workers": total_emp,
        "active_workers": available_emp,
        "available_employees": available_emp,
        "unavailable_employees": total_emp - available_emp,
        "total_tasks": len(tasks),
        "assigned_tasks": assigned_tasks,
        "unassigned_tasks": len(tasks) - assigned_tasks,
        "overloaded_employees": overloaded_emp,
        "overallocated_workers": overloaded_emp,
        "underallocated_workers": sum(1 for e in employees if e.workload < 50),
        "avg_utilization_pct": avg_util,
        "total_skills_tracked": 8,
        "departments": [
            {"department": "Platform Engineering", "utilization_pct": 82.5, "total_allocated_hours": 330, "total_capacity_hours": 400},
            {"department": "Core Infrastructure", "utilization_pct": 68.0, "total_allocated_hours": 272, "total_capacity_hours": 400},
            {"department": "Observability Hub", "utilization_pct": 52.0, "total_allocated_hours": 208, "total_capacity_hours": 400},
            {"department": "SecOps Boundary", "utilization_pct": 76.0, "total_allocated_hours": 304, "total_capacity_hours": 400}
        ]
    }

@app.get("/workforce/overloaded")
@app.get("/api/v1/workforce/overloaded")
def get_overloaded_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).filter(Employee.workload >= 80).order_by(Employee.workload.desc()).all()
    result = [_format_employee(e) for e in employees]
    return {
        "count": len(result),
        "overloaded_employees": result
    }

@app.get("/workforce/skills")
@app.get("/api/v1/workforce/skills")
def get_skills():
    return [
        {"id": "sk-1", "name": "AI/ML", "category": "Intelligence", "proficiency": 88, "totalEngineers": 6, "skillGapPercentage": 12, "demandLevel": "Critical", "targetCoverage": 95},
        {"id": "sk-2", "name": "Python", "category": "Backend", "proficiency": 94, "totalEngineers": 22, "skillGapPercentage": 6, "demandLevel": "High", "targetCoverage": 90},
        {"id": "sk-3", "name": "React", "category": "Frontend", "proficiency": 90, "totalEngineers": 14, "skillGapPercentage": 10, "demandLevel": "Medium", "targetCoverage": 85},
        {"id": "sk-4", "name": "Cloud (GCP/AWS)", "category": "Infrastructure", "proficiency": 86, "totalEngineers": 18, "skillGapPercentage": 14, "demandLevel": "Critical", "targetCoverage": 95},
        {"id": "sk-5", "name": "Data Engineering", "category": "Pipelines", "proficiency": 82, "totalEngineers": 8, "skillGapPercentage": 18, "demandLevel": "High", "targetCoverage": 90},
        {"id": "sk-6", "name": "Cybersecurity", "category": "Security Ops", "proficiency": 78, "totalEngineers": 5, "skillGapPercentage": 22, "demandLevel": "Critical", "targetCoverage": 85},
        {"id": "sk-7", "name": "DevOps & K8s", "category": "Infrastructure", "proficiency": 92, "totalEngineers": 16, "skillGapPercentage": 8, "demandLevel": "High", "targetCoverage": 92},
        {"id": "sk-8", "name": "Go Runtime", "category": "Backend Systems", "proficiency": 95, "totalEngineers": 9, "skillGapPercentage": 5, "demandLevel": "Critical", "targetCoverage": 95}
    ]

@app.get("/allocation/projects")
@app.get("/api/v1/allocation/projects")
def get_projects(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return [{
        "id": "proj-nordic",
        "name": "Nordic Enterprise Platform",
        "code": "NORDIC-09",
        "status": "Active",
        "tasks": [_format_task(t, db) for t in tasks[:10]]
    }]

@app.get("/allocation/projects/{project_id}")
@app.get("/api/v1/allocation/projects/{project_id}")
def get_project_detail(project_id: str, db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return {
        "id": project_id,
        "name": "Nordic Enterprise Platform",
        "code": "NORDIC-09",
        "tasks": [_format_task(t, db) for t in tasks[:15]]
    }

@app.post("/allocation/auto-optimize")
@app.post("/api/v1/allocation/auto-optimize")
def auto_optimize(db: Session = Depends(get_db)):
    unassigned = db.query(Task).filter(Task.assigned_employee_id == None).all()
    available = db.query(Employee).filter(Employee.availability == True).all()
    
    optimized = []
    for task in unassigned:
        best = find_best_employee(available, task)
        if best:
            emp = best["employee"]
            task.assigned_employee_id = emp.id
            task.status = "Assigned"
            emp.workload = min(100.0, emp.workload + (task.estimated_hours / 40.0 * 100.0))
            optimized.append({
                "task_id": task.id,
                "task_title": task.title,
                "worker_id": emp.id,
                "worker_name": emp.name,
                "score": best["score"]
            })
    
    db.commit()
    return optimized

@app.get("/allocation/conflicts")
@app.get("/api/v1/allocation/conflicts")
def get_conflicts(db: Session = Depends(get_db)):
    overloaded = db.query(Employee).filter(Employee.workload >= 80).all()
    critical_sla = db.query(Task).filter(Task.sla_hours <= 4).all()
    
    conflicts = []
    for emp in overloaded:
        conflicts.append({
            "id": f"conf-emp-{emp.id}",
            "type": "Capacity Overload",
            "severity": "Critical" if emp.workload >= 90 else "Urgent",
            "worker_id": emp.id,
            "worker_name": emp.name,
            "details": f"{emp.name} is operating at {emp.workload}% capacity with overloaded queue."
        })
        
    for task in critical_sla:
        conflicts.append({
            "id": f"conf-task-{task.id}",
            "type": "SLA Risk",
            "severity": "Critical",
            "task_id": task.id,
            "task_title": task.title,
            "details": f"Task '{task.title}' has {task.sla_hours}h remaining before SLA breach."
        })
        
    return conflicts

@app.post("/copilot/execute-tool")
@app.post("/api/v1/copilot/execute-tool")
def execute_copilot_tool(payload: Dict[str, Any], db: Session = Depends(get_db)):
    tool_name = payload.get("tool_name")
    params = payload.get("parameters", {})
    
    if tool_name == "get_workforce_summary":
        return workforce_overview(db)
    elif tool_name == "list_workforce_conflicts":
        return {"conflicts": get_conflicts(db)}
    elif tool_name == "identify_overloaded_workers":
        return get_overloaded_employees(db)
    elif tool_name == "auto_optimize":
        return auto_optimize(db)
        
    return {"success": True, "executed_tool": tool_name, "parameters": params}

@app.get("/audit-events")
@app.get("/api/v1/audit-events")
def get_audit_events(db: Session = Depends(get_db)):
    events = db.query(AuditEvent).order_by(AuditEvent.id.desc()).limit(50).all()
    return [{
        "id": f"aud-{e.id}",
        "timestamp": e.timestamp,
        "action": e.action,
        "task_id": e.task_id,
        "task_title": e.task_title,
        "previous_employee_name": e.previous_employee_name,
        "new_employee_name": e.new_employee_name,
        "reason": e.reason,
        "trigger": e.trigger,
        "status": e.status
    } for e in events]