"""
상태머신 - Phase 전이 테이블 (v2.2)

책임:
- PHASE_TRANSITIONS: 현재 phase → 다음 phase 매핑
- ROUND_START_PHASE: 라운드별 시작 phase 매핑
- get_next_phase(): 다음 phase 반환 (None 안전장치 포함)

핵심 원칙:
- Agent1은 Round 1에서만 호출 (Round 2/3 제거)
- WAIT_USER에서 사용자 입력 시에만 round 증가
- Unknown phase 시 FINALIZE_DONE 안전 복귀
"""
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# 최대 라운드 수
MAX_ROUNDS = 3


class Phase(str, Enum):
    """모든 가능한 phase 상태"""
    # Round 1
    A1_R1_PLAN = "A1_R1_PLAN"
    A2_R1_CRIT = "A2_R1_CRIT"
    A3_R1_SYN = "A3_R1_SYN"
    V_R1_AUDIT = "V_R1_AUDIT"
    
    # Round 2 (Agent1 없음!)
    A2_R2_CRIT = "A2_R2_CRIT"
    A3_R2_SYN = "A3_R2_SYN"
    V_R2_GATE = "V_R2_GATE"
    
    # Round 3
    A2_R3_LASTCHECK = "A2_R3_LASTCHECK"
    A3_R3_FINAL = "A3_R3_FINAL"
    V_R3_SIGNOFF = "V_R3_SIGNOFF"
    
    # 상태
    WAIT_USER = "WAIT_USER"
    FINALIZE_DONE = "FINALIZE_DONE"


# Phase 전이 테이블
PHASE_TRANSITIONS = {
    # Round 1
    Phase.A1_R1_PLAN: Phase.A2_R1_CRIT,
    Phase.A2_R1_CRIT: Phase.A3_R1_SYN,
    Phase.A3_R1_SYN: Phase.V_R1_AUDIT,
    Phase.V_R1_AUDIT: Phase.WAIT_USER,
    
    # Round 2 (Agent1 없음!)
    Phase.A2_R2_CRIT: Phase.A3_R2_SYN,
    Phase.A3_R2_SYN: Phase.V_R2_GATE,
    Phase.V_R2_GATE: Phase.WAIT_USER,  # or FINALIZE_DONE if No-Go
    
    # Round 3
    Phase.A2_R3_LASTCHECK: Phase.A3_R3_FINAL,
    Phase.A3_R3_FINAL: Phase.V_R3_SIGNOFF,
    Phase.V_R3_SIGNOFF: Phase.FINALIZE_DONE,
}


# 라운드별 시작 phase 매핑
ROUND_START_PHASE = {
    1: Phase.A1_R1_PLAN,
    2: Phase.A2_R2_CRIT,
    3: Phase.A2_R3_LASTCHECK,
}


# Phase별 담당 에이전트 매핑
PHASE_TO_AGENT = {
    Phase.A1_R1_PLAN: "agent1",
    Phase.A2_R1_CRIT: "agent2",
    Phase.A3_R1_SYN: "agent3",
    Phase.V_R1_AUDIT: "verifier",
    Phase.A2_R2_CRIT: "agent2",
    Phase.A3_R2_SYN: "agent3",
    Phase.V_R2_GATE: "verifier",
    Phase.A2_R3_LASTCHECK: "agent2",
    Phase.A3_R3_FINAL: "agent3",
    Phase.V_R3_SIGNOFF: "verifier",
}


# Phase별 라운드 번호
PHASE_TO_ROUND = {
    Phase.A1_R1_PLAN: 1,
    Phase.A2_R1_CRIT: 1,
    Phase.A3_R1_SYN: 1,
    Phase.V_R1_AUDIT: 1,
    Phase.A2_R2_CRIT: 2,
    Phase.A3_R2_SYN: 2,
    Phase.V_R2_GATE: 2,
    Phase.A2_R3_LASTCHECK: 3,
    Phase.A3_R3_FINAL: 3,
    Phase.V_R3_SIGNOFF: 3,
}


