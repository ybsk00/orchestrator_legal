"""
FastAPI 앱 엔트리포인트
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(
    title="3 에이전트 오케스트레이터",
    description="Google Gemini 3 Pro를 활용한 토론형 의사결정 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "오케스트레이터 API 서버 가동 중"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
