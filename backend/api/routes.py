"""
API Routes (v2.2)

핵심 변경:
- Phase 기반 실행 (turn_index → phase)
- WAIT_USER에서 사용자 입력 대기
- current_round=0 초기화, 사용자 입력 시 round++
- 라운드별 에이전트 프롬프트 설정
"""
import asyncio
import logging
import uuid
import httpx
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from orchestrator.state_machine import (
    Phase, MAX_ROUNDS, 
    get_next_phase, get_agent_for_phase, get_round_for_phase,
    get_round_start_phase, is_wait_user_phase, is_final_phase,
    state_machine
)
from orchestrator.turn_manager import turn_manager, get_phase_config
from agents.base_agent import gemini_client
from agents.agent1_planner import Agent1Planner
from agents.agent2_critic import Agent2Critic
from agents.agent3_synthesizer import Agent3Synthesizer
from agents.verifier import VerifierAgent
from storage import supabase_client as db
from .events import sse_event_manager, EventType
from config import BASE_URL

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# 에이전트 인스턴스
agents = {
    "agent1": Agent1Planner(gemini_client),
    "agent2": Agent2Critic(gemini_client),
    "agent3": Agent3Synthesizer(gemini_client),
    "verifier": VerifierAgent(gemini_client),
}


# Request/Response 모델
class CreateSessionRequest(BaseModel):
    category: str
    topic: str
    user_id: Optional[str] = None


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


class SessionResponse(BaseModel):
    id: str
    status: str
    category: str
    topic: str
    round_index: int
    phase: str


# Phase 실행 함수
async def execute_phase(session_id: str, phase: str, config: dict) -> str:
    """
    단일 phase를 실행합니다.
    
    Args:
        session_id: 세션 ID
        phase: 현재 phase
        config: phase 설정 (description, max_chars)
    
    Returns:
        에이전트 응답 텍스트
    """
    agent_name = get_agent_for_phase(phase)
    current_round = get_round_for_phase(phase)
    
    if not agent_name:
        logger.error(f"No agent for phase: {phase}")
        return ""
    
    agent = agents.get(agent_name)
    if not agent:
        logger.error(f"Agent not found: {agent_name}")
        return ""
    
    # 라운드 설정 (Agent2/Agent3/Verifier)
    if hasattr(agent, 'set_round'):
        agent.set_round(current_round)
    
    # 세션 및 CaseFile 조회
    session_data = await db.get_session(session_id)
    case_file_data = await db.get_case_file(session_id)
    
    # 이전 대화 맥락 구성
    case_file_summary = ""
    criticisms_last_round = ""
    
    if case_file_data:
        decisions = case_file_data.get('decisions', [])
        open_issues = case_file_data.get('open_issues', [])
        case_file_summary = f"결정사항: {'; '.join(decisions[-3:])}. 미해결: {'; '.join(open_issues[-3:])}"
        
        # Agent2용 이전 비판 목록
        criticisms = case_file_data.get('criticisms_last_round', [])
        if criticisms:
            criticisms_last_round = ", ".join(criticisms)
    
    # 이벤트 발송
    await sse_event_manager.emit(session_id, EventType.SPEAKER_CHANGE, {"active_speaker": agent_name})
    await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_START, {
        "role": agent_name,
        "round_index": current_round,
        "phase": phase
    })
    
    # 프롬프트 구성
    prompt = agent.system_prompt
    prompt = prompt.replace("{{max_chars}}", str(config.get("max_chars", 300)))
    prompt = prompt.replace("{{category}}", session_data.get("category", "general"))
    prompt = prompt.replace("{{topic}}", session_data.get("topic", ""))
    prompt = prompt.replace("{{case_file_summary}}", case_file_summary)
    prompt = prompt.replace("{{criticisms_last_round}}", criticisms_last_round)
    
    # 스트리밍 실행
    full_response = ""
    try:
        async for chunk in agent.stream_response(
            messages=[],
            user_message=f"주제: {session_data.get('topic')}",
            case_file_summary=case_file_summary,
            category=session_data.get("category", "general")
        ):
            full_response += chunk
            await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_CHUNK, {"text": chunk})
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        full_response = f"[오류 발생: {str(e)}]"
    
    # 스트리밍 종료
    await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_END, {
        "message_id": f"{agent_name}-{session_id}-{phase}"
    })
    
    # 메시지 저장
    await db.save_message(session_id, {
        "role": agent_name,
        "content_text": full_response,
        "round_index": current_round,
        "phase": phase
    })
    
    # Agent2 리스크 태그 추출 및 저장
    if agent_name == "agent2":
        tags = extract_risk_tags(full_response)
        if tags:
            await update_criticisms(session_id, tags)
    
    return full_response


