# backend/routers/holidays.py
import csv
import io
from fastapi import UploadFile, File, Form
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from bson.errors import InvalidId

from database import db
from core.security import require_role
from models.holiday import HolidayCreate, HolidayUpdate, HolidayOut
from pymongo.errors import DuplicateKeyError

router = APIRouter(prefix="/api/holidays", tags=["holidays"])


def parse_date(date_str: str) -> datetime:
    # turn "YYYY-MM-DD" into a real date so we can read weekday/year
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Date must be YYYY-MM-DD")


def to_out(doc: dict) -> HolidayOut:
    return HolidayOut(
        id=str(doc["_id"]),
        country=doc["country"],
        date=doc["date"],
        day_of_week=doc["day_of_week"],
        name=doc["name"],
        year=doc["year"],
    )


def oid(holiday_id: str) -> ObjectId:
    try:
        return ObjectId(holiday_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid holiday id")


# Accept several date formats in the file, store them all as YYYY-MM-DD internally.
def _parse_flexible_date(s: str):
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# management adds a holiday (weekday + year filled in automatically)
@router.post(
    "",
    response_model=HolidayOut,
    status_code=201,
    dependencies=[Depends(require_role("management"))],
)
async def create_holiday(payload: HolidayCreate):
    d = parse_date(payload.date)
    doc = {
        "country": payload.country,
        "date": payload.date,
        "name": payload.name,
        "day_of_week": d.strftime("%A"),  # e.g. "Monday"
        "year": d.year,
    }
    try:
        result = await db.holidays.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="This holiday already exists")
    doc["_id"] = result.inserted_id
    return to_out(doc)


# Bulk upload holidays from a CSV/TXT (or Excel) file. Country comes from the dropdown.
# File format: each row = date,name  ->  01-01-2026,New Year's Day  (dd-mm-yyyy or yyyy-mm-dd)
@router.post("/upload", dependencies=[Depends(require_role("management"))])
async def upload_holidays(country: str = Form(...), file: UploadFile = File(...)):
    filename = (file.filename or "").lower()
    content = await file.read()
    rows: list[tuple[str, str]] = []  # (date_str, name)

    if filename.endswith(".xlsx"):
        try:
            import openpyxl
        except ImportError:
            raise HTTPException(
                status_code=400,
                detail="Excel support not installed. Save the file as CSV, or run: pip install openpyxl",
            )
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        for r in ws.iter_rows(values_only=True):
            if not r or r[0] is None:
                continue
            date_cell = r[0]
            name_cell = r[1] if len(r) > 1 else ""
            date_str = (
                date_cell.strftime("%Y-%m-%d")
                if hasattr(date_cell, "strftime")
                else str(date_cell).strip()
            )
            rows.append((date_str, str(name_cell or "").strip()))
    else:
        text = content.decode("utf-8-sig", errors="ignore")
        for r in csv.reader(io.StringIO(text)):
            if not r or not r[0].strip():
                continue
            date_str = r[0].strip()
            name = r[1].strip() if len(r) > 1 else ""
            rows.append((date_str, name))

    added, skipped, errors = 0, 0, []
    for date_str, name in rows:
        d = _parse_flexible_date(date_str)
        if d is None:
            errors.append(f"Skipped bad date: {date_str!r}")
            continue
        normalized = d.strftime("%Y-%m-%d")  # always store ISO format
        doc = {
            "country": country,
            "date": normalized,
            "name": name or "Holiday",
            "day_of_week": d.strftime("%A"),
            "year": d.year,
        }
        try:
            await db.holidays.insert_one(doc)
            added += 1
        except DuplicateKeyError:
            skipped += 1

    return {"added": added, "skipped": skipped, "errors": errors}


# everyone logged in can list holidays, optional ?country= filter
@router.get(
    "",
    response_model=list[HolidayOut],
    dependencies=[Depends(require_role("management", "teacher", "student"))],
)
async def list_holidays(country: str | None = None):
    query = {"country": country} if country else {}
    holidays = await db.holidays.find(query).to_list(length=1000)
    return [to_out(h) for h in holidays]


# management edits a holiday
@router.put(
    "/{holiday_id}",
    response_model=HolidayOut,
    dependencies=[Depends(require_role("management"))],
)
async def update_holiday(holiday_id: str, payload: HolidayUpdate):
    _id = oid(holiday_id)
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # if the date changed, recompute weekday + year
    if "date" in updates:
        d = parse_date(updates["date"])
        updates["day_of_week"] = d.strftime("%A")
        updates["year"] = d.year

    result = await db.holidays.update_one({"_id": _id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Holiday not found")

    updated = await db.holidays.find_one({"_id": _id})
    assert updated is not None
    return to_out(updated)


# management removes a holiday
@router.delete(
    "/{holiday_id}", status_code=204, dependencies=[Depends(require_role("management"))]
)
async def delete_holiday(holiday_id: str):
    result = await db.holidays.delete_one({"_id": oid(holiday_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return None
