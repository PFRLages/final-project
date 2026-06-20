# backend/core/security.py
import os
from datetime import datetime, timezone, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from bson import ObjectId

from database import db

# --- Password hashing setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# --- Account activation / deactivation rules ---
STUDENT_GRACE_DAYS = 30  # students keep access for 30 days after being deactivated


def is_user_login_blocked(user: dict) -> bool:
    """Decide if a user is blocked from using the system.
    Teachers & management are blocked immediately when deactivated.
    Students get a 30-day grace period from their deactivation date."""
    if user.get("active", True):
        return False  # active (or no flag set) -> always allowed

    role = user.get("role")
    if role == "student":
        deactivated_at = user.get("deactivated_at")
        if not deactivated_at:
            return True  # deactivated with no date -> block to be safe
        if isinstance(deactivated_at, str):
            deactivated_at = datetime.fromisoformat(deactivated_at)
        if deactivated_at.tzinfo is None:
            deactivated_at = deactivated_at.replace(tzinfo=timezone.utc)
        # blocked only AFTER the grace period ends
        return datetime.now(timezone.utc) - deactivated_at > timedelta(
            days=STUDENT_GRACE_DAYS
        )

    # teacher / management -> blocked the moment they're deactivated
    return True


# --- JWT setup ---
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,  # "subject" = who the token belongs to
        "role": role,
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# This tells FastAPI: "look for a Bearer token, and the login URL is /auth/login"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception

    # Block deactivated users (teachers immediately, students after grace period)
    if is_user_login_blocked(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact administration.",
        )

    user["id"] = str(user["_id"])  # convert ObjectId -> string
    user.pop("_id", None)
    user.pop("password", None)  # never expose the hash
    return user


def require_role(*allowed_roles: str):
    """
    Returns a dependency that allows the request through ONLY if the
    logged-in user's role is in `allowed_roles`. Otherwise -> 403.

    Usage:  Depends(require_role("management"))
            Depends(require_role("management", "teacher"))
    """

    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker


# Checks whether the current user is allowed to see a given student's data.
async def assert_can_access_student(current_user: dict, student_id: str):
    role = current_user["role"]

    if role == "management":
        return  # management sees everything

    if role == "student":
        if current_user.get("student_id") != student_id:
            raise HTTPException(
                status_code=403, detail="You can only view your own data"
            )
        return

    if role == "teacher":
        assigned = await db.assignments.find_one(
            {
                "teacher_id": current_user["id"],
                "student_id": student_id,
            }
        )
        if not assigned:
            raise HTTPException(
                status_code=403, detail="This student is not assigned to you"
            )
        return

    raise HTTPException(status_code=403, detail="Not allowed")