def extract_risk_tags(response: str) -> List[str]:
    """응답에서 리스크 태그 추출"""
    import re
    tags = []
    # [태그] 형태 추출
    matches = re.findall(r'\[(\w+)\]', response)
    for match in matches:
        match_lower = match.lower()
        if match_lower in ['compliance', 'security', 'data_quality', 'cost', 'timeline', 
                           'ux', 'ops', 'deliverability', 'tracking', 'integration']:
            tags.append(match_lower)
    return list(set(tags))


async def update_criticisms(session_id: str, new_tags: List[str]):
    """CaseFile에 비판 태그 업데이트"""
    case_file = await db.get_case_file(session_id)
    if not case_file:
        return
    
    # 세션 누적
    criticisms_so_far = case_file.get('criticisms_so_far', [])
    for tag in new_tags:
        if tag not in criticisms_so_far:
            criticisms_so_far.append(tag)
    
    # 이번 라운드 태그
    await db.save_case_file(session_id, {
        **case_file,
        'criticisms_so_far': criticisms_so_far,
        'criticisms_last_round': new_tags
    })


async def execute_round(session_id: str, current_round: int):
    """
    라운드 내 모든 phase를 순차 실행합니다.
    """
    # 라운드 시작 phase
    phase = get_round_start_phase(current_round)
    if not phase:
        logger.error(f"Invalid round: {current_round}")
        await db.update_session(session_id, {"phase": Phase.FINALIZE_DONE.value, "status": "finalized"})
        await sse_event_manager.emit(session_id, EventType.SESSION_END, {})
        return
    
    gate_status = None
    
    # Phase 순차 실행
    while not is_wait_user_phase(phase) and not is_final_phase(phase):
        # 세션 상태 업데이트
        await db.update_session(session_id, {
            "phase": phase,
            "round_index": current_round
        })
        
        # 라운드 시작 이벤트 (첫 phase에서만)
        if phase == get_round_start_phase(current_round):
            await sse_event_manager.emit(session_id, EventType.ROUND_START, {"round_index": current_round})
        
        # Phase 설정 가져오기
        config = get_phase_config(phase)
        
        logger.info(f"[ExecuteRound] Executing phase={phase}, round={current_round}")
        
        # Phase 실행
        result = await execute_phase(session_id, phase, config)
        
        # Verifier gate 결과 추출
        if "V_R2_GATE" in phase or "V_R3_SIGNOFF" in phase:
            gate_status = extract_gate_status(result)
        
        # 다음 phase로 전이
        phase = get_next_phase(phase, gate_status)
    
    # 라운드 종료
    await db.update_session(session_id, {"phase": phase})
    
    if is_final_phase(phase):
        # 최종 리포트 저장
        messages = await db.get_messages(session_id)
        last_message = messages[-1] if messages else None
        if last_message:
            await db.save_final_report(
                session_id, 
                {"content": last_message.get("content_text", "")},
                last_message.get("content_text", "")
            )
        
        await db.update_session(session_id, {"status": "finalized"})
        await sse_event_manager.emit(session_id, EventType.SESSION_END, {})
    else:
        # WAIT_USER
        await sse_event_manager.emit(session_id, EventType.ROUND_END, {"round_index": current_round})


def extract_gate_status(response: str) -> Optional[str]:
    """Verifier 응답에서 gate_status 추출"""
    response_lower = response.lower()
    if "no-go" in response_lower or "no go" in response_lower or "rejected" in response_lower:
        return "No-Go"
    elif "conditional" in response_lower:
        return "Conditional"
    elif "approved" in response_lower or "go" in response_lower:
        return "Go"
    return None


# === 엔드포인트 ===

