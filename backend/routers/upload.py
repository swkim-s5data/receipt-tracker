from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services import ocr_service, storage_service

router = APIRouter(tags=["Upload"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다: {file.content_type}. JPG, PNG, PDF만 허용됩니다.")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기가 10MB를 초과합니다.")

    try:
        parsed = await ocr_service.parse_receipt(file_bytes, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 파싱에 실패했습니다: {str(e)}")

    return parsed
