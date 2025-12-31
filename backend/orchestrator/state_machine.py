"""
상태머신 - Phase 전이 테이블 (v2.2 + Legal v1.1)

책임:
- PHASE_TRANSITIONS: 현재 phase → 다음 phase 매핑
- ROUND_START_PHASE: 라운드별 시작 phase 매핑
- get_next_phase(): 다음 phase 반환 (None 안전장치 포함)

핵심 원칙:
- Agent1은 Round 1에서만 호출 (Round 2/3 제거)
- WAIT_USER에서 사용자 입력 시에만 round 증가
- Unknown phase 시 FINALIZE_DONE 안전 복귀

법무 시뮬레이션 (v1.1):
- 4인 구성: Judge, Claimant, Opposing, Verifier
- R1: JUDGE_R1_FRAME(프레임만) → Claimant → Opposing → Verifier
- R2/R3: Opposing → Claimant → Judge → Verifier
- 민사 No-Go 시 Round3 건너뛰고 END_GATE로 이동
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
    # === 일반 토론용 Phase (기존) ===
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
    
    # === 법무 시뮬레이션 전용 Phase ===
    # Facts 단계
    FACTS_INTAKE = "FACTS_INTAKE"
    FACTS_STIPULATE = "FACTS_STIPULATE"
    FACTS_GATE = "FACTS_GATE"  # MissingFacts >= 3일 때
    
    # Round 1 (Judge 프레임 선행)
    JUDGE_R1_FRAME = "JUDGE_R1_FRAME"
    CLAIMANT_R1 = "CLAIMANT_R1"
    OPPOSING_R1 = "OPPOSING_R1"
    VERIFIER_R1 = "VERIFIER_R1"
    
    # Round 2 (Opposing 선행)
    OPPOSING_R2 = "OPPOSING_R2"
    CLAIMANT_R2 = "CLAIMANT_R2"
    JUDGE_R2 = "JUDGE_R2"
    VERIFIER_R2 = "VERIFIER_R2"
    
    # Round 3
    OPPOSING_R3 = "OPPOSING_R3"
    CLAIMANT_R3 = "CLAIMANT_R3"
    JUDGE_R3 = "JUDGE_R3"
    VERIFIER_R3 = "VERIFIER_R3"
    
    # === 공통 상태 ===
    WAIT_USER = "WAIT_USER"
    USER_GATE = "USER_GATE"  # 라운드 종료 후 사용자 개입 대기
    END_GATE = "END_GATE"    # 최종 종료 전 대기
    FINALIZE_DONE = "FINALIZE_DONE"

    # === 개발 프로젝트 전용 Phase (v2.1) ===
    # Round 1 (Define)
    PRD_R1 = "PRD_R1"
    UX_R1 = "UX_R1"
    TECH_R1 = "TECH_R1"
    DM_R1 = "DM_R1"
    
    # Round 2 (Risk & Tradeoff)
    TECH_R2 = "TECH_R2"
    UX_R2 = "UX_R2"
    PRD_R2 = "PRD_R2"
    DM_R2 = "DM_R2"
    
    # Round 3 (Commit)
    DM_R3 = "DM_R3"
    TECH_R3 = "TECH_R3"
    UX_R3 = "UX_R3"
    VERIFIER_R3 = "VERIFIER_R3"


# ==========================================
# 일반 토론용 전이 테이블 (기존)
# ==========================================
PHASE_TRANSITIONS = {
    # Round 1
    Phase.A1_R1_PLAN: Phase.A2_R1_CRIT,
    Phase.A2_R1_CRIT: Phase.A3_R1_SYN,
    Phase.A3_R1_SYN: Phase.V_R1_AUDIT,
    Phase.V_R1_AUDIT: Phase.USER_GATE,  # Round 1 종료 -> USER_GATE
    
    # Round 2 (Agent1 없음!)
    Phase.A2_R2_CRIT: Phase.A3_R2_SYN,
    Phase.A3_R2_SYN: Phase.V_R2_GATE,
    Phase.V_R2_GATE: Phase.USER_GATE,  # Round 2 종료 -> USER_GATE
    
    # Round 3
    Phase.A2_R3_LASTCHECK: Phase.A3_R3_FINAL,
    Phase.A3_R3_FINAL: Phase.V_R3_SIGNOFF,
    Phase.V_R3_SIGNOFF: Phase.END_GATE,  # Round 3 종료 -> END_GATE
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


# ==========================================
# 법무 시뮬레이션 전용 전이 테이블
# ==========================================
LEGAL_PHASE_TRANSITIONS = {
    # Facts 단계
    Phase.FACTS_INTAKE: Phase.FACTS_STIPULATE,
    Phase.FACTS_STIPULATE: Phase.JUDGE_R1_FRAME,  # or FACTS_GATE if missing >= 3
    Phase.FACTS_GATE: Phase.JUDGE_R1_FRAME,
    
    # Round 1 (Judge 프레임 선행)
    Phase.JUDGE_R1_FRAME: Phase.CLAIMANT_R1,
    Phase.CLAIMANT_R1: Phase.OPPOSING_R1,
    Phase.OPPOSING_R1: Phase.VERIFIER_R1,
    Phase.VERIFIER_R1: Phase.USER_GATE,
    
    # Round 2 (Opposing 선행)
    Phase.OPPOSING_R2: Phase.CLAIMANT_R2,
    Phase.CLAIMANT_R2: Phase.JUDGE_R2,
    Phase.JUDGE_R2: Phase.VERIFIER_R2,
    Phase.VERIFIER_R2: Phase.USER_GATE,  # 민사 No-Go시 END_GATE로 분기
    
    # Round 3
    Phase.OPPOSING_R3: Phase.CLAIMANT_R3,
    Phase.CLAIMANT_R3: Phase.JUDGE_R3,
    Phase.JUDGE_R3: Phase.VERIFIER_R3,
    Phase.VERIFIER_R3: Phase.END_GATE,
}


# 법무 라운드별 시작 phase
LEGAL_ROUND_START_PHASE = {
    1: Phase.JUDGE_R1_FRAME,
    2: Phase.OPPOSING_R2,
    3: Phase.OPPOSING_R3,
}


# 법무 Phase별 담당 에이전트
LEGAL_PHASE_TO_AGENT = {
    Phase.FACTS_INTAKE: "system",
    Phase.FACTS_STIPULATE: "system",
    Phase.FACTS_GATE: "system",
    Phase.JUDGE_R1_FRAME: "judge",
    Phase.CLAIMANT_R1: "claimant",
    Phase.OPPOSING_R1: "opposing",
    Phase.VERIFIER_R1: "verifier",
    Phase.OPPOSING_R2: "opposing",
    Phase.CLAIMANT_R2: "claimant",
    Phase.JUDGE_R2: "judge",
    Phase.VERIFIER_R2: "verifier",
    Phase.OPPOSING_R3: "opposing",
    Phase.CLAIMANT_R3: "claimant",
    Phase.JUDGE_R3: "judge",
    Phase.VERIFIER_R3: "verifier",
}


# 법무 Phase별 라운드 번호
LEGAL_PHASE_TO_ROUND = {
    Phase.FACTS_INTAKE: 0,
    Phase.FACTS_STIPULATE: 0,
    Phase.FACTS_GATE: 0,
    Phase.JUDGE_R1_FRAME: 1,
    Phase.CLAIMANT_R1: 1,
    Phase.OPPOSING_R1: 1,
    Phase.VERIFIER_R1: 1,
    Phase.OPPOSING_R2: 2,
    Phase.CLAIMANT_R2: 2,
    Phase.JUDGE_R2: 2,
    Phase.VERIFIER_R2: 2,
    Phase.OPPOSING_R3: 3,
    Phase.CLAIMANT_R3: 3,
    Phase.JUDGE_R3: 3,
    Phase.VERIFIER_R3: 3,
}


# ==========================================
# 개발 프로젝트 전용 전이 테이블 (v2.1)
# ==========================================
DEV_PROJECT_PHASE_TRANSITIONS = {
    # Round 1: PRD -> UX -> TECH -> DM -> USER_GATE
    Phase.PRD_R1: Phase.UX_R1,
    Phase.UX_R1: Phase.TECH_R1,
    Phase.TECH_R1: Phase.DM_R1,
    Phase.DM_R1: Phase.USER_GATE,
    
    # Round 2: TECH -> UX -> PRD -> DM -> USER_GATE
    Phase.TECH_R2: Phase.UX_R2,
    Phase.UX_R2: Phase.PRD_R2,
    Phase.PRD_R2: Phase.DM_R2,
    Phase.DM_R2: Phase.USER_GATE,
    
    # Round 3: DM -> TECH -> UX -> VERIFIER -> END_GATE
    Phase.DM_R3: Phase.TECH_R3,
    Phase.TECH_R3: Phase.UX_R3,
    Phase.UX_R3: Phase.VERIFIER_R3,
    Phase.VERIFIER_R3: Phase.END_GATE,
}


# 개발 프로젝트 라운드별 시작 phase
DEV_PROJECT_ROUND_START_PHASE = {
    1: Phase.PRD_R1,
    2: Phase.TECH_R2,
    3: Phase.DM_R3,
}


# 개발 프로젝트 Phase별 담당 에이전트
DEV_PROJECT_PHASE_TO_AGENT = {
    Phase.PRD_R1: "prd",
    Phase.UX_R1: "ux",
    Phase.TECH_R1: "tech",
    Phase.DM_R1: "dm",
    Phase.TECH_R2: "tech",
    Phase.UX_R2: "ux",
    Phase.PRD_R2: "prd",
    Phase.DM_R2: "dm",
    Phase.DM_R3: "dm",
    Phase.TECH_R3: "tech",
    Phase.UX_R3: "ux",
    Phase.VERIFIER_R3: "verifier",
}


# 개발 프로젝트 Phase별 라운드 번호
DEV_PROJECT_PHASE_TO_ROUND = {
    Phase.PRD_R1: 1,
    Phase.UX_R1: 1,
    Phase.TECH_R1: 1,
    Phase.DM_R1: 1,
    Phase.TECH_R2: 2,
    Phase.UX_R2: 2,
    Phase.PRD_R2: 2,
    Phase.DM_R2: 2,
    Phase.DM_R3: 3,
    Phase.TECH_R3: 3,
    Phase.UX_R3: 3,
    Phase.VERIFIER_R3: 3,
}


# ==========================================
# 일반 토론용 함수
# ==========================================
def get_next_phase(
    current_phase: str, 
    project_type: str = "general",
    gate_status: Optional[str] = None,
    case_type: Optional[str] = None,
    missing_facts_count: int = 0
) -> str:
    """
    현재 phase에서 다음 phase를 반환합니다. (통합 함수)
    
    Args:
        current_phase: 현재 phase 문자열
        project_type: 프로젝트 유형 ("general", "legal", "dev_project")
        gate_status: Verifier gate 상태
        case_type: 법무 시뮬레이션 사건 유형
        missing_facts_count: 법무 Facts 단계 분기용
    """
    # 법무 시뮬레이션 처리
    if project_type == "legal":
        return get_next_phase_legal(current_phase, case_type, gate_status, missing_facts_count)
        
    # Phase enum 변환
    try:
        phase_enum = Phase(current_phase)
    except ValueError:
        logger.error(f"Unknown phase: {current_phase}, forcing FINALIZE_DONE")
        return Phase.FINALIZE_DONE.value

    # 개발 프로젝트 처리
    if project_type == "dev_project":
        next_phase = DEV_PROJECT_PHASE_TRANSITIONS.get(phase_enum)
        if next_phase is None:
            # USER_GATE나 END_GATE 등 전이가 없는 상태일 수 있음
            if phase_enum in [Phase.USER_GATE, Phase.END_GATE]:
                return phase_enum.value
            logger.error(f"No dev_project transition for phase: {current_phase}, forcing END_GATE")
            return Phase.END_GATE.value
        return next_phase.value

    # 일반 토론 처리 (기본)
    # No-Go면 즉시 종료
    if gate_status == "No-Go":
        logger.info("Gate status is No-Go, forcing FINALIZE_DONE")
        return Phase.FINALIZE_DONE.value
    
    next_phase = PHASE_TRANSITIONS.get(phase_enum)
    
    if next_phase is None:
        logger.error(f"No transition for phase: {current_phase}, forcing FINALIZE_DONE")
        return Phase.FINALIZE_DONE.value
    
    return next_phase.value


def get_round_start_phase(round_number: int, project_type: str = "general") -> Optional[str]:
    """라운드 시작 phase 반환 (프로젝트 타입 지원)"""
    if project_type == "legal":
        return get_legal_round_start_phase(round_number)
    elif project_type == "dev_project":
        phase = DEV_PROJECT_ROUND_START_PHASE.get(round_number)
        return phase.value if phase else None
        
    phase = ROUND_START_PHASE.get(round_number)
    return phase.value if phase else None


def get_agent_for_phase(phase: str) -> Optional[str]:
    """해당 phase를 담당하는 에이전트 이름을 반환합니다."""
    try:
        phase_enum = Phase(phase)
        
        # 1. 일반 토론
        if agent := PHASE_TO_AGENT.get(phase_enum):
            return agent
            
        # 2. 법무 시뮬레이션
        if agent := LEGAL_PHASE_TO_AGENT.get(phase_enum):
            return agent
            
        # 3. 개발 프로젝트
        if agent := DEV_PROJECT_PHASE_TO_AGENT.get(phase_enum):
            return agent
            
        return None
    except ValueError:
        return None


def get_round_for_phase(phase: str) -> Optional[int]:
    """해당 phase가 속한 라운드 번호를 반환합니다."""
    try:
        phase_enum = Phase(phase)
        
        # 1. 일반 토론
        if round_num := PHASE_TO_ROUND.get(phase_enum):
            return round_num
            
        # 2. 법무 시뮬레이션
        if round_num := LEGAL_PHASE_TO_ROUND.get(phase_enum):
            return round_num
            
        # 3. 개발 프로젝트
        if round_num := DEV_PROJECT_PHASE_TO_ROUND.get(phase_enum):
            return round_num
            
        return None
    except ValueError:
        return None


def is_wait_user_phase(phase: str) -> bool:
    """WAIT_USER phase인지 확인"""
    return phase == Phase.WAIT_USER.value


def is_final_phase(phase: str) -> bool:
    """FINALIZE_DONE phase인지 확인"""
    return phase == Phase.FINALIZE_DONE.value


# ==========================================
# 법무 시뮬레이션 전용 함수
# ==========================================
def get_next_phase_legal(
    current_phase: str, 
    case_type: Optional[str] = None,
    gate_status: Optional[str] = None,
    missing_facts_count: int = 0
) -> str:
    """
    법무 시뮬레이션용 다음 phase 반환.
    
    Args:
        current_phase: 현재 phase 문자열
        case_type: 사건 유형 ("criminal" | "civil")
        gate_status: Verifier gate 상태 ("Go", "Conditional", "No-Go")
        missing_facts_count: MissingFactsQuestions 개수 (Facts 단계 분기용)
    
    Returns:
        다음 phase 문자열
    """
    try:
        phase_enum = Phase(current_phase)
    except ValueError:
        logger.error(f"Unknown legal phase: {current_phase}, forcing FINALIZE_DONE")
        return Phase.FINALIZE_DONE.value
    
    # FACTS_STIPULATE에서 missing >= 3 이면 FACTS_GATE로
    if phase_enum == Phase.FACTS_STIPULATE and missing_facts_count >= 3:
        logger.info(f"Missing facts count ({missing_facts_count}) >= 3, routing to FACTS_GATE")
        return Phase.FACTS_GATE.value
    
    # VERIFIER_R2에서 민사 + No-Go면 END_GATE로 (Round3 스킵)
    if phase_enum == Phase.VERIFIER_R2:
        if case_type == "civil" and gate_status == "No-Go":
            logger.info("Civil case No-Go at R2, routing to END_GATE (skip R3)")
            return Phase.END_GATE.value
        return Phase.USER_GATE.value
    
    # 기본 전이 테이블 사용
    next_phase = LEGAL_PHASE_TRANSITIONS.get(phase_enum)
    
    if next_phase is None:
        logger.error(f"No legal transition for phase: {current_phase}, forcing END_GATE")
        return Phase.END_GATE.value
    
    return next_phase.value


def get_legal_round_start_phase(round_number: int) -> Optional[str]:
    """법무 시뮬레이션용 라운드 시작 phase 반환."""
    phase = LEGAL_ROUND_START_PHASE.get(round_number)
    return phase.value if phase else None


def get_legal_agent_for_phase(phase: str) -> Optional[str]:
    """법무 phase를 담당하는 에이전트 반환."""
    try:
        phase_enum = Phase(phase)
        return LEGAL_PHASE_TO_AGENT.get(phase_enum)
    except ValueError:
        return None


def get_legal_round_for_phase(phase: str) -> Optional[int]:
    """법무 phase가 속한 라운드 번호 반환."""
    try:
        phase_enum = Phase(phase)
        return LEGAL_PHASE_TO_ROUND.get(phase_enum)
    except ValueError:
        return None


def is_legal_phase(phase: str) -> bool:
    """법무 시뮬레이션 phase인지 확인."""
    legal_phases = [
        Phase.FACTS_INTAKE.value, Phase.FACTS_STIPULATE.value, Phase.FACTS_GATE.value,
        Phase.JUDGE_R1_FRAME.value, Phase.CLAIMANT_R1.value, Phase.OPPOSING_R1.value, Phase.VERIFIER_R1.value,
        Phase.OPPOSING_R2.value, Phase.CLAIMANT_R2.value, Phase.JUDGE_R2.value, Phase.VERIFIER_R2.value,
        Phase.OPPOSING_R3.value, Phase.CLAIMANT_R3.value, Phase.JUDGE_R3.value, Phase.VERIFIER_R3.value,
    ]
    return phase in legal_phases


def is_dev_project_phase(phase: str) -> bool:
    """개발 프로젝트 phase인지 확인."""
    dev_phases = [
        Phase.PRD_R1.value, Phase.UX_R1.value, Phase.TECH_R1.value, Phase.DM_R1.value,
        Phase.TECH_R2.value, Phase.UX_R2.value, Phase.PRD_R2.value, Phase.DM_R2.value,
        Phase.DM_R3.value, Phase.TECH_R3.value, Phase.UX_R3.value, Phase.VERIFIER_R3.value,
    ]
    return phase in dev_phases


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
