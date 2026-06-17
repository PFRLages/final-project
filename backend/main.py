from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os

load_dotenv() #read .env file

app =  FastAPI()

# CORS allow communication between frontend and backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client[os.getenv("DB_NAME", "ep_school")] # check better solution later for garanteing not none

class Student(BaseModel):
    name: str
    country: str
    
@app.get("/")
def read_root():
    return {"message": "Hello World!"}

@app.get("/ping-db")
async def ping_db():
    await client.admin.command("ping") # checks if mongodb is up
    return {"database": "Connected"}

# create student
@app.post("/students")
async def create_student(student: Student):
    result = await db.students.insert_one(student.model_dump())
    return {"id": str(result.inserted_id), "name": student.name, "country": student.country}

# return students list
@app.get("/students")
async def get_students():
    students = []
    async for doc in db.students.find():
        doc["id"] = str(doc["_id"])  # convert ObjectId to string
        del doc["_id"]               # delete raw ObjectID
        students.append(doc)
    return students

# update student data
@app.put("/students/{student_id}")
async def update_student(student_id: str, student: Student):
    result = await db.students.update_one(
        {"_id": ObjectId(student_id)},   # find document with this Id
        {"$set": student.model_dump()}  # update data
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student Updated"}

# delete student
@app.delete("/students/{student_id}")
async def delete_student(student_id: str):
    result = await db.students.delete_one({"_id": ObjectId(student_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student Deleted"}
    