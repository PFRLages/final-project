# backend/routers/users.py
# Management-only control panel for ALL login accounts (management, teacher, student):
# list, create management users, deactivate / reactivate, and reset passwords.
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

from database import db
from core.security import require_role, hash_password

router = APIRouter(prefix="/api/users", tags=["users"])


# ---------- Models ----------
class ManagementUserCreate(BaseModel):
    name: str
    email: EmailStr
    mobile: str | None = None


class UserAdminUpdate(BaseModel):
    name: str | None = None
    mobile: str | None = None


class UserAdminOut(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: str
    mobile: str | None = None
    active: bool = True
    must_change_password: bool = False
    student_id: str | None = None
    deactivated_at: str | None = None


class UserCreateResponse(BaseModel):
    user: UserAdminOut
    temp_password: str


class ResetPasswordResponse(BaseModel):
    temp_password: str


# ---------- Helpers ----------
def oid(user_id: str) -> ObjectId:
    try:
        return ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user id")


def to_out(doc: dict) -> UserAdminOut:
    da = doc.get("deactivated_at")
    if isinstance(da, datetime):
        da = da.isoformat()
    return UserAdminOut(
        id=str(doc["_id"]),
        email=doc["email"],
        name=doc.get("name", ""),
        role=doc["role"],
        mobile=doc.get("mobile"),
        active=doc.get("active", True),
        must_change_password=doc.get("must_change_password", False),
        student_id=doc.get("student_id"),
        deactivated_at=da,
    )


# ---------- Endpoints (management only) ----------

# LIST everyone (including inactive, so we can reactivate returning people)
@router.get("", response_model=list[UserAdminOut])
async def list_users(
    role: str | None = None,
    search: str | None = None,
    current_user: dict = Depends(require_role("management")),
):
    query: dict = {}
    if role:
        query["role"] = role
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    users = await db.users.find(query).to_list(length=2000)
    return [to_out(u) for u in users]


# CREATE a new management user (temp password, must change on first login)
@router.post("", response_model=UserCreateResponse, status_code=201)
async def create_management_user(
    payload: ManagementUserCreate,
    current_user: dict = Depends(require_role("management")),
):
    email = payload.email.lower()
    temp_password = secrets.token_urlsafe(6)
    doc = {
        "email": email,
        "password": hash_password(temp_password),
        "name": payload.name,
        "mobile": payload.mobile,
        "role": "management",
        "must_change_password": True,
        "active": True,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = await db.users.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="A user with this email already exists")
    doc["_id"] = result.inserted_id
    return UserCreateResponse(user=to_out(doc), temp_password=temp_password)


# EDIT name / mobile
@router.put("/{user_id}", response_model=UserAdminOut)
async def update_user(
    user_id: str,
    payload: UserAdminUpdate,
    current_user: dict = Depends(require_role("management")),
):
    _id = oid(user_id)
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.users.update_one({"_id": _id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    updated = await db.users.find_one({"_id": _id})
    assert updated is not None
    return to_out(updated)


# DEACTIVATE (block login per the role rules)
@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str, current_user: dict = Depends(require_role("management"))
):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    _id = oid(user_id)
    user = await db.users.find_one({"_id": _id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.users.update_one(
        {"_id": _id},
        {"$set": {"active": False, "deactivated_at": datetime.now(timezone.utc)}},
    )
    # keep the student record in sync
    if user.get("role") == "student" and user.get("student_id"):
        await db.students.update_one(
            {"_id": ObjectId(user["student_id"])}, {"$set": {"active": False}}
        )
    return {"message": "User deactivated"}


# REACTIVATE (e.g. a teacher/student returning to the company)
@router.post("/{user_id}/reactivate")
async def reactivate_user(
    user_id: str, current_user: dict = Depends(require_role("management"))
):
    _id = oid(user_id)
    user = await db.users.find_one({"_id": _id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.users.update_one(
        {"_id": _id},
        {"$set": {"active": True}, "$unset": {"deactivated_at": ""}},
    )
    if user.get("role") == "student" and user.get("student_id"):
        await db.students.update_one(
            {"_id": ObjectId(user["student_id"])}, {"$set": {"active": True}}
        )
    return {"message": "User reactivated"}


# RESET PASSWORD (admin sets a temp password, forces change on next login)
@router.post("/{user_id}/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    user_id: str, current_user: dict = Depends(require_role("management"))
):
    _id = oid(user_id)
    temp_password = secrets.token_urlsafe(6)
    result = await db.users.update_one(
        {"_id": _id},
        {"$set": {"password": hash_password(temp_password), "must_change_password": True}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return ResetPasswordResponse(temp_password=temp_password)