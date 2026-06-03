from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router

app = FastAPI(title="Travel Mate Agent API")

# ==========================================
# CORS 미들웨어 설정 (Local Development 용)
# ==========================================
# 프론트엔드(예: http://localhost:5173)와 백엔드(http://localhost:8000)의 
# 포트가 서로 다르기 때문에, 브라우저의 자원 공유 차단(CORS)을 해제해 주어야 합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 로컬 개발 단계이므로 모든 도메인에서의 접근을 허용합니다.
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, OPTIONS 등 모든 HTTP 메서드 허용
    allow_headers=["*"],  # Content-Type 등 모든 헤더 허용
)

# API 라우터 등록 
# 모든 게임 및 대화 관련 API는 자동으로 "/api" 접두사가 붙습니다. (예: /api/chat)
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "message": "Travel Mate Agent API가 정상 작동 중입니다. 프론트엔드 개발 시 /api/chat 엔드포인트를 호출하세요."
    }