def get_next_phase(current_phase: str, gate_status: Optional[str] = None) -> str:
    """
    현재 phase에서 다음 phase를 반환합니다.
    
    Args:
        current_phase: 현재 phase 문자열
        gate_status: Verifier gate 상태 ("Go", "Conditional", "No-Go")
    
    Returns:
        다음 phase 문자열. Unknown이면 FINALIZE_DONE 안전 복귀.
    """
    # No-Go면 즉시 종료
    if gate_status == "No-Go":
        logger.info("Gate status is No-Go, forcing FINALIZE_DONE")
        return Phase.FINALIZE_DONE.value
    
    # Phase enum으로 변환 시도
    try:
        phase_enum = Phase(current_phase)
    except ValueError:
        logger.error(f"Unknown phase: {current_phase}, forcing FINALIZE_DONE")
        return Phase.FINALIZE_DONE.value
    
    # 전이 테이블에서 다음 phase 조회
    next_phase = PHASE_TRANSITIONS.get(phase_enum)
    
    if next_phase is None:
        logger.error(f"No transition for phase: {current_phase}, forcing FINALIZE_DONE")
        return Phase.FINALIZE_DONE.value
    
    return next_phase.value


def get_round_start_phase(round_number: int) -> Optional[str]:
    """
    라운드 시작 phase를 반환합니다.
    
    Args:
        round_number: 라운드 번호 (1, 2, 3)
    
    Returns:
        해당 라운드의 시작 phase. 범위 초과시 None.
    """
    phase = ROUND_START_PHASE.get(round_number)
    return phase.value if phase else None


def get_agent_for_phase(phase: str) -> Optional[str]:
    """해당 phase를 담당하는 에이전트 이름을 반환합니다."""
    try:
        phase_enum = Phase(phase)
        return PHASE_TO_AGENT.get(phase_enum)
    except ValueError:
        return None


def get_round_for_phase(phase: str) -> Optional[int]:
    """해당 phase가 속한 라운드 번호를 반환합니다."""
    try:
        phase_enum = Phase(phase)
        return PHASE_TO_ROUND.get(phase_enum)
    except ValueError:
        return None


def is_wait_user_phase(phase: str) -> bool:
    """WAIT_USER phase인지 확인"""
    return phase == Phase.WAIT_USER.value


def is_final_phase(phase: str) -> bool:
    """FINALIZE_DONE phase인지 확인"""
    return phase == Phase.FINALIZE_DONE.value


class StateMachine:
    """
    세션 상태 머신
    
    - 라운드/턴 전이 관리
    - 동시성 제어 (세션별 락)
    - 취소 토큰 관리
    """
    
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}
        self._abort_events: Dict[str, asyncio.Event] = {}
        self._request_cache: Dict[str, Dict[str, str]] = {}  # 아이들포턴시
        self._input_buffers: Dict[str, str] = {}  # 입력 버퍼
    
    def get_or_create_lock(self, session_id: str) -> asyncio.Lock:
        """세션 락 (없으면 생성)"""
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()
        return self._locks[session_id]
    
    def is_aborted(self, session_id: str) -> bool:
        """취소 여부 확인"""
        event = self._abort_events.get(session_id)
        return event.is_set() if event else False
    
    def abort_session(self, session_id: str):
        """세션 취소"""
        if session_id not in self._abort_events:
            self._abort_events[session_id] = asyncio.Event()
        self._abort_events[session_id].set()
    
    def clear_abort(self, session_id: str):
        """취소 상태 초기화"""
        if session_id in self._abort_events:
            self._abort_events[session_id].clear()
    
    # 아이들포턴시: 같은 request_id면 캐시 반환
    def get_cached_response(self, session_id: str, request_id: str) -> Optional[str]:
        """캐시된 응답 반환 (아이들포턴시)"""
        cache = self._request_cache.get(session_id, {})
        return cache.get(request_id)
    
    def cache_response(self, session_id: str, request_id: str, response: str):
        """응답 캐시 저장"""
        if session_id not in self._request_cache:
            self._request_cache[session_id] = {}
        self._request_cache[session_id][request_id] = response
    
    # 입력 버퍼 (마지막 입력만 반영)
    def buffer_input(self, session_id: str, user_input: str):
        """입력 버퍼에 저장 (마지막 입력만 유지)"""
        self._input_buffers[session_id] = user_input
    
    def get_buffered_input(self, session_id: str) -> Optional[str]:
        """버퍼된 입력 반환 및 삭제"""
        return self._input_buffers.pop(session_id, None)


# 싱글톤 인스턴스
state_machine = StateMachine()
