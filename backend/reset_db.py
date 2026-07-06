# backend/reset_db.py
# DANGER: deletes ALL data and recreates the admin + 2 teachers + 2 students.
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
]

# (name, email, password, country) for the starting student accounts.
# Each one gets a student record plus a linked login account.
STUDENTS = [
    ("Lucas Gabriel", "lucas@ep.com", "test26", "South Korea"),
    ("Kana", "kana@ep.com", "test26", "Japan"),
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

    # 4) Seed the teachers
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

    # 5) Seed the students (student record + linked login account)
    for name, email, pw, country in STUDENTS:
        student_doc = {
            "name": name,
            "email": email,
            "level": None,
            "mobile": None,
            "preferred_name": None,
            "country": country,
            "active": True,
            "created_at": datetime.now(timezone.utc),
        }
        result = await db.students.insert_one(student_doc)
        student_id = str(result.inserted_id)

        await db.users.insert_one({
            "email": email,
            "password": hash_password(pw),
            "name": name,
            "role": "student",
            "must_change_password": False,
            "active": True,
            "student_id": student_id,  # link login -> student record
            "created_at": datetime.now(timezone.utc),
        })
        print(f"Created student -> {email} / {pw} ({country})")

    # 6) Re-import any PDFs already sitting in the uploads folder
    count = await import_existing_pdfs()
    print(f"Imported {count} existing PDF(s) from the uploads folder.")


if __name__ == "__main__":
    asyncio.run(reset())