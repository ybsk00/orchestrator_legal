"""
오케스트레이터 환경 설정
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API 설정
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-pro-preview")

# 오케스트레이터 설정
MAX_ROUNDS = 3  # 최대 라운드 수
CASEFILE_MAX_CHARS = 1200  # CaseFile 요약 최대 길이
SSE_BUFFER_SIZE = 100  # SSE 이벤트 버퍼 크기

# 카테고리 정의
CATEGORIES = ["newbiz", "marketing", "dev", "domain"]
