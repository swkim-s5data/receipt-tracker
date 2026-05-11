import base64
import json
import os
import httpx
from langchain_upstage import ChatUpstage
from langchain_core.messages import HumanMessage, SystemMessage

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")
DOCUMENT_PARSE_URL = "https://api.upstage.ai/v1/document-ai/document-parse"

SYSTEM_PROMPT = """당신은 영수증 OCR 전문가입니다.
아래 JSON 형식으로만 응답하세요. 마크다운 코드 블록이나 다른 텍스트는 포함하지 마세요.

{
  "store_name": "string",
  "receipt_date": "YYYY-MM-DD",
  "receipt_time": "HH:MM or null",
  "category": "식료품|외식|교통|쇼핑|의료|기타",
  "items": [{"name": "string", "quantity": 0, "unit_price": 0, "total_price": 0}],
  "subtotal": 0,
  "discount": 0,
  "tax": 0,
  "total_amount": 0,
  "payment_method": "string or null"
}"""


async def _call_document_parse(file_bytes: bytes, content_type: str) -> str:
    """Upstage Document Parse API 호출 → HTML 텍스트 반환"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            DOCUMENT_PARSE_URL,
            headers={"Authorization": f"Bearer {UPSTAGE_API_KEY}"},
            files={"document": ("receipt", file_bytes, content_type)},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("content", {}).get("html", "")


def _call_solar_pro(html_text: str) -> dict:
    """solar-pro로 HTML → JSON 구조화"""
    llm = ChatUpstage(model="solar-pro", api_key=UPSTAGE_API_KEY)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"다음 영수증 텍스트를 JSON으로 변환해줘:\n{html_text}"),
    ]
    response = llm.invoke(messages)
    raw = response.content.strip()
    # 마크다운 코드 블록 제거
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


async def parse_receipt(file_bytes: bytes, content_type: str) -> dict:
    """2단계 파이프라인: Document Parse → solar-pro JSON 구조화"""
    html_text = await _call_document_parse(file_bytes, content_type)
    return _call_solar_pro(html_text)
