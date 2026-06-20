# backend/routers/assignments.py
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

from database import db
from core.security import require_role
from models.assignment import AssignmentCreate, AssignmentOut

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


def to_out(doc: dict) -> AssignmentOut:
    return AssignmentOut(
        id=str(doc["_id"]),
        teacher_id=doc["teacher_id"],
        student_id=doc["student_id"],
    )


# management links a teacher to a student
@router.post("", response_model=AssignmentOut, status_code=201,
             dependencies=[Depends(require_role("management"))])
async def create_assignment(payload: AssignmentCreate):
    doc = payload.model_dump()
    try:
        result = await db.assignments.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="This teacher is already assigned to this student")
    doc["_id"] = result.inserted_id
    return to_out(doc)


# list assignments, optional ?teacher_id= filter
@router.get("", response_model=list[AssignmentOut],
            dependencies=[Depends(require_role("management", "teacher"))])
async def list_assignments(teacher_id: str | None = None):
    query = {"teacher_id": teacher_id} if teacher_id else {}
    rows = await db.assignments.find(query).to_list(length=1000)
    return [to_out(r) for r in rows]


# management unlinks
@router.delete("/{assignment_id}", status_code=204,
               dependencies=[Depends(require_role("management"))])
async def delete_assignment(assignment_id: str):
    try:
        _id = ObjectId(assignment_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid assignment id")
    result = await db.assignments.delete_one({"_id": _id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return None