# backend/models/user.py
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class Role(str, Enum):
    management = "management"
    teacher = "teacher"
    student = "student"


# What the client SENDS when registering
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str
    role: Role = Role.student


# What the client SENDS when logging in
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# What we SEND BACK
class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: Role
    mobile: str | None = None
    must_change_password: bool = False
    student_id: str | None = None  # links a student login to its record
    grace_days_left: int | None = None  # days left before a deactivated student loses access


# What comes back from /login
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# A logged-in user changing their own password.
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


# A logged-in user updating their own profile.
class ProfileUpdate(BaseModel):
    name: str | None = None
    mobile: str | None = None
