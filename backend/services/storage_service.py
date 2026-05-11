import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

_BASE = Path(__file__).parent.parent

DATA_FILE = (
    Path("/tmp/expenses.json")
    if os.getenv("VERCEL")
    else _BASE / "data" / "expenses.json"
)


def _ensure_file() -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def load_expenses() -> list:
    _ensure_file()
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_expenses(data: list) -> None:
    _ensure_file()
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_expense(item: dict) -> dict:
    item = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        **item,
    }
    expenses = load_expenses()
    expenses.append(item)
    save_expenses(expenses)
    return item
