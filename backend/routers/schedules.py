# backend/routers/schedules.py
# Schedules = the weekly class slots that link a teacher to a student.
# Rules I enforce here:
#   - a class lasts between 30 minutes and 1 hour
#   - the same teacher can't have two classes that overlap on the same day

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from bson.errors import InvalidId

from database import db
from core.security import require_role
from models.schedule import ScheduleCreate, ScheduleOut

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


# ---------- Helpers ----------


def to_minutes(t: str) -> int:
    # I store times as "HH:MM" strings, but to compare them I turn them
    # into total minutes, e.g. "08:30" -> 510. Numbers are easy to compare.
    try:
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Time must be in HH:MM format")


def to_out(doc: dict) -> ScheduleOut:
    # Mongo stores _id as an ObjectId, which isn't JSON-safe.
    # I turn it into a string and reshape the document into my clean output model.
    return ScheduleOut(
        id=str(doc["_id"]),
        teacher_id=doc["teacher_id"],
        student_id=doc["student_id"],
        day_of_week=doc["day_of_week"],
        start_time=doc["start_time"],
        end_time=doc["end_time"],
        status=doc["status"],
    )


def parse_object_id(schedule_id: str) -> ObjectId:
    # The URL gives me a string id; Mongo needs a real ObjectId.
    # If someone passes a bad id I return 400 instead of crashing with 500.
    try:
        return ObjectId(schedule_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid schedule id")


# ---------- CRUD endpoints ----------


# CREATE — management or a teacher can add a class slot.
@router.post(
    "",
    response_model=ScheduleOut,
    status_code=201,
    dependencies=[Depends(require_role("management", "teacher"))],
)
async def create_schedule(payload: ScheduleCreate):
    start = to_minutes(payload.start_time)
    end = to_minutes(payload.end_time)

    # The class must actually have a positive length.
    if end <= start:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    # A class is a minimum of 30 minutes and a maximum of 1 hour.
    duration = end - start
    if duration < 30 or duration > 60:
        raise HTTPException(
            status_code=400, detail="A class must be between 30 and 60 minutes"
        )

    # Get every class this teacher already has on the same weekday,
    # then check if the new class overlaps any of them.
    same_day = await db.schedules.find(
        {
            "teacher_id": payload.teacher_id,
            "day_of_week": payload.day_of_week,
        }
    ).to_list(length=1000)

    for existing in same_day:
        existing_start = to_minutes(existing["start_time"])
        existing_end = to_minutes(existing["end_time"])
        # Two ranges overlap when: new starts before the old one ends
        # AND new ends after the old one starts.
        # I use strict < and > so back-to-back classes (21:00-21:30 then
        # 21:30-22:00) are allowed - they only touch at the boundary.
        if start < existing_end and end > existing_start:
            raise HTTPException(
                status_code=409,
                detail="This class overlaps an existing class for this teacher",
            )

    # All checks passed, save the new class slot.
    doc = payload.model_dump()
    result = await db.schedules.insert_one(doc)
    doc["_id"] = result.inserted_id
    return to_out(doc)

# return schedule
@router.get("", response_model=list[ScheduleOut])
async def list_schedules(
    teacher_id: str | None = None,
    student_id: str | None = None,
    current_user: dict = Depends(require_role("management", "teacher", "student")),
):
    role = current_user["role"]
    query = {}

    if role == "student":
        query["student_id"] = current_user.get("student_id")  # only my classes
    elif role == "teacher":
        query["teacher_id"] = current_user["id"]  # only my classes
    else:  # management can filter freely
        if teacher_id:
            query["teacher_id"] = teacher_id
        if student_id:
            query["student_id"] = student_id

    rows = await db.schedules.find(query).to_list(length=1000)
    return [to_out(r) for r in rows]


# DELETE — management or a teacher can remove a class slot.
@router.delete(
    "/{schedule_id}",
    status_code=204,
    dependencies=[Depends(require_role("management", "teacher"))],
)
async def delete_schedule(schedule_id: str):
    result = await db.schedules.delete_one({"_id": parse_object_id(schedule_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return None
