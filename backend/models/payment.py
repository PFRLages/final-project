# backend/models/payment.py
from pydantic import BaseModel


# What I send to create the 12 month rows for a student's year.
class GenerateYearRequest(BaseModel):
    student_id: str
    year: int


# What management sends when filling in a month's payment.
class PaymentUpdate(BaseModel):
    payment_date: str | None = None        # "YYYY-MM-DD" the day it was paid
    amount: int | None = None              # in Korean Won
    make_up_classes_count: int | None = None


# One month's payment row.
class PaymentOut(BaseModel):
    id: str
    student_id: str
    month: int
    month_name: str                        # "January"...
    year: int
    period_from: str                       # first day of the month
    period_to: str                         # last day of the month
    payment_date: str | None = None
    amount: int | None = None
    make_up_classes_count: int = 0
    paid: bool                             # true once date + amount are filled


# The whole year: the 12 rows + a few totals.
class PaymentYearOut(BaseModel):
    year: int
    all_settled: bool                      # true when every month is paid
    total_paid: int                        # sum of amounts
    total_makeup_classes: int
    rows: list[PaymentOut]