@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session_endpoint(request: CreateSessionRequest, background_tasks: BackgroundTasks):
    """
    새 토론 세션 생성 (v2.2)
    
    - current_round = 0
    - phase = WAIT_USER
    - 사용자 첫 메시지 대기
    """
    try:
        # Supabase에 세션 생성
        session_data = await db.create_session(
            user_id=request.user_id,
            category=request.category,
            topic=request.topic
        )
        
        if not session_data:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        session_id = session_data["id"]
        
        # 초기 상태 설정 (v2.2: current_round=0, phase=WAIT_USER)
        await db.update_session(session_id, {
            "round_index": 0,
            "phase": Phase.WAIT_USER.value,
            "status": "active"
        })
        
        # CaseFile 초기화 (기존 스키마 필드만 사용)
        await db.save_case_file(session_id, {
            "facts": [], "goals": [], "constraints": [], "decisions": [], 
            "open_issues": [], "assumptions": [], "next_experiments": []
        })
        
        # 첫 번째 라운드 자동 시작 (사용자 입력 없이 바로 시작)
        background_tasks.add_task(start_round, session_id)
        
        return CreateSessionResponse(
            session_id=session_id,
            category=session_data["category"],
            topic=session_data["topic"],
            status="active"
        )
        
    except Exception as e:
        logger.error(f"[CreateSession] 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def start_round(session_id: str):
    """라운드 시작 (current_round 증가 후 실행)"""
    session = await db.get_session(session_id)
    if not session:
        return
    
    current_round = session.get("round_index", 0) + 1
    
    if current_round > MAX_ROUNDS:
        # 라운드 제한 도달
        await db.update_session(session_id, {
            "phase": Phase.FINALIZE_DONE.value,
            "status": "finalized"
        })
        await sse_event_manager.emit(session_id, EventType.SESSION_END, {})
        return
    
    # 라운드 증가
    await db.update_session(session_id, {
        "round_index": current_round,
        "status": "active"
    })
    
    # 라운드 실행
    await execute_round(session_id, current_round)


@router.post("/sessions/{session_id}/message", response_model=UserMessageResponse)
async def send_message_endpoint(session_id: str, request: UserMessageRequest, background_tasks: BackgroundTasks):
    """
    사용자 메시지 수신 (v2.2)
    
    WAIT_USER 상태에서만 다음 라운드 트리거
    """
    try:
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        current_phase = session.get("phase", "")
        
        # WAIT_USER가 아니면 버퍼에 저장
        if not is_wait_user_phase(current_phase):
            state_machine.buffer_input(session_id, request.message)
            return UserMessageResponse(
                status="buffered",
                round_index=session.get("round_index"),
                phase=current_phase
            )
        
        # 사용자 메시지 저장
        await db.save_message(session_id, {
            "role": "user",
            "content_text": request.message,
            "round_index": session.get("round_index"),
            "phase": "user_input"
        })
        
        # 다음 라운드 시작
        background_tasks.add_task(start_round, session_id)
        
        return UserMessageResponse(
            status="round_started",
            round_index=session.get("round_index", 0) + 1,
            phase="starting"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SendMessage] 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(session_id: str):
    """세션 상태 조회"""
    try:
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            id=session["id"],
            status=session.get("status", "unknown"),
            category=session.get("category", ""),
            topic=session.get("topic", ""),
            round_index=session.get("round_index", 0),
            phase=session.get("phase", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GetSession] 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions_endpoint(user_id: Optional[str] = Query(None)):
    """세션 목록 조회 (user_id로 필터링 가능)"""
    try:
        sessions = await db.list_sessions(user_id)
        return [
            SessionResponse(
                id=s["id"],
                status=s.get("status", "unknown"),
                category=s.get("category", ""),
                topic=s.get("topic", ""),
                round_index=s.get("round_index", 0) or 0,
                phase=s.get("phase", "idle") or "idle"
            ) for s in sessions
        ]
    except Exception as e:
        logger.error(f"[ListSessions] 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/events")
async def session_events_endpoint(session_id: str):
    """SSE 이벤트 스트림"""
    return StreamingResponse(
        sse_event_manager.subscribe(session_id),
        media_type="text/event-stream"
    )


class FinalReportResponse(BaseModel):
    report_json: Optional[dict] = None
    report_md: Optional[str] = None


@router.get("/sessions/{session_id}/report", response_model=FinalReportResponse)
async def get_final_report(session_id: str):
    """최종 리포트 조회"""
    report = await db.get_final_report(session_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/sessions/{session_id}/report/generate", response_model=FinalReportResponse)
async def generate_report(session_id: str):
    """최종 리포트 생성 (On-Demand)"""
    # 세션 및 메시지 조회
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await db.get_messages(session_id)
    if not messages:
        raise HTTPException(status_code=400, detail="No messages to summarize")

    # 프롬프트 구성
    conversation_text = ""
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content_text", "")
        conversation_text += f"{role}: {content}\n\n"

    prompt = f"""
    다음은 AI 에이전트들이 나눈 토론 내용입니다.
    이 내용을 바탕으로 최종 결론 보고서를 작성해주세요.
    
    [토론 내용]
    {conversation_text}
    
    [작성 양식]
    1. **종합 결론**: 토론의 핵심 결과 요약
    2. **실행 방안**: 구체적인 실행 단계 및 계획
    3. **구현 방향**: 기술적/실무적 구현 가이드
    
    분량은 공백 포함 1500자 내외로 상세하게 작성해주세요.
    """

    # Gemini 호출
    try:
        response = await gemini_client.generate_content(prompt)
        report_content = response.text
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

    # 저장
    report_json = {"content": report_content}
    await db.save_final_report(session_id, report_json, report_content)
    
    return {"report_json": report_json, "report_md": report_content}
