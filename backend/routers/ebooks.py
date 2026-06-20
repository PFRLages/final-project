# backend/routers/ebooks.py
import os
import secrets
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

from database import db
from core.security import require_role
from models.ebook import EbookCreate, EbookUpdate, EbookOut

router = APIRouter(prefix="/api/ebooks", tags=["ebooks"])

UPLOAD_DIR = "uploads"


# Request body for sharing a book with one user.
class ShareRequest(BaseModel):
    user_id: str


def to_out(doc: dict) -> EbookOut:
    return EbookOut(
        id=str(doc["_id"]),
        name=doc["name"],
        level=doc["level"],
        file_url=doc["file_url"],
        shared_with=doc.get("shared_with", []),
    )


def oid(ebook_id: str) -> ObjectId:
    try:
        return ObjectId(ebook_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ebook id")


# Leaf folders inside /uploads are the available levels (e.g. "Beginner 1").
# A folder that only contains other folders (e.g. "Beginner") is a container, not a level.
def list_level_folders() -> list[str]:
    if not os.path.isdir(UPLOAD_DIR):
        return []
    levels = set()
    for root, dirs, files in os.walk(UPLOAD_DIR):
        if os.path.abspath(root) == os.path.abspath(UPLOAD_DIR):
            continue
        if not dirs:  # no subfolders -> this is a level folder
            levels.add(os.path.basename(root))
    return sorted(levels)


@router.get("/levels", dependencies=[Depends(require_role("management"))])
async def get_levels():
    return {"levels": list_level_folders()}


# Add an ebook record for any PDF in /uploads (recursively).
# The level is the name of the folder that directly contains the PDF.
async def import_existing_pdfs() -> int:
    if not os.path.isdir(UPLOAD_DIR):
        return 0
    added = 0
    for root, dirs, files in os.walk(UPLOAD_DIR):
        for fname in sorted(files):
            if not fname.lower().endswith(".pdf"):
                continue
            rel_path = os.path.relpath(os.path.join(root, fname), UPLOAD_DIR)
            file_url = "/uploads/" + rel_path.replace(os.sep, "/")
            if await db.ebooks.find_one({"file_url": file_url}):
                continue  # already tracked
            # level = the folder holding this pdf ("" if it sits in /uploads itself)
            at_root = os.path.abspath(root) == os.path.abspath(UPLOAD_DIR)
            level = "" if at_root else os.path.basename(root)
            doc = {
                "name": os.path.splitext(fname)[0],
                "level": level,
                "file_url": file_url,
                "shared_with": [],
            }
            try:
                await db.ebooks.insert_one(doc)
            except DuplicateKeyError:
                doc["name"] = fname  # name clash -> use full filename
                try:
                    await db.ebooks.insert_one(doc)
                except DuplicateKeyError:
                    continue
            added += 1
    return added


# Upload a pdf into its level folder. Name = filename (minus ".pdf"); level = chosen folder.
@router.post(
    "/upload",
    response_model=EbookOut,
    status_code=201,
    dependencies=[Depends(require_role("management"))],
)
async def upload_ebook(level: str = Form(...), file: UploadFile = File(...)):
    book_name = os.path.splitext(file.filename or "")[0].strip() or "Untitled"
    original = os.path.basename(file.filename or "file.pdf")

    level = level.strip()
    target_dir = os.path.join(UPLOAD_DIR, level) if level else UPLOAD_DIR
    os.makedirs(target_dir, exist_ok=True)  # creates the level folder if it's new

    dest = os.path.join(target_dir, original)
    if os.path.exists(dest):  # avoid overwriting a same-named file
        original = f"{secrets.token_hex(4)}_{original}"
        dest = os.path.join(target_dir, original)
    with open(dest, "wb") as f:
        f.write(await file.read())

    rel_path = os.path.relpath(dest, UPLOAD_DIR).replace(os.sep, "/")
    doc = {
        "name": book_name,
        "level": level,
        "file_url": "/uploads/" + rel_path,
        "shared_with": [],
    }
    try:
        result = await db.ebooks.insert_one(doc)
    except DuplicateKeyError:
        os.remove(dest)
        raise HTTPException(status_code=409, detail="An ebook with this name already exists")
    doc["_id"] = result.inserted_id
    return to_out(doc)


# management adds a book (no file)
@router.post(
    "",
    response_model=EbookOut,
    status_code=201,
    dependencies=[Depends(require_role("management"))],
)
async def create_ebook(payload: EbookCreate):
    doc = payload.model_dump()
    doc.setdefault("shared_with", [])
    try:
        result = await db.ebooks.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409, detail="An eBook with this name already exists"
        )
    doc["_id"] = result.inserted_id
    return to_out(doc)


# management sees all books; teachers/students see only what's shared with them
@router.get("", response_model=list[EbookOut])
async def list_ebooks(
    current_user: dict = Depends(require_role("management", "teacher", "student")),
):
    query: dict = {}
    if current_user["role"] != "management":
        query["shared_with"] = current_user["id"]  # array contains my user id
    books = await db.ebooks.find(query).to_list(length=1000)
    return [to_out(b) for b in books]


# management scans the uploads folder and adds any untracked PDFs
@router.post("/import-folder", dependencies=[Depends(require_role("management"))])
async def import_folder():
    count = await import_existing_pdfs()
    return {"imported": count}


# management edits a book
@router.put(
    "/{ebook_id}",
    response_model=EbookOut,
    dependencies=[Depends(require_role("management"))],
)
async def update_ebook(ebook_id: str, payload: EbookUpdate):
    _id = oid(ebook_id)
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await db.ebooks.update_one({"_id": _id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ebook not found")

    updated = await db.ebooks.find_one({"_id": _id})
    assert updated is not None
    return to_out(updated)


# management shares a book with a specific teacher/student
@router.post(
    "/{ebook_id}/share",
    response_model=EbookOut,
    dependencies=[Depends(require_role("management"))],
)
async def share_ebook(ebook_id: str, payload: ShareRequest):
    _id = oid(ebook_id)
    try:
        user = await db.users.find_one({"_id": ObjectId(payload.user_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user id")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.ebooks.update_one(
        {"_id": _id}, {"$addToSet": {"shared_with": payload.user_id}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ebook not found")
    updated = await db.ebooks.find_one({"_id": _id})
    assert updated is not None
    return to_out(updated)


# management removes a share
@router.delete(
    "/{ebook_id}/share/{user_id}",
    response_model=EbookOut,
    dependencies=[Depends(require_role("management"))],
)
async def unshare_ebook(ebook_id: str, user_id: str):
    _id = oid(ebook_id)
    result = await db.ebooks.update_one(
        {"_id": _id}, {"$pull": {"shared_with": user_id}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ebook not found")
    updated = await db.ebooks.find_one({"_id": _id})
    assert updated is not None
    return to_out(updated)


# management removes a book
@router.delete(
    "/{ebook_id}", status_code=204, dependencies=[Depends(require_role("management"))]
)
async def delete_ebook(ebook_id: str):
    result = await db.ebooks.delete_one({"_id": oid(ebook_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ebook not found")
    return None
