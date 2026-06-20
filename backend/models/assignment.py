# backend/models/assignment.py
from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    teacher_id: str
    student_id: str


class AssignmentOut(BaseModel):
    id: str
    teacher_id: str
    student_id: str