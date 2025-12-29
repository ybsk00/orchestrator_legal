"""
턴 관리자 - 동시성 제어 및 턴 실행

핵심 보완사항 반영:
- 세션별 락으로 동시에 1턴만 실행
- 최종화 중 추가 메시지 거부
- 취소된 세션 처리
"""
import asyncio
from typing import Callable, Any, Optional

from models.session import SessionStatus
from .state_machine import state_machine


class TurnManager:
    """
    턴 실행 관리자
    
    - 세션별 락으로 동시에 1턴만 실행
    - 최종화 중 추가 메시지 거부
    - 취소 토큰 확인
    """
    
    async def execute_turn(
        self, 
        session_id: str, 
        turn_func: Callable[[], Any]
    ) -> Optional[Any]:
        """
        세션별 락으로 동시에 1턴만 실행
        
        Args:
            session_id: 세션 ID
            turn_func: 실행할 턴 함수
            
        Returns:
            턴 실행 결과 또는 None (취소/거부 시)
            
        Raises:
            RuntimeError: 최종화 중 추가 메시지 거부
        """
        session = state_machine.get_session(session_id)
        lock = state_machine.get_lock(session_id)
        
        if not session or not lock:
            raise ValueError(f"Session not found: {session_id}")
        
        # 최종화 중이면 추가 메시지 거부
        if session.status == SessionStatus.FINALIZING:
            raise RuntimeError("Session is finalizing, no more messages allowed")
        
        if session.status == SessionStatus.FINALIZED:
            raise RuntimeError("Session is already finalized")
        
        async with lock:
            # 락 획득 후 다시 확인 (레이스 컨디션 방지)
            if state_machine.is_aborted(session_id):
                return None
            
            try:
                result = await turn_func()
                return result
            except asyncio.CancelledError:
                # 조기 종료로 인한 취소
                return None
    
    async def execute_finalization(
        self,
        session_id: str,
        finalize_func: Callable[[], Any]
    ) -> Optional[Any]:
        """
        최종화 실행 (Agent3 Finalizer)
        
        Args:
            session_id: 세션 ID
            finalize_func: 최종화 함수
            
        Returns:
            최종 리포트 또는 None
        """
        session = state_machine.get_session(session_id)
        lock = state_machine.get_lock(session_id)
        
        if not session or not lock:
            raise ValueError(f"Session not found: {session_id}")
        
        async with lock:
            try:
                result = await finalize_func()
                state_machine.complete_finalization(session_id)
                return result
            except Exception as e:
                # 최종화 실패 시에도 상태는 finalized로
                state_machine.complete_finalization(session_id)
                raise e


# 싱글톤 인스턴스
turn_manager = TurnManager()
