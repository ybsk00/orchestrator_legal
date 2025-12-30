"""
턴 매니저 - 턴 실행 orchestration (v2.2)

책임:
- 세션별 락으로 동시 실행 방지
- 라운드 내 턴 순차 실행
- state_machine.py의 전이 테이블 활용

변경 (v2.2):
- Agent1은 Round 1에서만 호출
- phase 기반 턴 관리로 전환
- 아이들포턴시 지원
"""
import asyncio
import logging
from typing import Optional, Dict, Callable, Any
from datetime import datetime

from .state_machine import (
    Phase, 
    MAX_ROUNDS, 
    ROUND_START_PHASE,
    get_next_phase, 
    get_agent_for_phase,
    get_round_for_phase,
    get_round_start_phase,
    is_wait_user_phase,
    is_final_phase,
    state_machine
)

logger = logging.getLogger(__name__)


# Phase별 턴 설명 및 글자 수 제한
PHASE_CONFIG = {
    # Round 1
    Phase.A1_R1_PLAN: {"description": "초기 구현 계획 제시 (MVP/KPI 포함)", "max_chars": 600},
    Phase.A2_R1_CRIT: {"description": "핵심 비판 및 리스크 Top 3 지적", "max_chars": 400},
    Phase.A3_R1_SYN: {"description": "1차 절충안 제시", "max_chars": 400},
    Phase.V_R1_AUDIT: {"description": "1차 라운드 검증 및 Round 2 방향 제시", "max_chars": 400},
    
    # Round 2 (Agent1 없음!)
    Phase.A2_R2_CRIT: {"description": "새로운/남은 리스크만 지적 (기존 반복 금지)", "max_chars": 400},
    Phase.A3_R2_SYN: {"description": "2차 절충안 및 결정 초안", "max_chars": 400},
    Phase.V_R2_GATE: {"description": "Gate 판정 (Go/Conditional/No-Go)", "max_chars": 400},
    
    # Round 3
    Phase.A2_R3_LASTCHECK: {"description": "최종 경고 1~2개만", "max_chars": 300},
    Phase.A3_R3_FINAL: {"description": "최종 결정문 작성", "max_chars": 1500},
    Phase.V_R3_SIGNOFF: {"description": "최종 서명 (Approved/Conditional/Rejected)", "max_chars": 500},
}


def get_phase_config(phase: str) -> dict:
    """Phase의 설정(description, max_chars) 반환"""
    try:
        phase_enum = Phase(phase)
        return PHASE_CONFIG.get(phase_enum, {"description": "unknown", "max_chars": 300})
    except ValueError:
        return {"description": "unknown", "max_chars": 300}


class TurnManager:
    """
    턴 매니저 (v2.2)
    
    - phase 기반 턴 관리
    - state_machine과 연동
    - 세션별 락으로 동시 실행 방지
    """
    
    def __init__(self):
        self._running_sessions: Dict[str, bool] = {}
    
    async def execute_round(
        self, 
        session_id: str,
        current_round: int,
        execute_phase_fn: Callable[[str, str, dict], Any],
        update_session_fn: Callable[[str, dict], Any],
        on_round_end: Optional[Callable[[str, int], Any]] = None
    ) -> str:
        """
        라운드 내 모든 phase를 순차 실행합니다.
        
        Args:
            session_id: 세션 ID
            current_round: 현재 라운드 (1, 2, 3)
            execute_phase_fn: phase 실행 함수 (session_id, phase, config) -> result
            update_session_fn: 세션 업데이트 함수 (session_id, updates)
            on_round_end: 라운드 종료 콜백
        
        Returns:
            마지막 phase 또는 "WAIT_USER"/"FINALIZE_DONE"
        """
        lock = state_machine.get_or_create_lock(session_id)
        
        async with lock:
            # 이미 실행 중인지 확인
            if self._running_sessions.get(session_id):
                logger.warning(f"Session {session_id} is already running")
                return "ALREADY_RUNNING"
            
            self._running_sessions[session_id] = True
            
            try:
                # 라운드 시작 phase 결정
                start_phase = get_round_start_phase(current_round)
                if not start_phase:
                    logger.error(f"Invalid round: {current_round}")
                    return Phase.FINALIZE_DONE.value
                
                phase = start_phase
                gate_status = None
                
                # 라운드 내 phase 순차 실행
                while not is_wait_user_phase(phase) and not is_final_phase(phase):
                    # 취소 확인
                    if state_machine.is_aborted(session_id):
                        logger.info(f"Session {session_id} aborted")
                        return Phase.FINALIZE_DONE.value
                    
                    # phase 설정 가져오기
                    config = get_phase_config(phase)
                    agent = get_agent_for_phase(phase)
                    
                    logger.info(f"[TurnManager] Executing phase={phase}, agent={agent}")
                    
                    # 세션 상태 업데이트
                    await update_session_fn(session_id, {
                        "phase": phase,
                        "round_index": current_round
                    })
                    
                    # phase 실행
                    result = await execute_phase_fn(session_id, phase, config)
                    
                    # Verifier gate 결과 추출
                    if "V_R2_GATE" in phase or "V_R3_SIGNOFF" in phase:
                        gate_status = self._extract_gate_status(result)
                    
                    # 다음 phase로 전이
                    phase = get_next_phase(phase, gate_status)
                
                # 라운드 종료
                logger.info(f"[TurnManager] Round {current_round} ended, phase={phase}")
                
                # 세션 상태 업데이트
                await update_session_fn(session_id, {"phase": phase})
                
                # 콜백 호출
                if on_round_end:
                    await on_round_end(session_id, current_round)
                
                return phase
                
            finally:
                self._running_sessions[session_id] = False
    
    def _extract_gate_status(self, result: Any) -> Optional[str]:
        """Verifier 응답에서 gate_status 추출"""
        if isinstance(result, dict):
            return result.get("gate_status")
        
        # 텍스트에서 추출 시도
        if isinstance(result, str):
            result_lower = result.lower()
            if "no-go" in result_lower or "no go" in result_lower:
                return "No-Go"
            elif "conditional" in result_lower:
                return "Conditional"
            elif "approved" in result_lower or "go" in result_lower:
                return "Go"
        
        return None
    
    def is_running(self, session_id: str) -> bool:
        """세션이 현재 실행 중인지 확인"""
        return self._running_sessions.get(session_id, False)


# 싱글톤 인스턴스
turn_manager = TurnManager()
