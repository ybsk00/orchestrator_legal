"""
상태 머신 - 라운드/턴 전이 관리

핵심 보완사항 반영:
- 라운드 증가 로직: start_new_round()에서 round_index 증가
- 동시성 제어: asyncio.Lock으로 세션별 락
- 취소 토큰: _abort_event로 진행 중 작업 취소
"""
import asyncio
from typing import Dict, Optional
from datetime import datetime

from models.session import Session, SessionStatus, Phase


class StateMachine:
    """
    세션 상태 머신
    
    - 라운드/턴 전이 관리
    - 동시성 제어 (세션별 락)
    - 취소 토큰 관리
    """
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._abort_events: Dict[str, asyncio.Event] = {}
    
    def create_session(self, session: Session) -> Session:
        """새 세션 생성"""
        self._sessions[session.id] = session
        self._locks[session.id] = asyncio.Lock()
        self._abort_events[session.id] = asyncio.Event()
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """세션 조회"""
        return self._sessions.get(session_id)
    
    def get_lock(self, session_id: str) -> Optional[asyncio.Lock]:
        """세션 락 조회"""
        return self._locks.get(session_id)
    
    def is_aborted(self, session_id: str) -> bool:
        """취소 여부 확인"""
        event = self._abort_events.get(session_id)
        return event.is_set() if event else False
    
    def start_new_round(self, session_id: str) -> bool:
        """
        새 라운드 시작 (사용자 메시지 수신 시 호출)
        
        Returns:
            True: 라운드 시작 성공
            False: 라운드 제한 도달 → 자동 최종화
        """
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        if session.phase != Phase.IDLE:
            return False  # 진행 중인 라운드가 있음
        
        if not session.can_start_new_round():
            # 3라운드 완료 → 자동 최종화
            session.status = SessionStatus.FINALIZING
            session.phase = Phase.FINALIZING
            session.ended_reason = "reached_round_limit"
            session.updated_at = datetime.utcnow()
            return False
        
        # ⭐ 라운드 증가 (핵심 보완사항)
        session.round_index += 1
        session.phase = Phase.A1_PLAN
        session.updated_at = datetime.utcnow()
        return True
    
    def advance_phase(self, session_id: str) -> Optional[Phase]:
        """
        다음 phase로 진행 (라운드 내 턴 전이)
        
        Returns:
            다음 phase 또는 None (라운드 완료 시 IDLE)
        """
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        next_phase = session.get_next_phase()
        if next_phase:
            session.phase = next_phase
            session.updated_at = datetime.utcnow()
        
        return session.phase
    
    def force_finalize(self, session_id: str) -> bool:
        """
        조기 종료 (사용자 요청)
        
        - 진행 중 작업 취소 신호 발생
        - 상태를 FINALIZING으로 변경
        """
        session = self._sessions.get(session_id)
        abort_event = self._abort_events.get(session_id)
        
        if not session:
            return False
        
        # 취소 신호 발생
        if abort_event:
            abort_event.set()
        
        session.status = SessionStatus.FINALIZING
        session.phase = Phase.FINALIZING
        session.ended_reason = "user_stop"
        session.updated_at = datetime.utcnow()
        return True
    
    def complete_finalization(self, session_id: str) -> bool:
        """최종화 완료"""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.status = SessionStatus.FINALIZED
        session.phase = Phase.FINALIZED
        session.updated_at = datetime.utcnow()
        return True
    
    def get_current_agent(self, session_id: str) -> Optional[str]:
        """현재 phase에 해당하는 에이전트 반환"""
        session = self._sessions.get(session_id)
        return session.get_current_agent() if session else None


# 싱글톤 인스턴스
state_machine = StateMachine()
