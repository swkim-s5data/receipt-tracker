from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.routers import upload, expenses, summary

load_dotenv()

app = FastAPI(
    title="Receipt Expense Tracker API",
    description="영수증 OCR 기반 지출 관리 앱 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")
app.include_router(summary.router, prefix="/api")


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "receipt-expense-tracker"}
