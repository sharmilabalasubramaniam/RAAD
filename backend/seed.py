import random

from app.database import Base, engine, SessionLocal
from app.models import Employee, Task


# ==================================================
# RESET DATABASE
# ==================================================

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()


# ==================================================
# DEMO DATA CONFIGURATION
# ==================================================

random.seed(42)

FIRST_NAMES = [
    "Arun", "Priya", "Rahul", "Divya", "Karthik",
    "Vijay", "Anjali", "Sanjay", "Meena", "Ravi",
    "Nithya", "Suresh", "Kavya", "Aditya", "Sneha",
    "Rohan", "Deepa", "Harish", "Swathi", "Manoj"
]

LAST_NAMES = [
    "Kumar", "Sharma", "Patel", "Iyer", "Reddy",
    "Nair", "Das", "Menon", "Singh", "Rao"
]

ROLES = {
    "Backend Engineer": [
        "Python", "FastAPI", "PostgreSQL", "Java", "Spring"
    ],
    "Frontend Engineer": [
        "React", "Next.js", "TypeScript", "JavaScript"
    ],
    "DevOps Engineer": [
        "AWS", "Docker", "Kubernetes", "Jenkins", "Linux"
    ],
    "Cloud Engineer": [
        "AWS", "Azure", "Docker", "Kubernetes", "Terraform"
    ],
    "Database Engineer": [
        "PostgreSQL", "MySQL", "MongoDB", "Python"
    ],
    "Data Engineer": [
        "Python", "SQL", "Spark", "Airflow", "AWS"
    ],
    "ML Engineer": [
        "Python", "Machine Learning", "TensorFlow", "PyTorch"
    ],
    "QA Engineer": [
        "Selenium", "Python", "API Testing", "Postman"
    ],
    "Security Engineer": [
        "Linux", "AWS", "Cybersecurity", "Python"
    ],
    "Mobile Engineer": [
        "Flutter", "Dart", "Android", "Firebase"
    ]
}

DEPARTMENTS = [
    "Engineering",
    "Data",
    "Cloud",
    "Security",
    "Quality",
    "Mobile"
]

LOCATIONS = [
    "Coimbatore",
    "Chennai",
    "Bangalore",
    "Hyderabad",
    "Pune"
]

PRIORITIES = [
    "Critical",
    "High",
    "Medium",
    "Low"
]

TASK_TEMPLATES = [
    "Fix API Performance",
    "Build Customer Dashboard",
    "Deploy Kubernetes Service",
    "Resolve Database Issue",
    "Develop Authentication Module",
    "Cloud Infrastructure Setup",
    "Data Pipeline Failure",
    "Machine Learning Model Update",
    "Security Vulnerability Fix",
    "Mobile Application Bug",
    "Automated Testing",
    "AWS Infrastructure Migration",
    "PostgreSQL Optimization",
    "Frontend Performance Fix",
    "Production Deployment"
]


# ==================================================
# CREATE EMPLOYEES
# ==================================================

employees = []

for i in range(100):

    role = random.choice(list(ROLES.keys()))

    role_skills = ROLES[role]

    # Each employee gets 3–5 skills
    employee_skills = random.sample(
        role_skills,
        min(
            random.randint(3, 5),
            len(role_skills)
        )
    )

    name = (
        f"{random.choice(FIRST_NAMES)} "
        f"{random.choice(LAST_NAMES)}"
    )

    employee = Employee(
        name=name,
        role=role,
        department=random.choice(DEPARTMENTS),
        skills=",".join(employee_skills),
        workload=random.randint(10, 85),
        availability=random.random() > 0.10,
        location=random.choice(LOCATIONS),
        performance_score=random.randint(65, 98)
    )

    employees.append(employee)


db.add_all(employees)
db.commit()


# ==================================================
# CREATE TASKS
# ==================================================

TASK_SKILL_GROUPS = [
    ["Python", "FastAPI"],
    ["Python", "PostgreSQL"],
    ["React", "Next.js", "TypeScript"],
    ["AWS", "Docker"],
    ["Kubernetes", "AWS", "Docker"],
    ["PostgreSQL", "MySQL"],
    ["Python", "Machine Learning"],
    ["TensorFlow", "Python"],
    ["Selenium", "Python"],
    ["Cybersecurity", "Linux"],
    ["Flutter", "Dart"],
    ["Spark", "Python"],
    ["Airflow", "AWS"],
    ["Terraform", "AWS"],
    ["Java", "Spring"]
]

tasks = []

for i in range(1000):

    priority = random.choices(
        PRIORITIES,
        weights=[10, 25, 40, 25]
    )[0]

    if priority == "Critical":
        sla_hours = random.choice([1, 2, 4])
        estimated_hours = random.choice([1, 2, 3, 4])
    elif priority == "High":
        sla_hours = random.choice([4, 6, 8, 12])
        estimated_hours = random.choice([2, 4, 6])
    elif priority == "Medium":
        sla_hours = random.choice([12, 24, 48])
        estimated_hours = random.choice([4, 6, 8, 12])
    else:
        sla_hours = random.choice([24, 48, 72])
        estimated_hours = random.choice([2, 4, 6, 8])

    required_skills = random.choice(
        TASK_SKILL_GROUPS
    )

    task = Task(
        title=random.choice(TASK_TEMPLATES),
        priority=priority,
        required_skills=",".join(required_skills),
        sla_hours=sla_hours,
        estimated_hours=estimated_hours,
        location=random.choice(LOCATIONS),
        status="Unassigned",
        assigned_employee_id=None
    )

    tasks.append(task)


db.add_all(tasks)
db.commit()


# ==================================================
# SUMMARY
# ==================================================

print("==========================================")
print("AI WORKFORCE DEMO DATA CREATED")
print("==========================================")
print(f"Employees created : {len(employees)}")
print(f"Tasks created     : {len(tasks)}")
print("Database reset    : YES")
print("==========================================")

db.close()