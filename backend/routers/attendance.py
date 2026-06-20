# backend/routers/attendance.py
# This is the reporting engine. It builds a month of class rows for a student,
# lets the teacher edit each row, and returns the report with the summary counters
# that appear at the top of my spreadsheet.
import calendar
from datetime import date as date_cls
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from bson.errors import InvalidId
from database import db
from core.security import require_role, assert_can_access_student
from core.statuses import STUDENT_STATUSES, STATUS_COLORS
from models.attendance import (
    GenerateReportRequest,
    AttendanceUpdate,
    AttendanceOut,
    ReportSummary,
    ReportOut,
)

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


# ---------- Helpers ----------


def make_row(
    req: GenerateReportRequest,
    date_str: str,
    weekday: str,
    status: str,
    payable: int | None = None,
) -> dict:
    # Builds one row document ready to save in Mongo.
    return {
        "student_id": req.student_id,
        "date": date_str,
        "day_of_week": weekday,
        "status": status,
        "status_label": STUDENT_STATUSES[status],
        "color": STATUS_COLORS[status],
        "payable_time_minutes": payable,  # only attended rows have a payable time
        "book": "" if status == "attended" else None,
        "teacher_remarks": "",
        "month": req.month,
        "year": req.year,
    }


def to_out(doc: dict) -> AttendanceOut:
    return AttendanceOut(
        id=str(doc["_id"]),
        student_id=doc["student_id"],
        date=doc["date"],
        day_of_week=doc["day_of_week"],
        status=doc["status"],
        status_label=doc["status_label"],
        color=doc["color"],
        payable_time_minutes=doc.get("payable_time_minutes"),
        book=doc.get("book"),
        teacher_remarks=doc.get("teacher_remarks"),
        month=doc["month"],
        year=doc["year"],
    )


def parse_object_id(attendance_id: str) -> ObjectId:
    try:
        return ObjectId(attendance_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid attendance id")


# ---------- Endpoints ----------


# GENERATE — build the whole month skeleton for one student.
# Holidays auto-fill, non-class days become Rest Day, and each scheduled
# class becomes a Present row the teacher can then edit.
@router.post("/generate", dependencies=[Depends(require_role("management", "teacher"))])
async def generate_report(payload: GenerateReportRequest):
    if not 1 <= payload.month <= 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    # Regenerate fresh: clear any existing rows for this student/month/year first.
    await db.attendance.delete_many(
        {
            "student_id": payload.student_id,
            "month": payload.month,
            "year": payload.year,
        }
    )

    # Which countries' holidays apply to this student:
    # Philippines is always included (all our teachers are Filipino),
    # plus the student's own country. Using a set means a Filipino
    # student naturally ends up with just {"Philippines"} (no duplicates).
    student = await db.students.find_one({"_id": ObjectId(payload.student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    countries = {"Philippines"}
    if student.get("country"):
        countries.add(student["country"])

    # Collect those countries' holiday dates for the month.
    holiday_dates = set()
    holidays = await db.holidays.find(
        {
            "country": {"$in": list(countries)},
            "year": payload.year,
        }
    ).to_list(length=1000)
    for h in holidays:
        if int(h["date"][5:7]) == payload.month:  # the MM part of "YYYY-MM-DD"
            holiday_dates.add(h["date"])

    # Count how many classes the student has on each weekday (from the schedule).
    schedules = await db.schedules.find({"student_id": payload.student_id}).to_list(
        length=1000
    )
    classes_per_weekday: dict[str, int] = {}
    for s in schedules:
        classes_per_weekday[s["day_of_week"]] = (
            classes_per_weekday.get(s["day_of_week"], 0) + 1
        )

    # Walk every day of the month and decide what row(s) it gets.
    rows: list[dict] = []
    num_days = calendar.monthrange(payload.year, payload.month)[1]
    for day in range(1, num_days + 1):
        d = date_cls(payload.year, payload.month, day)
        date_str = d.strftime("%Y-%m-%d")
        weekday = d.strftime("%A")

        if date_str in holiday_dates:
            rows.append(make_row(payload, date_str, weekday, "holiday"))
        else:
            class_count = classes_per_weekday.get(weekday, 0)
            if class_count == 0:
                # student has no class this weekday -> rest day
                rows.append(make_row(payload, date_str, weekday, "rest_day"))
            else:
                # one row per class (handles 2 classes on the same day)
                for _ in range(class_count):
                    rows.append(
                        make_row(
                            payload,
                            date_str,
                            weekday,
                            "attended",
                            payable=payload.payable_time_minutes,
                        )
                    )

    if rows:
        await db.attendance.insert_many(rows)
    return {"created": len(rows)}


# REPORT — the student's monthly report: rows + the summary counters on top.
@router.get("/report", response_model=ReportOut)
async def get_report(
    student_id: str,
    month: int,
    year: int,
    current_user: dict = Depends(require_role("management", "teacher", "student")),
):
    # Access check (raises 403 if this user can't see this student).
    await assert_can_access_student(current_user, student_id)

    rows = (
        await db.attendance.find(
            {
                "student_id": student_id,
                "month": month,
                "year": year,
            }
        )
        .sort("date", 1)
        .to_list(length=1000)
    )

    # Counters, exactly like the boxes at the top of my spreadsheet.
    attended = sum(1 for r in rows if r["status"] == "attended")
    with_notice = sum(
        1 for r in rows if r["status"] in ("absent_notice", "absent_late")
    )
    without_notice = sum(1 for r in rows if r["status"] == "absent_no_notice")
    holidays = sum(1 for r in rows if r["status"] == "holiday")

    num_days = calendar.monthrange(year, month)[1]
    month_name = calendar.month_abbr[month]
    title = f"{month_name} 1 - {month_name} {num_days}, {year}"

    summary = ReportSummary(
        title=title,
        attended_classes=attended,
        absent_with_notice=with_notice,
        absent_without_notice=without_notice,
        holidays=holidays,
    )
    return ReportOut(summary=summary, rows=[to_out(r) for r in rows])


# UPDATE ROW — the teacher fills in a row (book, attendance, remarks).
# If the status changes I also refresh the label + color to match.
@router.put(
    "/{attendance_id}",
    response_model=AttendanceOut,
    dependencies=[Depends(require_role("management", "teacher"))],
)
async def update_row(attendance_id: str, payload: AttendanceUpdate):
    _id = parse_object_id(attendance_id)

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "status" in updates:
        if updates["status"] not in STUDENT_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid status")
        updates["status_label"] = STUDENT_STATUSES[updates["status"]]
        updates["color"] = STATUS_COLORS[updates["status"]]

    result = await db.attendance.update_one({"_id": _id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Attendance row not found")

    updated = await db.attendance.find_one({"_id": _id})
    assert updated is not None
    return to_out(updated)
