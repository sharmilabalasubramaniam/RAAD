from pydantic import BaseModel
from typing import List, Optional


class EmployeeCreate(BaseModel):
    name: str
    role: str
    department: str
    skills: List[str]
    workload: float = 0
    availability: bool = True
    location: Optional[str] = None
    performance_score: float = 70


class TaskCreate(BaseModel):
    title: str
    priority: str
    required_skills: List[str]
    sla_hours: float
    estimated_hours: float
    location: Optional[str] = None