# backend/routers/teachers.py
# A teacher is just a user with role "teacher". Management manages them here.
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

from database import db
from core.security import require_role, hash_password

router = APIRouter(prefix="/api/teachers", tags=["teachers"])


class TeacherCreate(BaseModel):
    name: str
    email: EmailStr
    mobile: str | None = None


class TeacherUpdate(BaseModel):
    name: str | None = None
    mobile: str | None = None


class TeacherOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    mobile: str | None = None


class TeacherCreateResponse(BaseModel):
    teacher: TeacherOut
    temp_password: str


def to_out(doc: dict) -> TeacherOut:
    return TeacherOut(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        mobile=doc.get("mobile"),
    )


def oid(teacher_id: str) -> ObjectId:
    try:
        return ObjectId(teacher_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid teacher id")


@router.post(
    "",
    response_model=TeacherCreateResponse,
    status_code=201,
    dependencies=[Depends(require_role("management"))],
)
async def create_teacher(payload: TeacherCreate):
    email = payload.email.lower()
    temp_password = secrets.token_urlsafe(6)
    doc = {
        "email": email,
        "password": hash_password(temp_password),
        "name": payload.name,
        "mobile": payload.mobile,
        "role": "teacher",
        "must_change_password": True,
        "created_at": datetime.now(timezone.utc),
        "active": True,
    }
    try:
        result = await db.users.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409, detail="A user with this email already exists"
        )
    doc["_id"] = result.inserted_id
    return TeacherCreateResponse(teacher=to_out(doc), temp_password=temp_password)


@router.get(
    "",
    response_model=list[TeacherOut],
    dependencies=[Depends(require_role("management"))],
)
async def list_teachers(search: str | None = None):
    query = {"role": "teacher", "active": {"$ne": False}}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    teachers = await db.users.find(query).to_list(length=1000)
    return [to_out(t) for t in teachers]


@router.put(
    "/{teacher_id}",
    response_model=TeacherOut,
    dependencies=[Depends(require_role("management"))],
)
async def update_teacher(teacher_id: str, payload: TeacherUpdate):
    _id = oid(teacher_id)
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.users.update_one(
        {"_id": _id, "role": "teacher"}, {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Teacher not found")
    updated = await db.users.find_one({"_id": _id})
    assert updated is not None
    return to_out(updated)

# Sets teacher as inactive and keeps record
@router.delete("/{teacher_id}", status_code=204,
               dependencies=[Depends(require_role("management"))])
async def delete_teacher(teacher_id: str):
    result = await db.users.update_one(
        {"_id": oid(teacher_id), "role": "teacher"}, {"$set": {"active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return None
