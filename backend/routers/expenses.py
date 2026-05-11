from fastapi import APIRouter, HTTPException
from typing import Optional
from backend.services import storage_service

router = APIRouter(tags=["Expenses"])


@router.get("/expenses")
def list_expenses(from_date: Optional[str] = None, to_date: Optional[str] = None):
    expenses = storage_service.load_expenses()
    if from_date:
        expenses = [e for e in expenses if e.get("receipt_date", "") >= from_date]
    if to_date:
        expenses = [e for e in expenses if e.get("receipt_date", "") <= to_date]
    return expenses


@router.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str):
    expenses = storage_service.load_expenses()
    updated = [e for e in expenses if e.get("id") != expense_id]
    if len(updated) == len(expenses):
        raise HTTPException(status_code=404, detail="해당 지출 항목을 찾을 수 없습니다.")
    storage_service.save_expenses(updated)
    return {"message": "삭제되었습니다."}


@router.put("/expenses/{expense_id}")
def update_expense(expense_id: str, body: dict):
    expenses = storage_service.load_expenses()
    for i, e in enumerate(expenses):
        if e.get("id") == expense_id:
            expenses[i] = {**e, **body, "id": expense_id}
            storage_service.save_expenses(expenses)
            return expenses[i]
    raise HTTPException(status_code=404, detail="해당 지출 항목을 찾을 수 없습니다.")


@router.post("/expenses")
def save_expense(body: dict):
    return storage_service.append_expense(body)
