# backend/routers/countries.py
# Manage the list of countries used by the holiday + student dropdowns.
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

from database import db
from core.security import require_role

router = APIRouter(prefix="/api/countries", tags=["countries"])


class CountryCreate(BaseModel):
    name: str


class CountryOut(BaseModel):
    id: str
    name: str


def to_out(doc: dict) -> CountryOut:
    return CountryOut(id=str(doc["_id"]), name=doc["name"])


# Any logged-in user can read the list (the dropdowns use this).
@router.get(
    "",
    response_model=list[CountryOut],
    dependencies=[Depends(require_role("management", "teacher", "student"))],
)
async def list_countries():
    docs = await db.countries.find().sort("name", 1).to_list(length=500)
    return [to_out(d) for d in docs]


# Management adds a new country.
@router.post(
    "",
    response_model=CountryOut,
    status_code=201,
    dependencies=[Depends(require_role("management"))],
)
async def create_country(payload: CountryCreate):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Country name is required")
    try:
        result = await db.countries.insert_one({"name": name})
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="This country already exists")
    return CountryOut(id=str(result.inserted_id), name=name)


# Management removes a country.
@router.delete(
    "/{country_id}",
    status_code=204,
    dependencies=[Depends(require_role("management"))],
)
async def delete_country(country_id: str):
    try:
        _id = ObjectId(country_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid country id")
    result = await db.countries.delete_one({"_id": _id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Country not found")
    return None
