# backend/models/holiday.py
from pydantic import BaseModel


class HolidayCreate(BaseModel):
    country: str
    date: str       # "YYYY-MM-DD"
    name: str


class HolidayUpdate(BaseModel):
    country: str | None = None
    date: str | None = None
    name: str | None = None


class HolidayOut(BaseModel):
    id: str
    country: str
    date: str
    day_of_week: str
    name: str
    year: int