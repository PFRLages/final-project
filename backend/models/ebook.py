# backend/models/ebook.py
from pydantic import BaseModel


class EbookCreate(BaseModel):
    name: str
    level: str
    file_url: str
    shared_with: list[str] = []   # user ids this book is shared with


class EbookUpdate(BaseModel):
    name: str | None = None
    level: str | None = None
    file_url: str | None = None
    shared_with: list[str] | None = None


class EbookOut(BaseModel):
    id: str
    name: str
    level: str
    file_url: str
    shared_with: list[str] = []