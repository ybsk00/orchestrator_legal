"""
API 라우트 정의
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from models.session import Session, SessionStatus, Category, Phase
from models.case_file import CaseFile
from orchestrator.state_machine import state_machine
from orchestrator.turn_manager import turn_manager
from orchestrator.stop_detector import stop_detector, StopConfidence
from .events import sse_event_manager, EventType

router = APIRouter(prefix="/api")


# Request/Response 모델
class CreateSessionRequest(BaseModel):
    category: str
    topic: str


class CreateSessionResponse(BaseModel):
    session_id: str
    category: str
    topic: str
    status: str


class UserMessageRequest(BaseModel):
    message: str


class UserMessageResponse(BaseModel):
    status: str
    round_index: Optional[int] = None
    phase: Optional[str] = None
    stop_confidence: Optional[str] = None
    trigger: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    status: str
    category: str
    topic: str
    round_index: int
    phase: str


# 세션 저장소 (인메모리)
sessions_store: dict[str, Session] = {}
case_files_store: dict[str, CaseFile] = {}


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    새 토론 세션 생성
    """
    # 카테고리 검증
    try:
        category = Category(request.category)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {request.category}. Valid: newbiz, marketing, dev, domain"
        )
    
    # 세션 생성
    session = Session(
        category=category,
        topic=request.topic
    )
    
    # 상태 머신에 등록
    state_machine.create_session(session)
    sessions_store[session.id] = session
    
    # CaseFile 초기화
    case_file = CaseFile(session_id=session.id)
    case_files_store[session.id] = case_file
    
    return CreateSessionResponse(
        session_id=session.id,
        category=session.category,
        topic=session.topic,
        status=session.status
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """
    세션 상태 조회
    """
    session = state_machine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=session.id,
        status=session.status,
        category=session.category,
        topic=session.topic,
        round_index=session.round_index,
        phase=session.phase
    )


@router.post("/sessions/{session_id}/messages", response_model=UserMessageResponse)
async def send_message(session_id: str, request: UserMessageRequest):
    """
    사용자 메시지 전송 & 토론 시작
    
    - 조기 종료 감지
    - 새 라운드 시작 또는 진행 중 라운드 처리
    """
    session = state_machine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 최종화 중이면 거부
    if session.status == SessionStatus.FINALIZING:
        raise HTTPException(
            status_code=409,
            detail="Session is finalizing. Wait for completion or start a new session."
        )
    
    if session.status == SessionStatus.FINALIZED:
        raise HTTPException(
            status_code=409,
            detail="Session is already finalized. Start a new session."
        )
    
    # 조기 종료 감지
    stop_confidence, trigger = stop_detector.detect(request.message)
    
    if stop_confidence == StopConfidence.COMMAND:
        # 명령어로 확실한 종료 → 즉시 최종화
        state_machine.force_finalize(session_id)
        await sse_event_manager.emit(
            session_id,
            EventType.FINALIZE_START,
            {"reason": "user_command", "trigger": trigger}
        )
        return UserMessageResponse(
            status="finalizing",
            stop_confidence=stop_confidence.value,
            trigger=trigger
        )
    
    if stop_confidence == StopConfidence.KEYWORD:
        # 키워드 감지 → 확인 필요
        await sse_event_manager.emit(
            session_id,
            EventType.STOP_CONFIRM,
            {"trigger": trigger, "message": "토론을 마무리할까요?"}
        )
        return UserMessageResponse(
            status="confirm_stop",
            stop_confidence=stop_confidence.value,
            trigger=trigger
        )
    
    # 정상 메시지 처리
    if session.phase == Phase.IDLE:
        # 새 라운드 시작
        success = state_machine.start_new_round(session_id)
        if not success:
            # 3라운드 완료 → 자동 최종화
            await sse_event_manager.emit(
                session_id,
                EventType.FINALIZE_START,
                {"reason": "round_limit_reached"}
            )
            return UserMessageResponse(
                status="finalizing",
                round_index=session.round_index,
                phase=session.phase
            )
        
        await sse_event_manager.emit(
            session_id,
            EventType.ROUND_START,
            {"round_index": session.round_index}
        )
    
    # TODO: 실제 에이전트 턴 실행 로직 추가
    
    return UserMessageResponse(
        status="processing",
        round_index=session.round_index,
        phase=session.phase
    )


@router.post("/sessions/{session_id}/finalize")
async def force_finalize(session_id: str):
    """
    조기 종료 요청 (마무리 버튼)
    """
    session = state_machine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=409,
            detail=f"Session cannot be finalized. Current status: {session.status}"
        )
    
    state_machine.force_finalize(session_id)
    await sse_event_manager.emit(
        session_id,
        EventType.FINALIZE_START,
        {"reason": "user_button"}
    )
    
    # TODO: Agent3 Finalizer 실행 로직 추가
    
    return {"status": "finalizing", "session_id": session_id}


@router.post("/sessions/{session_id}/confirm-stop")
async def confirm_stop(session_id: str, confirmed: bool):
    """
    키워드 종료 확인 응답
    """
    session = state_machine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if confirmed:
        state_machine.force_finalize(session_id)
        await sse_event_manager.emit(
            session_id,
            EventType.FINALIZE_START,
            {"reason": "user_confirmed_keyword"}
        )
        return {"status": "finalizing"}
    else:
        return {"status": "continue"}


@router.get("/sessions/{session_id}/stream")
async def stream_events(
    session_id: str,
    last_event_id: Optional[int] = Query(None, alias="lastEventId")
):
    """
    SSE 스트림 연결
    
    - Last-Event-ID 지원으로 재연결 시 이벤트 복구
    """
    session = state_machine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return StreamingResponse(
        sse_event_manager.stream_events(session_id, last_event_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/sessions/{session_id}/report")
async def get_final_report(session_id: str):
    """
    최종 리포트 조회
    """
    session = state_machine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != SessionStatus.FINALIZED:
        raise HTTPException(
            status_code=400,
            detail=f"Report not ready. Session status: {session.status}"
        )
    
    # TODO: FinalReport 저장소에서 조회
    
    return {"message": "Report endpoint - to be implemented"}
