# backend/main.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

from database import ensure_indexes
from core.seed import seed_admin
from routers import (auth, students, ebooks, holidays, assignments,
                     schedules, attendance, payments, teachers, users, countries)


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)   # folder for uploaded eBooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    await seed_admin()
    yield


app = FastAPI(title="English Passion API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://final-project-pearl-six.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files (e.g. http://127.0.0.1:8000/uploads/abc.pdf)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(ebooks.router)
app.include_router(holidays.router)
app.include_router(assignments.router)
app.include_router(schedules.router)
app.include_router(attendance.router)
app.include_router(payments.router)
app.include_router(teachers.router)
app.include_router(users.router)
app.include_router(countries.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}