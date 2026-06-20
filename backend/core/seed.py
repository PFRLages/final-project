# backend/core/seed.py
import os
from datetime import datetime, timezone
from database import db
from core.security import hash_password


async def seed_admin():
    # Create the one hardcoded admin if it doesn't exist yet.
    email = os.environ["ADMIN_EMAIL"].lower()
    password = os.environ["ADMIN_PASSWORD"]
    if await db.users.find_one({"email": email}) is None:
        await db.users.insert_one(
            {
                "email": email,
                "password": hash_password(password),
                "name": "Admin",
                "role": "management",
                "must_change_password": True,  # forced to change on first login
                "created_at": datetime.now(timezone.utc),
            }
        )
