from sqlalchemy import Column, Integer, String, Float, Boolean, Text

from .database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    role = Column(String, nullable=False)

    department = Column(String, nullable=False)

    skills = Column(Text, nullable=False)

    workload = Column(Float, default=0)

    availability = Column(Boolean, default=True)

    location = Column(String, nullable=True)

    performance_score = Column(Float, default=70)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    priority = Column(String, nullable=False)

    required_skills = Column(Text, nullable=False)

    sla_hours = Column(Float, nullable=False)

    estimated_hours = Column(Float, nullable=False)

    location = Column(String, nullable=True)

    status = Column(String, default="Unassigned")

    assigned_employee_id = Column(
        Integer,
        nullable=True
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String, nullable=False)
    action = Column(String, nullable=False)
    task_id = Column(String, nullable=True)
    task_title = Column(String, nullable=True)
    previous_employee_name = Column(String, nullable=True)
    new_employee_name = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    trigger = Column(String, nullable=True)
    status = Column(String, default="Completed")