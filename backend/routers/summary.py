from fastapi import APIRouter
from typing import Optional
from backend.services import storage_service

router = APIRouter(tags=["Summary"])


@router.get("/summary")
def get_summary(month: Optional[str] = None):
    expenses = storage_service.load_expenses()

    if month:
        expenses = [e for e in expenses if e.get("receipt_date", "").startswith(month)]

    from datetime import date
    current_month = date.today().strftime("%Y-%m")
    this_month = [e for e in storage_service.load_expenses() if e.get("receipt_date", "").startswith(current_month)]

    total_amount = sum(e.get("total_amount", 0) for e in expenses)
    this_month_amount = sum(e.get("total_amount", 0) for e in this_month)

    category_map: dict[str, int] = {}
    for e in expenses:
        cat = e.get("category", "기타")
        category_map[cat] = category_map.get(cat, 0) + e.get("total_amount", 0)

    return {
        "total_amount": total_amount,
        "this_month_amount": this_month_amount,
        "category_summary": [{"category": k, "amount": v} for k, v in category_map.items()],
    }
