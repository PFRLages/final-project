# backend/routers/payments.py
# The yearly payment table for a student: one row per month, with the
# period pre-filled. Management fills in when it was paid and how much.
# Amounts are in Korean Won.
import calendar
from datetime import date as date_cls
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from bson.errors import InvalidId
from database import db
from core.security import require_role, assert_can_access_student
from models.payment import (
    GenerateYearRequest,
    PaymentUpdate,
    PaymentOut,
    PaymentYearOut,
)

router = APIRouter(prefix="/api/payments", tags=["payments"])


# ---------- Helpers ----------


def to_out(doc: dict) -> PaymentOut:
    # A month counts as "paid" once it has both a payment date and an amount.
    paid = doc.get("payment_date") is not None and doc.get("amount") is not None
    return PaymentOut(
        id=str(doc["_id"]),
        student_id=doc["student_id"],
        month=doc["month"],
        month_name=str(calendar.month_name[doc["month"]]),
        year=doc["year"],
        period_from=doc["period_from"],
        period_to=doc["period_to"],
        payment_date=doc.get("payment_date"),
        amount=doc.get("amount"),
        make_up_classes_count=doc.get("make_up_classes_count", 0),
        paid=paid,
    )


def parse_object_id(payment_id: str) -> ObjectId:
    try:
        return ObjectId(payment_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid payment id")


# ---------- Endpoints ----------


# GENERATE — create the 12 month rows for a student's year.
# Safe to run more than once: it only adds months that don't exist yet,
# so I never wipe amounts I've already entered.
@router.post("/generate-year", dependencies=[Depends(require_role("management"))])
async def generate_year(payload: GenerateYearRequest):
    existing = await db.payments.find(
        {
            "student_id": payload.student_id,
            "year": payload.year,
        }
    ).to_list(length=12)
    existing_months = {row["month"] for row in existing}

    new_rows = []
    for month in range(1, 13):
        if month in existing_months:
            continue
        last_day = calendar.monthrange(payload.year, month)[1]
        new_rows.append(
            {
                "student_id": payload.student_id,
                "year": payload.year,
                "month": month,
                "period_from": date_cls(payload.year, month, 1).strftime("%Y-%m-%d"),
                "period_to": date_cls(payload.year, month, last_day).strftime(
                    "%Y-%m-%d"
                ),
                "payment_date": None,
                "amount": None,
                "make_up_classes_count": 0,
            }
        )

    if new_rows:
        await db.payments.insert_many(new_rows)
    return {"created": len(new_rows)}


# YEAR — the full payment table for a student + year, with totals.
@router.get("/year", response_model=PaymentYearOut)
async def get_year(
    student_id: str,
    year: int,
    current_user: dict = Depends(require_role("management", "teacher", "student")),
):
    # Access check (raises 403 if this user can't see this student).
    await assert_can_access_student(current_user, student_id)

    rows = (
        await db.payments.find(
            {
                "student_id": student_id,
                "year": year,
            }
        )
        .sort("month", 1)
        .to_list(length=12)
    )

    out_rows = [to_out(r) for r in rows]
    all_settled = len(out_rows) == 12 and all(r.paid for r in out_rows)
    total_paid = sum(r.amount or 0 for r in out_rows)
    total_makeup = sum(r.make_up_classes_count for r in out_rows)

    return PaymentYearOut(
        year=year,
        all_settled=all_settled,
        total_paid=total_paid,
        total_makeup_classes=total_makeup,
        rows=out_rows,
    )


# UPDATE — management fills in a month's payment.
@router.put(
    "/{payment_id}",
    response_model=PaymentOut,
    dependencies=[Depends(require_role("management"))],
)
async def update_payment(payment_id: str, payload: PaymentUpdate):
    _id = parse_object_id(payment_id)

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await db.payments.update_one({"_id": _id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Payment row not found")

    updated = await db.payments.find_one({"_id": _id})
    assert updated is not None
    return to_out(updated)
