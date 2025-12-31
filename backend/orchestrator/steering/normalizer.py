"""
Steering Normalizer
사용자 입력을 구조화된 Steering Input으로 변환합니다.
"""
import logging
from typing import List, Optional
from pydantic import BaseModel, Field

from agents.base_agent import gemini_client

logger = logging.getLogger(__name__)


class SteeringInput(BaseModel):
    """구조화된 사용자 입력"""
    focus: str = Field(..., description="토론의 핵심 주제 (예: MVP범위, 기술리스크, 일정단축)")
    goal: str = Field(..., description="토론의 목표 (예: speed, quality, cost, learning)")
    constraints: List[str] = Field(default_factory=list, description="제약사항 목록 (예: 2주내, 1인개발)")
    changes: List[str] = Field(default_factory=list, description="변경 요청 사항 (add/remove/reprioritize)")
    
    # 원문 포함 (디버깅용)
    raw_text: Optional[str] = None


async def normalize_input(user_input: str) -> SteeringInput:
    """
    사용자 입력을 구조화된 SteeringInput으로 변환합니다.
    LLM을 사용하여 자연어를 정규화합니다.
    """
    if not user_input or not user_input.strip():
        return SteeringInput(focus="General", goal="Quality", raw_text=user_input)

    prompt = f"""
    당신은 개발 프로젝트 기획 회의의 서기입니다.
    사용자의 발언을 분석하여 다음 4가지 항목으로 구조화하세요.
    
    [입력 텍스트]
    "{user_input}"
    
    [출력 스키마 (JSON)]
    {{
        "focus": "토론의 핵심 주제 (MVP범위, 기술리스크, UX전환, 일정단축, 안정성, 비용절감, 데이터/추적 중 택1 또는 직접 요약)",
        "goal": "토론의 목표 (speed, quality, cost, learning 중 택1)",
        "constraints": ["제약사항1", "제약사항2", ...],
        "changes": ["변경사항1", "변경사항2", ...]
    }}
    
    규칙:
    1. focus와 goal은 가능한 예시 중에서 선택하되, 없으면 가장 적절한 단어로 요약하세요.
    2. constraints는 명시적인 제약조건(시간, 인력, 기술 등)만 추출하세요.
    3. changes는 기능 추가/삭제/우선순위 변경 요청을 추출하세요.
    4. 불명확한 내용은 제외하고 확실한 내용만 포함하세요.
    """
    
    json_schema = {
        "type": "object",
        "properties": {
            "focus": {"type": "string"},
            "goal": {"type": "string"},
            "constraints": {"type": "array", "items": {"type": "string"}},
            "changes": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["focus", "goal", "constraints", "changes"]
    }
    
    try:
        result = await gemini_client.generate_json(prompt, json_schema)
        
        if "error" in result:
            logger.error(f"Normalizer LLM error: {result['error']}")
            # Fallback
            return SteeringInput(
                focus="General", 
                goal="Quality", 
                raw_text=user_input
            )
            
        return SteeringInput(
            focus=result.get("focus", "General"),
            goal=result.get("goal", "Quality"),
            constraints=result.get("constraints", []),
            changes=result.get("changes", []),
            raw_text=user_input
        )
        
    except Exception as e:
        logger.error(f"Normalizer exception: {e}")
        return SteeringInput(focus="General", goal="Quality", raw_text=user_input)
