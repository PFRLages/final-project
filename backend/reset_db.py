# backend/reset_db.py
# DANGER: deletes ALL data and recreates the admin + 3 teachers.
# Run from the backend folder:  python reset_db.py
import asyncio
from datetime import datetime, timezone

from database import db, ensure_indexes
from core.security import hash_password
from routers.ebooks import import_existing_pdfs

ADMIN_EMAIL = "admin@ep.com"
ADMIN_PASSWORD = "test26"

# (name, email, password) for the starting teacher accounts
TEACHERS = [
    ("Kristin", "kristin@ep.com", "test26"),
    ("Mai", "mai@ep.com", "test26"),
    ("Irene", "irene@ep.com", "test26"),
]

COLLECTIONS = [
    "users", "students", "ebooks", "holidays",
    "schedules", "assignments", "attendance", "payments", "countries",
]


async def reset():
    # 1) Drop every collection
    for name in COLLECTIONS:
        await db[name].drop()
    print("Cleared all collections.")

    # 2) Recreate indexes (also re-seeds the default countries)
    await ensure_indexes()
    print("Recreated indexes + seeded default countries.")

    # 3) Seed the admin account
    await db.users.insert_one({
        "email": ADMIN_EMAIL,
        "password": hash_password(ADMIN_PASSWORD),
        "name": "Admin",
        "role": "management",
        "must_change_password": False,
        "active": True,
        "created_at": datetime.now(timezone.utc),
    })
    print(f"Created admin -> {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

    # 4) Seed the 3 teachers
    for name, email, pw in TEACHERS:
        await db.users.insert_one({
            "email": email,
            "password": hash_password(pw),
            "name": name,
            "role": "teacher",
            "must_change_password": False,
            "active": True,
            "created_at": datetime.now(timezone.utc),
        })
        print(f"Created teacher -> {email} / {pw}")

    # 5) Re-import any PDFs already sitting in the uploads folder
    count = await import_existing_pdfs()
    print(f"Imported {count} existing PDF(s) from the uploads folder.")


if __name__ == "__main__":
    asyncio.run(reset())