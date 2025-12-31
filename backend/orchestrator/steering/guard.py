"""
Steering Guard
사용자 입력(SteeringInput)을 검증하여 반영 여부를 결정합니다.
"""
import logging
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from agents.base_agent import gemini_client
from orchestrator.steering.normalizer import SteeringInput

logger = logging.getLogger(__name__)


class SteeringStatus(str, Enum):
    COMMITTED = "committed"  # 반영 확정
    PENDING = "pending"      # 보류 (사용자 확인 필요)
    REJECTED = "rejected"    # 거부 (금지 규칙 위반)


class SteeringResult(BaseModel):
    """검증 결과"""
    status: SteeringStatus
    input_data: SteeringInput
    conflicts: List[str] = []  # 모순/충돌 사유
    questions: List[str] = []  # 확인 질문 (Pending 시)
    reason: Optional[str] = None  # 거부 사유 (Rejected 시)


async def check_steering(input_data: SteeringInput, current_round: int) -> SteeringResult:
    """
    SteeringInput을 검증합니다.
    """
    # 1. 스코프 폭발 검사 (Rule-based)
    if len(input_data.changes) > 3:
        return SteeringResult(
            status=SteeringStatus.PENDING,
            input_data=input_data,
            conflicts=["변경 요청 사항이 너무 많습니다 (3개 초과)."],
            questions=["가장 중요한 변경사항 3가지만 선택해주시겠습니까?", "다음 라운드로 일부를 이월하시겠습니까?"]
        )

    # 2. 금지 규칙 검사 (Rule-based)
    # 예: 개인정보, 보안 위반 등 (여기서는 간단한 예시만)
    blacklist = ["해킹", "불법", "개인정보"]
    for item in input_data.constraints + input_data.changes:
        for word in blacklist:
            if word in item:
                return SteeringResult(
                    status=SteeringStatus.REJECTED,
                    input_data=input_data,
                    reason=f"금지된 키워드가 포함되어 있습니다: {word}"
                )

    # 3. 모순/논리적 충돌 검사 (LLM)
    # Focus, Goal, Constraints 간의 충돌 여부 확인
    prompt = f"""
    다음 프로젝트 기획 요구사항의 논리적 모순을 검사하세요.
    
    [요구사항]
    Focus: {input_data.focus}
    Goal: {input_data.goal}
    Constraints: {input_data.constraints}
    Changes: {input_data.changes}
    Current Round: {current_round}
    
    [검사 기준]
    1. Goal과 Constraints가 상충하는가? (예: "최고 품질" vs "1일 내 개발")
    2. Focus와 Changes가 상충하는가? (예: "MVP 집중" vs "대규모 기능 추가")
    3. 라운드에 맞지 않는 요구인가? (예: R1에서 구체적 구현 상세 요구)
    
    [출력 스키마 (JSON)]
    {{
        "has_conflict": boolean,
        "conflict_reasons": ["이유1", "이유2"],
        "clarification_questions": ["질문1", "질문2"]
    }}
    """
    
    json_schema = {
        "type": "object",
        "properties": {
            "has_conflict": {"type": "boolean"},
            "conflict_reasons": {"type": "array", "items": {"type": "string"}},
            "clarification_questions": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["has_conflict"]
    }
    
    try:
        result = await gemini_client.generate_json(prompt, json_schema)
        
        if result.get("has_conflict"):
            return SteeringResult(
                status=SteeringStatus.PENDING,
                input_data=input_data,
                conflicts=result.get("conflict_reasons", []),
                questions=result.get("clarification_questions", [])
            )
            
    except Exception as e:
        logger.error(f"Guard LLM error: {e}")
        # LLM 에러 시 안전하게 Pass (또는 Pending)
        pass
        
    # 통과
    return SteeringResult(
        status=SteeringStatus.COMMITTED,
        input_data=input_data
    )
