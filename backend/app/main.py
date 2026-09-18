from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Employee, Task
from .schemas import EmployeeCreate, TaskCreate
from .allocation import find_best_employee


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AI Workforce Decision & Resource Allocation Agent",
    description="AI-powered workforce allocation and reallocation system",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "AI Workforce API is running 🚀"
    }


# ==================================================
# EMPLOYEES
# ==================================================

@app.post("/employees")
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db)
):

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

    return new_employee


@app.get("/employees")
def get_employees(
    db: Session = Depends(get_db)
):

    return db.query(Employee).all()


# ==================================================
# TASKS
# ==================================================

@app.post("/tasks")
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db)
):

    new_task = Task(
        title=task.title,
        priority=task.priority,
        required_skills=",".join(task.required_skills),
        sla_hours=task.sla_hours,
        estimated_hours=task.estimated_hours,
        location=task.location
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


@app.get("/tasks")
def get_tasks(
    db: Session = Depends(get_db)
):

    return db.query(Task).all()


# ==================================================
# INTELLIGENT TASK ALLOCATION
# ==================================================

@app.post("/tasks/{task_id}/allocate")
def allocate_task(
    task_id: int,
    db: Session = Depends(get_db)
):

    # Find task
    task = db.query(Task).filter(
        Task.id == task_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # Get all employees
    employees = db.query(Employee).all()

    # Find best employee
    result = find_best_employee(
        employees,
        task
    )

    if not result:
        return {
            "success": False,
            "message": "No available employee found"
        }

    employee = result["employee"]

    # Assign task
    task.assigned_employee_id = employee.id
    task.status = "Assigned"

    # Update workload
    employee.workload += task.estimated_hours

    db.commit()

    return {
        "success": True,
        "task_id": task.id,
        "task_title": task.title,
        "employee_id": employee.id,
        "employee_name": employee.name,
        "assignment_score": result["score"],
        "explanation": result["explanation"]
    }
# ==================================================
# DYNAMIC TASK REALLOCATION
# ==================================================

@app.post("/employees/{employee_id}/unavailable")
def employee_unavailable(
    employee_id: int,
    db: Session = Depends(get_db)
):

    # Find employee
    employee = db.query(Employee).filter(
        Employee.id == employee_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    # Mark employee unavailable
    employee.availability = False

    # Find all tasks assigned to this employee
    affected_tasks = db.query(Task).filter(
        Task.assigned_employee_id == employee_id
    ).all()

    reallocated_tasks = []

    # Get other available employees
    available_employees = db.query(Employee).filter(
        Employee.availability == True,
        Employee.id != employee_id
    ).all()

    for task in affected_tasks:

        # Find best replacement
        result = find_best_employee(
            available_employees,
            task
        )

        if not result:
            task.assigned_employee_id = None
            task.status = "Unassigned"

            reallocated_tasks.append({
                "task_id": task.id,
                "task_title": task.title,
                "status": "Unassigned",
                "reason": "No suitable available employee found"
            })

            continue

        new_employee = result["employee"]

        # Reassign task
        task.assigned_employee_id = new_employee.id
        task.status = "Reassigned"

        # Update new employee workload
        new_employee.workload += task.estimated_hours

        reallocated_tasks.append({
            "task_id": task.id,
            "task_title": task.title,
            "new_employee_id": new_employee.id,
            "new_employee_name": new_employee.name,
            "assignment_score": result["score"],
            "explanation": result["explanation"],
            "status": "Reassigned"
        })

    db.commit()

    return {
        "success": True,
        "unavailable_employee": employee.name,
        "affected_tasks": len(affected_tasks),
        "reallocated_tasks": reallocated_tasks
    }
# ==================================================
# UPDATE EMPLOYEE AVAILABILITY
# ==================================================

@app.put("/employees/{employee_id}/availability")
def update_employee_availability(
    employee_id: int,
    availability: bool,
    db: Session = Depends(get_db)
):

    # Find employee
    employee = db.query(Employee).filter(
        Employee.id == employee_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    # Update availability
    employee.availability = availability

    db.commit()
    db.refresh(employee)

    return {
        "success": True,
        "employee_id": employee.id,
        "employee_name": employee.name,
        "availability": employee.availability
    }
# ==================================================
# WORKFORCE OVERVIEW
# ==================================================

@app.get("/workforce/overview")
def workforce_overview(
    db: Session = Depends(get_db)
):

    employees = db.query(Employee).all()
    tasks = db.query(Task).all()

    total_employees = len(employees)

    available_employees = sum(
        1 for employee in employees
        if employee.availability
    )

    unavailable_employees = (
        total_employees - available_employees
    )

    assigned_tasks = sum(
        1 for task in tasks
        if task.assigned_employee_id is not None
    )

    unassigned_tasks = (
        len(tasks) - assigned_tasks
    )

    overloaded_employees = sum(
        1 for employee in employees
        if employee.workload >= 80
    )

    return {
        "total_employees": total_employees,
        "available_employees": available_employees,
        "unavailable_employees": unavailable_employees,
        "total_tasks": len(tasks),
        "assigned_tasks": assigned_tasks,
        "unassigned_tasks": unassigned_tasks,
        "overloaded_employees": overloaded_employees
    }
# ==================================================
# OVERLOADED EMPLOYEES
# ==================================================

@app.get("/workforce/overloaded")
def get_overloaded_employees(
    db: Session = Depends(get_db)
):

    employees = db.query(Employee).filter(
        Employee.workload >= 80
    ).order_by(
        Employee.workload.desc()
    ).all()

    result = []

    for employee in employees:

        result.append({
            "employee_id": employee.id,
            "employee_name": employee.name,
            "role": employee.role,
            "workload": employee.workload,
            "availability": employee.availability,
            "skills": employee.skills.split(","),
            "performance_score": employee.performance_score
        })

    return {
        "count": len(result),
        "overloaded_employees": result
    }