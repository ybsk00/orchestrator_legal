"""
Vercel Python Function 엔트리포인트

기존 backend/main.py의 FastAPI app을 Vercel에서 인식할 수 있도록 노출
"""
import sys
from pathlib import Path

# backend 패키지를 Python 경로에 추가
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# FastAPI 앱 임포트 및 노출
from main import app

# Vercel은 이 app 객체를 인식하여 Function으로 실행
