# backend/routers/students.py
import secrets
from fastapi import APIRouter, HTTPException, Depends
from core.security import require_role
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError
from pymongo.errors import DuplicateKeyError
from core.security import hash_password
from database import db

router = APIRouter(prefix="/api/students", tags=["students"])


# ---------- Pydantic models (the shape of a student) ----------
class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    level: str | None = None
    mobile: str | None = None
    preferred_name: str | None = None
    country: str | None = None


class StudentUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    level: str | None = None
    mobile: str | None = None
    preferred_name: str | None = None
    country: str | None = None


class StudentOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    level: str | None = None
    mobile: str | None = None
    preferred_name: str | None = None
    country: str | None = None


class StudentCreateResponse(BaseModel):
    student: StudentOut
    temp_password: str  # shown once so management can share it


# ---------- Helpers ----------
def to_out(doc: dict) -> StudentOut:
    """Convert a raw Mongo document into our clean StudentOut shape."""
    return StudentOut(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        level=doc.get("level"),
        mobile=doc.get("mobile"),
        preferred_name=doc.get("preferred_name"),
        country=doc.get("country"),
    )


def parse_object_id(student_id: str) -> ObjectId:
    """Mongo ids are ObjectId, the URL gives us a string. Convert safely."""
    try:
        return ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student id")


# ---------- CRUD endpoints ----------


# CREATE - Management onlhy
@router.post(
    "",
    response_model=StudentCreateResponse,
    status_code=201,
    dependencies=[Depends(require_role("management"))],
)
async def create_student(payload: StudentCreate):
    email = payload.email.lower()

    # 1) Create the student record
    doc = payload.model_dump()
    doc["email"] = email
    doc["created_at"] = datetime.now(timezone.utc)
    doc["active"] = True
    try:
        result = await db.students.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409, detail="A student with this email already exists"
        )

    student_id = str(result.inserted_id)

    # 2) Create the login account with a temporary password
    temp_password = secrets.token_urlsafe(6)  # e.g. "Qk7sP2a"
    user_doc = {
        "email": email,
        "password": hash_password(temp_password),
        "name": payload.name,
        "role": "student",
        "must_change_password": True,  # force change on first login
        "student_id": student_id,  # link login -> record
        "created_at": datetime.now(timezone.utc),
    }
    try:
        await db.users.insert_one(user_doc)
    except DuplicateKeyError:
        # roll back the student we just created so we don't leave an orphan
        await db.students.delete_one({"_id": result.inserted_id})
        raise HTTPException(
            status_code=409, detail="A user with this email already exists"
        )

    doc["_id"] = result.inserted_id
    return StudentCreateResponse(student=to_out(doc), temp_password=temp_password)


# Get students
@router.get("", response_model=list[StudentOut])
async def list_students(
    search: str | None = None,
    current_user: dict = Depends(require_role("management", "teacher")),
):
    query = {"active": {"$ne": False}}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]

    # A teacher only sees students assigned to them.
    if current_user["role"] == "teacher":
        assignments = await db.assignments.find(
            {"teacher_id": current_user["id"]}
        ).to_list(length=1000)
        ids = [ObjectId(a["student_id"]) for a in assignments]
        query["_id"] = {"$in": ids}

    students = await db.students.find(query).to_list(length=1000)
    return [to_out(s) for s in students]


# READ ONE - management or teacher
@router.get(
    "/{student_id}",
    response_model=StudentOut,
    dependencies=[Depends(require_role("management", "teacher"))],
)
async def get_student(student_id: str):
    doc = await db.students.find_one({"_id": parse_object_id(student_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Student not found")
    return to_out(doc)


# UPDATE - management only
@router.put(
    "/{student_id}",
    response_model=StudentOut,
    dependencies=[Depends(require_role("management", "teacher"))],
)
async def update_student(student_id: str, payload: StudentUpdate):
    oid = parse_object_id(student_id)

    # Only update the fields the client actually sent (skip the None ones)
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await db.students.update_one({"_id": oid}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")

    updated = await db.students.find_one({"_id": oid})
    assert updated is not None
    return to_out(updated)


# DELETE - management only (Keeps records and sets student inactive)
@router.delete(
    "/{student_id}", status_code=204, dependencies=[Depends(require_role("management"))]
)
async def delete_student(student_id: str):
    result = await db.students.update_one(
        {"_id": parse_object_id(student_id)}, {"$set": {"active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return None
