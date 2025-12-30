"""
기본 에이전트 클래스 및 Gemini 클라이언트

핵심 보완사항 반영:
- 2-step 방식: 스트리밍(UI용) + JSON(저장용) 분리
- 재시도 로직
"""
import json
import os
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Tuple, Callable, Optional, List
from tenacity import retry, stop_after_attempt, wait_exponential

from config import GEMINI_API_KEY, GEMINI_MODEL

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Google Generative AI 임포트 (설치 필요)
try:
    from google import genai
    from google.genai import types
    logger.info("[GeminiClient] google.genai 모듈 임포트 성공")
except ImportError:
    genai = None
    types = None
    logger.error("[GeminiClient] google.genai 모듈 임포트 실패")


class GeminiClient:
    """Google Gemini API 클라이언트 래퍼"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            
            # API 키 확인 (GEMINI_API_KEY 또는 GOOGLE_API_KEY)
            api_key = GEMINI_API_KEY or os.environ.get("GOOGLE_API_KEY")
            
            logger.info(f"[GeminiClient] genai 모듈: {genai is not None}")
            logger.info(f"[GeminiClient] GEMINI_API_KEY 설정됨: {bool(GEMINI_API_KEY)}")
            logger.info(f"[GeminiClient] GOOGLE_API_KEY 설정됨: {bool(os.environ.get('GOOGLE_API_KEY'))}")
            logger.info(f"[GeminiClient] 사용할 API 키 존재: {bool(api_key)}")
            
            if genai and api_key:
                try:
                    cls._instance.client = genai.Client(api_key=api_key)
                    logger.info(f"[GeminiClient] 클라이언트 초기화 성공, 모델: {GEMINI_MODEL}")
                except Exception as e:
                    logger.error(f"[GeminiClient] 클라이언트 초기화 실패: {e}")
                    cls._instance.client = None
            elif genai:
                # API 키 없이 시도 (GOOGLE_API_KEY 환경변수 자동 감지)
                try:
                    cls._instance.client = genai.Client()
                    logger.info(f"[GeminiClient] 클라이언트 초기화 성공 (환경변수 자동 감지)")
                except Exception as e:
                    logger.error(f"[GeminiClient] 클라이언트 초기화 실패: {e}")
                    cls._instance.client = None
            else:
                logger.error("[GeminiClient] genai 모듈이 없어서 클라이언트 초기화 불가")
                cls._instance.client = None
                
        return cls._instance
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=5, max=60)
    )
    async def generate_stream(
        self,
        system_prompt: str,
        messages: List[dict],
        user_message: str
    ) -> AsyncGenerator[str, None]:
        """
        스트리밍 응답 생성 (UI 표시용)
        google-genai SDK의 models.generate_content_stream() 사용
        """
        if not self.client:
            yield "[Gemini API 클라이언트가 초기화되지 않았습니다]"
            return
        
        # 대화 히스토리 + 현재 메시지를 포함한 전체 컨텐츠 구성
        contents = []
        
        # 시스템 프롬프트를 첫 번째 user 메시지로 추가
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"[시스템 지시사항]\n{system_prompt}"}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "네, 지시사항을 이해했습니다. 해당 역할을 수행하겠습니다."}]
            })
        
        # 대화 히스토리 추가
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        
        # 현재 사용자 메시지 추가
        contents.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })
        
        try:
            logger.info(f"[GeminiClient] Streaming 요청 시작 - model={GEMINI_MODEL}")
            
            # models.generate_content_stream 사용
            response = self.client.models.generate_content_stream(
                model=GEMINI_MODEL,
                contents=contents
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
            logger.info(f"[GeminiClient] Streaming 완료")
        except Exception as e:
            logger.error(f"[GeminiClient] Streaming 오류: {e}")
            yield f"[오류 발생: {str(e)}]"
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=5, max=60)
    )
    async def generate_json(
        self,
        prompt: str,
        json_schema: dict
    ) -> dict:
        """
        구조화된 JSON 응답 생성 (저장용)
        """
        if not self.client:
            return {"error": "Gemini API 클라이언트가 초기화되지 않았습니다"}
        
        try:
            response = await self.client.models.generate_content_async(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": json_schema
                }
            )
            return json.loads(response.text)
        except Exception as e:
            return {"error": str(e)}


class BaseAgent(ABC):
    """
    에이전트 기본 클래스
    
    2-step 방식:
    1. stream_response(): UI 표시용 스트리밍
    2. get_structured_response(): 저장용 JSON
    """
    
    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client
        self._last_full_text = ""
    
    @property
    @abstractmethod
    def role_name(self) -> str:
        """에이전트 역할명"""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """시스템 프롬프트"""
        pass
    
    @abstractmethod
    def get_json_schema(self) -> dict:
        """JSON 출력 스키마"""
        pass
    
    async def stream_response(
        self,
        messages: List[dict],
        user_message: str,
        case_file_summary: str = "",
        category: str = "",
        rubric: str = "",
        steering_block: str = ""
    ) -> AsyncGenerator[str, None]:
        """
        Step 1: 스트리밍 응답 (UI 표시용)
        
        응답 전체를 _last_full_text에 저장
        """
        self._last_full_text = ""
        
        # 프롬프트 구성
        full_prompt = self._build_prompt(
            case_file_summary=case_file_summary,
            category=category,
            rubric=rubric,
            steering_block=steering_block
        )
        
        async for chunk in self.client.generate_stream(
            system_prompt=full_prompt,
            messages=messages,
            user_message=user_message
        ):
            self._last_full_text += chunk
            yield chunk
    
    async def get_structured_response(self) -> dict:
        """
        Step 2: 구조화된 JSON 응답 (저장용)
        
        스트리밍 완료 후 호출하여 JSON 변환
        """
        if not self._last_full_text:
            return {"error": "스트리밍 응답이 없습니다"}
        
        json_prompt = f"""
아래 응답을 지정된 JSON 스키마에 맞게 구조화하세요:

{self._last_full_text}
"""
        
        return await self.client.generate_json(
            prompt=json_prompt,
            json_schema=self.get_json_schema()
        )
    
    def _build_prompt(
        self,
        case_file_summary: str = "",
        category: str = "",
        rubric: str = "",
        steering_block: str = ""
    ) -> str:
        """시스템 프롬프트 구성"""
        prompt = self.system_prompt
        
        # Steering Block 최상단 주입
        if steering_block:
            prompt = f"{steering_block}\n\n{prompt}"
        
        if category:
            prompt = prompt.replace("{{category}}", category)
        if rubric:
            prompt = prompt.replace("{{rubric}}", rubric)
        if case_file_summary:
            prompt = prompt.replace("{{case_file_summary}}", case_file_summary)
        
        return prompt


# 싱글톤 Gemini 클라이언트
gemini_client = GeminiClient()
