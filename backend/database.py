# backend/database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pymongo.collation import Collation

load_dotenv()

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ.get("DB_NAME", "ep_school")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# case-insensitive
CI = Collation(locale="en", strength=2)

async def ensure_indexes():
    await db.users.create_index("email", unique=True)
    await db.students.create_index("name", unique=True, collation=CI)
    await db.ebooks.create_index("name", unique=True, collation=CI)
    await db.holidays.create_index(
        [("country", 1), ("date", 1)], unique=True, collation=CI
    )
    await db.countries.create_index("name", unique=True, collation=CI)
    # Seed the starting countries once (only if the collection is empty)
    if await db.countries.count_documents({}) == 0:
        await db.countries.insert_many(
            [{"name": n} for n in ["Philippines", "South Korea", "Japan"]]
        )
    await db.assignments.create_index(
        [("teacher_id", 1), ("student_id", 1)], unique=True
    )
    await db.payments.create_index(
        [("student_id", 1), ("year", 1), ("month", 1)], unique=True
    )