"""
API 라우트 정의
"""
import asyncio
import logging
import uuid
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from models.session import Session, SessionStatus, Category, Phase
from models.case_file import CaseFile
from orchestrator.state_machine import state_machine
from orchestrator.turn_manager import turn_manager
from orchestrator.stop_detector import stop_detector, StopConfidence
from agents.base_agent import gemini_client
from agents.agent1_planner import Agent1Planner
from agents.agent2_critic import Agent2Critic
from storage import supabase_client as db
from .events import sse_event_manager, EventType

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# 에이전트 인스턴스
agent1 = Agent1Planner(gemini_client)
agent2 = Agent2Critic(gemini_client)


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


# Supabase 기반 세션 저장소 (인메모리 제거)
# sessions_store와 case_files_store는 더 이상 사용하지 않음


async def run_agent1_turn(session_id: str, topic: str, category: str):
    """
    Agent 1 (구현계획 전문가) 턴 실행
    
    세션 생성 후 자동으로 호출되어 첫 대화를 시작합니다.
    """
    logger.info(f"[Agent1Turn] 시작 - session_id={session_id}, topic={topic}, category={category}")
    
    try:
        # Supabase에서 세션 조회
        session_data = await db.get_session(session_id)
        if not session_data:
            logger.error(f"[Agent1Turn] 세션을 찾을 수 없음 - session_id={session_id}")
            return
        
        logger.info(f"[Agent1Turn] 세션 조회 성공 - status={session_data.get('status')}, round={session_data.get('round_index')}")
        
        # CaseFile 조회
        case_file_data = await db.get_case_file(session_id)
        case_file_summary = ""
        if case_file_data:
            # CaseFile 요약 생성
            decisions = case_file_data.get('decisions', [])
            open_issues = case_file_data.get('open_issues', [])
            case_file_summary = f"결정사항: {'; '.join(decisions[-3:])}. 미해결: {'; '.join(open_issues[-3:])}"
        logger.info(f"[Agent1Turn] CaseFile 조회 - found={case_file_data is not None}")
        
        # 라운드 인덱스 업데이트
        new_round_index = (session_data.get('round_index', 0) or 0) + 1
        await db.update_session(session_id, {
            "round_index": new_round_index,
            "phase": "agent1_turn"
        })
        logger.info(f"[Agent1Turn] 라운드 시작됨 - round_index={new_round_index}")
        
        await sse_event_manager.emit(
            session_id,
            EventType.ROUND_START,
            {"round_index": new_round_index}
        )
        logger.info(f"[Agent1Turn] ROUND_START 이벤트 발송 완료")
        
        # Agent 1 발언 시작 알림
        await sse_event_manager.emit(
            session_id,
            EventType.SPEAKER_CHANGE,
            {"active_speaker": "agent1"}
        )
        logger.info(f"[Agent1Turn] SPEAKER_CHANGE 이벤트 발송 완료")
        
        await sse_event_manager.emit(
            session_id,
            EventType.MESSAGE_STREAM_START,
            {"role": "agent1", "round_index": new_round_index, "phase": "agent1_turn"}
        )
        logger.info(f"[Agent1Turn] MESSAGE_STREAM_START 이벤트 발송 완료")
        
        # Agent 1 실행 (스트리밍)
        logger.info(f"[Agent1Turn] Gemini API 호출 시작")
        full_response = ""
        chunk_count = 0
        async for chunk in agent1.stream_response(
            messages=[],
            user_message=f"주제: {topic}",
            case_file_summary=case_file_summary,
            category=category
        ):
            full_response += chunk
            chunk_count += 1
            await sse_event_manager.emit(
                session_id,
                EventType.MESSAGE_STREAM_CHUNK,
                {"text": chunk}
            )
        logger.info(f"[Agent1Turn] 스트리밍 완료 - chunks={chunk_count}, response_len={len(full_response)}")
        
        # 스트리밍 종료 알림
        await sse_event_manager.emit(
            session_id,
            EventType.MESSAGE_STREAM_END,
            {"message_id": f"agent1-{session_id}-{new_round_index}"}
        )
        logger.info(f"[Agent1Turn] MESSAGE_STREAM_END 이벤트 발송 완료")
        
        # 메시지 저장
        await db.save_message(session_id, {
            "role": "agent1",
            "content_text": full_response,
            "round_index": new_round_index,
            "phase": "agent1_turn"
        })
        logger.info(f"[Agent1Turn] 메시지 저장 완료")
        
    except Exception as e:
        logger.error(f"[Agent1Turn] 오류 발생 - {type(e).__name__}: {str(e)}", exc_info=True)
        await sse_event_manager.emit(
            session_id,
            EventType.ERROR,
            {"error": str(e)}
        )


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session_endpoint(request: CreateSessionRequest, background_tasks: BackgroundTasks):
    """
    새 토론 세션 생성
    
    세션 생성 후 Agent 1이 자동으로 첫 발언을 시작합니다.
    """
    logger.info(f"[CreateSession] 요청 수신 - category={request.category}, topic={request.topic}")
    
    # 카테고리 검증
    if request.category not in ["newbiz", "marketing", "dev", "domain"]:
        logger.error(f"[CreateSession] 잘못된 카테고리 - {request.category}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {request.category}. Valid: newbiz, marketing, dev, domain"
        )
    
    try:
        # Supabase에 세션 생성 (user_id는 NULL - 익명 세션)
        session_data = await db.create_session(
            user_id=None,
            category=request.category,
            topic=request.topic
        )
        
        if not session_data:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        session_id = session_data["id"]
        logger.info(f"[CreateSession] 세션 생성됨 - session_id={session_id}")
        
        # CaseFile 초기화
        await db.save_case_file(session_id, {
            "facts": [],
            "goals": [],
            "constraints": [],
            "decisions": [],
            "open_issues": [],
            "assumptions": [],
            "next_experiments": []
        })
        logger.info(f"[CreateSession] CaseFile 초기화됨")
        
        # Agent 1 자동 시작 (백그라운드)
        logger.info(f"[CreateSession] 백그라운드 태스크 등록 시작 - run_agent1_turn")
        background_tasks.add_task(run_agent1_turn, session_id, request.topic, request.category)
        logger.info(f"[CreateSession] 백그라운드 태스크 등록 완료")
        
        return CreateSessionResponse(
            session_id=session_id,
            category=session_data["category"],
            topic=session_data["topic"],
            status=session_data["status"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CreateSession] 오류 발생 - {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(session_id: str):
    """
    세션 상태 조회
    """
    try:
        session_data = await db.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            id=session_data["id"],
            status=session_data["status"],
            category=session_data["category"],
            topic=session_data["topic"],
            round_index=session_data.get("round_index", 0) or 0,
            phase=session_data.get("phase", "idle") or "idle"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GetSession] 오류 발생 - {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



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
