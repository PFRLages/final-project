# backend/routers/auth.py
from bson import ObjectId
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from database import db
from models.user import (
    UserCreate,
    UserLogin,
    UserOut,
    Token,
    ChangePasswordRequest,
    ProfileUpdate,
)
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    is_user_login_blocked,
    STUDENT_GRACE_DAYS,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(payload: UserCreate):
    email = payload.email.lower()

    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    doc = {
        "email": email,
        "password": hash_password(payload.password),
        "name": payload.name,
        "role": payload.role.value,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(doc)

    return UserOut(
        id=str(result.inserted_id), email=email, name=payload.name, role=payload.role
    )


@router.post("/login", response_model=Token)
async def login(payload: UserLogin):
    user = await db.users.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Stop deactivated accounts from logging in
    if is_user_login_blocked(user):
        raise HTTPException(
            status_code=403,
            detail="Your account has been deactivated. Please contact administration.",
        )

    token = create_access_token(user_id=str(user["_id"]), role=user["role"])
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    # Tell a deactivated student how many days of access they have left.
    if current_user.get("role") == "student" and not current_user.get("active", True):
        deactivated_at = current_user.get("deactivated_at")
        if deactivated_at:
            if isinstance(deactivated_at, str):
                deactivated_at = datetime.fromisoformat(deactivated_at)
            if deactivated_at.tzinfo is None:
                deactivated_at = deactivated_at.replace(tzinfo=timezone.utc)
            days_used = (datetime.now(timezone.utc) - deactivated_at).days
            current_user["grace_days_left"] = max(0, STUDENT_GRACE_DAYS - days_used)
    return UserOut(**current_user)


# A logged-in user updates their own name / mobile.
@router.put("/me", response_model=UserOut)
async def update_profile(
    payload: ProfileUpdate, current_user: dict = Depends(get_current_user)
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if updates:
        await db.users.update_one(
            {"_id": ObjectId(current_user["id"])}, {"$set": updates}
        )

    user = await db.users.find_one({"_id": ObjectId(current_user["id"])})
    assert user is not None  # the logged-in user always exists
    user["id"] = str(user["_id"])
    user.pop("_id", None)
    user.pop("password", None)
    return UserOut(**user)


# A logged-in user changes their own password (must give the current one).
@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest, current_user: dict = Depends(get_current_user)
):
    user = await db.users.find_one({"_id": ObjectId(current_user["id"])})
    assert user is not None
    if not verify_password(payload.current_password, user["password"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password": hash_password(payload.new_password),
                "must_change_password": False,
            }
        },
    )
    return {"message": "Password updated"}
