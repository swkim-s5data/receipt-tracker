# CLAUDE.md

이 파일은 Claude Code (claude.ai/code)가 이 저장소에서 작업할 때 참고하는 가이드입니다.

## 프로젝트 개요

영수증 지출 관리 앱 — 사용자가 영수증 이미지/PDF를 업로드하면 AI가 자동으로 지출 데이터(가게명, 날짜, 품목, 합계)를 추출하는 웹 애플리케이션. DB 미사용, JSON 파일 기반 저장.

**현재 상태**: 기획 단계. 소스 코드 없음. PRD(`PRD_영수증_지출관리앱.md`)와 프로그램 개요서(`프로그램개요서_영수증_지출관리앱_v2.md`)가 권위 있는 명세 문서입니다.

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| 프론트엔드 | React 18 + Vite 5 + TailwindCSS 3 + Axios |
| 백엔드 | Python FastAPI 0.111 + Uvicorn |
| LLM 오케스트레이션 | LangChain 0.2 + `langchain-upstage` 0.1 |
| OCR API | Upstage Document Parse API (`/v1/document-ai/document-parse`) — 모델: `document-parse-260128` |
| JSON 구조화 LLM | Upstage `solar-pro` (Chat Completions API) |
| 이미지 처리 | Pillow (JPG/PNG 전처리), PDF는 API 직접 전송 (pdf2image 불필요) |
| 데이터 저장 | `backend/data/expenses.json` (누적 추가 JSON 배열) |
| 배포 | Vercel (프론트엔드 정적 + 백엔드 서버리스, Mangum 사용) |

---

## 디렉토리 구조 (목표)

```
receipt-tracker/
├── frontend/
│   ├── src/
│   │   ├── pages/         # Dashboard.jsx, UploadPage.jsx, ExpenseDetail.jsx
│   │   ├── components/    # DropZone, ParsePreview, ExpenseCard, SummaryCard,
│   │   │                  # FilterBar, Badge, Modal, Toast, Header, ProgressBar
│   │   └── api/
│   │       └── axios.js   # Axios 인스턴스 — baseURL은 VITE_API_BASE_URL에서 주입
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── main.py            # FastAPI 앱: CORS 설정 + 라우터 등록
│   ├── routers/
│   │   ├── upload.py      # POST /api/upload
│   │   ├── expenses.py    # GET/DELETE/PUT /api/expenses
│   │   └── summary.py     # GET /api/summary
│   ├── services/
│   │   ├── ocr_service.py     # LangChain Chain + Upstage 호출 로직
│   │   └── storage_service.py # expenses.json 읽기/쓰기 헬퍼
│   ├── data/
│   │   └── expenses.json
│   └── requirements.txt
└── vercel.json
```

---

## 개발 명령어

### 백엔드
```bash
# 저장소 루트에서 — FastAPI 개발 서버 실행
uvicorn backend.main:app --reload

# Swagger UI: http://localhost:8000/docs
```

### 프론트엔드
```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build
```

---

## 환경변수

| 변수명 | 사용 위치 | 설명 |
|--------|----------|------|
| `UPSTAGE_API_KEY` | 백엔드 | OCR 호출에 필수. 로컬은 `.env`, 프로덕션은 Vercel 환경변수에 등록 |
| `VITE_API_BASE_URL` | 프론트엔드 빌드 | 기본값 `http://localhost:8000`. Vercel 배포 시 `.env.production`에서 `""`(빈값)으로 설정하여 동일 도메인 상대 경로 사용 |
| `DATA_FILE_PATH` | 백엔드 | `VERCEL=1` 감지 시 자동으로 `/tmp/expenses.json` 사용 |

---

## 아키텍처

### OCR 처리 흐름 (2단계 파이프라인)

> Phase 0 검증(2026-05-11)에서 확인된 실제 동작 방식. PRD 원안의 `document-digitization-vision` 모델은 존재하지 않음.

1. 프론트엔드가 `multipart/form-data`로 `POST /api/upload` 호출
2. 백엔드에서 파일 형식(JPG/PNG/PDF)과 크기(10MB 이하) 검증
3. **[1단계]** `ocr_service.py`가 Upstage Document Parse API(`/v1/document-ai/document-parse`)에 파일 직접 전송 → HTML 구조화 텍스트 반환 (모델: `document-parse-260128`)
4. **[2단계]** HTML 텍스트를 `solar-pro` (Chat Completions)에 전달 → LangChain `JsonOutputParser`로 JSON 스키마 추출
5. 구조화된 JSON을 `expenses.json`에 append 저장하고 응답으로 반환
6. 프론트엔드의 `ParsePreview`에서 사용자가 내용을 확인·수정 후 최종 저장

