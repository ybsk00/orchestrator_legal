"""
세션 모델 및 상태 정의
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class Phase(str, Enum):
    """토론 단계 (라운드 내 5턴)"""
    IDLE = "idle"
    A1_PLAN = "A1_PLAN"           # Agent1: 구현계획/실행방안
    A2_CRIT_1 = "A2_CRIT_1"       # Agent2: 문제점/반대의견
    A3_SYN_1 = "A3_SYN_1"         # Agent3: 절충안/개선방향
    A2_CRIT_2 = "A2_CRIT_2"       # Agent2: 재반박
    A3_SYN_FINAL = "A3_SYN_FINAL" # Agent3: 최종 절충안(라운드 결론)
    VERIFIER_REVIEW = "VERIFIER_REVIEW" # Verifier: 검증 및 정리
    FINALIZING = "finalizing"
    FINALIZED = "finalized"


class SessionStatus(str, Enum):
    """세션 상태"""
    ACTIVE = "active"
    FINALIZING = "finalizing"
    FINALIZED = "finalized"


class Category(str, Enum):
    """토론 카테고리 (4종)"""
    NEWBIZ = "newbiz"       # 신규사업
    MARKETING = "marketing" # 마케팅
    DEV = "dev"             # 개발
    DOMAIN = "domain"       # 영역(운영/기타)


class Session(BaseModel):
    """토론 세션"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: SessionStatus = SessionStatus.ACTIVE
    category: Category
    topic: str
    round_index: int = 0  # 0에서 시작, 새 라운드 시작 시 증가
    phase: Phase = Phase.IDLE
    max_rounds: int = 3
    ended_reason: Optional[str] = None  # "user_stop" | "reached_round_limit"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def can_start_new_round(self) -> bool:
        """새 라운드 시작 가능 여부"""
        return self.round_index < self.max_rounds
    
    def get_next_phase(self) -> Optional[Phase]:
        """현재 phase에서 다음 phase 반환"""
        transitions = {
            Phase.A1_PLAN: Phase.A2_CRIT_1,
            Phase.A2_CRIT_1: Phase.A3_SYN_1,
            Phase.A3_SYN_1: Phase.A2_CRIT_2,
            Phase.A2_CRIT_2: Phase.A3_SYN_FINAL,
            Phase.A3_SYN_FINAL: Phase.VERIFIER_REVIEW,
            Phase.VERIFIER_REVIEW: Phase.IDLE,
        }
        return transitions.get(self.phase)
    
    def get_current_agent(self) -> Optional[str]:
        """현재 phase에 해당하는 에이전트 반환"""
        agent_map = {
            Phase.A1_PLAN: "agent1",
            Phase.A2_CRIT_1: "agent2",
            Phase.A3_SYN_1: "agent3",
            Phase.A2_CRIT_2: "agent2",
            Phase.A3_SYN_FINAL: "agent3",
            Phase.VERIFIER_REVIEW: "verifier",
        }
        return agent_map.get(self.phase)
    
    class Config:
        use_enum_values = True
