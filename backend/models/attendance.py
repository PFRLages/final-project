# backend/models/attendance.py
from pydantic import BaseModel


# What I send when generating a whole month's report skeleton.
class GenerateReportRequest(BaseModel):
    student_id: str
    month: int                       # 1 = January ... 12 = December
    year: int
    country: str                     # used to auto-fill that country's holidays
    payable_time_minutes: int = 25   # standard class length


# What the teacher sends when editing a single row.
class AttendanceUpdate(BaseModel):
    status: str | None = None
    payable_time_minutes: int | None = None
    book: str | None = None
    teacher_remarks: str | None = None


# One row of the report = one class on one date.
class AttendanceOut(BaseModel):
    id: str
    student_id: str
    date: str                        # "YYYY-MM-DD"
    day_of_week: str
    status: str                      # the key, e.g. "attended"
    status_label: str                # what the student sees, e.g. "Present"
    color: str
    payable_time_minutes: int | None = None
    book: str | None = None
    teacher_remarks: str | None = None
    month: int
    year: int


# The counters shown at the top of the report.
class ReportSummary(BaseModel):
    title: str                       # "Jan 1 - Jan 31, 2026"
    attended_classes: int
    absent_with_notice: int          # warn the teacher if this goes over 5
    absent_without_notice: int
    holidays: int


# The full report = summary counters + all the rows.
class ReportOut(BaseModel):
    summary: ReportSummary
    rows: list[AttendanceOut]