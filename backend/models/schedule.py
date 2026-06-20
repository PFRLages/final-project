# backend/models/schedule.py
from pydantic import BaseModel


class ScheduleCreate(BaseModel):
    teacher_id: str
    student_id: str
    day_of_week: str    # "Monday" ... "Sunday"
    start_time: str     # "08:00"
    end_time: str       # "08:30"
    status: str = "booked"   # booked / available / vacation


class ScheduleOut(BaseModel):
    id: str
    teacher_id: str
    student_id: str
    day_of_week: str
    start_time: str
    end_time: str
    status: str