**핵심 주의사항**: `solar-pro2`는 Vision(이미지 입력) 미지원. PDF/이미지 모두 Document Parse API에 직접 전송해야 함.

### 데이터 스키마 (주요 필드)
```json
{
  "id": "uuid-v4",
  "store_name": "string",
  "receipt_date": "YYYY-MM-DD",
  "category": "식료품|외식|교통|쇼핑|의료|기타",
  "items": [{ "name": "", "quantity": 0, "unit_price": 0, "total_price": 0 }],
  "total_amount": 0,
  "payment_method": "string|null"
}
```

### Vercel 서버리스 제약사항
- `/tmp` 디렉토리 사용 가능 (최대 500MB). 단, 요청 간 파일 영속성 없음.
- `VERCEL=1` 환경변수로 감지하여 데이터 파일 경로를 `/tmp/expenses.json`으로 자동 전환.
- Poppler 같은 시스템 바이너리는 Vercel 서버리스에서 사용 불가 → Document Parse API 직접 전송으로 해결됨.
- 프론트엔드에서는 `localStorage`를 병행 저장소로 사용하여 서버리스 데이터 손실에 대응.
- FastAPI는 Mangum 래핑 없이도 Vercel 서버리스 네이티브 지원 (`pyproject.toml`의 `[tool.vercel]` 섹션으로 설정).

### API 엔드포인트
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/upload` | 영수증 업로드 → OCR 파싱 → 구조화 JSON 반환 |
| GET | `/api/expenses` | 전체 지출 목록 조회. `from`/`to` 쿼리 파라미터로 날짜 필터링 (YYYY-MM-DD) |
| DELETE | `/api/expenses/{id}` | UUID로 항목 삭제. 없으면 404 반환 |
| PUT | `/api/expenses/{id}` | UUID로 항목 부분 수정 |
| GET | `/api/summary` | 총합계 + 카테고리별 통계. `month` 파라미터로 월별 필터 (YYYY-MM) |

---

## UI/스타일 규칙

- **스타일**: TailwindCSS만 사용. 커스텀 애니메이션이 필요한 경우에만 CSS 파일 허용.
- **주요 색상**: CTA 버튼에 `indigo-600` / `indigo-700` 사용.
- **폰트**: Pretendard CDN → Noto Sans KR → 시스템 sans-serif 순으로 폴백.
- **Toast**: `fixed bottom-4 right-4`, 3초 자동 소멸, 동시에 하나만 표시.
- **커스텀 키프레임** (`slide-up`, `scale-in`, `fade-in`)은 `tailwind.config.js`에 선언.
- **레이아웃**: `max-w-4xl mx-auto px-4`, 반응형 그리드 `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`.

## 오류 처리 규칙

- 4xx 오류 → 노란 Toast; 5xx 오류 → 빨간 Toast + 재시도 버튼.
- 비동기 작업 중에는 제출 버튼을 `opacity-50 cursor-not-allowed`로 비활성화.
- 파일 형식·크기 검증은 클라이언트와 서버 양쪽에서 모두 수행.
- OCR 실패 → 빨간 인라인 배너 + "다시 시도" 버튼 표시. 무음 실패 처리 금지.

---

## Phase 0 사전 검증 결과 (2026-05-11 완료)

| 항목 | 결과 | 비고 |
|------|------|------|
| Upstage API Key | ✅ 유효 | `solar-pro2-251215` 200 OK 확인 |
| pdf2image + Poppler | ✅ 로컬 동작 | Poppler `C:\poppler\poppler-24.08.0\Library\bin`. Vercel에서는 불필요 (Document Parse API 직접 전송) |
| Vercel `/tmp` | ✅ 사용 가능 | 500MB, 단 요청 간 비영속. Poppler 바이너리 사용 불가 |
| OCR API | ✅ 확인 완료 | `document-digitization-vision` 존재 안 함. 실제: Document Parse API (`/v1/document-ai/document-parse`), 모델 `document-parse-260128` |
| Vite 환경변수 | ✅ 표준 동작 | `VITE_` 접두사 → `import.meta.env.VITE_*`로 프로덕션 빌드에 주입 |

### Source Code가 변경되거나 라이브러리 버전이 변경되면 반드시 @PRD_영수증_지출관리앱.md 같이 업데이트 하고, 완료 기준의 Check Box에 완료된 사항들도 모두 체크표시 하세요.