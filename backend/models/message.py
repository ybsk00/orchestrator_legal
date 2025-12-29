"""
메시지 모델
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class MessageRole(str, Enum):
    """메시지 발신자 역할"""
    USER = "user"
    AGENT1 = "agent1"
    AGENT2 = "agent2"
    AGENT3 = "agent3"
    SYSTEM = "system"


class Message(BaseModel):
    """채팅 메시지"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: MessageRole
    round_index: int
    phase: str
    content: str  # 채팅 본문
    reasoning_summary: List[str] = Field(default_factory=list)  # 논리 요약 bullets
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class AgentResponse(BaseModel):
    """에이전트 응답 구조 (JSON 스키마)"""
    conclusion: str  # 결론 1~2문장
    reasoning_summary: List[str]  # 논리 요약 3~6개 bullet
    assumptions: Optional[List[str]] = None  # 가정/제약
    next_actions: List[str] = Field(default_factory=list)  # 다음 액션 체크리스트


class Agent2Response(AgentResponse):
    """Agent2(반박/리스크) 전용 응답"""
    failure_scenarios: List[str] = Field(default_factory=list)
    verification_experiments: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)


class Agent3Response(AgentResponse):
    """Agent3(절충안) 전용 응답"""
    critique_responses: List[dict] = Field(default_factory=list)  # {"critique", "response_type", "action"}
    improved_plan: Optional[str] = None
    plan_b: Optional[str] = None
    two_week_validation: List[str] = Field(default_factory=list)
