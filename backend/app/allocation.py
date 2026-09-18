PRIORITY_WEIGHT = {
    "Critical": 1.0,
    "High": 0.8,
    "Medium": 0.5,
    "Low": 0.2
}


def calculate_skill_match(employee_skills, required_skills):
    employee_skills = {
        skill.strip().lower()
        for skill in employee_skills
    }

    required_skills = {
        skill.strip().lower()
        for skill in required_skills
    }

    if not required_skills:
        return 1.0

    matched = employee_skills.intersection(required_skills)

    return len(matched) / len(required_skills)


def calculate_workload_score(workload):
    """
    Lower workload = higher score.
    """

    workload = max(0, min(workload, 100))

    return 1 - (workload / 100)


def calculate_sla_score(estimated_hours, sla_hours):
    if sla_hours <= 0:
        return 0

    ratio = estimated_hours / sla_hours

    if ratio <= 0.5:
        return 1.0

    if ratio <= 0.75:
        return 0.8

    if ratio <= 1:
        return 0.6

    return 0.3


def calculate_location_score(employee_location, task_location):
    if not employee_location or not task_location:
        return 0.5

    if employee_location.lower() == task_location.lower():
        return 1.0

    return 0.4


def calculate_assignment_score(employee, task):

    employee_skills = employee.skills.split(",")
    required_skills = task.required_skills.split(",")

    skill_score = calculate_skill_match(
        employee_skills,
        required_skills
    )

    workload_score = calculate_workload_score(
        employee.workload
    )

    sla_score = calculate_sla_score(
        task.estimated_hours,
        task.sla_hours
    )

    location_score = calculate_location_score(
        employee.location,
        task.location
    )

    performance_score = employee.performance_score / 100

    priority_score = PRIORITY_WEIGHT.get(
        task.priority,
        0.5
    )

    final_score = (
        skill_score * 0.40 +
        workload_score * 0.20 +
        sla_score * 0.15 +
        performance_score * 0.15 +
        location_score * 0.05 +
        priority_score * 0.05
    )

    return round(final_score * 100, 2)


def generate_explanation(employee, task):

    employee_skills = [
        skill.strip().lower()
        for skill in employee.skills.split(",")
    ]

    required_skills = [
        skill.strip()
        for skill in task.required_skills.split(",")
    ]

    matched = [
        skill
        for skill in required_skills
        if skill.lower() in employee_skills
    ]

    return (
        f"{employee.name} was selected because they have "
        f"{len(matched)}/{len(required_skills)} required skills, "
        f"current workload is {employee.workload}%, "
        f"they are available, and their historical "
        f"performance score is {employee.performance_score}%."
    )

def find_best_employee(employees, task):

    candidates = []

    for employee in employees:

        # Ignore unavailable employees
        if not employee.availability:
            continue

        employee_skills = employee.skills.split(",")
        required_skills = task.required_skills.split(",")

        skill_match = calculate_skill_match(
            employee_skills,
            required_skills
        )

        # Employee must have at least 50% of required skills
        if skill_match < 0.5:
            continue

        score = calculate_assignment_score(
            employee,
            task
        )

        explanation = generate_explanation(
            employee,
            task
        )

        candidates.append({
            "employee": employee,
            "score": score,
            "skill_match": round(skill_match * 100, 2),
            "explanation": explanation
        })

    if not candidates:
        return None

    candidates.sort(
        key=lambda candidate: candidate["score"],
        reverse=True
    )

    return candidates[0]